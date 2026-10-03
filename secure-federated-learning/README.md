# Secure Federated Learning in Healthcare — Central Server

This repository contains the central server for a 4-laptop mini-project that demonstrates secure federated learning for diabetic prediction while keeping raw patient data on the hospital laptops.

## Project overview

The system has four machines:

- Laptop 1: Central server
- Laptop 2: Hospital 1 client
- Laptop 3: Hospital 2 client
- Laptop 4: Hospital 3 client

The central server coordinates training rounds and receives only protected model updates. Hospital laptops train locally on private data and send metadata plus aggregated protected updates. The server does not receive raw patient records, features, labels, or local datasets.

## Architecture

```text
Hospital 1        Hospital 2        Hospital 3
   |                 |                 |
   | TLS 1.3 + mTLS | TLS 1.3 + mTLS | TLS 1.3 + mTLS
   v                 v                 v
      -------------------------------
              Central Server
      - authenticates clients
      - validates updates
      - runs security monitoring
      - performs robust aggregation
      - saves checkpoints
      - tracks differential privacy metrics
```

## Central server responsibilities

The server is responsible for:

- client registration and authentication
- global model maintenance
- model distribution to hospitals
- training round tracking
- validation and anomaly detection
- secure aggregation and robust aggregation
- FedAvg weighted model merging
- checkpoint persistence and recovery
- monitoring and health endpoints

## Network architecture

The central server listens on a LAN IP rather than localhost-only. Configure via environment variables:

```bash
SERVER_HOST=0.0.0.0
SERVER_PORT=8443
```

Hospital clients connect to the server using the server laptop's LAN IP:

```text
https://192.168.1.10:8443
```

Replace the IP with the actual server machine address on the local network.

## Installation

1. Create a virtual environment:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Initialize directories:

```bash
python scripts/initialize_server.py
```

4. Generate certificates for development:

```bash
python scripts/generate_certificates.py
```

5. Start the server:

```bash
cd secure-federated-learning
python run_server.py
```

If your shell is already in the parent `Federated_Learning` directory, use:

```bash
python -m uvicorn server.main:app --app-dir secure-federated-learning --host 0.0.0.0 --port 8443
```

## Virtual environment

Use a project-local virtual environment to keep dependencies isolated.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

## Dependencies

The project uses:

- FastAPI
- Uvicorn
- Pydantic
- PyTorch
- NumPy
- Pandas
- scikit-learn
- cryptography
- pytest
- python-dotenv

## Certificate generation

Development certificates are generated in the `certificates` directory. The script creates:

- `ca.crt`
- `server.crt`
- `server.key`
- `hospital_01.crt` / `hospital_01.key`
- `hospital_02.crt` / `hospital_02.key`
- `hospital_03.crt` / `hospital_03.key`

Run:

```bash
python scripts/generate_certificates.py
```

## Configuration

The main runtime settings are loaded from `.env` and `.env.example` is the template.

```env
SERVER_HOST=0.0.0.0
SERVER_PORT=8443
NUM_ROUNDS=5
MIN_CLIENTS=2
MAX_CLIENTS=3
LOCAL_EPOCHS=3
ANOMALY_THRESHOLD=0.80
DP_EPSILON_TARGET=2.0
DP_DELTA=1e-5
DP_CLIPPING_NORM=1.0
TLS_ENABLED=true
TLS_CERT_FILE=certificates/server.crt
TLS_KEY_FILE=certificates/server.key
TLS_CA_FILE=certificates/ca.crt
```

## Starting server

```bash
cd secure-federated-learning
source .venv/bin/activate
python run_server.py
```

The server binds to `0.0.0.0:8443` by default and uses TLS 1.3 when configured.

## Connecting hospital clients

Hospital clients should use the server laptop's actual LAN IP. They must be configured with:

- `client_id`: `hospital_01`, `hospital_02`, or `hospital_03`
- certificate chain pointing to the CA and the client certificate
- API base URL like `https://192.168.1.10:8443`
- TLS 1.3 enabled with client verification

The central server rejects unknown clients.

## Federated training lifecycle

```text
Initialize global model
    |
    v
Round 1
  - hospital clients request model
  - local training on private data
  - protected updates submitted
  - server authenticates and validates
  - anomaly detection and robust aggregation
  - FedAvg update
  - checkpoint saved
    |
    v
Round 2 ... Round N
```

Default values:

- `NUM_ROUNDS = 5`
- `MIN_CLIENTS = 2`
- `MAX_CLIENTS = 3`
- `LOCAL_EPOCHS = 3`

## FedAvg explanation

The server implements weighted FedAvg:

```text
global_model = sum_k (n_k * W_k) / sum_k n_k
```

where:

- `W_k` is the client model state
- `n_k` is the number of local training samples

The implementation is in `server/federated/fedavg.py`.

## Secure aggregation explanation

This project uses an academic secure aggregation pattern:

```text
Client update -> mask -> protected update -> server
                                            |
                                combined masked updates
                                            |
                                            v
                                      mask cancellation
                                            |
                                            v
                                        aggregate result
```

This demonstrates the concept without claiming production-grade cryptography.

> TLS protects data while it is traveling between hospitals and the server. TLS alone does not prevent the server from seeing a decrypted individual update. Secure aggregation is therefore a separate privacy layer.

## Differential privacy explanation

The hospitals perform their own local clipping and noise addition. The server tracks the corresponding privacy metadata:

- epsilon
- delta
- clipping norm
- noise multiplier
- number of rounds

The monitoring endpoint exposes current values at `/monitoring/privacy`.

## Anomaly detection

The server computes a score based on:

- update norm magnitude
- cosine similarity with the reference/global update
- unusual parameter deviations

If the score exceeds the configured threshold, the update is marked suspicious.

## Robust aggregation

Suspicious updates are rejected or down-weighted before FedAvg. This makes the training more resilient to simulated model poisoning.

## Client dropout

Clients can disconnect during a round. The server does not crash; it continues aggregation when the minimum quorum is satisfied and otherwise pauses safely.

## Checkpoint recovery

After each completed round, the server saves a checkpoint under `checkpoints/round_XXX/`.

Saved state includes:

- global model
- round number
- model version
- client participation
- metrics
- privacy state
- configuration

On restart, the server automatically checks for the latest valid checkpoint and restores it.

## API documentation

Key endpoints:

- `GET /health`
- `POST /auth/register`
- `POST /auth/heartbeat`
- `GET /training/status`
- `POST /training/join`
- `GET /training/model`
- `POST /training/update`
- `POST /training/complete`
- `GET /monitoring/clients`
- `GET /monitoring/round`
- `GET /monitoring/metrics`
- `GET /monitoring/privacy`
- `GET /monitoring/anomalies`
- `POST /admin/start-round`
- `POST /admin/stop-round`
- `POST /admin/recover`

## Testing

Run:

```bash
pytest -q
```

Tests cover:

- FedAvg
- secure aggregation
- anomaly detection
- authentication
- checkpointing
- API smoke tests

## Troubleshooting

- If TLS fails, ensure certificates exist under `certificates/`.
- If the server rejects a client, verify the client ID is one of `hospital_01`, `hospital_02`, or `hospital_03`.
- If a round cannot complete, ensure at least `MIN_CLIENTS` clients submitted updates.
- If checkpoints are not found, run `python scripts/initialize_server.py` and restart the server.

## Security limitations

The code intentionally marks security elements that are simplified for the student project:

- TLS 1.3 is configured, but this is a local development setup for a classroom network.
- Secure aggregation is the masked additive design pattern, not a production-grade cryptographic protocol.
- The central server never sees raw patient data, but TLS is a transit-security layer, not a replacement for secure aggregation.

## Viva questions

1. Why is TLS 1.3 alone not enough to protect patient privacy from the server?
2. Why is FedAvg weighted by the number of samples?
3. What is the purpose of robust aggregation?
4. Why is checkpoint recovery necessary in a multi-client setup?
5. What does the server accept from a client: raw data or protected model updates?

## Security disclosure

```python
# ACADEMIC IMPLEMENTATION
# This secure aggregation implementation demonstrates the principle of masked
# aggregation for the mini-project. It is not claimed to be a production-grade
# deployment.
```

The project is designed for a clear technical explanation and demonstration, not for a production security guarantee.
