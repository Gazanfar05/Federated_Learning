# Hospital 03 — Integrity & Audit Portal

A standalone, read-only browser frontend for **Hospital 03 — Integrity & Audit Unit**. It uses the repository's existing zero-build, vanilla JavaScript approach and does not change the coordinator, OpenFL configuration, training code, certificates, checkpoints, or datasets.

## Run locally

From the repository root, serve this directory with Python:

```powershell
python -m http.server 4173 --directory hospital_03_client/frontend
```

Open <http://127.0.0.1:4173>. The page defaults to the coordinator URL `http://127.0.0.1:8000`. Set the API URL in **Identity & connectivity** if the coordinator uses another address. This setting is stored in browser local storage; do not enter URL credentials or secrets.

The coordinator must allow browser CORS requests from the frontend origin. The browser service sends unauthenticated GET requests only, omits credentials, and times out each request after eight seconds. It does not perform client-certificate authentication.

## Current endpoint inventory

| Method | Endpoint | Portal use | What the response establishes |
| --- | --- | --- | --- |
| `GET` | `/health` | Coordinator health and last successful check | The API returned its health response; it does not establish an authenticated browser session, certificate validation, or OpenFL participation. |
| `GET` | `/model/current?client_id=hospital_03` | Current model metadata | The coordinator returned its model snapshot fields. The `update_hash` value is displayed as untrusted metadata, not as a trusted digest. |

The portal does not call registration, heartbeat, training join, model update, completion, or administrative routes.

## Unavailable contracts and required backend work

The following are not currently exposed as read-only portal data. Add and document authenticated contracts before presenting these as observed states:

- **Application session and hospital identity:** a genuine session-status API returning authenticated principal, hospital identifier, issuance/expiry data, and authorization scope. Never accept a browser-supplied hospital ID as identity proof.
- **Certificate status:** a server-side contract that reports certificate identity, trust/expiry state, and validation outcome without disclosing private keys or sensitive TLS settings. Keep certificate authentication in the backend or trusted local agent, not browser JavaScript.
- **Artifact integrity:** a trusted, versioned/signed manifest with algorithm and expected digest, plus a safe artifact retrieval operation returning the exact bytes. A browser or trusted local agent must independently hash those bytes and compare against the trusted expected digest before declaring verification.
- **OpenFL collaborator state:** evidence from the actual OpenFL runtime, clearly separated from application coordinator state.
- **Structured audit events:** a read-only event contract with `event_type`, `timestamp`, `source_type` (`application` or `openfl_lifecycle`), message, trusted source/provenance, and optional `hospital_id`, `round_number`, and `operation_id`. Application and OpenFL lifecycle records must be identified separately. Lifecycle records do not prove model transfer or broadcast success.
- **Update review:** a read-only update record contract with update ID, base version, round, artifact digest, verification and validation states, receipt ID, and acceptance/rejection reason. This portal intentionally does not submit updates.
- **Integrity checks:** backend or agent-backed freshness policy, manifest validation, digest comparison, artifact availability, and update-rejection evidence.

## Security and behavior notes

- `hospital_03` is fixed in frontend configuration. Its presence is configuration only, never proof of authentication.
- Only the two GET endpoints above are requested. There are no training or update submission controls.
- Server-provided values are inserted as text; they are not interpreted as HTML.
- No patient records, certificates, private keys, credentials, or local filesystem paths are accessed by the frontend.
- The model endpoint currently returns a placeholder-like `update_hash` (`sha256:global_model_v...`) and does not provide model bytes. The portal labels this as reported metadata and always leaves artifact verification unverified.
- No session, certificate, collaborator, update-review, or structured audit endpoint is currently available. These are shown as unavailable, not as incidents or successful checks.
- Failed reads display the error and preserve any prior successful response with a stale-data indicator. Refresh controls only repeat read-only GET requests.
