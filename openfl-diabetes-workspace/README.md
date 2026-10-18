# OpenFL diabetes experiment

This workspace is separate from `secure-federated-learning`. The FastAPI dashboard and its `.venv` remain a demonstration/monitoring app; OpenFL performs the real federated training.

## Participants

One aggregator and three collaborators: `hospital_01`, `hospital_02`, and `hospital_03`.

Each collaborator keeps its own CSV locally. It needs a header, eight numeric feature columns, and a binary target column named `Outcome`. No CSV is committed, exported, or uploaded to the aggregator.

## Run OpenFL in Linux

The host macOS Python environment is not usable for OpenFL 1.9 because its supported gRPC and SciPy native dependencies fail to load on this macOS release. `Dockerfile` supplies a separate Linux/Python 3.10 environment; it does not modify the FastAPI project or its `.venv`.

Build and initialize the experiment with:

```bash
docker compose build
docker compose run --rm tools fx plan initialize
```

The compose file reserves one aggregator and three collaborators. Do not start the `federation` profile until certificates are generated and each collaborator has registered its own local CSV. Every hospital must retain its CSV locally; no patient data belongs in this repository or image.
