#!/usr/bin/env python3
"""Create reproducible, clearly labeled synthetic diabetes datasets.

The source files are treated as local tabular data, not as verified clinical
records. A class-conditional Gaussian copula preserves approximate marginal
distributions and feature relationships without copying source rows.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
from pathlib import Path

import numpy as np

SCHEMA = [
    "Pregnancies",
    "Glucose",
    "BloodPressure",
    "SkinThickness",
    "Insulin",
    "BMI",
    "DiabetesPedigreeFunction",
    "Age",
    "Outcome",
]
FEATURES = SCHEMA[:-1]
INTEGER_FEATURES = {"Pregnancies", "Glucose", "BloodPressure", "SkinThickness", "Insulin", "Age"}
HOSPITALS = {
    "hospital1": Path("hospital1-client/data/hospital1.csv"),
    "hospital2": Path("hospital_02_client/data/hospital2.csv"),
    "hospital3": Path("hospital_03_client/data/hospital3.csv"),
}


def inverse_normal_cdf(probability: np.ndarray) -> np.ndarray:
    """Acklam's rational approximation for the standard normal quantile."""
    p = np.clip(probability, 1e-10, 1 - 1e-10)
    a = np.array(
        [-39.6968302866538, 220.946098424521, -275.928510446969,
         138.357751867269, -30.6647980661472, 2.50662827745924]
    )
    b = np.array([-54.4760987982241, 161.585836858041, -155.698979859887,
                  66.8013118877197, -13.2806815528857])
    c = np.array([-0.00778489400243029, -0.322396458041136,
                  -2.40075827716184, -2.54973253934373, 4.37466414146497,
                  2.93816398269878])
    d = np.array([0.00778469570904146, 0.32246712907004,
                  2.445134137143, 3.75440866190742])
    result = np.empty_like(p)
    low = p < 0.02425
    high = p > 1 - 0.02425
    middle = ~(low | high)
    if np.any(low):
        q = np.sqrt(-2 * np.log(p[low]))
        numerator = ((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]
        denominator = (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1
        result[low] = numerator / denominator
    if np.any(high):
        q = np.sqrt(-2 * np.log(1 - p[high]))
        numerator = ((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]
        denominator = (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1
        result[high] = -numerator / denominator
    if np.any(middle):
        q = p[middle] - 0.5
        r = q * q
        numerator = ((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]
        denominator = ((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1
        result[middle] = numerator * q / denominator
    return result


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != SCHEMA:
            raise ValueError(f"{path} must have columns exactly {SCHEMA}; found {reader.fieldnames}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path} contains no data rows")
    return rows


def source_matrix(rows: list[dict[str, str]]) -> tuple[np.ndarray, np.ndarray]:
    values = np.array([[float(row[column]) for column in FEATURES] for row in rows], dtype=float)
    outcomes = np.array([int(row["Outcome"]) for row in rows], dtype=int)
    if not np.isin(outcomes, [0, 1]).all():
        raise ValueError("Outcome must contain only 0 and 1")
    return values, outcomes


def gaussian_copula_sample(values: np.ndarray, outcomes: np.ndarray, count: int, rng: np.random.Generator) -> np.ndarray:
    class_counts = np.bincount(outcomes, minlength=2)
    class_probability = class_counts[1] / len(outcomes)
    generated_outcomes = rng.binomial(1, class_probability, count)
    generated = np.empty((count, len(FEATURES)), dtype=float)

    for label in (0, 1):
        output_indices = np.flatnonzero(generated_outcomes == label)
        source = values[outcomes == label]
        if len(source) < 3 or not len(output_indices):
            continue
        ranks = np.empty_like(source)
        for column in range(source.shape[1]):
            order = np.argsort(source[:, column], kind="mergesort")
            rank = np.empty(len(source), dtype=float)
            rank[order] = np.arange(len(source), dtype=float)
            ranks[:, column] = (rank + 0.5) / len(source)
        latent = inverse_normal_cdf(ranks)
        correlation = np.corrcoef(latent, rowvar=False)
        correlation = np.nan_to_num(correlation, nan=0.0)
        correlation = 0.95 * correlation + 0.05 * np.eye(len(FEATURES))
        eigenvalues, eigenvectors = np.linalg.eigh(correlation)
        correlation = (eigenvectors * np.maximum(eigenvalues, 1e-6)) @ eigenvectors.T
        scale = np.sqrt(np.diag(correlation))
        correlation /= np.outer(scale, scale)
        latent_sample = rng.multivariate_normal(np.zeros(len(FEATURES)), correlation, len(output_indices))
        probabilities = 0.5 * (1 + np.vectorize(math.erf)(latent_sample / math.sqrt(2)))
        for column in range(len(FEATURES)):
            generated[output_indices, column] = np.quantile(
                source[:, column], probabilities[:, column], method="linear"
            )

    # Keep values within each hospital's observed support and preserve the
    # integer conventions used by the existing loader/data files.
    for column, name in enumerate(FEATURES):
        generated[:, column] = np.clip(generated[:, column], values[:, column].min(), values[:, column].max())
        if name in INTEGER_FEATURES:
            generated[:, column] = np.rint(generated[:, column])
    return np.column_stack((generated, generated_outcomes))


def write_csv(path: Path, matrix: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(SCHEMA)
        for row in matrix:
            writer.writerow([
                str(int(value)) if name in INTEGER_FEATURES or name == "Outcome" else f"{value:.6g}"
                for name, value in zip(SCHEMA, row)
            ])


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-count", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20261019)
    parser.add_argument("--output-root", type=Path, default=Path("openfl-diabetes-workspace/datasets"))
    args = parser.parse_args()
    if args.target_count < 2:
        raise SystemExit("--target-count must be at least 2")

    baseline_root = args.output_root / "baseline"
    expanded_root = args.output_root / "expanded"
    manifest = {
        "provenance": "Synthetic research data generated from the three local CSV inputs; not real patient records.",
        "method": "Per-hospital, per-outcome Gaussian copula fitted to empirical feature ranks; labels sampled from each hospital's observed prevalence.",
        "seed": args.seed,
        "target_count_per_hospital": args.target_count,
        "schema": SCHEMA,
        "hospitals": {},
        "limitations": [
            "The source files contain only 256 rows each and do not establish clinical validity.",
            "Synthetic rows are not independently observed patients and must not be used for clinical claims.",
            "Zero values retain the source convention and may represent missing measurements.",
        ],
    }
    for hospital, source_path in HOSPITALS.items():
        rows = read_csv(source_path)
        values, outcomes = source_matrix(rows)
        baseline_path = baseline_root / f"{hospital}.csv"
        if baseline_path.exists() and sha256(baseline_path) != sha256(source_path):
            raise SystemExit(f"Refusing to overwrite a different baseline: {baseline_path}")
        if not baseline_path.exists():
            baseline_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, baseline_path)
        hospital_seed = args.seed + list(HOSPITALS).index(hospital) * 1009
        matrix = gaussian_copula_sample(values, outcomes, args.target_count, np.random.default_rng(hospital_seed))
        output_path = expanded_root / f"{hospital}.csv"
        write_csv(output_path, matrix)
        manifest["hospitals"][hospital] = {
            "source": str(source_path),
            "source_sha256": sha256(source_path),
            "original_row_count": len(rows),
            "generated_row_count": args.target_count,
            "seed": hospital_seed,
            "output": str(output_path),
            "baseline": str(baseline_path),
            "source_outcome_counts": {str(k): int(v) for k, v in zip(*np.unique(outcomes, return_counts=True))},
        }
    report_root = args.output_root / "reports"
    report_root.mkdir(parents=True, exist_ok=True)
    (report_root / "expansion_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"target_count_per_hospital": args.target_count, "total": args.target_count * 3, "manifest": str(report_root / "expansion_manifest.json")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
