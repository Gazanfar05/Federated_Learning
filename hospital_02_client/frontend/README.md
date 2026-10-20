# Hospital 02 Frontend - Dataset Quality and Evaluation Portal

Hospital identity:

- `hospital_02`
- `Hospital 02 - Data Quality and Evaluation Unit`

This frontend is designed for local dataset integrity and evaluation visibility while preserving privacy constraints.

## Design profile

- Dark navy analytical interface with cyan/blue accents
- Technical typography with compact research-oriented panels
- Strong empty/error/loading handling
- No fabricated training or evaluation metrics
- No patient-level record display

## What this portal includes

Pages:

- Data Intelligence Overview
- Dataset Validation
- Feature Quality
- Evaluation Laboratory
- Model Comparison (read-only)
- Dataset and Model History (timeline)

Architecture modules:

- `js/config/hospital-config.js`: Hospital identity and runtime defaults
- `js/services/api-service.js`: Centralized API service
- `js/components/portal-controller.js`: Page orchestration and data refresh logic
- `js/components/state-components.js`: Reusable rendering for loading/empty/error and metric blocks
- `js/components/charts.js`: Lightweight chart rendering
- `js/utils/dom.js`: Safe text and DOM utilities

## Run locally

```bash
cd /Users/aman/Federated_Learning/hospital_02_client/frontend
python3 serve.py --port 3002 --open
```

Then open:

- `http://localhost:3002`

## Configuration

Use the in-app API Settings panel to configure:

- Central API base URL (default `https://127.0.0.1:8443`)
- Local agent API base URL (optional; required for dataset/evaluation reports)
- Request timeout
- Stale-data threshold

Settings are saved in browser local storage under `hospital_02_frontend_settings`.

## Verified vs proposed endpoints

See:

- `ENDPOINT_INVENTORY.md`

The portal only assumes central endpoints that are verified in the current server code. All local-agent routes are treated as proposed contracts.

## Privacy and safety guarantees in UI behavior

- No raw row rendering
- No CSV upload operations
- No browser logs with sensitive dataset contents
- No synthetic local sample counts, class distributions, or evaluation trends
- Explicit unavailable states when real data is absent

## Current integration status

Central status/model metadata is supported through verified server endpoints.

Local dataset validation and local evaluation require a future hospital-local agent exposing approved aggregate summaries.

See:

- `INTEGRATION_GAPS.md`
