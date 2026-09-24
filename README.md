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

The program uses the instructor-supplied `data_generator.py` (unmodified) to
generate the participant profile and observations for each scenario.

## Files

- `main.py` – all the classes, calculation functions, and the program entry point.
- `data_generator.py` – instructor-supplied generator, not modified.
- `sample_data.py` – some hand-built test scenarios I used earlier while developing.
  Not used by `main.py` anymore since I switched to the real generator, but kept
  since some of it overlaps with `tests.py`.
- `tests.py` – automated tests.

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

## Assumptions

- The generator's profile only gives a resting heart rate, not a max heart rate,
  so `build_participant_from_profile()` estimates one as `resting_hr + 130`
  (capped at 220). Not a real formula, just a rough number so the program has
  something to compare against.
- Recovery detection compares the average heart rate/activity of the first ~25%
  of a session against the last ~30%, instead of just the first and last reading.
  I originally compared single points, but with randomly generated data that gave
  false positives from noise, so I switched to averaging groups instead.

## Rules I used for classification

- Under 15% above resting HR → resting
- 15–50% above → moderate activity
- Over 50% above → high activity
- Heart rate/activity clearly dropping near the end of the session → recovering (overrides the above)
- Fewer than 2 valid readings → insufficient data

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
Session Report — P001
========================================
Observations used: 12 / 12
Heart rate — avg: 112.8, min: 86, max: 141
Compared to resting HR (78.0): 44.7% above
Recovering: True
Classification: RECOVERING
========================================
```

## Limitations

- Classification thresholds are the same for everyone, not adjusted per person.
- Max heart rate is estimated, not measured, since the generator doesn't provide it.
- A session can still be classified with only 2-3 valid readings, which isn't a lot
  of data.