class Participant:
    """Represents a person taking part in fitness sessions, with reference
    (baseline) measurements used to interpret their session data."""

    def __init__(self, name: str, resting_hr: float, max_hr: float, age: int = None):
        self.name = name
        self._resting_hr = self._validate_hr(resting_hr) # protected attribute
        self._max_hr = self._validate_hr(max_hr)
        self.age = age

    @staticmethod
    def _validate_hr(value: float) -> float:
            if not isinstance(value, (int, float )) or not (30 <= value <= 250):
                raise ValueError(f"Heart rate reference value out of range: {value}")
            return float(value)

    @property 
    def resting_hr(self) -> float:
            """Read-only-by-default access to resting heart rate reference value."""
            return self._resting_hr

    @property
    def max_hr(self) -> float:
            return self._max_hr

    @resting_hr.setter
    def resting_hr(self, value: float):
            self._resting_hr = self._validate_hr(value)


def build_participant_from_profile(profile: dict) -> Participant:
    """Converts the instructor-supplied generator's profile dict into a
    Participant. The generator provides baseline_heart_rate but not a max
    heart rate, so we estimate one with a documented margin above resting HR."""
    resting_hr = profile["baseline_heart_rate"]
    estimated_max_hr = min(220, resting_hr + 130)
    return Participant(
        name=profile["participant_id"],
        resting_hr=resting_hr,
        max_hr=estimated_max_hr,
    )



class Observation:
        """A single measurement window taken from a wearable device during a
    session. Validates itself on construction and reports whether it's usable."""

        REQUIRED_FIELDS = ["timestamp", "heart_rate", "skin_response", "temperature", "activity_level", "signal_quality"]

        def __init__(self, timestamp, heart_rate, skin_response, temperature, activity_level, signal_quality):
                self.timestamp = timestamp
                self.heart_rate = heart_rate
                self.skin_response = skin_response
                self.temperature = temperature
                self.activity_level = activity_level
                self.signal_quality = signal_quality
                self._valid, self._reason = self._validate()


        @classmethod
        def from_dict(cls, data: dict) -> "Observation":
                return cls(
                        timestamp=data.get("timestamp"),
                        heart_rate=data.get("heart_rate"),
                        skin_response=data.get("skin_response"),
                        temperature=data.get("temperature"),
                        activity_level=data.get("activity_level"),
                        signal_quality=data.get("signal_quality")
                )

        def _validate(self) -> tuple[bool, str]:
                if any(v is None for v in (self.timestamp, self.heart_rate,
                                self.skin_response, self.temperature,
                                self.activity_level, self.signal_quality,)):
                        return False, "Missing required field(s)"
                if not (30 <= self.heart_rate <= 220):
                        return False, "heart_rate out of realistic range"
                if not (0.0 <= self.activity_level <= 1.0):
                        return False, "activity_level out of range"
                if not (0.0 <= self.signal_quality <= 1.0):
                        return False, "signal_quality out of range"
                if self.signal_quality < 0.5:
                        return False, "signal quality too low to trust"
                if not (15 <= self.temperature <= 45):
                        return False, "temperature out of realistic range"
                return True, ""

        @property
        def is_valid(self) -> bool:
                return self._valid

        @property
        def rejection_reason(self) -> str:
                return self._reason

        

class Session:
    """Represents a single fitness session, with a collection of observations related to a participant.
    Composition - A session is composed of multiple observations, it is not kind of either. The session is not a subclass of observation, but rather contains a list of observations as an attribute."""

    def __init__(self, participant: Participant, observations: list = None):
        self.participant = participant
        # avoid a mutable default argument (a classic Python pitfall —
        # a default list would be shared across every Session instance)
        self._observations = observations if observations is not None else []

    def add_observation(self, observation: Observation):
        self._observations.append(observation)

    @property
    def observations(self) -> list:
        """All observations, valid or not."""
        return self._observations

    @property
    def valid_observations(self) -> list:
        """Only the observations that passed validation."""
        return [o for o in self._observations if o.is_valid]


def compare_to_reference(summary: dict, participant: Participant) -> dict:
    """Compares a heart-rate summary against the participant's reference
    values, expressed as a percentage above resting HR."""
    if summary["average"] is None:
        return {"comparison": "insufficient data"}
    avg_hr = summary["average"]
    pct_above_resting = (avg_hr - participant.resting_hr) / participant.resting_hr * 100
    return {
        "avg_heart_rate": avg_hr,
        "resting_hr": participant.resting_hr,
        "pct_above_resting": round(pct_above_resting, 1),
    }

def compute_summary(observations: list, field: str) -> dict:
    """Calculates average, minimum and maximum for one numeric field
    across a list of Observations. Returns an empty summary if there's
    no usable data."""
    values = [getattr(o, field) for o in observations]
    if not values:
        return {"average": None, "minimum": None, "maximum": None, "count": 0}
    return {
        "average": sum(values) / len(values),
        "minimum": min(values),
        "maximum": max(values),
        "count": len(values),
    }


def detect_recovery(observations: list, head_fraction: float = 0.25,
                     tail_fraction: float = 0.3, hr_drop_threshold: float = 10.0) -> bool:
    """Checks whether heart rate and activity level show a genuine declining
    trend from the early part of the session to the late part, using group
    averages (not single points) to avoid false positives from random noise.
    Requires at least a hr_drop_threshold percentage drop in average heart
    rate, alongside a drop in average activity level."""
    valid = [o for o in observations if o.is_valid]
    if len(valid) < 4:
        return False

    head_size = max(2, int(len(valid) * head_fraction))
    tail_size = max(2, int(len(valid) * tail_fraction))
    head = valid[:head_size]
    tail = valid[-tail_size:]

    head_avg_hr = sum(o.heart_rate for o in head) / len(head)
    tail_avg_hr = sum(o.heart_rate for o in tail) / len(tail)
    head_avg_activity = sum(o.activity_level for o in head) / len(head)
    tail_avg_activity = sum(o.activity_level for o in tail) / len(tail)

    hr_drop_pct = (head_avg_hr - tail_avg_hr) / head_avg_hr * 100
    activity_declining = tail_avg_activity < head_avg_activity

    return hr_drop_pct > hr_drop_threshold and activity_declining


def classify_session(summary: dict, comparison: dict, is_recovering: bool = False, min_observations: int = 2) -> str:
    """Classifies session intensity based on average heart rate compared
    to the participant's resting HR. Thresholds are simplified, fixed
    percentages applied uniformly across participants. Requires at least
    min_observations valid readings to produce a confident classification."""
    if summary["count"] < min_observations:
        return "insufficient data"
    if is_recovering:
        return "recovering"
    pct = comparison["pct_above_resting"]
    if pct < 15:
        return "resting"
    elif pct < 50:
        return "moderate activity"
    else:
        return "high activity"
    

def build_session_result(session: Session) -> dict:
    """Runs the full analysis pipeline on a Session and packages the
    result as a single structured dictionary."""
    valid_obs = session.valid_observations
    total = len(session.observations)
    usable = len(valid_obs)

    hr_summary = compute_summary(valid_obs, "heart_rate")
    comparison = compare_to_reference(hr_summary, session.participant)
    recovering = detect_recovery(valid_obs)
    classification = classify_session(hr_summary, comparison, recovering)

    return {
        "participant": session.participant.name,
        "total_observations": total,
        "usable_observations": usable,
        "heart_rate_summary": hr_summary,
        "comparison": comparison,
        "is_recovering": recovering,
        "classification": classification,
    }

def print_report(result: dict) -> None:
    """Prints a readable console report from a session result dictionary."""
    print("=" * 40)
    print(f"Session Report — {result['participant']}")
    print("=" * 40)
    print(f"Observations used: {result['usable_observations']} / {result['total_observations']}")

    hr = result["heart_rate_summary"]
    if hr["count"] == 0:
        print("No usable heart rate data.")
    else:
        print(f"Heart rate — avg: {hr['average']:.1f}, min: {hr['minimum']}, max: {hr['maximum']}")

    comp = result["comparison"]
    if "pct_above_resting" in comp:
        print(f"Compared to resting HR ({comp['resting_hr']}): {comp['pct_above_resting']}% above")

    print(f"Recovering: {result['is_recovering']}")
    print(f"Classification: {result['classification'].upper()}")
    print("=" * 40)


if __name__ == "__main__":
    from data_generator import generate_fitness_data, available_scenarios

    print("Available scenarios:", available_scenarios())

    scenario_labels = {
        "resting": "Resting",
        "moderate_activity": "Moderate activity",
        "high_activity": "High activity",
        "recovery": "Activity followed by recovery",
        "poor_quality": "Poor-quality / invalid data",
    }

    for scenario_key, label in scenario_labels.items():
        profile, raw_observations = generate_fitness_data(
            participant_id="P001",
            scenario=scenario_key,
            seed=42,
            number_of_windows=12,
        )
        participant = build_participant_from_profile(profile)
        observations = [Observation.from_dict(o) for o in raw_observations]
        session = Session(participant, observations)
        result = build_session_result(session)

        print(f"\n### {label} ###")
        print_report(result)


    

    