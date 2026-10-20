# Missing Backend Operations For Real Hospital 02 Integration

The frontend is ready to render approved aggregate summaries, but the following hospital-local operations are still required.

## 1. Local dataset validation report endpoint

Needed to populate Dataset Validation and part of Data Intelligence Overview.

Suggested response fields:

- `required_feature_columns_check`
- `missing_value_check`
- `numeric_type_check`
- `target_value_check`
- `duplicate_detection`
- `sample_count`
- `class_balance`
- `split_info`
- `validation_warnings`
- `generated_at`

## 2. Local feature quality endpoint

Needed to render feature completeness, valid/invalid ratios, and range warnings.

Suggested response fields:

- `feature_completeness`
- `valid_invalid_summary`
- `range_warning_count`
- `schema_compatibility`
- `summary_status`
- `features[]` with per-feature aggregate valid percentages

## 3. Local evaluation endpoints

Needed for Evaluation Laboratory and Model Comparison.

Suggested routes:

- `GET /evaluation/latest`
- `GET /evaluation/history`
- `GET /evaluation/comparison`

Suggested fields:

- accuracy, loss, validation sample count
- model version, round number
- evaluation timestamp

## 4. Local timeline endpoint

Needed for Dataset and Model History page.

Suggested route:

- `GET /timeline/events`

Suggested event types:

- dataset validation completed/failed
- model metadata changed
- local evaluation recorded
- warning emitted
- operation failure

## 5. Data freshness metadata

Each local aggregate response should include timestamps so stale-data labeling is reliable.

## 6. Approved aggregate-only policy

Each endpoint should return aggregate summaries only. No patient-level values should be exposed to browser clients.
