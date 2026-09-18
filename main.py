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



class Observation:
        """A single measurement window taken from a wearable device during a
    session. Validates itself on construction and reports whether it's usable."""

        REQUIRED_FIELDS = ["timestamp", "heart_rate", "skin_response", "steps", "temperature", "activity_level", "signal_quality"]

        def __init__(self, timestamp, heart_rate, steps, skin_response, temperature, activity_level, signal_quality):
                self.timestamp = timestamp
                self.heart_rate = heart_rate
                self.steps = steps
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
                        steps=data.get("steps"),
                        skin_response=data.get("skin_response"),
                        temperature=data.get("temperature"),
                        activity_level=data.get("activity_level"),
                        signal_quality=data.get("signal_quality")
                )

        def _validate(self) -> tuple[bool, str]:
                if any(v is None for v in (self.timestamp, self.heart_rate,
                                self.skin_response, self.temperature,
                                self.activity_level, self.signal_quality,
                                self.steps)):
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
                if not (0 <= self.steps <= 10000):
                        return False, "steps out of realistic range for one observation window"
                return True, ""

        @property
        def is_valid(self) -> bool:
                return self._valid

        @property
        def rejection_reason(self) -> str:
                return self._reason


if __name__ == "__main__":
    p = Participant("Anna", resting_hr=62, max_hr=190, age=27)
    print(p.name, p.resting_hr, p.max_hr)

    obs = Observation.from_dict({
        "timestamp": 2, "heart_rate": 118, "skin_response": 2.5,
        "temperature": 32.9, "activity_level": 0.72, "signal_quality": 0.93,
        "steps": 1500
    })
    print(obs.is_valid, obs.rejection_reason)

    bad_obs = Observation.from_dict({
        "timestamp": 3, "heart_rate": 400, "skin_response": 2.1,
        "temperature": 32.5, "activity_level": 0.5, "signal_quality": 0.91,
        "steps": 1200
    })
    print(bad_obs.is_valid, bad_obs.rejection_reason)
        
           