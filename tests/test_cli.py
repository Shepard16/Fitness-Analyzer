import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from fitness_analyzer.cli import main, run

from .helpers import PARTICIPANTS, SESSIONS, SESSIONS_INVALID


class TestEndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name) / "nested" / "output"   # does not exist yet

    def tearDown(self):
        self.tmp.cleanup()

    def test_creates_output_dir_and_files(self):
        summary = run(PARTICIPANTS, [SESSIONS, SESSIONS_INVALID], self.out)
        self.assertEqual(summary["accepted_rows"], 30)
        self.assertEqual(summary["rejected_rows"], 10)
        for name in ["analysis_summary.csv", "analysis_report.txt", "rejected_records.txt"]:
            self.assertTrue((self.out / name).is_file(), name)
        lines = (self.out / "analysis_summary.csv").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1 + 6)   # header + one row per session

    def test_second_run_gives_identical_output(self):
        run(PARTICIPANTS, [SESSIONS, SESSIONS_INVALID], self.out)
        first = {p.name: p.read_bytes() for p in self.out.iterdir()}
        run(PARTICIPANTS, [SESSIONS, SESSIONS_INVALID], self.out)
        second = {p.name: p.read_bytes() for p in self.out.iterdir()}
        self.assertEqual(first, second)

    def test_missing_session_file_is_skipped(self):
        missing = Path(self.tmp.name) / "missing.csv"
        summary = run(PARTICIPANTS, [missing, SESSIONS], self.out)
        self.assertEqual(summary["accepted_rows"], 29)
        self.assertEqual(len(summary["file_errors"]), 1)
        report = (self.out / "rejected_records.txt").read_text(encoding="utf-8")
        self.assertIn("missing.csv", report)

    def test_missing_participants_file_exits_with_error(self):
        stderr = io.StringIO()
        with redirect_stderr(stderr), redirect_stdout(io.StringIO()):
            code = main(["--profiles", str(Path(self.tmp.name) / "nope.csv"),
                         "--output", str(self.out)])
        self.assertEqual(code, 1)
        self.assertIn("not found", stderr.getvalue())

    def test_main_prints_summary(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = main(["--profiles", str(PARTICIPANTS), "--sessions", str(SESSIONS),
                         str(SESSIONS_INVALID), "--output", str(self.out)])
        self.assertEqual(code, 0)
        self.assertIn("Rejected rows: 10", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
