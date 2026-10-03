from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env", override=False)


@dataclass(frozen=True)
class Settings:
    server_host: str = os.getenv("SERVER_HOST", "0.0.0.0")
    server_port: int = int(os.getenv("SERVER_PORT", "8443"))
    num_rounds: int = int(os.getenv("NUM_ROUNDS", "5"))
    min_clients: int = int(os.getenv("MIN_CLIENTS", "2"))
    max_clients: int = int(os.getenv("MAX_CLIENTS", "3"))
    local_epochs: int = int(os.getenv("LOCAL_EPOCHS", "3"))
    anomaly_threshold: float = float(os.getenv("ANOMALY_THRESHOLD", "0.80"))
    dp_epsilon_target: float = float(os.getenv("DP_EPSILON_TARGET", "2.0"))
    dp_delta: float = float(os.getenv("DP_DELTA", "1e-5"))
    dp_clipping_norm: float = float(os.getenv("DP_CLIPPING_NORM", "1.0"))
    checkpoint_dir: Path = Path(os.getenv("CHECKPOINT_DIR", str(BASE_DIR / "checkpoints")))
    log_dir: Path = Path(os.getenv("LOG_DIR", str(BASE_DIR / "logs")))
    tls_enabled: bool = os.getenv("TLS_ENABLED", "true").lower() == "true"
    tls_cert_file: str = os.getenv("TLS_CERT_FILE", str(BASE_DIR / "certificates" / "server.crt"))
    tls_key_file: str = os.getenv("TLS_KEY_FILE", str(BASE_DIR / "certificates" / "server.key"))
    tls_ca_file: str = os.getenv("TLS_CA_FILE", str(BASE_DIR / "certificates" / "ca.crt"))


settings = Settings()
