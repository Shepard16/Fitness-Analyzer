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



if __name__ == "__main__":
                p = Participant("Anna", resting_hr=62, max_hr=190, age=27)
                print(p.name, p.resting_hr, p.max_hr)

                