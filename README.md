# Smart Fitness Session Analyzer

**Course:** Object-Oriented Python — Programming Assignment I
**Option:** A — Smart Fitness Session Analyzer
**Student:** Shepard Cyiza
**Student number:** 413414

## What it does

Simulates fitness sessions recorded by a wearable device. It takes a participant's
baseline heart rate, groups sensor readings into a session, checks each reading is
valid, compares the session against the participant's baseline, and classifies the
session as resting, moderate, high activity, or recovering. Bad or missing readings
get filtered out automatically.

## Classes

- **Participant** – a person and their baseline heart rate values.
- **Observation** – one sensor reading. Validates itself when created.
- **Session** – a participant plus a list of observations recorded during training.

The calculations (summaries, comparisons, recovery detection, classification) are
separate functions instead of class methods, so the classes just hold data and the
functions do the work on that data.

## Design choices

`Session` is made up of a `Participant` and a list of `Observation`s (composition).
I didn't use inheritance — every observation has the same shape and rules, so
subclassing didn't make sense here. Composition fit the relationship better.

`Participant` and `Observation` both keep some internal values protected (`_resting_hr`,
`_valid`, etc.) and only expose them through properties, so they can't be set to
invalid values from outside the class.

`Observation.from_dict` is a classmethod that builds an observation from a raw dict.
`Participant._validate_hr` is a staticmethod since it doesn't need any instance data.

## Rules I used for classification

- Under 15% above resting HR → resting
- 15–50% above → moderate activity
- Over 50% above → high activity
- Heart rate/activity clearly dropping near the end of the session → recovering (overrides the above)
- Fewer than 2 valid readings → insufficient data

These percentages are just fixed numbers I picked, not something scientifically
derived — a more accurate version would probably scale based on each person's
heart rate range instead of a flat percentage.

## How to run it

```bash
git clone https://github.com/Shepard16/Fitness-Analyzer.git
cd Fitness-Analyzer
python3 main.py
```

Only the Python standard library is used, no extra installs needed.

Run the tests with:
```bash
python3 -m unittest tests -v
```

## Example output

```
### Activity followed by recovery ###
========================================
Session Report — Anna
========================================
Observations used: 4 / 4
Heart rate — avg: 107.5, min: 80, max: 130
Compared to resting HR (62.0): 73.4% above
Recovering: True
Classification: RECOVERING
========================================
```

## Limitations

- Classification thresholds are the same for everyone, not adjusted per person.
- Recovery detection only compares the first and last reading of the final part of
  the session, not the whole trend.
- A session can still be classified with only 2-3 valid readings, which isn't a lot
  of data.