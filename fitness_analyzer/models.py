"""Domain classes: Participant, Observation, Session and RejectedRecord.

Same idea as Assignment I: a Session is *composed of* a Participant and a
list of Observations (no inheritance). The difference now is that the
values arrive from CSV files, so all type conversion and range checking
happens in validation.py before an object is created. The classes here
only hold already-checked data and answer simple questions about it.
"""

from dataclasses import dataclass

# Documented data-quality rule (see README):
# a reading with signal_quality below this value is kept as an accepted
# row, but it is NOT used in the analysis because the sensor reading
# cannot be trusted. Values outside 0-1 are impossible and are rejected
# during validation instead.
LOW_SIGNAL_THRESHOLD = 0.50


class Participant:
    """A person with personal reference (baseline) values."""

    def __init__(self, participant_id: str, name: str, baseline_heart_rate: float,
                 baseline_skin_response: float, baseline_temperature: float):
        self._participant_id = participant_id
        self._name = name
        self._baseline_heart_rate = float(baseline_heart_rate)
        self._baseline_skin_response = float(baseline_skin_response)
        self._baseline_temperature = float(baseline_temperature)

    # Read-only properties: a participant's reference values should not
    # change after they have been loaded and validated.
    @property
    def participant_id(self) -> str:
        return self._participant_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def baseline_heart_rate(self) -> float:
        return self._baseline_heart_rate

    @property
    def baseline_skin_response(self) -> float:
        return self._baseline_skin_response

    @property
    def baseline_temperature(self) -> float:
        return self._baseline_temperature

    def __repr__(self) -> str:
        return f"Participant({self._participant_id!r}, {self._name!r})"


class Observation:
    """One measurement window from the wearable device."""

    def __init__(self, timestamp: int, heart_rate: int, skin_response: float,
                 temperature: float, activity_level: float, signal_quality: float):
        self.timestamp = timestamp
        self.heart_rate = heart_rate
        self.skin_response = skin_response
        self.temperature = temperature
        self.activity_level = activity_level
        self.signal_quality = signal_quality

    @property
    def has_low_signal(self) -> bool:
        return self.signal_quality < LOW_SIGNAL_THRESHOLD

    @property
    def is_usable(self) -> bool:
        """Usable for analysis = accepted row with trustworthy signal."""
        return not self.has_low_signal

    def __repr__(self) -> str:
        return f"Observation(t={self.timestamp}, hr={self.heart_rate})"


class Session:
    """A fitness session: one participant plus their observations."""

    def __init__(self, session_id: str, participant: Participant):
        self._session_id = session_id
        self._participant = participant
        self._observations = []

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def participant(self) -> Participant:
        return self._participant

    def add_observation(self, observation: Observation) -> None:
        self._observations.append(observation)

    @property
    def observations(self) -> list:
        """All accepted observations, sorted by timestamp (a copy, so the
        caller cannot change the session's internal list)."""
        return sorted(self._observations, key=lambda o: o.timestamp)

    @property
    def usable_observations(self) -> list:
        return [o for o in self.observations if o.is_usable]

    @property
    def low_signal_count(self) -> int:
        return sum(1 for o in self._observations if o.has_low_signal)

    def has_timestamp(self, timestamp: int) -> bool:
        return any(o.timestamp == timestamp for o in self._observations)


@dataclass(frozen=True)
class RejectedRecord:
    """Why a single CSV row was not accepted."""

    source: str        # file name, e.g. fitness_sessions_invalid.csv
    row_number: int    # line number in the file (the header is line 1)
    field: str         # column name, or "row" for whole-row problems
    reason: str

    def to_line(self) -> str:
        return f"{self.source}, row {self.row_number}, field '{self.field}': {self.reason}"
