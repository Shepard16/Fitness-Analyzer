"""Reading the CSV files into domain objects.

Error-handling idea:
- Problems with a *whole file* (missing, no permission, wrong header,
  not UTF-8) become a DataFileError. The caller decides whether the
  program can carry on without that file.
- Problems with a *single row* become RejectedRecord entries, and the
  loader simply moves on to the next row.
"""

import csv
from pathlib import Path

from .exceptions import DataFileError, InvalidRecordError
from .models import Observation, Participant, RejectedRecord, Session
from .validation import (PARTICIPANT_COLUMNS, SESSION_COLUMNS, is_valid_csv_filename,
                         parse_participant_row, parse_session_row)


def read_csv_rows(path: Path, expected_columns: list, rejected: list) -> list:
    """Return a list of (row_number, row_dict) for every row that has the
    right number of values. Rows with the wrong length are added to
    `rejected`. Raises DataFileError if the file cannot be used at all."""
    path = Path(path)
    if not is_valid_csv_filename(path.name):
        raise DataFileError(path, "file name must look like name.csv")

    rows = []
    try:
        with open(path, encoding="utf-8", newline="") as file:
            reader = csv.reader(file)
            header = next(reader, None)
            if header is None:
                raise DataFileError(path, "file is empty")
            header = [column.strip() for column in header]
            missing = [c for c in expected_columns if c not in header]
            if missing:
                raise DataFileError(path, f"missing required column(s): {', '.join(missing)}")

            try:
                for row in reader:
                    if not any(cell.strip() for cell in row):
                        continue  # ignore completely blank lines
                    if len(row) != len(header):
                        rejected.append(RejectedRecord(
                            path.name, reader.line_num, "row",
                            f"expected {len(header)} values but found {len(row)}"))
                        continue
                    rows.append((reader.line_num, dict(zip(header, row))))
            except csv.Error as err:
                # The csv module cannot reliably resume after a format error,
                # so we keep the rows read so far and stop reading this file.
                rejected.append(RejectedRecord(
                    path.name, reader.line_num, "row",
                    f"CSV format error, rest of file skipped: {err}"))
    except FileNotFoundError as err:
        raise DataFileError(path, "file not found") from err
    except PermissionError as err:
        raise DataFileError(path, "permission denied when opening the file") from err
    except UnicodeDecodeError as err:
        raise DataFileError(path, f"file is not valid UTF-8 text ({err.reason})") from err
    return rows


def _reject(rejected: list, source: str, row_number: int, error: InvalidRecordError) -> None:
    for field, reason in error.problems:
        rejected.append(RejectedRecord(source, row_number, field, reason))


def load_participants(path: Path) -> tuple:
    """Return ({participant_id: Participant}, [RejectedRecord])."""
    path = Path(path)
    rejected = []
    participants = {}
    for row_number, raw in read_csv_rows(path, PARTICIPANT_COLUMNS, rejected):
        try:
            values = parse_participant_row(raw)
            if values["participant_id"] in participants:
                raise InvalidRecordError(
                    ("participant_id", f"duplicate participant {values['participant_id']!r}"))
        except InvalidRecordError as err:
            _reject(rejected, path.name, row_number, err)
            continue
        participants[values["participant_id"]] = Participant(**values)
    return participants, rejected


def find_participant(participant_id: str, participants: dict) -> Participant:
    """Look up a participant, turning a KeyError into a record error."""
    try:
        return participants[participant_id]
    except KeyError:
        raise InvalidRecordError(
            ("participant_id", f"unknown participant {participant_id!r} "
                               "(not found in the participants file)")) from None


def load_sessions(path: Path, participants: dict, sessions: dict) -> tuple:
    """Read one session file and add its observations to `sessions`
    ({session_id: Session}). Passing the same dict for several files lets
    the program combine the valid and invalid files.

    Returns (number_of_accepted_rows, [RejectedRecord])."""
    path = Path(path)
    rejected = []
    accepted = 0

    for row_number, raw in read_csv_rows(path, SESSION_COLUMNS, rejected):
        try:
            values = parse_session_row(raw)
            participant = find_participant(values["participant_id"], participants)
            session = sessions.get(values["session_id"])
            if session is not None and session.participant is not participant:
                raise InvalidRecordError((
                    "participant_id",
                    f"session {session.session_id} already belongs to "
                    f"{session.participant.participant_id}, not {participant.participant_id}"))
            if session is not None and session.has_timestamp(values["timestamp"]):
                raise InvalidRecordError((
                    "timestamp", f"duplicate timestamp {values['timestamp']} "
                                 f"in session {session.session_id}"))
        except InvalidRecordError as err:
            _reject(rejected, path.name, row_number, err)
            continue

        if session is None:
            session = Session(values["session_id"], participant)
            sessions[session.session_id] = session
        session.add_observation(Observation(
            timestamp=values["timestamp"],
            heart_rate=values["heart_rate"],
            skin_response=values["skin_response"],
            temperature=values["temperature"],
            activity_level=values["activity_level"],
            signal_quality=values["signal_quality"],
        ))
        accepted += 1

    return accepted, rejected
