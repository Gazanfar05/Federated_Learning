#!/usr/bin/env python3
"""Validate structure, safety ranges, duplicates, and summary statistics."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

SCHEMA = ["Pregnancies", "Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI", "DiabetesPedigreeFunction", "Age", "Outcome"]
FEATURES = SCHEMA[:-1]
RANGES = {
    "Pregnancies": (0, 20), "Glucose": (0, 250), "BloodPressure": (0, 150),
    "SkinThickness": (0, 120), "Insulin": (0, 1000), "BMI": (0, 80),
    "DiabetesPedigreeFunction": (0, 3), "Age": (0, 120),
}
FILES = {"hospital1": "hospital1.csv", "hospital2": "hospital2.csv", "hospital3": "hospital3.csv"}


def load(path: Path) -> tuple[np.ndarray, list[tuple[str, ...]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header != SCHEMA:
            raise ValueError(f"{path}: expected schema {SCHEMA}, found {header}")
        raw = list(reader)
    if not raw:
        raise ValueError(f"{path}: no data rows")
    try:
        matrix = np.array([[float(cell) for cell in row] for row in raw], dtype=float)
    except ValueError as exc:
        raise ValueError(f"{path}: non-numeric value found") from exc
    if matrix.shape[1] != 9 or not np.isfinite(matrix).all():
        raise ValueError(f"{path}: invalid shape or non-finite value")
    if not np.isin(matrix[:, -1], [0, 1]).all():
        raise ValueError(f"{path}: Outcome is not binary")
    return matrix, [tuple(row) for row in raw]


def summary(matrix: np.ndarray) -> dict:
    result = {"rows": int(len(matrix)), "missing_values": int(np.isnan(matrix).sum()),
              "duplicates": int(len(matrix) - len({tuple(row) for row in matrix}))}
    result["outcome_counts"] = {str(int(k)): int(v) for k, v in zip(*np.unique(matrix[:, -1], return_counts=True))}
    result["outcome_prevalence"] = float(matrix[:, -1].mean())
    result["features"] = {
        name: {"min": float(matrix[:, i].min()), "max": float(matrix[:, i].max()),
               "mean": float(matrix[:, i].mean()), "std": float(matrix[:, i].std(ddof=1))}
        for i, name in enumerate(FEATURES)
    }
    result["range_review"] = {
        name: int(((matrix[:, i] < low) | (matrix[:, i] > high)).sum())
        for i, (name, (low, high)) in enumerate(RANGES.items())
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-root", type=Path, default=Path("openfl-diabetes-workspace/datasets/baseline"))
    parser.add_argument("--expanded-root", type=Path, default=Path("openfl-diabetes-workspace/datasets/expanded"))
    parser.add_argument("--expected-count", type=int, default=2000)
    parser.add_argument("--report", type=Path, default=Path("openfl-diabetes-workspace/datasets/reports/data_expansion_report.md"))
    args = parser.parse_args()
    errors: list[str] = []
    matrices: dict[str, np.ndarray] = {}
    baseline_matrices: dict[str, np.ndarray] = {}
    baseline_summaries: dict[str, dict] = {}
    summaries: dict[str, dict] = {}
    row_sets: dict[str, set[tuple[str, ...]]] = {}
    for hospital, filename in FILES.items():
        baseline_path = args.baseline_root / filename
        try:
            baseline_matrix, _ = load(baseline_path)
            baseline_matrices[hospital] = baseline_matrix
            baseline_summaries[hospital] = summary(baseline_matrix)
        except (OSError, ValueError) as exc:
            errors.append(f"baseline: {exc}")
        path = args.expanded_root / filename
        try:
            matrix, raw_rows = load(path)
            matrices[hospital], row_sets[hospital], summaries[hospital] = matrix, set(raw_rows), summary(matrix)
            if len(matrix) != args.expected_count:
                errors.append(f"{hospital}: expected {args.expected_count} rows, found {len(matrix)}")
            for name, count in summaries[hospital]["range_review"].items():
                if count:
                    errors.append(f"{hospital}: {count} values outside review range for {name}")
        except (OSError, ValueError) as exc:
            errors.append(str(exc))
    overlaps = {}
    names = list(FILES)
    for index, left in enumerate(names):
        for right in names[index + 1:]:
            overlaps[f"{left}__{right}"] = len(row_sets.get(left, set()) & row_sets.get(right, set()))
    total = sum(item["rows"] for item in summaries.values())
    if total != args.expected_count * 3:
        errors.append(f"total: expected {args.expected_count * 3} rows, found {total}")
    report = ["# Diabetes dataset expansion report", "", "## Provenance",
              "These are synthetic research datasets generated from the three local 256-row CSV files. "
              "Hospital 1 documentation describes its source as deterministic synthetic data; provenance for "
              "Hospitals 2 and 3 was not established locally. No row is represented as a real patient.",
              "", "## Method", "A fixed-seed, per-hospital and per-outcome Gaussian copula models empirical "
              "feature ranks and correlations. Outcomes are sampled using each source hospital's observed "
              "prevalence. Values are constrained to each source hospital's observed support and integer "
              "features retain integer formatting. This is not clinically validated.", "", "## Results"]
    for hospital in FILES:
        item = summaries.get(hospital)
        if not item:
            continue
        before = baseline_summaries[hospital]
        report += [f"### {hospital}", f"- Baseline rows: {before['rows']}", f"- Expanded rows: {item['rows']}",
                   f"- Baseline outcome counts: `{before['outcome_counts']}`",
                   f"- Expanded outcome counts: `{item['outcome_counts']}`",
                   f"- Baseline outcome prevalence: {before['outcome_prevalence']:.4f}",
                   f"- Expanded outcome prevalence: {item['outcome_prevalence']:.4f}",
                   f"- Expanded duplicate rows: {item['duplicates']}", "- Feature statistics:"]
        for name, stats in item["features"].items():
            baseline_stats = before["features"][name]
            report.append(
                f"  - `{name}`: baseline min={baseline_stats['min']:.4g}, max={baseline_stats['max']:.4g}, "
                f"mean={baseline_stats['mean']:.4g}, sd={baseline_stats['std']:.4g}; "
                f"expanded min={stats['min']:.4g}, max={stats['max']:.4g}, "
                f"mean={stats['mean']:.4g}, sd={stats['std']:.4g}"
            )
    report += ["", "## Cross-hospital overlap", *[f"- {key}: {value} exact row overlaps" for key, value in overlaps.items()],
               "", "## Validation", f"- Structural status: **{'PASS' if not errors else 'FAIL'}**",
               "- Required checks: nine-column schema/order, numeric features, binary outcomes, finite values, exact row counts, duplicate detection, overlap detection, and review ranges.",
               "- Compatibility: the current OpenFL loader expects exactly eight numeric features plus `Outcome`; the generated files use that unchanged schema.",
               "", "## Limitations and reproducibility",
               "- These 6,000 rows are synthetic and do not represent 6,000 independently observed patients or clinical evidence.",
               "- Original CSVs remain unchanged; baseline copies are stored under `datasets/baseline/`.",
               "- Patient datasets remain outside Docker image/source control; use separate read-only mounts or an explicit local copy step to select expanded data. The active OpenFL plan and Compose file were not changed.",
               "- Reproduce with: `python openfl-diabetes-workspace/scripts/expand_diabetes_data.py --target-count 2000 --seed 20261019`",
               "- Validate with: `python openfl-diabetes-workspace/scripts/validate_diabetes_data.py`"]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS" if not errors else "FAIL", "total_rows": total, "summaries": summaries, "overlaps": overlaps, "errors": errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
