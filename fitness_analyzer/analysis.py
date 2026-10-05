"""Session analysis, reused from Assignment I and improved.

Changes from Assignment I:
- Every result now carries a list of human-readable reasons.
- "Insufficient data" needs at least MIN_USABLE_OBSERVATIONS usable
  readings (was 2), and the reason says *why* data was unusable.
- Skin response and temperature are compared with the participant's
  own baselines as supporting evidence.
- Recovery detection compares the end of the session with the session
  *peak* instead of with the first windows, which is less sensitive to
  how the session started.
- A new "below baseline" class flags a session whose average heart rate
  is clearly lower than the participant's resting reference, which is
  unusual and worth checking.
"""

from .models import LOW_SIGNAL_THRESHOLD, Session

MIN_USABLE_OBSERVATIONS = 3

# Average heart rate compared with the participant's baseline (percent).
BELOW_BASELINE_LIMIT = -15.0   # below this -> "below baseline"
RESTING_LIMIT = 15.0           # below this -> "resting"
MODERATE_LIMIT = 50.0          # below this -> "moderate activity", else "high activity"

# Recovery rule (see detect_recovery).
RECOVERY_MIN_PEAK_PCT = 30.0   # the peak must show real effort
RECOVERY_MIN_RETURN = 0.5      # end must have come back >= 50% of the way to baseline
RECOVERY_TAIL_SIZE = 2         # number of final windows used as "the end"


def compute_summary(observations: list, field: str) -> dict:
    """Average, minimum, maximum and count for one numeric field."""
    values = [getattr(o, field) for o in observations]
    if not values:
        return {"average": None, "minimum": None, "maximum": None, "count": 0}
    return {
        "average": round(sum(values) / len(values), 2),
        "minimum": min(values),
        "maximum": max(values),
        "count": len(values),
    }


def percent_change(value: float, reference: float) -> float:
    return round((value - reference) / reference * 100, 1)


def detect_recovery(observations: list, baseline_hr: float) -> tuple:
    """Return (is_recovering, explanation).

    A session counts as recovery when:
    1. there are at least 4 usable observations,
    2. the peak heart rate is at least 30% above baseline (real effort),
    3. the peak happens before the final 2 windows,
    4. the average of the final 2 windows has come at least 50% of the
       way back from the peak towards the baseline, and
    5. activity at the end is lower than activity at the peak.
    """
    if len(observations) < 4:
        return False, "too few readings to judge recovery"

    peak_index = max(range(len(observations)), key=lambda i: observations[i].heart_rate)
    peak = observations[peak_index]
    peak_pct = percent_change(peak.heart_rate, baseline_hr)
    if peak_pct < RECOVERY_MIN_PEAK_PCT:
        return False, f"peak heart rate only {peak_pct}% above baseline"
    if peak_index >= len(observations) - RECOVERY_TAIL_SIZE:
        return False, "heart rate peaks at the end of the session"

    tail = observations[-RECOVERY_TAIL_SIZE:]
    tail_hr = sum(o.heart_rate for o in tail) / len(tail)
    tail_activity = sum(o.activity_level for o in tail) / len(tail)
    returned = (peak.heart_rate - tail_hr) / (peak.heart_rate - baseline_hr)

    if returned >= RECOVERY_MIN_RETURN and tail_activity < peak.activity_level:
        return True, (f"heart rate fell from a peak of {peak.heart_rate} bpm to an average of "
                      f"{tail_hr:.1f} bpm in the last {RECOVERY_TAIL_SIZE} windows "
                      f"({returned:.0%} of the way back to baseline) while activity dropped")
    return False, f"heart rate only {returned:.0%} of the way back to baseline at the end"


def classify_intensity(pct_above_baseline: float) -> str:
    if pct_above_baseline < BELOW_BASELINE_LIMIT:
        return "below baseline"
    if pct_above_baseline < RESTING_LIMIT:
        return "resting"
    if pct_above_baseline < MODERATE_LIMIT:
        return "moderate activity"
    return "high activity"


def analyse_session(session: Session) -> dict:
    """Run the full analysis on one Session and return a structured
    result dictionary (used by every report writer)."""
    participant = session.participant
    all_obs = session.observations
    usable = session.usable_observations
    low_signal = session.low_signal_count

    result = {
        "session_id": session.session_id,
        "participant_id": participant.participant_id,
        "participant_name": participant.name,
        "total_observations": len(all_obs),
        "usable_observations": len(usable),
        "low_signal_observations": low_signal,
        "baseline_heart_rate": participant.baseline_heart_rate,
        "heart_rate": compute_summary(usable, "heart_rate"),
        "pct_above_baseline": None,
        "avg_skin_response": None,
        "skin_response_change_pct": None,
        "avg_temperature": None,
        "temperature_change": None,
        "is_recovering": False,
        "classification": "insufficient data",
        "reasons": [],
    }
    reasons = result["reasons"]

    if low_signal:
        reasons.append(f"{low_signal} of {len(all_obs)} readings had signal quality below "
                       f"{LOW_SIGNAL_THRESHOLD:.2f} and were left out")

    if len(usable) < MIN_USABLE_OBSERVATIONS:
        reasons.append(f"only {len(usable)} usable reading(s); at least "
                       f"{MIN_USABLE_OBSERVATIONS} are needed for a reliable result")
        return result

    avg_hr = result["heart_rate"]["average"]
    pct = percent_change(avg_hr, participant.baseline_heart_rate)
    result["pct_above_baseline"] = pct

    skin = compute_summary(usable, "skin_response")["average"]
    temp = compute_summary(usable, "temperature")["average"]
    result["avg_skin_response"] = skin
    result["skin_response_change_pct"] = percent_change(skin, participant.baseline_skin_response)
    result["avg_temperature"] = temp
    result["temperature_change"] = round(temp - participant.baseline_temperature, 2)

    intensity = classify_intensity(pct)
    reasons.append(f"average heart rate {avg_hr:.1f} bpm is {pct:+.1f}% compared with the "
                   f"baseline of {participant.baseline_heart_rate:.0f} bpm ({intensity} range)")

    recovering, recovery_reason = detect_recovery(usable, participant.baseline_heart_rate)
    result["is_recovering"] = recovering
    if recovering:
        result["classification"] = "recovering"
        reasons.append("recovery: " + recovery_reason)
    else:
        result["classification"] = intensity
        reasons.append("no recovery: " + recovery_reason)

    reasons.append(f"skin response {result['skin_response_change_pct']:+.1f}% and temperature "
                   f"{result['temperature_change']:+.2f} °C compared with baseline")
    return result
