# Diabetes dataset expansion report

## Provenance
These are synthetic research datasets generated from the three local 256-row CSV files. Hospital 1 documentation describes its source as deterministic synthetic data; provenance for Hospitals 2 and 3 was not established locally. No row is represented as a real patient.

## Method
A fixed-seed, per-hospital and per-outcome Gaussian copula models empirical feature ranks and correlations. Outcomes are sampled using each source hospital's observed prevalence. Values are constrained to each source hospital's observed support and integer features retain integer formatting. This is not clinically validated.

## Results
### hospital1
- Baseline rows: 256
- Expanded rows: 2000
- Baseline outcome counts: `{'0': 227, '1': 29}`
- Expanded outcome counts: `{'0': 1756, '1': 244}`
- Baseline outcome prevalence: 0.1133
- Expanded outcome prevalence: 0.1220
- Expanded duplicate rows: 0
- Feature statistics:
  - `Pregnancies`: baseline min=0, max=14, mean=3.27, sd=3.129; expanded min=0, max=14, mean=3.363, sd=3.124
  - `Glucose`: baseline min=0, max=105, mean=88.66, sd=16.46; expanded min=0, max=105, mean=88.54, sd=15.95
  - `BloodPressure`: baseline min=0, max=122, mean=65.27, sd=19.02; expanded min=0, max=120, mean=64.64, sd=19.67
  - `SkinThickness`: baseline min=0, max=60, mean=20.57, sd=14.14; expanded min=0, max=60, mean=20.09, sd=13.97
  - `Insulin`: baseline min=0, max=265, mean=44.81, sd=54.43; expanded min=0, max=264, mean=44.18, sd=53.19
  - `BMI`: baseline min=0, max=55, mean=30.07, sd=8.228; expanded min=0, max=53.62, mean=29.79, sd=8.412
  - `DiabetesPedigreeFunction`: baseline min=0.078, max=1.699, mean=0.4335, sd=0.2755; expanded min=0.0793, max=1.699, mean=0.432, sd=0.2661
  - `Age`: baseline min=21, max=68, mean=29.63, sd=9.684; expanded min=21, max=68, mean=29.94, sd=9.896
### hospital2
- Baseline rows: 256
- Expanded rows: 2000
- Baseline outcome counts: `{'0': 179, '1': 77}`
- Expanded outcome counts: `{'0': 1371, '1': 629}`
- Baseline outcome prevalence: 0.3008
- Expanded outcome prevalence: 0.3145
- Expanded duplicate rows: 0
- Feature statistics:
  - `Pregnancies`: baseline min=0, max=13, mean=3.785, sd=3.241; expanded min=0, max=13, mean=3.775, sd=3.219
  - `Glucose`: baseline min=105, max=130, mean=117, sd=7.497; expanded min=105, max=130, mean=116.9, sd=7.436
  - `BloodPressure`: baseline min=0, max=110, mean=69.37, sd=19.1; expanded min=0, max=109, mean=69.75, sd=17.42
  - `SkinThickness`: baseline min=0, max=54, mean=19.71, sd=16.03; expanded min=0, max=54, mean=19.37, sd=15.95
  - `Insulin`: baseline min=0, max=600, mean=71.94, sd=92.49; expanded min=0, max=551, mean=69.41, sd=87.63
  - `BMI`: baseline min=0, max=67.1, mean=31.66, sd=7.719; expanded min=0, max=64.58, mean=31.59, sd=7.127
  - `DiabetesPedigreeFunction`: baseline min=0.088, max=1.731, mean=0.4674, sd=0.3222; expanded min=0.08836, max=1.716, mean=0.4719, sd=0.3085
  - `Age`: baseline min=21, max=72, mean=32.43, sd=10.68; expanded min=21, max=71, mean=32.89, sd=10.5
### hospital3
- Baseline rows: 256
- Expanded rows: 2000
- Baseline outcome counts: `{'0': 94, '1': 162}`
- Expanded outcome counts: `{'0': 729, '1': 1271}`
- Baseline outcome prevalence: 0.6328
- Expanded outcome prevalence: 0.6355
- Expanded duplicate rows: 0
- Feature statistics:
  - `Pregnancies`: baseline min=0, max=17, mean=4.48, sd=3.621; expanded min=0, max=16, mean=4.523, sd=3.588
  - `Glucose`: baseline min=130, max=199, mean=157.1, sd=19.38; expanded min=130, max=199, mean=156.5, sd=19.02
  - `BloodPressure`: baseline min=0, max=114, mean=72.67, sd=19.3; expanded min=0, max=114, mean=73.82, sd=18.49
  - `SkinThickness`: baseline min=0, max=99, mean=21.32, sd=17.53; expanded min=0, max=90, mean=21.77, sd=17.27
  - `Insulin`: baseline min=0, max=846, mean=122.6, sd=159.1; expanded min=0, max=798, mean=120.4, sd=153
  - `BMI`: baseline min=0, max=59.4, mean=34.24, sd=7.125; expanded min=0.1707, max=57.96, mean=34.41, sd=6.723
  - `DiabetesPedigreeFunction`: baseline min=0.088, max=2.42, mean=0.5148, sd=0.3836; expanded min=0.08863, max=2.412, mean=0.5018, sd=0.3528
  - `Age`: baseline min=21, max=81, mean=37.66, sd=13.22; expanded min=21, max=79, mean=37.84, sd=12.83

## Cross-hospital overlap
- hospital1__hospital2: 0 exact row overlaps
- hospital1__hospital3: 0 exact row overlaps
- hospital2__hospital3: 0 exact row overlaps

## Validation
- Structural status: **PASS**
- Required checks: nine-column schema/order, numeric features, binary outcomes, finite values, exact row counts, duplicate detection, overlap detection, and review ranges.
- Compatibility: the current OpenFL loader expects exactly eight numeric features plus `Outcome`; the generated files use that unchanged schema.

## Limitations and reproducibility
- These 6,000 rows are synthetic and do not represent 6,000 independently observed patients or clinical evidence.
- Original CSVs remain unchanged; baseline copies are stored under `datasets/baseline/`.
- Patient datasets remain outside Docker image/source control; use separate read-only mounts or an explicit local copy step to select expanded data. The active OpenFL plan and Compose file were not changed.
- Reproduce with: `python openfl-diabetes-workspace/scripts/expand_diabetes_data.py --target-count 2000 --seed 20261019`
- Validate with: `python openfl-diabetes-workspace/scripts/validate_diabetes_data.py`
