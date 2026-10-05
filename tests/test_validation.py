import unittest

from fitness_analyzer.exceptions import InvalidIdentifierError, InvalidRecordError
from fitness_analyzer.models import Observation
from fitness_analyzer.validation import (PARTICIPANT_ID_PATTERN, SESSION_FIELD_RULES,
                                         SESSION_ID_PATTERN, convert_value,
                                         is_valid_csv_filename, parse_session_row,
                                         validate_identifier)


class TestIdentifiers(unittest.TestCase):
    def test_valid_identifiers(self):
        self.assertEqual(validate_identifier("P001", PARTICIPANT_ID_PATTERN, "id"), "P001")
        self.assertEqual(validate_identifier("FIT-2026-001", SESSION_ID_PATTERN, "id"),
                         "FIT-2026-001")

    def test_invalid_participant_ids(self):
        for bad in ["001", "P01", "P0012", "p001", " P001", "P00A", ""]:
            with self.subTest(bad=bad), self.assertRaises(InvalidIdentifierError):
                validate_identifier(bad, PARTICIPANT_ID_PATTERN, "participant ID")

    def test_invalid_session_ids(self):
        for bad in ["FIT-26-102", "FIT-2026-1000", "FIT2026001", "fit-2026-001"]:
            with self.subTest(bad=bad), self.assertRaises(InvalidIdentifierError):
                validate_identifier(bad, SESSION_ID_PATTERN, "session ID")

    def test_identifier_error_is_a_value_error(self):
        self.assertTrue(issubclass(InvalidIdentifierError, ValueError))

    def test_csv_filename(self):
        self.assertTrue(is_valid_csv_filename("fitness_sessions.csv"))
        self.assertFalse(is_valid_csv_filename("fitness_sessions.txt"))


class TestConvertValue(unittest.TestCase):
    def test_converts_to_correct_types(self):
        self.assertIsInstance(convert_value("heart_rate", "72", SESSION_FIELD_RULES), int)
        self.assertIsInstance(convert_value("temperature", "32.5", SESSION_FIELD_RULES), float)

    def test_boundaries_are_inclusive(self):
        for field, raw in [("heart_rate", "30"), ("heart_rate", "220"),
                           ("activity_level", "0"), ("activity_level", "1"),
                           ("signal_quality", "0.0"), ("signal_quality", "1.0"),
                           ("timestamp", "0")]:
            with self.subTest(field=field, raw=raw):
                convert_value(field, raw, SESSION_FIELD_RULES)

    def test_just_outside_boundaries_rejected(self):
        for field, raw in [("heart_rate", "29"), ("heart_rate", "221"),
                           ("activity_level", "-0.01"), ("activity_level", "1.01"),
                           ("signal_quality", "1.4"), ("timestamp", "-1")]:
            with self.subTest(field=field, raw=raw), self.assertRaises(InvalidRecordError):
                convert_value(field, raw, SESSION_FIELD_RULES)

    def test_wrong_type_and_missing(self):
        with self.assertRaises(InvalidRecordError) as ctx:
            convert_value("heart_rate", "fast", SESSION_FIELD_RULES)
        self.assertEqual(ctx.exception.problems[0][0], "heart_rate")
        with self.assertRaises(InvalidRecordError) as ctx:
            convert_value("activity_level", "  ", SESSION_FIELD_RULES)
        self.assertIn("missing", str(ctx.exception))


class TestParseSessionRow(unittest.TestCase):
    def test_reports_all_problems_in_a_row(self):
        raw = {"session_id": "FIT-2026-102", "participant_id": "P002", "timestamp": "4",
               "heart_rate": "126", "skin_response": "-0.50", "temperature": "55.0",
               "activity_level": "1.30", "signal_quality": "0.91"}
        with self.assertRaises(InvalidRecordError) as ctx:
            parse_session_row(raw)
        fields = [field for field, _ in ctx.exception.problems]
        self.assertEqual(fields, ["skin_response", "temperature", "activity_level"])


class TestSignalQualityRule(unittest.TestCase):
    def make(self, quality):
        return Observation(0, 70, 1.2, 32.5, 0.1, quality)

    def test_threshold_boundary(self):
        self.assertTrue(self.make(0.50).is_usable)
        self.assertFalse(self.make(0.49).is_usable)


if __name__ == "__main__":
    unittest.main()
