# Hospital 2 Client for Secure Federated Learning

Hospital 2 is the client-side participant for a privacy-preserving diabetes prediction demo. It keeps raw patient data on this laptop, trains locally, protects model updates, and submits only the server-approved update payload over TLS with mutual authentication.

## Project Purpose

This client is built for Laptop 3 in a 4-laptop federated learning setup:

- Laptop 1: central federated learning server
- Laptop 2: Hospital 1 client
- Laptop 3: Hospital 2 client, this machine
- Laptop 4: Hospital 3 client

The client is intentionally conservative about outbound data. It never sends raw records, labels, batches, or CSV contents to the server.

## Hospital 2 Role

This client must identify as:

- `CLIENT_ID=hospital_02`
- `HOSPITAL_NAME=Hospital 2`

It uses:

- `data/hospital2.csv`
- `certificates/hospital2.crt`
- `certificates/hospital2.key`
- `certificates/ca.crt`

## Architecture

Core modules live under [app](app):

- [config.py](app/config.py): environment-driven configuration
- [preprocessing.py](app/preprocessing.py): local CSV validation, imputation, scaling, split, and DataLoader creation
- [training.py](app/training.py): the shared diabetes MLP and local training loop
- [differential_privacy.py](app/differential_privacy.py): clipping and Gaussian noise
- [secure_aggregation.py](app/secure_aggregation.py): deterministic client-side masking
- [serialization.py](app/serialization.py): canonical JSON serialization and hashing
- [networking.py](app/networking.py): TLS 1.3 + mTLS server client
- [checkpoint.py](app/checkpoint.py): local checkpoint save/load
- [heartbeat.py](app/heartbeat.py): periodic heartbeat worker
- [client.py](app/client.py): state machine and round orchestration

## Installation

Create and activate a virtual environment, then install dependencies:

```bash
cd /Users/aman/Federated_Learning/hospital_02_client
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If `python-dotenv` is not installed, the client still imports cleanly, but `.env` loading will be unavailable until dependencies are installed.

## Dataset Setup

Place the Hospital 2 dataset at:

- [data/hospital2.csv](data/hospital2.csv)

The sample CSV in this repository is development-only. Replace it with the assigned Hospital 2 partition when available.

Required columns:

- `Pregnancies`
- `Glucose`
- `BloodPressure`
- `SkinThickness`
- `Insulin`
- `BMI`
- `DiabetesPedigreeFunction`
- `Age`
- `Outcome`

## Certificate Setup

Place certificates under [certificates](certificates):

- `ca.crt`
- `hospital2.crt`
- `hospital2.key`

The client uses TLS 1.3 and verifies the server certificate against `ca.crt`. It never disables verification and never falls back to HTTP.

### Certificate naming

Use the Hospital 2 identity consistently:

- `hospital_02`
- `hospital2.crt`
- `hospital2.key`

Do not reuse Hospital 1 files such as `hospital1.crt` or `hospital1.key`.

## .env Configuration

Copy `.env.example` to `.env` and edit the server address:

```env
CLIENT_ID=hospital_02
HOSPITAL_NAME=Hospital 2
SERVER_URL=https://192.168.1.10:8443
CA_CERT=certificates/ca.crt
CLIENT_CERT=certificates/hospital2.crt
CLIENT_KEY=certificates/hospital2.key
DATA_PATH=data/hospital2.csv
LOCAL_EPOCHS=3
BATCH_SIZE=32
LEARNING_RATE=0.001
DP_ENABLED=true
DP_CLIP_NORM=1.0
DP_EPSILON=2.0
DP_DELTA=1e-5
HEARTBEAT_INTERVAL=10
REQUEST_TIMEOUT=15
MAX_RETRIES=3
```

Never hard-code Laptop 1’s IP in the source code. Set it only through `.env`.

## How to Connect to Laptop 1

Edit `SERVER_URL` so it points to the server’s LAN IP and port 8443:

```env
SERVER_URL=https://<CENTRAL_SERVER_IP>:8443
```

The current integration contract expects the server to expose at least:

- `GET /health`
- `POST /auth/register`
- `POST /auth/heartbeat`
- `POST /training/join`
- `GET /training/model?client_id=hospital_02`
- `POST /training/update`
- `POST /training/complete`
- `GET /training/status`

## How to Run

Validate config and dataset:

```bash
python run_client.py --check
```

Check server health:

```bash
python run_client.py --health
```

Run local-only training:

```bash
python run_client.py --train
```

Resume from the latest checkpoint and continue polling the server:

```bash
python run_client.py --resume
```

Participate in a specific round:

```bash
python run_client.py --round 1
```

Start normal long-running client operation:

```bash
python run_client.py
```

## Federated Learning Round Flow

The client follows this state sequence:

`IDLE -> AUTHENTICATING -> JOINING_ROUND -> RECEIVING_GLOBAL_MODEL -> LOCAL_TRAINING -> UPDATE_CLIPPING -> DIFFERENTIAL_PRIVACY -> SECURE_AGGREGATION -> HASHING -> SUBMITTING_UPDATE -> WAITING_FOR_AGGREGATION -> ROUND_COMPLETE`

The implementation keeps the state machine explicit in [app/client.py](app/client.py).

## Local Preprocessing

Preprocessing is entirely local:

1. Load `data/hospital2.csv`
2. Validate required columns
3. Separate features and labels
4. Median impute missing values
5. Standardize features locally
6. Split into train and validation sets
7. Convert to PyTorch tensors and DataLoaders

No raw records are transmitted during preprocessing.

## Local Model

The client uses the same shared architecture as the server:

```text
Input(8) -> Linear(8,16) -> ReLU -> Dropout(0.1) -> Linear(16,16) -> ReLU -> Linear(16,1)
```

Loss: `BCEWithLogitsLoss`

Optimizer: `Adam`

## Differential Privacy

The client applies privacy in this order:

1. Compute local model update
2. Clip the update to `DP_CLIP_NORM`
3. Add calibrated Gaussian noise when `DP_ENABLED=true`
4. Mask the protected update for secure aggregation semantics

Privacy metadata is logged locally. The client does not claim stronger guarantees than the implemented mechanism provides.

## Secure Aggregation

The client masks updates locally before submission.

Important:

- This is a client-side masking layer intended to match the classroom server contract
- It is not a substitute for full production cryptographic secure aggregation
- The payload shape must remain compatible with the server schema

The server expects `protected_update` to be a flat list of floats and forbids extra JSON fields.

## TLS 1.3 and mTLS

The networking layer uses:

- TLS 1.3 only
- server CA verification via `certificates/ca.crt`
- client certificate authentication via `certificates/hospital2.crt` and `certificates/hospital2.key`

The client never uses `verify=False` and never downgrades to plaintext HTTP.

## Checkpointing

Local checkpoints are stored under [checkpoints](checkpoints) as files like:

```text
round_001.pt
round_002.pt
round_003.pt
```

Each checkpoint stores:

- `client_id`
- `round_id`
- `model_version`
- model state
- local config
- local metrics

## Dropout Recovery

If Hospital 2 loses power or Wi-Fi:

1. Restart the client
2. Restore the latest checkpoint
3. Re-authenticate with the server
4. Query current server status
5. Resume safely without submitting stale round data

## Testing

The test suite covers:

- dataset loading and split behavior
- model creation and local training
- update clipping and DP noise
- secure aggregation masking round-trip
- deterministic serialization and hashing
- checkpoint save/load and resume
- TLS configuration

Run tests after installing dependencies:

```bash
pytest -q
```

## Troubleshooting

If you see import errors:

- confirm the virtual environment is activated
- run `pip install -r requirements.txt`
- verify `SERVER_URL` uses `https://`
- confirm `ca.crt`, `hospital2.crt`, and `hospital2.key` exist

If the server rejects the client:

- confirm `CLIENT_ID=hospital_02`
- confirm `certificate_identity` on the server side resolves to `hospital_02`
- confirm the certificate files belong to Hospital 2

If training fails locally:

- check that `data/hospital2.csv` has the expected columns
- ensure the dataset contains both classes when possible

## Security Limitations

This repository is designed for a classroom / demo environment.

What it does well:

- keeps raw patient rows local
- uses TLS with certificate verification
- uses deterministic update serialization and SHA-256 hashing
- applies update clipping, DP noise, and masking before submission

What it does not claim:

- production-grade cryptographic secure aggregation
- formal differential privacy accounting across multiple rounds
- resilience against a malicious server

## What Never Leaves Hospital 2

The following remain on this laptop:

- raw patient records
- CSV contents
- patient IDs
- individual labels
- raw training batches
- local database contents

The server only receives protected model-update payloads, round metadata, and heartbeat/authentication messages.

## Integration Notes for Laptop 1

The current server contract exposes model metadata, not raw model weights. This client is ready for that contract and uses the shared `DiabetesMLP` architecture and the fixed update schema.

If Laptop 1 later adds a true model-weight download endpoint, hook it into [app/networking.py](app/networking.py) and [app/client.py](app/client.py) where the model metadata is currently fetched.
