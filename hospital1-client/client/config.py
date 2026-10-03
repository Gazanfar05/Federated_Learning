from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    load_dotenv(ROOT_DIR / ".env.example")


def get_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


CLIENT_ID = get_env("CLIENT_ID", "hospital_01")
SERVER_URL = get_env("SERVER_URL", "https://127.0.0.1:8443")
CA_CERT = str(ROOT_DIR / get_env("CA_CERT", "certificates/ca.crt"))
CLIENT_CERT = str(ROOT_DIR / get_env("CLIENT_CERT", "certificates/hospital1.crt"))
CLIENT_KEY = str(ROOT_DIR / get_env("CLIENT_KEY", "certificates/hospital1.key"))
DATA_PATH = str(ROOT_DIR / get_env("DATA_PATH", "data/hospital1.csv"))
LOCAL_EPOCHS = int(get_env("LOCAL_EPOCHS", "3"))
LEARNING_RATE = float(get_env("LEARNING_RATE", "0.001"))
BATCH_SIZE = int(get_env("BATCH_SIZE", "32"))
DP_ENABLED = get_env("DP_ENABLED", "true").lower() == "true"
DP_NOISE_MULTIPLIER = float(get_env("DP_NOISE_MULTIPLIER", "0.5"))
DP_CLIPPING_NORM = float(get_env("DP_CLIPPING_NORM", "1.0"))
DP_DELTA = float(get_env("DP_DELTA", "1e-5"))
RETRY_ATTEMPTS = int(get_env("RETRY_ATTEMPTS", "5"))
HEARTBEAT_INTERVAL = int(get_env("HEARTBEAT_INTERVAL", "10"))
DATA_SPLIT_SEED = int(get_env("DATA_SPLIT_SEED", "42"))


def ensure_paths() -> None:
    for p in [CA_CERT, CLIENT_CERT, CLIENT_KEY, DATA_PATH]:
        if not os.path.exists(p):
            raise FileNotFoundError(f"Required path does not exist: {p}")


__all__ = [
    "CLIENT_ID",
    "SERVER_URL",
    "CA_CERT",
    "CLIENT_CERT",
    "CLIENT_KEY",
    "DATA_PATH",
    "LOCAL_EPOCHS",
    "LEARNING_RATE",
    "BATCH_SIZE",
    "DP_ENABLED",
    "DP_NOISE_MULTIPLIER",
    "DP_CLIPPING_NORM",
    "DP_DELTA",
    "RETRY_ATTEMPTS",
    "HEARTBEAT_INTERVAL",
    "DATA_SPLIT_SEED",
    "ROOT_DIR",
    "ensure_paths",
]
