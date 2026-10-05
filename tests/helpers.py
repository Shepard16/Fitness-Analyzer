"""Shared helpers for the tests: paths to the official data and a way
to write small temporary CSV files."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PARTICIPANTS = DATA / "participants.csv"
SESSIONS = DATA / "fitness_sessions.csv"
SESSIONS_INVALID = DATA / "fitness_sessions_invalid.csv"

SESSION_HEADER = ("session_id,participant_id,timestamp,heart_rate,skin_response,"
                  "temperature,activity_level,signal_quality")


def write_csv(directory: Path, name: str, lines: list) -> Path:
    path = Path(directory) / name
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def session_row(session="FIT-2026-001", pid="P001", t=0, hr=70, skin=1.2,
                temp=32.5, activity=0.1, quality=0.95) -> str:
    return f"{session},{pid},{t},{hr},{skin},{temp},{activity},{quality}"
