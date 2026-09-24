import unittest
from main import (
    Participant, Observation, Session,
    compute_summary, compare_to_reference,
    detect_recovery, classify_session, build_session_result,
)


class TestParticipant(unittest.TestCase):
    def test_valid_participant_created_correctly(self):
        p = Participant("Anna", resting_hr=62, max_hr=190, age=27)
        self.assertEqual(p.resting_hr, 62.0)
        self.assertEqual(p.max_hr, 190.0)

    def test_invalid_resting_hr_raises_error(self):
        with self.assertRaises(ValueError):
            Participant("Bad", resting_hr=-10, max_hr=190)

    def test_resting_hr_setter_validates(self):
        p = Participant("Anna", resting_hr=62, max_hr=190)
        with self.assertRaises(ValueError):
            p.resting_hr = 999


class TestObservation(unittest.TestCase):
    def test_valid_observation_is_valid(self):
        obs = Observation.from_dict({
            "timestamp": 1, "heart_rate": 100, "skin_response": 2.0,
            "temperature": 32.5, "activity_level": 0.5, "signal_quality": 0.9,
            "steps": 200
        })
        self.assertTrue(obs.is_valid)

    def test_missing_field_is_invalid(self):
        obs = Observation.from_dict({
            "timestamp": 1, "heart_rate": 100, "skin_response": 2.0,
            "temperature": 32.5, "activity_level": 0.5, "signal_quality": 0.9,
            # "steps" missing
        })
        self.assertFalse(obs.is_valid)
        self.assertEqual(obs.rejection_reason, "Missing required field(s)")

    def test_impossible_heart_rate_is_invalid(self):
        obs = Observation.from_dict({
            "timestamp": 1, "heart_rate": 400, "skin_response": 2.0,
            "temperature": 32.5, "activity_level": 0.5, "signal_quality": 0.9,
            "steps": 200
        })
        self.assertFalse(obs.is_valid)

    def test_low_signal_quality_is_invalid(self):
        obs = Observation.from_dict({
            "timestamp": 1, "heart_rate": 100, "skin_response": 2.0,
            "temperature": 32.5, "activity_level": 0.5, "signal_quality": 0.2,
            "steps": 200
        })
        self.assertFalse(obs.is_valid)
        self.assertEqual(obs.rejection_reason, "signal quality too low to trust")


class TestSession(unittest.TestCase):
    def setUp(self):
        self.participant = Participant("Anna", resting_hr=62, max_hr=190)

    def test_session_filters_invalid_observations(self):
        good = Observation.from_dict({
            "timestamp": 1, "heart_rate": 100, "skin_response": 2.0,
            "temperature": 32.5, "activity_level": 0.5, "signal_quality": 0.9,
            "steps": 200
        })
        bad = Observation.from_dict({
            "timestamp": 2, "heart_rate": 400, "skin_response": 2.0,
            "temperature": 32.5, "activity_level": 0.5, "signal_quality": 0.9,
            "steps": 200
        })
        session = Session(self.participant, [good, bad])
        self.assertEqual(len(session.observations), 2)
        self.assertEqual(len(session.valid_observations), 1)


class TestCalculations(unittest.TestCase):
    def setUp(self):
        self.participant = Participant("Anna", resting_hr=62, max_hr=190)

    def test_compute_summary_basic(self):
        obs = [
            Observation.from_dict({"timestamp": i, "heart_rate": hr, "skin_response": 2.0,
                                    "temperature": 32.5, "activity_level": 0.5,
                                    "signal_quality": 0.9, "steps": 100})
            for i, hr in enumerate([100, 110, 120])
        ]
        summary = compute_summary(obs, "heart_rate")
        self.assertEqual(summary["average"], 110.0)
        self.assertEqual(summary["minimum"], 100)
        self.assertEqual(summary["maximum"], 120)

    def test_compute_summary_empty(self):
        summary = compute_summary([], "heart_rate")
        self.assertEqual(summary["count"], 0)
        self.assertIsNone(summary["average"])

    def test_classify_resting(self):
        summary = {"average": 65, "count": 3}
        comparison = compare_to_reference(summary, self.participant)
        result = classify_session(summary, comparison)
        self.assertEqual(result, "resting")

    def test_classify_high_activity(self):
        summary = {"average": 160, "count": 3}
        comparison = compare_to_reference(summary, self.participant)
        result = classify_session(summary, comparison)
        self.assertEqual(result, "high activity")

    def test_classify_insufficient_data(self):
        summary = {"average": 100, "count": 1}
        comparison = compare_to_reference(summary, self.participant)
        result = classify_session(summary, comparison)
        self.assertEqual(result, "insufficient data")

    def test_detect_recovery_true_for_declining_trend(self):
        obs = [
            Observation.from_dict({"timestamp": 1, "heart_rate": 130, "skin_response": 2.0,
                                    "temperature": 32.5, "activity_level": 0.8,
                                    "signal_quality": 0.9, "steps": 300}),
            Observation.from_dict({"timestamp": 2, "heart_rate": 125, "skin_response": 2.0,
                                    "temperature": 32.5, "activity_level": 0.6,
                                    "signal_quality": 0.9, "steps": 250}),
            Observation.from_dict({"timestamp": 3, "heart_rate": 95, "skin_response": 2.0,
                                    "temperature": 32.5, "activity_level": 0.2,
                                    "signal_quality": 0.9, "steps": 100}),
            Observation.from_dict({"timestamp": 4, "heart_rate": 80, "skin_response": 2.0,
                                    "temperature": 32.5, "activity_level": 0.1,
                                    "signal_quality": 0.9, "steps": 50}),
        ]
        self.assertTrue(detect_recovery(obs))

    def test_detect_recovery_false_for_too_few_observations(self):
        obs = [
            Observation.from_dict({"timestamp": 1, "heart_rate": 100, "skin_response": 2.0,
                                    "temperature": 32.5, "activity_level": 0.5,
                                    "signal_quality": 0.9, "steps": 200}),
        ]
        self.assertFalse(detect_recovery(obs))


class TestBuildSessionResult(unittest.TestCase):
    def test_full_pipeline_produces_expected_keys(self):
        participant = Participant("Anna", resting_hr=62, max_hr=190)
        obs = [
            Observation.from_dict({"timestamp": 1, "heart_rate": 100, "skin_response": 2.0,
                                    "temperature": 32.5, "activity_level": 0.5,
                                    "signal_quality": 0.9, "steps": 200}),
        ]
        session = Session(participant, obs)
        result = build_session_result(session)
        expected_keys = {"participant", "total_observations", "usable_observations",
                          "heart_rate_summary", "comparison", "is_recovering", "classification"}
        self.assertEqual(set(result.keys()), expected_keys)
        self.assertEqual(result["participant"], "Anna")


if __name__ == "__main__":
    unittest.main()