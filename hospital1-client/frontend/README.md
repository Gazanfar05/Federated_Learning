# Hospital 01 Frontend

This frontend is a modular, read-only clinical research portal for Hospital 01. It is designed to be connected to the real backend later without pretending that non-existent endpoints exist.

## Purpose

The portal provides a premium hospital dashboard shell for:
- overview and federation status
- global model metadata
- dataset readiness state
- training workspace placeholder
- evaluation readiness
- update review placeholder
- activity history

It intentionally avoids inventing data, simulated training, or fake model artifacts.

## Folder structure

- `index.html` — application shell
- `styles.css` — medical research styling
- `config.js` — fixed hospital identity and API base URL
- `api.js` — centralized API client
- `components.js` — reusable UI helpers
- `app.js` — initialization and view rendering

## How to run locally

From the project root:

```bash
cd hospital1-client/frontend
python3 -m http.server 8000
```

Then open:

```text
http://localhost:8000
```

Optional API override:

```text
http://localhost:8000?api=https://127.0.0.1:8443
```

If the central server is not running, the UI remains local-only and displays unavailable states clearly.

## Verified endpoints used

This frontend only calls routes that are already present in the existing project:

- `GET /health`
- `GET /training/status`
- `GET /training/model?client_id=hospital_01`
- `GET /monitoring/clients`
- `GET /monitoring/round`
- `GET /monitoring/metrics`
- `GET /monitoring/privacy`
- `GET /monitoring/anomalies`

## Future endpoints required for full integration

These are placeholders for real backend work that does not exist yet:

- dataset validation status endpoint
- dataset schema validation result endpoint
- local evaluation metrics endpoint
- OpenFL training job metadata endpoint
- model artifact download endpoint
- model artifact digest verification endpoint
- operation history endpoint for real events
- update review metadata endpoint

## Design notes

- White and off-white surfaces with deep navy, teal, and blue accents
- clinical research interface with professional spacing and clear hierarchy
- modular, easy to extend for real API contracts
- read-only placeholder states instead of fake training data

## Security caveats

- no certificates, private keys, passwords, or patient records are embedded in frontend code
- hospital identity is treated as a local identifier only, not proof of authentication
- no raw patient data is uploaded from the browser
