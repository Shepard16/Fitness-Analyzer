"""Validation rules for identifiers and CSV values."""

import re

from .exceptions import InvalidIdentifierError, InvalidRecordError

# Regular expressions used for validating identifiers and filenames.

PARTICIPANT_ID_PATTERN = re.compile(r"P\d{3}")
SESSION_ID_PATTERN = re.compile(r"FIT-\d{4}-\d{3}")
CSV_FILENAME_PATTERN = re.compile(r"[\w-]+.csv")

PARTICIPANT_COLUMNS = [
    "participant_id",
    "name",
    "baseline_heart_rate",
    "baseline_skin_response",
    "baseline_temperature",
]

SESSION_COLUMNS = [
    "session_id",
    "participant_id",
    "timestamp",
    "heart_rate",
    "skin_response",
    "temperature",
    "activity_level",
    "signal_quality",
]

# field -> (type, minimum, maximum)

SESSION_FIELD_RULES = {
    "timestamp": (int, 0, None),
    "heart_rate": (int, 30, 220),
    "skin_response": (float, 0.0, 20.0),
    "temperature": (float, 20.0, 42.0),
    "activity_level": (float, 0.0, 1.0),
    "signal_quality": (float, 0.0, 1.0),
}

PARTICIPANT_FIELD_RULES = {
    "baseline_heart_rate": (float, 30.0, 120.0),
    "baseline_skin_response": (float, 0.0, 20.0),
    "baseline_temperature": (float, 20.0, 42.0),
}


def validate_identifier(value: str, pattern: re.Pattern, label: str) -> str:
    """Validate an identifier and return it when the format is correct."""
    if value is None or pattern.fullmatch(value) is None:
        raise InvalidIdentifierError(
            f"{value!r} is not a valid {label} "
            f"(expected format {pattern.pattern})"
        )

    return value


def is_valid_csv_filename(name: str) -> bool:
    """Return True when the filename matches the expected CSV format."""
    match = CSV_FILENAME_PATTERN.fullmatch(name)
    return match is not None


def convert_value(field: str, raw: str, rules: dict):
    """Convert a CSV value and make sure it is within the allowed range."""
    value_type, minimum, maximum = rules[field]
    text = (raw or "").strip()

    if not text:
        raise InvalidRecordError((field, "missing value"))

    try:
        value = value_type(text)
    except ValueError as err:
        type_name = "integer" if value_type is int else "number"
        message = f"{text!r} is not a valid {type_name}"
        raise InvalidRecordError((field, message)) from err

    if minimum is not None and value < minimum:
        message = f"{value} is below the allowed minimum {minimum}"
        raise InvalidRecordError((field, message))

    if maximum is not None and value > maximum:
        message = f"{value} is above the allowed maximum {maximum}"
        raise InvalidRecordError((field, message))

    return value


def _parse_fields(raw: dict, id_fields: dict, rules: dict, text_fields=()) -> dict:
    """Validate all fields in a row and collect any problems found."""
    parsed = {}
    problems = []

    for field, identifier_info in id_fields.items():
        pattern, label = identifier_info
        value = (raw.get(field) or "").strip()

        try:
            parsed[field] = validate_identifier(value, pattern, label)
        except InvalidIdentifierError as err:
            problems.append((field, str(err)))

    for field in rules:
        try:
            parsed[field] = convert_value(field, raw.get(field), rules)
        except InvalidRecordError as err:
            problems.extend(err.problems)

    for field in text_fields:
        value = (raw.get(field) or "").strip()

        if value:
            parsed[field] = value
        else:
            problems.append((field, "missing value"))

    if problems:
        raise InvalidRecordError(problems)

    return parsed


def parse_session_row(raw: dict) -> dict:
    return _parse_fields(
        raw,
        {
            "session_id": (SESSION_ID_PATTERN, "session ID"),
            "participant_id": (PARTICIPANT_ID_PATTERN, "participant ID"),
        },
        SESSION_FIELD_RULES,
    )


def parse_participant_row(raw: dict) -> dict:
    return _parse_fields(
        raw,
        {
            "participant_id": (PARTICIPANT_ID_PATTERN, "participant ID"),
        },
        PARTICIPANT_FIELD_RULES,
        text_fields=("name",),
    )
