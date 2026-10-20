# Secure Federated Learning in Healthcare

## Privacy-Preserving Diabetes Prediction

> **Status: Development and integration in progress.** The central
> dashboard, demo-coordinator endpoints, workspace configuration,
> metadata placeholders, and OpenFL lifecycle events are not by
> themselves proof that a live multi-hospital federation has trained,
> exchanged model updates, or distributed a global model.

## Overview

This academic project explores federated learning for diabetes
prediction across three intended hospital collaborators. The goal is to
let each hospital train locally and contribute model updates to a shared
model without routinely centralizing raw patient records.

The project includes a central FastAPI application and dashboard, an
OpenFL 1.9 workspace, and three planned hospital portals.

## Goals

-   Explore privacy-preserving collaborative machine learning for
    diabetes prediction.
-   Keep raw hospital datasets local during local training.
-   Use OpenFL 1.9 as the intended federation framework.
-   Monitor available workspace configuration, metrics, and structured
    events.
-   Build hospital portals for clinical workflow, dataset quality, and
    model integrity/audit.
-   Distinguish configured, observed, unavailable, and cryptographically
    verified states.

## Intended workflow

1.  Each hospital validates its local dataset.
2.  Each collaborator trains the model locally.
3.  Collaborators produce updates for a federation round.
4.  The OpenFL aggregator combines eligible updates.
5.  The global model is distributed to collaborators.
6.  Monitoring views display evidence from real artifacts, logs, and
    runtime operations.

This is the intended workflow, not a claim that every step is already
working end to end.

## Architecture

``` text
                 Central machine
        +--------------------------------+
        | Central dashboard / FastAPI    |
        | OpenFL aggregator (intended)   |
        | Monitoring and audit adapters  |
        +---------------+----------------+
                        |
              OpenFL communication
             /          |          \
    +-------------+ +-------------+ +-------------+
    | Hospital 01 | | Hospital 02 | | Hospital 03 |
    | Local data  | | Local data  | | Local data  |
    | Local train | | Local train | | Local train |
    | Portal      | | Portal      | | Portal      |
    +-------------+ +-------------+ +-------------+
```

The diagram describes the intended design. The FastAPI demo coordinator
and OpenFL runtime are separate components. A demo API response is not
proof that an OpenFL transport operation occurred.

## Technology

-   Python
-   FastAPI
-   OpenFL 1.9
-   PyTorch
-   HTML, CSS, and JavaScript for the dashboard and planned standalone
    portals
-   SQLite/OpenFL tensor database artifacts where present
-   TLS and certificates in the intended secure communication setup

Use the repository's dependency and deployment files as the source of
truth for exact versions and commands.

## Repository structure

The exact tree may differ by branch; this is the intended organization.

``` text
secure-federated-learning/
├── server/                         # FastAPI backend and services
├── frontend/                       # Central dashboard
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── metrics/                        # Metrics artifacts, if generated
├── logs/                            # Logs, if generated
├── checkpoints/                     # Checkpoints, if generated
├── certificates/                    # Handle certificate material carefully
├── openfl-diabetes-workspace/       # OpenFL plan and source
│   ├── plan/
│   └── src/
├── hospital-portals/                # Intended portal destination
│   ├── hospital-01/
│   ├── hospital-02/
│   └── hospital-03/
├── requirements.txt
├── run_server.py
└── README.md
```

Do not assume every directory exists in every checkout. Keep secrets and
private data out of version control.

## Requirements

Check `requirements.txt`, the Dockerfile, Compose configuration, and
OpenFL workspace instructions for exact versions and commands. The
current development setup has used Python 3.10-compatible environments.

## Run the central application

From the repository root on macOS/Linux:

``` bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python run_server.py
```

In the current development setup, the dashboard has been expected at
`http://127.0.0.1:8443/`. Confirm the actual scheme, host, and port
printed by the application. If HTTPS is configured, use the
corresponding `https://` URL and certificate setup. Do not permanently
bypass browser certificate warnings.

For access from other laptops, confirm the server bind address, LAN
reachability, and firewall rules. Do not expose a development server
directly to the public internet.

## OpenFL workspace

The OpenFL workspace is intended to define the plan, collaborators, data
configuration, task runner, and event callback.

Before running a real experiment:

1.  Confirm the OpenFL version and follow the workspace's actual startup
    instructions.
2.  Check collaborator configuration and local dataset paths.
3.  Verify network reachability and certificate/trust configuration.
4.  Start the aggregator and collaborators using the documented OpenFL
    commands.
5.  Inspect runtime logs and generated model artifacts.
6.  Confirm local training, update exchange, aggregation, and
    global-model distribution.

A successful import check, configuration parse, container build, or
isolated fixture test is not evidence of a successful federation.

## Monitoring API

These routes have been identified in the current development
implementation. Verify response schemas and behavior in the current
source before relying on them.

  ---------------------------------------------------------------------------------
  Endpoint                          Method                  Meaning / limitation
  --------------------------------- ----------------------- -----------------------
  `/health`                         GET                     Central API health

  `/server-status`                  GET                     Application/server
                                                            status

  `/model/current?client_id=...`    GET                     Model metadata; not
                                                            necessarily artifact
                                                            bytes

  `/training/model?client_id=...`   GET                     Model/training
                                                            metadata; do not assume
                                                            artifact download

  `/training/status`                GET                     Demo-coordinator
                                                            training state

  `/training/join`                  POST                    Demo-coordinator
                                                            operation

  `/training/update`                POST                    Demo-coordinator update
                                                            route, not proof of
                                                            OpenFL transport

  `/training/complete`              POST                    Demo-coordinator
                                                            operation

  `/training/admin/start-round`     POST                    Demo-coordinator round
                                                            control

  `/training/admin/stop-round`      POST                    Demo-coordinator round
                                                            control

  `/training/admin/recover`         POST                    Demo-coordinator
                                                            recovery

  `/monitoring/clients`             GET                     Application-level
                                                            client monitoring

  `/monitoring/round`               GET                     Application-level round
                                                            information

  `/monitoring/metrics`             GET                     Application-level
                                                            metrics

  `/monitoring/privacy`             GET                     Application-level
                                                            privacy information

  `/monitoring/anomalies`           GET                     Application-level
                                                            anomaly information

  `/monitoring/openfl`              GET                     Read-only OpenFL
                                                            workspace monitoring

  `/monitoring/openfl/metrics`      GET                     Metrics available from
                                                            workspace artifacts

  `/monitoring/openfl/events`       GET                     Structured lifecycle
                                                            events when configured
  ---------------------------------------------------------------------------------

POST routes can change application state. Review their schemas and
authorization before using them. Do not casually trigger state-changing
operations from a frontend.

### Events and integrity

The OpenFL event endpoint depends on a configured JSONL event source.
The API and callback must point to the same intended log file. Missing
event sources should be reported as unavailable.

Lifecycle events such as training-started do not prove that a model was
transmitted, an update accepted, or a global model received. A metadata
placeholder such as `sha256:global_model_v1` is not a cryptographic
digest of a model artifact. Genuine verification requires the actual
artifact bytes, an independently computed digest, and a trusted expected
digest.

## Hospital portals

### Hospital 01 --- Clinical Research & Training

**ID:** `hospital_01`

Planned focus: clinical research overview, dataset readiness, model
metadata, training status where genuine evidence exists, evaluation
results, and read-only activity information.

### Hospital 02 --- Dataset Quality & Evaluation

**ID:** `hospital_02`

Planned focus: local schema validation, missing values, numeric feature
and target checks, class distribution, train/validation split, and
evaluation results computed from actual local data. Raw patient records
must not be uploaded for dashboard convenience.

### Hospital 03 --- Model Integrity, Security & Audit

**ID:** `hospital_03`

Planned focus: model manifest and artifact integrity, API health,
session/certificate state only when supported by a real backend
contract, read-only update review, structured audit history, and
explicit unavailable states.

### Shared portal conventions

-   Keep each portal in its own directory.
-   Prefer a consistent frontend stack.
-   Centralize the configurable API base URL.
-   Use fixed, documented hospital IDs.
-   Use existing verified endpoints; document future endpoints
    separately.
-   Include loading, timeout, error, unavailable, and stale-data states.
-   Render server-provided text safely.
-   Never put credentials or private keys in frontend code.
-   Do not implement training or update submission as a fake UI-only
    operation.

## GitHub collaboration

Recommended branches:

  -----------------------------------------------------------------------
  Contributor             Branch                  Scope
  ----------------------- ----------------------- -----------------------
  Project owner           `main`                  Central backend,
                                                  OpenFL, approved
                                                  integration

  Teammate 1              `hospital-01-portal`    Hospital 01 portal

  Teammate 2              `hospital-02-portal`    Hospital 02 portal

  Teammate 3              `hospital-03-portal`    Hospital 03 portal
  -----------------------------------------------------------------------

Suggested process:

1.  Pull the latest `main`.
2.  Create/switch to the assigned feature branch.
3.  Work only inside the assigned portal directory.
4.  Test the frontend and update its README.
5.  Commit and push the feature branch.
6.  Open a pull request against `main`.
7.  Review the diff and tests before merging.

If work has already been committed directly to `main`, coordinate before
rewriting history or moving commits.

Do not commit `.env` files containing secrets, private keys, sensitive
certificate material, patient records, virtual environments, caches, or
unnecessary generated artifacts. Review staged files before every
commit.

## Privacy and security

-   Keep raw patient data on the relevant hospital machine.
-   Use synthetic or approved de-identified data for development.
-   Never upload patient records to GitHub, issue trackers, or
    screenshots.
-   Do not hard-code secrets or private keys.
-   A request-body hospital ID is not identity proof.
-   Use correctly configured TLS, certificate validation,
    authentication, and authorization.
-   Treat model updates as potentially sensitive.
-   Consider robust aggregation, gradient clipping, anomaly detection,
    and differential privacy as distinct controls with different
    trade-offs.
-   Record provenance for security-relevant events.
-   Do not claim HIPAA/GDPR compliance merely because a control is
    mentioned in documentation.

## Current limitations

-   The central demo coordinator is separate from the OpenFL runtime.
-   Workspace configuration does not prove that a federation has run.
-   Monitoring adapters inspect available configuration, artifacts,
    metrics, and structured events; they do not prove every runtime
    operation.
-   Historical metric series may not be available even when a
    best-so-far metric exists.
-   The event callback records lifecycle events, not proof of model
    transfer or receipt.
-   Logs on physical hospital machines are not automatically collected
    centrally.
-   Model metadata endpoints do not necessarily return artifact bytes.
-   Placeholder hashes are not cryptographic artifact digests.
-   Hospital portals may require future backend contracts for genuine
    local-agent status, authentication, artifact verification, and
    update transport.

Update this section only when limitations are resolved and validated.

## Testing and verification

### Frontend checks

-   Portal renders when the central API is unavailable.
-   Loading, timeout, retry, empty, and stale states work.
-   Server-provided messages are rendered safely.
-   No patient records are uploaded.
-   Each portal uses the correct hospital ID and API base URL.

### Backend / monitoring checks

-   Run the repository's existing test suite.
-   Test missing and malformed workspace artifacts.
-   Verify missing event sources are reported as unavailable.
-   Verify placeholder hashes are not treated as digests.
-   Verify lifecycle events are not interpreted as model-transfer
    evidence.

### End-to-end federation

Only report a successful federation after evidence confirms that the
aggregator starts, collaborators connect to the actual OpenFL runtime,
local training executes, updates are exchanged, aggregation produces a
global model, and collaborators receive that model. Record the
environment, commands, logs, artifacts, and metrics used to validate the
run.

## Future work

-   Complete and review the three hospital portals.
-   Define stable backend contracts for hospital-side operations.
-   Implement authenticated hospital identity and session handling.
-   Implement artifact retrieval and genuine digest verification.
-   Design a safe collection mechanism for structured events from
    separate hospital machines.
-   Connect portals to real collaborator-side status and training
    operations.
-   Complete OpenFL 1.9 integration across physical laptops.
-   Validate local training, update exchange, aggregation, and
    global-model distribution end to end.
-   Test collaborator dropout, invalid updates, recovery, and network
    failures.
-   Document privacy parameters actually used.

## Disclaimer

This project is for academic and educational use. It is not intended for
clinical diagnosis, treatment decisions, or production deployment.
Predictions are not a substitute for professional medical advice. Do not
use real patient information without appropriate authorization,
governance, and safeguards.

------------------------------------------------------------------------

**Project:** Secure Federated Learning in Healthcare\
**Use case:** Privacy-preserving diabetes prediction\
**Intended federation framework:** OpenFL 1.9\
**Status:** Development and integration in progress
