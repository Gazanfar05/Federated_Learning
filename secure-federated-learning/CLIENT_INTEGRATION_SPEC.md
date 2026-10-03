# Client Integration Specification

This document tells the three hospital developers exactly what to build so their clients remain compatible with the central server.

## 1. Server connection

- Base URL: `https://<server-lan-ip>:8443`
- Example: `https://192.168.1.10:8443`
- Do not use localhost unless the hospital laptop is the same machine as the server.
- TLS 1.3 must be enabled.
- Client certificates are required for mutual TLS.

## 2. Certificate requirements

Each hospital must have:

- `hospital_01.crt` and `hospital_01.key`
- `hospital_02.crt` and `hospital_02.key`
- `hospital_03.crt` and `hospital_03.key`

The server has:

- `server.crt`
- `server.key`
- `ca.crt`

The client must trust the server CA and present its own client certificate when connecting.

## 3. Client identity

Valid IDs:

- `hospital_01`
- `hospital_02`
- `hospital_03`

Unknown IDs are rejected with a 403 or 401 error.

## 4. Registration and heartbeat

### Register

```http
POST /auth/register
Content-Type: application/json
```

Request JSON:

```json
{
  "client_id": "hospital_01",
  "certificate_identity": "hospital_01"
}
```

### Heartbeat

```http
POST /auth/heartbeat
Content-Type: application/json
```

Request JSON:

```json
{
  "client_id": "hospital_01",
  "certificate_identity": "hospital_01",
  "status": "CONNECTED"
}
```

## 5. Training lifecycle

### Start a round

The server may manage rounds centrally, but clients should call:

```http
POST /training/join
```

Request:

```json
{
  "client_id": "hospital_01",
  "round_id": 1
}
```

### Get the global model metadata

```http
GET /training/model?client_id=hospital_01
```

Response includes:

```json
{
  "client_id": "hospital_01",
  "model_version": 1,
  "round_id": 1,
  "architecture": "DiabetesMLP(input_dim=8, hidden_dim=16)",
  "parameter_count": 211,
  "update_hash": "sha256:global_model_v1"
}
```

## 6. Model architecture

The model architecture used by the server is:

```text
Input(8) -> Linear(8,16) -> ReLU -> Dropout(0.1) -> Linear(16,16) -> ReLU -> Linear(16,1)
```

This matches the `DiabetesMLP` in the server code and should be used by all hospital clients for compatibility.

## 7. Model serialization format

The server expects model update payloads to be safe, deterministic, and non-pickled. Each client should flatten the model parameters into a 1D float array and submit it as a list of float values.

It is strongly recommended that each client uses the same order of tensor flattening as the server's default template order.

A typical structure is:

```json
{
  "client_id": "hospital_01",
  "round_id": 1,
  "model_version": 1,
  "num_samples": 250,
  "update_hash": "sha256:abcdef123456",
  "protected_update": [0.12, -0.05, 0.1, 0.2],
  "timestamp": "2026-10-03T12:00:00Z"
}
```

No raw patient records, features, labels, or row-level data should be sent to the server.

## 8. Required update schema

```http
POST /training/update
Content-Type: application/json
```

Request:

```json
{
  "client_id": "hospital_01",
  "round_id": 1,
  "model_version": 1,
  "num_samples": 250,
  "update_hash": "sha256:somehash",
  "protected_update": [0.01, -0.02, 0.03],
  "timestamp": "2026-10-03T12:00:00Z"
}
```

Field validation:

- `client_id` must be `hospital_01`, `hospital_02`, or `hospital_03`
- `round_id` must be positive integer
- `model_version` must be positive integer
- `num_samples` must be positive integer
- `update_hash` must be a non-empty string
- `protected_update` must be a non-empty list of numbers
- `timestamp` must be a valid ISO timestamp

## 9. Secure aggregation contract

This is not a production-grade cryptographic protocol. It is a masked aggregation demonstration:

- client masks its update before submission
- server aggregates masked values
- mask cancellation is performed conceptually in the secure aggregation layer
- the server exposes only the aggregate to FedAvg

The central server will log and evaluate anomalies on the received update.

## 10. Differential privacy metadata expected

Each hospital is expected to report the local DP metadata as part of its training log or out-of-band system metadata.

Expected server-side tracking includes:

- epsilon
- delta
- noise multiplier
- clipping norm
- round count

The server exposes this via:

```http
GET /monitoring/privacy
```

## 11. Round lifecycle

1. Server initializes global model.
2. Client requests model metadata.
3. Client trains locally on private data.
4. Client protects the update.
5. Client submits protected update.
6. Server authenticates and validates the client.
7. Server runs anomaly detection.
8. Server runs robust aggregation.
9. Server saves checkpoint.
10. Next round starts.

## 12. Error handling

Known errors:

- 401: authentication failed
- 403: unknown client or client not allowed
- 422: invalid payload or schema mismatch
- 500: server-side failure or unexpected processing issue

## 13. Dropout behavior

If a client disconnects during a round:

- the server marks it as dropped or disconnected
- training continues if the minimum client quorum is still satisfied
- otherwise the round is paused safely and no crash occurs

## 14. Example successful request/response

Request:

```http
POST /training/update
```

```json
{
  "client_id": "hospital_02",
  "round_id": 2,
  "model_version": 2,
  "num_samples": 180,
  "update_hash": "sha256:abc123",
  "protected_update": [0.14, 0.02, -0.08, 0.11],
  "timestamp": "2026-10-03T12:10:00Z"
}
```

Response:

```json
{
  "accepted": true,
  "status": "ACCEPTED",
  "client_id": "hospital_02",
  "anomaly_score": 0.29
}
```

## 15. Hospital client implementation checklist

Each hospital client must implement:

- TLS 1.3 with mutual authentication
- secure registration step
- heartbeat mechanism
- model request logic
- local training on local private data only
- protected update creation
- update submission to `/training/update`
- training metadata reporting
- graceful history/reconnection logic
- no raw patient data transmission

## 16. Security notes

The server intentionally does not load hospital CSV files or expect raw patient data. The only ML-related information sent is protected model updates and training metadata. TLS protects transmission; secure aggregation protects the server from seeing a decrypted per-client update.

## 17. Final demonstration plan

The final viva should show:

- all 3 hospitals connect
- 5 rounds run successfully
- one hospital sends a malicious update and gets flagged
- a hospital disconnects and the server continues safely if the quorum is still valid
- the server restarts and recovers the latest checkpoint
- unknown client attempts are rejected
