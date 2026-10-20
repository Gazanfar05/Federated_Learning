# Hospital 02 Frontend Endpoint Inventory

This document distinguishes verified endpoints from proposed contracts.

## Verified central endpoints (implemented in secure-federated-learning server)

- `GET /health`
- `GET /training/status`
- `GET /training/model?client_id=hospital_02`
- `GET /monitoring/clients`

These routes are currently used by this frontend and are considered verified.

## Proposed local-agent endpoints (not currently implemented in this repository)

These routes are contracts for a future hospital-local validation/evaluation agent:

- `GET /dataset/validation/latest`
- `GET /dataset/validation/history`
- `GET /dataset/features/quality/latest`
- `GET /evaluation/latest`
- `GET /evaluation/history`
- `GET /evaluation/comparison?left_version=<x>&right_version=<y>`
- `GET /timeline/events`

The frontend treats these endpoints as optional. If unavailable, the UI shows explicit empty/unavailable states.

## Explicit non-goals in this frontend

- No raw patient record retrieval.
- No CSV upload from browser to central server.
- No training trigger, model update submission, or federation control operations.
- No fabricated local quality or evaluation metrics.
