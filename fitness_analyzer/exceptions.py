"""Custom exceptions used across the package.

The two record-level errors subclass ValueError because they are both
"this value is not acceptable" problems. DataFileError is for problems
with a whole file (for example a missing column), where the program
cannot read any rows from it.
"""


class InvalidIdentifierError(ValueError):
    """Raised when an identifier has an invalid format."""


class InvalidRecordError(ValueError):
    """Raised when a CSV record cannot be accepted.

    Holds a list of (field, reason) problems so that a row with several
    issues can be reported in full, not just the first issue found.
    """

    def __init__(self, problems):
        # Accept a single (field, reason) pair or a list of them.
        if isinstance(problems, tuple):
            problems = [problems]
        self.problems = list(problems)
        message = "; ".join(f"{field}: {reason}" for field, reason in self.problems)
        super().__init__(message)


class DataFileError(Exception):
    """Raised when a whole input file cannot be used (missing, unreadable,
    wrong header or not valid CSV)."""

    def __init__(self, path, reason):
        self.path = path
        self.reason = reason
        super().__init__(f"{path}: {reason}")
