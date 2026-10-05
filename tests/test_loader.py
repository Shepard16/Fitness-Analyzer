import tempfile
import unittest
from pathlib import Path

from fitness_analyzer.exceptions import DataFileError
from fitness_analyzer.loader import load_participants, load_sessions

from .helpers import (PARTICIPANTS, SESSION_HEADER, SESSIONS, SESSIONS_INVALID,
                      session_row, write_csv)


class TestOfficialFiles(unittest.TestCase):
    def setUp(self):
        self.participants, rejected = load_participants(PARTICIPANTS)
        self.assertEqual(rejected, [])

    def test_participants_loaded(self):
        self.assertEqual(sorted(self.participants), ["P001", "P002", "P003"])
        self.assertEqual(self.participants["P001"].baseline_heart_rate, 68.0)

    def test_valid_file_all_rows_accepted(self):
        sessions = {}
        accepted, rejected = load_sessions(SESSIONS, self.participants, sessions)
        self.assertEqual(accepted, 29)
        self.assertEqual(rejected, [])
        self.assertEqual(len(sessions), 5)
        self.assertIs(sessions["FIT-2026-004"].participant, self.participants["P001"])

    def test_invalid_file_rows_rejected_with_context(self):
        sessions = {}
        accepted, rejected = load_sessions(SESSIONS_INVALID, self.participants, sessions)
        self.assertEqual(accepted, 1)
        self.assertEqual(len({r.row_number for r in rejected}), 10)
        by_row = {(r.row_number, r.field) for r in rejected}
        self.assertIn((3, "heart_rate"), by_row)        # "fast"
        self.assertIn((4, "participant_id"), by_row)    # "001"
        self.assertIn((8, "participant_id"), by_row)    # unknown P999
        self.assertIn((12, "row"), by_row)              # short row
        self.assertTrue(all(r.source == "fitness_sessions_invalid.csv" for r in rejected))


class TestFileProblems(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.participants, _ = load_participants(PARTICIPANTS)

    def tearDown(self):
        self.tmp.cleanup()

    def test_missing_file_raises_data_file_error(self):
        with self.assertRaises(DataFileError) as ctx:
            load_sessions(self.dir / "does_not_exist.csv", self.participants, {})
        self.assertIn("not found", str(ctx.exception))
        self.assertIsInstance(ctx.exception.__cause__, FileNotFoundError)

    def test_missing_column_raises_data_file_error(self):
        path = write_csv(self.dir, "bad_header.csv",
                         ["session_id,participant_id,timestamp", "FIT-2026-001,P001,0"])
        with self.assertRaises(DataFileError) as ctx:
            load_sessions(path, self.participants, {})
        self.assertIn("heart_rate", str(ctx.exception))

    def test_empty_file_raises_data_file_error(self):
        path = write_csv(self.dir, "empty.csv", [])
        path.write_text("", encoding="utf-8")
        with self.assertRaises(DataFileError):
            load_sessions(path, self.participants, {})

    def test_duplicate_timestamp_rejected(self):
        path = write_csv(self.dir, "dupes.csv",
                         [SESSION_HEADER, session_row(t=0), session_row(t=0)])
        accepted, rejected = load_sessions(path, self.participants, {})
        self.assertEqual(accepted, 1)
        self.assertEqual(rejected[0].field, "timestamp")
        self.assertEqual(rejected[0].row_number, 3)

    def test_session_cannot_switch_participant(self):
        path = write_csv(self.dir, "mixed.csv",
                         [SESSION_HEADER, session_row(pid="P001", t=0),
                          session_row(pid="P002", t=1)])
        accepted, rejected = load_sessions(path, self.participants, {})
        self.assertEqual(accepted, 1)
        self.assertEqual(rejected[0].field, "participant_id")

    def test_blank_lines_are_ignored(self):
        path = write_csv(self.dir, "blank.csv", [SESSION_HEADER, session_row(t=0), "",
                                                 session_row(t=1)])
        accepted, rejected = load_sessions(path, self.participants, {})
        self.assertEqual((accepted, rejected), (2, []))


if __name__ == "__main__":
    unittest.main()
