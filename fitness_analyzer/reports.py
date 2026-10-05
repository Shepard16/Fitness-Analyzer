"""Writing the three output files.
"""

import csv
from pathlib import Path

SUMMARY_FILENAME = "analysis_summary.csv"
REPORT_FILENAME = "analysis_report.txt"
REJECTED_FILENAME = "rejected_records.txt"

SUMMARY_COLUMNS = [
    "session_id", "participant_id", "participant_name",
    "total_observations", "usable_observations", "low_signal_observations",
    "avg_heart_rate", "min_heart_rate", "max_heart_rate",
    "baseline_heart_rate", "pct_above_baseline",
    "avg_skin_response", "skin_response_change_pct",
    "avg_temperature", "temperature_change",
    "is_recovering", "classification", "reasons",
]


def _blank_if_none(value):
    return "" if value is None else value


def _summary_row(result: dict) -> dict:
    hr = result["heart_rate"]
    row = {column: result.get(column) for column in SUMMARY_COLUMNS}
    row["avg_heart_rate"] = hr["average"]
    row["min_heart_rate"] = hr["minimum"]
    row["max_heart_rate"] = hr["maximum"]
    row["reasons"] = " | ".join(result["reasons"])
    return {key: _blank_if_none(value) for key, value in row.items()}


def write_summary_csv(results: list, path: Path) -> Path:
    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=SUMMARY_COLUMNS)
        writer.writeheader()
        for result in results:
            writer.writerow(_summary_row(result))
    return path


def write_text_report(results: list, path: Path, input_files: list) -> Path:
    lines = ["SMART FITNESS SESSION ANALYZER - ANALYSIS REPORT", "=" * 60, "Input files:"]
    lines += [f"  - {name}" for name in input_files]
    lines += [f"Sessions analysed: {len(results)}", ""]

    for result in results:
        hr = result["heart_rate"]
        lines.append(f"Session {result['session_id']} - {result['participant_name']} "
                     f"({result['participant_id']})")
        lines.append("-" * 60)
        lines.append(f"Result: {result['classification'].upper()}")
        lines.append(f"Readings used: {result['usable_observations']} of "
                     f"{result['total_observations']} accepted readings")
        if hr["count"]:
            lines.append(f"Heart rate: average {hr['average']:.1f}, min {hr['minimum']}, "
                         f"max {hr['maximum']} bpm (baseline {result['baseline_heart_rate']:.0f})")
        lines.append("Why:")
        lines += [f"  * {reason}" for reason in result["reasons"]]
        lines.append("")

    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_rejected_records(rejected: list, file_errors: list, path: Path) -> Path:
    rows = sorted(rejected, key=lambda r: (r.source, r.row_number))
    lines = ["REJECTED RECORDS", "=" * 60,
             "Row numbers are line numbers in the CSV file (the header is row 1).", ""]

    if file_errors:
        lines.append("Files that could not be read:")
        lines += [f"  - {error}" for error in file_errors]
        lines.append("")

    rejected_rows = {(r.source, r.row_number) for r in rows}
    lines.append(f"Rejected rows: {len(rejected_rows)} ({len(rows)} problem(s) in total)")
    lines.append("")
    lines += [r.to_line() for r in rows]
    if not rows:
        lines.append("No rows were rejected.")

    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_all_reports(results: list, rejected: list, file_errors: list,
                      output_dir: Path, input_files: list) -> list:
    """Create the output directory if needed and write all reports.
    Returns the list of created file paths."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    return [
        write_summary_csv(results, output_dir / SUMMARY_FILENAME),
        write_text_report(results, output_dir / REPORT_FILENAME, input_files),
        write_rejected_records(rejected, file_errors, output_dir / REJECTED_FILENAME),
    ]
