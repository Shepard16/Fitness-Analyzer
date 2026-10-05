import unittest

from fitness_analyzer.analysis import (MIN_USABLE_OBSERVATIONS, analyse_session,
                                       classify_intensity, detect_recovery)
from fitness_analyzer.loader import load_participants, load_sessions
from fitness_analyzer.models import Observation, Participant, Session

from .helpers import PARTICIPANTS, SESSIONS


def make_session(heart_rates, activity=None, quality=0.95, baseline=70):
    participant = Participant("P001", "Test", baseline, 1.2, 32.5)
    session = Session("FIT-2026-900", participant)
    activity = activity or [0.5] * len(heart_rates)
    for t, (hr, act) in enumerate(zip(heart_rates, activity)):
        session.add_observation(Observation(t, hr, 1.5, 33.0, act, quality))
    return session


class TestClassification(unittest.TestCase):
    def test_intensity_boundaries(self):
        self.assertEqual(classify_intensity(-15.1), "below baseline")
        self.assertEqual(classify_intensity(-15.0), "resting")
        self.assertEqual(classify_intensity(14.9), "resting")
        self.assertEqual(classify_intensity(15.0), "moderate activity")
        self.assertEqual(classify_intensity(49.9), "moderate activity")
        self.assertEqual(classify_intensity(50.0), "high activity")

    def test_official_sessions(self):
        participants, _ = load_participants(PARTICIPANTS)
        sessions = {}
        load_sessions(SESSIONS, participants, sessions)
        expected = {
            "FIT-2026-001": "resting",
            "FIT-2026-002": "moderate activity",
            "FIT-2026-003": "high activity",
            "FIT-2026-004": "recovering",
            "FIT-2026-005": "insufficient data",
        }
        for sid, label in expected.items():
            with self.subTest(session=sid):
                self.assertEqual(analyse_session(sessions[sid])["classification"], label)


class TestInsufficientData(unittest.TestCase):
    def test_one_below_minimum_is_insufficient(self):
        result = analyse_session(make_session([70] * (MIN_USABLE_OBSERVATIONS - 1)))
        self.assertEqual(result["classification"], "insufficient data")
        self.assertIsNone(result["pct_above_baseline"])

    def test_exactly_minimum_is_enough(self):
        result = analyse_session(make_session([70] * MIN_USABLE_OBSERVATIONS))
        self.assertEqual(result["classification"], "resting")

    def test_low_signal_session_explains_why(self):
        result = analyse_session(make_session([70, 72, 74, 76], quality=0.3))
        self.assertEqual(result["classification"], "insufficient data")
        self.assertEqual(result["low_signal_observations"], 4)
        self.assertIn("signal quality", result["reasons"][0])


class TestRecovery(unittest.TestCase):
    def test_clear_recovery(self):
        session = make_session([80, 140, 150, 120, 95, 80], [0.3, 0.9, 0.9, 0.6, 0.3, 0.2])
        recovering, _ = detect_recovery(session.usable_observations, 70)
        self.assertTrue(recovering)

    def test_peak_at_end_is_not_recovery(self):
        session = make_session([80, 100, 120, 140, 150, 160])
        recovering, reason = detect_recovery(session.usable_observations, 70)
        self.assertFalse(recovering)
        self.assertIn("end", reason)

    def test_too_few_readings(self):
        session = make_session([150, 120, 90])
        self.assertFalse(detect_recovery(session.usable_observations, 70)[0])


if __name__ == "__main__":
    unittest.main()
