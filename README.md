# Smart Fitness Session Analyzer

**Course:** Object-Oriented Python — Programming Assignment II
**Option:** A — Smart Fitness Session Analyzer
**Student:** Shepard Cyiza
**Student number:** 413414

## What it does

Continues my Assignment I project. The program reads the official CSV files, validates
every row, analyses each session against the participant's own baseline and saves three
report files. Bad rows are written to `rejected_records.txt` (file, row, field, reason)
and the program moves on to the next row.

## How to run it

```bash
python3 main.py --profiles data/participants.csv \
    --sessions data/fitness_sessions.csv data/fitness_sessions_invalid.csv \
    --output output
```

All arguments are optional and default to the files above. Run the tests with
`python3 -m unittest -v`. Only the standard library is used.

## Project structure

```
main.py                  entry point
data/                    official CSV files (not modified)
fitness_analyzer/
    exceptions.py        InvalidIdentifierError, InvalidRecordError, DataFileError
    models.py            Participant, Observation, Session, RejectedRecord
    validation.py        regex patterns, range rules, type conversion
    loader.py            reads the CSV files
    analysis.py          summaries, comparison, recovery, classification
    reports.py           writes the output files
    cli.py               command-line arguments
tests/                   unittest tests
```

## Rules

- IDs are checked with regex: participant `P\d{3}`, session `FIT-\d{4}-\d{3}`.
- Numbers are checked with ranges, e.g. heart rate 30–220, activity and signal quality 0–1.
- Rows with missing values, wrong types, unknown participants or the wrong number of
  values are rejected.
- **Signal quality:** outside 0–1 → rejected. Below 0.50 → accepted but not used in the
  analysis, since the reading can't be trusted.

Classification (average heart rate compared with baseline):

- Fewer than 3 usable readings → insufficient data
- Below −15% → below baseline
- −15% to 15% → resting
- 15% to 50% → moderate activity
- 50% or more → high activity
- Clear drop from a peak back towards baseline → recovering

## Output

`output/` is created if missing and overwritten on each run:
`analysis_summary.csv`, `analysis_report.txt` and `rejected_records.txt`.

## Use of AI

I used **Claude** (Anthropic) in this assignment. I meant to use it as a guide like in
Assignment I, but it ended up writing some of the Assignment II code and the tests.
The design builds on my Assignment I work (Participant / Observation / Session,
composition, the classification idea). I set up the project and data, went through the
code with Claude to understand it, and ran the program and tests. The course has no
specific AI rules, so I followed OsloMet's guidelines on disclosing AI use.
