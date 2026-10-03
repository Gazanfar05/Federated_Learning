from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path


OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "hospital1.csv"


def generate_hospital1_dataset(path: str | Path | None = None) -> Path:
    out = Path(path) if path is not None else OUTPUT_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42)
    rows = []
    for _ in range(600):
        pregnancies = int(rng.integers(0, 10))
        glucose = int(rng.normal(120, 25))
        glucose = max(50, min(200, glucose))
        blood_pressure = int(rng.normal(72, 15))
        blood_pressure = max(40, min(115, blood_pressure))
        skin = int(rng.normal(25, 11))
        skin = max(8, min(60, skin))
        insulin = int(rng.normal(95, 30))
        insulin = max(20, min(300, insulin))
        bmi = float(rng.normal(31, 6))
        bmi = max(15, min(52, bmi))
        dpf = float(rng.normal(0.5, 0.25))
        dpf = max(0.1, min(2.5, dpf))
        age = int(rng.normal(45, 13))
        age = max(20, min(80, age))
        base_risk = (
            0.1
            + 0.02 * pregnancies
            + 0.015 * ((glucose - 100) / 20)
            + 0.02 * ((bmi - 25) / 10)
            + 0.02 * ((age - 45) / 10)
            + 0.5 * dpf
        )
        prob = 1 / (1 + np.exp(-base_risk))
        outcome = 1 if rng.random() < prob else 0
        rows.append(
            {
                "Pregnancies": pregnancies,
                "Glucose": glucose,
                "BloodPressure": blood_pressure,
                "SkinThickness": skin,
                "Insulin": insulin,
                "BMI": bmi,
                "DiabetesPedigreeFunction": round(dpf, 4),
                "Age": age,
                "Outcome": outcome,
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(out, index=False)
    return out


if __name__ == "__main__":
    path = generate_hospital1_dataset()
    print(f"Created dataset at {path}")
