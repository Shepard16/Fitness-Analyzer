from main import Observation


def get_resting_observations() -> list:
    return [
        Observation.from_dict({"timestamp": 1, "heart_rate": 65, "skin_response": 1.2,
                                "temperature": 32.0, "activity_level": 0.05, "signal_quality": 0.95, "steps": 5}),
        Observation.from_dict({"timestamp": 2, "heart_rate": 63, "skin_response": 1.1,
                                "temperature": 32.0, "activity_level": 0.04, "signal_quality": 0.96, "steps": 3}),
        Observation.from_dict({"timestamp": 3, "heart_rate": 66, "skin_response": 1.3,
                                "temperature": 32.1, "activity_level": 0.06, "signal_quality": 0.94, "steps": 4}),
    ]


def get_moderate_observations() -> list:
    return [
        Observation.from_dict({"timestamp": 1, "heart_rate": 90, "skin_response": 2.0,
                                "temperature": 32.5, "activity_level": 0.4, "signal_quality": 0.93, "steps": 200}),
        Observation.from_dict({"timestamp": 2, "heart_rate": 92, "skin_response": 2.1,
                                "temperature": 32.6, "activity_level": 0.42, "signal_quality": 0.92, "steps": 210}),
        Observation.from_dict({"timestamp": 3, "heart_rate": 88, "skin_response": 2.0,
                                "temperature": 32.5, "activity_level": 0.39, "signal_quality": 0.94, "steps": 190}),
    ]


def get_high_observations() -> list:
    return [
        Observation.from_dict({"timestamp": 1, "heart_rate": 150, "skin_response": 3.5,
                                "temperature": 33.5, "activity_level": 0.9, "signal_quality": 0.96, "steps": 450}),
        Observation.from_dict({"timestamp": 2, "heart_rate": 155, "skin_response": 3.6,
                                "temperature": 33.6, "activity_level": 0.92, "signal_quality": 0.95, "steps": 460}),
        Observation.from_dict({"timestamp": 3, "heart_rate": 152, "skin_response": 3.5,
                                "temperature": 33.5, "activity_level": 0.91, "signal_quality": 0.97, "steps": 455}),
    ]


def get_recovery_observations() -> list:
    return [
        Observation.from_dict({"timestamp": 1, "heart_rate": 130, "skin_response": 3.1,
                                "temperature": 33.0, "activity_level": 0.8, "signal_quality": 0.95, "steps": 400}),
        Observation.from_dict({"timestamp": 2, "heart_rate": 125, "skin_response": 2.9,
                                "temperature": 32.8, "activity_level": 0.6, "signal_quality": 0.93, "steps": 300}),
        Observation.from_dict({"timestamp": 3, "heart_rate": 95, "skin_response": 2.0,
                                "temperature": 32.5, "activity_level": 0.2, "signal_quality": 0.90, "steps": 100}),
        Observation.from_dict({"timestamp": 4, "heart_rate": 80, "skin_response": 1.5,
                                "temperature": 32.2, "activity_level": 0.1, "signal_quality": 0.92, "steps": 50}),
    ]


def get_invalid_observations() -> list:
    return [
        Observation.from_dict({"timestamp": 1, "heart_rate": 100, "skin_response": 2.2,
                                "temperature": 32.4, "activity_level": 0.5, "signal_quality": 0.93, "steps": 250}),
        Observation.from_dict({"timestamp": 2, "heart_rate": 400, "skin_response": 2.1,
                                "temperature": 32.5, "activity_level": 0.5, "signal_quality": 0.91, "steps": 200}),
        Observation.from_dict({"timestamp": 3, "heart_rate": 98, "skin_response": 2.0,
                                "temperature": 32.3, "activity_level": 0.48, "signal_quality": 0.2, "steps": 240}),
        Observation.from_dict({"timestamp": 4, "heart_rate": None, "skin_response": 2.0,
                                "temperature": 32.3, "activity_level": 0.48, "signal_quality": 0.9, "steps": 240}),
    ]