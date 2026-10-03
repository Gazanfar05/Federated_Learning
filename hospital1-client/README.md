# Hospital 1 Client — Secure Federated Learning in Healthcare

This repository contains the Hospital 1 client for a multi-hospital federated learning setup. It keeps local patient data on the hospital machine, trains a local diabetes-prediction model, applies clipping and differential privacy, and submits only protected model-update artifacts to a central server over TLS 1.3 with mutual authentication.

## Purpose

Hospital 1 is an independent healthcare institution participating in federated learning with Laptop 1 as the central server. The client never sends raw patient records. It only shares model deltas, metadata, and security-related hashes.

## Architecture

- Local preprocessing and deterministic split
- PyTorch binary classifier
- Local training on Hospital 1 data only
- Gradient clipping before DP
- Gaussian noise injection
- Client-side masking for secure aggregation semantics
- mTLS over HTTPS/TLS 1.3 to the central server
- Heartbeat and retry logic
- Local checkpointing

## Installation

```bash
cd hospital1-client
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Python environment

The project targets Python 3.10+ and uses PyTorch, pandas, scikit-learn, requests/httpx, python-dotenv, and cryptography.

## Dataset setup

The repository includes a deterministic synthetic Hospital 1 diabetes dataset at `data/hospital1.csv`.

```bash
python run_client.py prepare-data
```

## Data partition

Hospital 1 uses a fixed deterministic split with `DATA_SPLIT_SEED=42`. The client does not share raw rows; only aggregated local metrics and protected updates are transmitted.

## Certificate setup

Certificates are stored under `certificates/`.

Create or replace:

- `ca.crt`
- `hospital1.crt`
- `hospital1.key`

This key is excluded from Git via `.gitignore`.

```bash
mkdir -p certificates
# generate CA and client certs if needed
openssl req -x509 -newkey rsa:2048 -sha256 -days 3650 -nodes \
  -keyout certificates/ca.key -out certificates/ca.crt -subj "/CN=Hospital1-CA"
openssl genrsa -out certificates/hospital1.key 2048
openssl req -new -key certificates/hospital1.key -out certificates/hospital1.csr \
  -subj "/CN=hospital_01"
openssl x509 -req -in certificates/hospital1.csr -CA certificates/ca.crt \
  -CAkey certificates/ca.key -CAcreateserial -out certificates/hospital1.crt \
  -days 3650 -sha256 -extfile <(printf "subjectAltName=DNS:localhost,IP:127.0.0.1\n")
chmod 600 certificates/hospital1.key
rm -f certificates/hospital1.csr certificates/ca.srl
```

## .env configuration

Edit `.env` based on `.env.example`:

```env
CLIENT_ID=hospital_01
SERVER_URL=https://127.0.0.1:8443
CA_CERT=certificates/ca.crt
CLIENT_CERT=certificates/hospital1.crt
CLIENT_KEY=certificates/hospital1.key
DATA_PATH=data/hospital1.csv
LOCAL_EPOCHS=3
LEARNING_RATE=0.001
BATCH_SIZE=32
DP_ENABLED=true
DP_NOISE_MULTIPLIER=0.5
DP_CLIPPING_NORM=1.0
DP_DELTA=1e-5
RETRY_ATTEMPTS=5
HEARTBEAT_INTERVAL=10
DATA_SPLIT_SEED=42
```

Update the server URL to Laptop 1’s actual LAN IP before deployment.

## How to find Laptop 1's IP

On the central server, run:

```bash
ipconfig
# or
ifconfig
# or
hostname -I
```

Then set:

```env
SERVER_URL=https://192.168.1.10:8443
```

## How to test connectivity

```bash
python run_client.py test-connection
```

This checks the server is reachable, TLS is valid, and the certificate is accepted.

## How to start Hospital 1

```bash
python run_client.py start
```

or:

```bash
python -m client.main start
```

## Federated-learning lifecycle

The client follows this lifecycle:

- DISCONNECTED
- CONNECTING
- AUTHENTICATING
- AUTHENTICATED
- WAITING_FOR_ROUND
- DOWNLOADING_MODEL
- LOCAL_TRAINING
- EVALUATING
- CLIPPING
- DP_PROTECTION
- SECURE_MASKING
- SUBMITTING_UPDATE
- SUBMITTED
- WAITING_FOR_NEXT_ROUND

## Local training

The model is trained using Hospital 1's local dataset only and uses a small MLP classifier.

Exact model used:

```text
Input -> Linear(8, 16) -> ReLU -> Dropout -> Linear(16, 8) -> ReLU -> Linear(8, 1)
```

Loss: `BCEWithLogitsLoss`

## Differential privacy

Update clipping is done before noise addition:

```text
norm = ||update||
if norm > C:
    update = update * C / norm
```

Gaussian noise is then applied with `DP_NOISE_MULTIPLIER` and `DP_DELTA`.

The client reports privacy metadata only in the API payload; it does not claim exact guarantee unless the server/accountant computes it.

## Secure aggregation

The client applies a client-side masked update schema designed to match the project’s secure-aggregation concept. It does not use a fake `base64`-encoded update as a security mechanism.

## TLS 1.3

The client uses HTTPS with certificate verification and mTLS:

- verifies the server CA certificate
- presents `hospital1.crt` and `hospital1.key`
- enforces certificate validation
- never sets `verify=False`

## Client authentication

The client authenticates using the fixed ID:

```text
hospital_01
```

The startup flow is:

1. Connect to server
2. TLS handshake
3. Client cert verification
4. Hospital identity verification
5. Authenticated

## Checkpointing

Checkpoints are stored under `models/`:

```text
models/local_round_001.pt
```

Checkpoint contents include:

- round id
- model version
- model state
- optimizer state
- training config

## Failure recovery

The client retries failed connections, re-authenticates, and avoids blindly resubmitting stale rounds.

## Testing

```bash
pytest -q
```

## Troubleshooting

- If PD package issues happen, reinstall requirements.
- If the server rejects the certificate, ensure CA and client cert validity.
- If the server is down, verify the `SERVER_URL` and LAN connectivity.
- If the dataset is missing, generate it again with `prepare-data`.

## Security limitations

This client follows the project contract and does not claim production-grade secure aggregation beyond the project’s defined masking and client-side protocol. Raw patient data never leaves this machine.
