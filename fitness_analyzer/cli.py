"""Command-line entry point: ties loading, analysis and reporting together."""

import argparse
import sys
from pathlib import Path

from .analysis import analyse_session
from .exceptions import DataFileError
from .loader import load_participants, load_sessions
from .reports import write_all_reports

DEFAULT_PROFILES = Path("data") / "participants.csv"
DEFAULT_SESSIONS = [Path("data") / "fitness_sessions.csv",
                    Path("data") / "fitness_sessions_invalid.csv"]
DEFAULT_OUTPUT = Path("output")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyse wearable fitness sessions against participant baselines.")
    parser.add_argument("--profiles", type=Path, default=DEFAULT_PROFILES,
                        help="participants CSV file (default: %(default)s)")
    parser.add_argument("--sessions", type=Path, nargs="+", default=DEFAULT_SESSIONS,
                        help="one or more session CSV files (default: both official files)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="output directory, created if missing (default: %(default)s)")
    return parser


def run(profiles: Path, session_files: list, output_dir: Path) -> dict:
    """Run the whole pipeline. Returns a small dict with the counts so it
    is easy to test. Raises DataFileError if the participants file cannot
    be used, because no session can be analysed without it."""
    participants, rejected = load_participants(profiles)
    accepted_participants = len(participants)

    sessions = {}
    accepted_rows = 0
    file_errors = []
    for path in session_files:
        try:
            accepted, file_rejected = load_sessions(path, participants, sessions)
        except DataFileError as err:
            # One bad session file should not stop the others.
            file_errors.append(str(err))
            continue
        accepted_rows += accepted
        rejected.extend(file_rejected)

    results = [analyse_session(sessions[sid]) for sid in sorted(sessions)]
    input_files = [str(profiles)] + [str(p) for p in session_files]
    created = write_all_reports(results, rejected, file_errors, output_dir, input_files)

    return {
        "participants": accepted_participants,
        "accepted_rows": accepted_rows,
        "rejected_rows": len({(r.source, r.row_number) for r in rejected}),
        "sessions": len(results),
        "file_errors": file_errors,
        "created_files": created,
    }


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = run(args.profiles, args.sessions, args.output)
    except DataFileError as err:
        print(f"Error: cannot continue without the participants file - {err}", file=sys.stderr)
        return 1
    except (PermissionError, FileExistsError, NotADirectoryError) as err:
        print(f"Error: could not write reports to '{args.output}': {err}", file=sys.stderr)
        return 1

    print("Analysis complete.")
    print(f"  Participants loaded: {summary['participants']}")
    print(f"  Accepted session rows: {summary['accepted_rows']}")
    print(f"  Rejected rows: {summary['rejected_rows']}")
    print(f"  Sessions analysed: {summary['sessions']}")
    for error in summary["file_errors"]:
        print(f"  Skipped file: {error}")
    print("  Created files:")
    for path in summary["created_files"]:
        print(f"    - {path}")
    return 0
