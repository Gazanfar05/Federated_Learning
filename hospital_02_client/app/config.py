from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - optional dependency for runtime convenience
    def load_dotenv(*args, **kwargs):  # type: ignore[no-redef]
        return False


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _path_from_env(name: str, default: str) -> Path:
    raw = os.getenv(name, default)
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT_DIR / path
    return path.resolve()


@dataclass(frozen=True)
class ClientConfig:
    client_id: str = "hospital_02"
    hospital_name: str = "Hospital 2"
    server_url: str = "https://127.0.0.1:8443"
    ca_cert: Path = ROOT_DIR / "certificates" / "ca.crt"
    client_cert: Path = ROOT_DIR / "certificates" / "hospital2.crt"
    client_key: Path = ROOT_DIR / "certificates" / "hospital2.key"
    data_path: Path = ROOT_DIR / "data" / "hospital2.csv"
    checkpoints_dir: Path = ROOT_DIR / "checkpoints"
    logs_dir: Path = ROOT_DIR / "logs"
    local_epochs: int = 3
    batch_size: int = 32
    learning_rate: float = 0.001
    dp_enabled: bool = True
    dp_clip_norm: float = 1.0
    dp_epsilon: float = 2.0
    dp_delta: float = 1e-5
    heartbeat_interval: int = 10
    request_timeout: int = 15
    max_retries: int = 3
    retry_backoff_seconds: float = 1.5
    validation_ratio: float = 0.2
    random_seed: int = 42
    mask_scale: float = 0.05
    dev_mode: bool = False

    @classmethod
    def from_env(cls) -> "ClientConfig":
        return cls(
            client_id=os.getenv("CLIENT_ID", "hospital_02"),
            hospital_name=os.getenv("HOSPITAL_NAME", "Hospital 2"),
            server_url=os.getenv("SERVER_URL", "https://127.0.0.1:8443"),
            ca_cert=_path_from_env("CA_CERT", "certificates/ca.crt"),
            client_cert=_path_from_env("CLIENT_CERT", "certificates/hospital2.crt"),
            client_key=_path_from_env("CLIENT_KEY", "certificates/hospital2.key"),
            data_path=_path_from_env("DATA_PATH", "data/hospital2.csv"),
            local_epochs=int(os.getenv("LOCAL_EPOCHS", "3")),
            batch_size=int(os.getenv("BATCH_SIZE", "32")),
            learning_rate=float(os.getenv("LEARNING_RATE", "0.001")),
            dp_enabled=_env_bool("DP_ENABLED", True),
            dp_clip_norm=float(os.getenv("DP_CLIP_NORM", "1.0")),
            dp_epsilon=float(os.getenv("DP_EPSILON", "2.0")),
            dp_delta=float(os.getenv("DP_DELTA", "1e-5")),
            heartbeat_interval=int(os.getenv("HEARTBEAT_INTERVAL", "10")),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "15")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            retry_backoff_seconds=float(os.getenv("RETRY_BACKOFF_SECONDS", "1.5")),
            validation_ratio=float(os.getenv("VALIDATION_RATIO", "0.2")),
            random_seed=int(os.getenv("RANDOM_SEED", "42")),
            mask_scale=float(os.getenv("MASK_SCALE", "0.05")),
            dev_mode=_env_bool("DEV_MODE", False),
        )

    def ensure_directories(self) -> None:
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def validation_errors(self) -> list[str]:
        errors: list[str] = []
        if self.client_id != "hospital_02":
            errors.append("CLIENT_ID must be hospital_02 for this machine.")
        if not self.server_url.startswith("https://"):
            errors.append("SERVER_URL must use https://")
        if self.batch_size <= 0:
            errors.append("BATCH_SIZE must be positive.")
        if self.local_epochs <= 0:
            errors.append("LOCAL_EPOCHS must be positive.")
        if self.learning_rate <= 0:
            errors.append("LEARNING_RATE must be positive.")
        if self.dp_clip_norm <= 0:
            errors.append("DP_CLIP_NORM must be positive.")
        if self.dp_delta <= 0 or self.dp_delta >= 1:
            errors.append("DP_DELTA must be in (0, 1).")
        if self.heartbeat_interval <= 0:
            errors.append("HEARTBEAT_INTERVAL must be positive.")
        if self.request_timeout <= 0:
            errors.append("REQUEST_TIMEOUT must be positive.")
        if self.max_retries < 0:
            errors.append("MAX_RETRIES must be non-negative.")
        return errors


def load_config() -> ClientConfig:
    config = ClientConfig.from_env()
    config.ensure_directories()
    return config
