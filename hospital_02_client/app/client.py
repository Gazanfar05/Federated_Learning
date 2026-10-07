from __future__ import annotations

from dataclasses import asdict
from enum import Enum
from typing import Any

import numpy as np

from .checkpoint import CheckpointManager, CheckpointState
from .config import ClientConfig, load_config
from .differential_privacy import apply_differential_privacy, clip_update
from .heartbeat import HeartbeatWorker
from .logging_config import configure_logging
from .networking import AuthenticationError, HospitalAPI
from .preprocessing import PreprocessedData, prepare_data
from .secure_aggregation import mask_update
from .serialization import compute_update_hash
from .training import DiabetesMLP, build_model, model_update_vector, train_local_model
from .utils import set_deterministic_seed, utc_now_iso


class ClientState(str, Enum):
    IDLE = "IDLE"
    AUTHENTICATING = "AUTHENTICATING"
    WAITING_FOR_ROUND = "WAITING_FOR_ROUND"
    JOINING_ROUND = "JOINING_ROUND"
    RECEIVING_GLOBAL_MODEL = "RECEIVING_GLOBAL_MODEL"
    LOCAL_TRAINING = "LOCAL_TRAINING"
    UPDATE_CLIPPING = "UPDATE_CLIPPING"
    DIFFERENTIAL_PRIVACY = "DIFFERENTIAL_PRIVACY"
    SECURE_AGGREGATION = "SECURE_AGGREGATION"
    HASHING = "HASHING"
    SUBMITTING_UPDATE = "SUBMITTING_UPDATE"
    WAITING_FOR_AGGREGATION = "WAITING_FOR_AGGREGATION"
    ROUND_COMPLETE = "ROUND_COMPLETE"
    ERROR = "ERROR"


class Hospital2Client:
    def __init__(self, config: ClientConfig | None = None) -> None:
        self.config = config or load_config()
        self.config.ensure_directories()
        self.logger = configure_logging(self.config.logs_dir)
        self.api = HospitalAPI(
            server_url=self.config.server_url,
            client_id=self.config.client_id,
            certificate_identity=self.config.client_id,
            ca_cert=str(self.config.ca_cert),
            client_cert=str(self.config.client_cert),
            client_key=str(self.config.client_key),
            timeout_seconds=self.config.request_timeout,
            max_retries=self.config.max_retries,
            backoff_seconds=self.config.retry_backoff_seconds,
        )
        self.checkpoints = CheckpointManager(self.config.checkpoints_dir)
        self.state = ClientState.IDLE
        self.current_round = 0
        self.current_model_version = 1
        self.preprocessed: PreprocessedData | None = None
        self.model = build_model()
        self.heartbeat = HeartbeatWorker(self.config.heartbeat_interval, self.api.heartbeat)

    def validate(self) -> list[str]:
        errors = self.config.validation_errors()
        if not self.config.data_path.exists():
            errors.append(f"Dataset not found: {self.config.data_path}")
        return errors

    def load_data(self) -> PreprocessedData:
        set_deterministic_seed(self.config.random_seed)
        self.preprocessed = prepare_data(
            self.config.data_path,
            batch_size=self.config.batch_size,
            validation_ratio=self.config.validation_ratio,
            seed=self.config.random_seed,
        )
        return self.preprocessed

    def restore_latest_checkpoint(self) -> CheckpointState | None:
        checkpoint = self.checkpoints.latest()
        if checkpoint is None:
            return None
        self.model.load_state_dict(checkpoint.model_state_dict)
        self.current_round = checkpoint.round_id
        self.current_model_version = checkpoint.model_version
        return checkpoint

    def check_server_health(self) -> dict[str, Any]:
        response = self.api.health()
        return asdict(response)

    def register(self) -> dict[str, Any]:
        self.state = ClientState.AUTHENTICATING
        response = self.api.register()
        if not response.ok:
            raise AuthenticationError(response.error or "registration failed")
        self.logger.info("Authentication successful")
        return asdict(response)

    def _prepare_model(self, input_dim: int) -> DiabetesMLP:
        self.model = build_model(input_dim=input_dim)
        return self.model

    def local_train_only(self) -> dict[str, Any]:
        if self.preprocessed is None:
            self.load_data()
        assert self.preprocessed is not None
        self._prepare_model(self.preprocessed.input_dim)
        result = train_local_model(
            self.model,
            self.preprocessed.train_loader,
            self.preprocessed.val_loader,
            epochs=self.config.local_epochs,
            learning_rate=self.config.learning_rate,
        )
        return {"loss": result.loss, "accuracy": result.accuracy, "num_samples": result.num_samples}

    def _build_update_payload(self, round_id: int, model_version: int, update_vector: np.ndarray, num_samples: int) -> dict[str, Any]:
        base_payload = {
            "client_id": self.config.client_id,
            "round_id": round_id,
            "model_version": model_version,
            "num_samples": num_samples,
            "protected_update": update_vector.astype(np.float32).ravel().tolist(),
            "timestamp": utc_now_iso(),
        }
        return {**base_payload, "update_hash": compute_update_hash(base_payload)}

    def participate_in_round(self, round_id: int | None = None) -> dict[str, Any]:
        if self.preprocessed is None:
            self.load_data()
        assert self.preprocessed is not None

        self.restore_latest_checkpoint()
        if round_id is None:
            status = self.api.training_status()
            if not status.ok:
                raise RuntimeError(status.error or "Unable to fetch training status")
            payload = status.data or {}
            round_id = int(payload.get("current_round", 0) or 1)
        if round_id <= 0:
            round_id = 1

        self.state = ClientState.JOINING_ROUND
        self.api.join_round(round_id)
        self.state = ClientState.RECEIVING_GLOBAL_MODEL
        metadata_response = self.api.fetch_model_metadata()
        if not metadata_response.ok:
            raise RuntimeError(metadata_response.error or "Unable to fetch model metadata")
        metadata = metadata_response.data or {}
        self.current_round = round_id
        self.current_model_version = int(metadata.get("model_version", 1))
        self._prepare_model(self.preprocessed.input_dim)

        self.state = ClientState.LOCAL_TRAINING
        result = train_local_model(
            self.model,
            self.preprocessed.train_loader,
            self.preprocessed.val_loader,
            epochs=self.config.local_epochs,
            learning_rate=self.config.learning_rate,
        )

        reference_model = build_model(input_dim=self.preprocessed.input_dim)
        update_vector = model_update_vector(reference_model, result.model)

        self.state = ClientState.UPDATE_CLIPPING
        clipped_update, clip_meta = clip_update(update_vector, self.config.dp_clip_norm)
        self.logger.info(
            "Update clipping round=%s original_norm=%.6f clipped_norm=%.6f threshold=%.6f",
            round_id,
            clip_meta["original_norm"],
            clip_meta["clipped_norm"],
            clip_meta["clip_norm"],
        )

        self.state = ClientState.DIFFERENTIAL_PRIVACY
        dp_update, privacy_meta = apply_differential_privacy(
            clipped_update,
            enabled=self.config.dp_enabled,
            clip_norm=self.config.dp_clip_norm,
            epsilon=self.config.dp_epsilon,
            delta=self.config.dp_delta,
            seed_parts=(self.config.client_id, round_id, self.current_model_version, "dp"),
        )

        self.state = ClientState.SECURE_AGGREGATION
        masked_update, mask_meta = mask_update(
            dp_update,
            client_id=self.config.client_id,
            round_id=round_id,
            model_version=self.current_model_version,
            mask_scale=self.config.mask_scale,
        )

        self.state = ClientState.HASHING
        payload = self._build_update_payload(
            round_id=round_id,
            model_version=self.current_model_version,
            update_vector=masked_update,
            num_samples=result.num_samples,
        )
        payload["update_hash"] = compute_update_hash({k: v for k, v in payload.items() if k != "update_hash"})
        self.logger.info("SHA-256: %s", payload["update_hash"])

        self.state = ClientState.SUBMITTING_UPDATE
        response = self.api.submit_update(payload)
        if not response.ok:
            raise RuntimeError(response.error or "Update submission failed")

        self.state = ClientState.WAITING_FOR_AGGREGATION
        completion = self.api.complete_round(round_id)
        if not completion.ok:
            raise RuntimeError(completion.error or "Round completion failed")

        checkpoint = CheckpointState(
            client_id=self.config.client_id,
            round_id=round_id,
            model_version=self.current_model_version,
            model_state_dict=self.model.state_dict(),
            optimizer_state_dict=None,
            config={
                "client_id": self.config.client_id,
                "data_path": str(self.config.data_path),
                "local_epochs": self.config.local_epochs,
                "batch_size": self.config.batch_size,
                "learning_rate": self.config.learning_rate,
                "dp_enabled": self.config.dp_enabled,
                "dp_clip_norm": self.config.dp_clip_norm,
                "dp_epsilon": self.config.dp_epsilon,
                "dp_delta": self.config.dp_delta,
            },
            metrics={"loss": result.loss, "accuracy": result.accuracy, "num_samples": result.num_samples, "clip": clip_meta, "privacy": privacy_meta.__dict__},
        )
        self.checkpoints.save(checkpoint)
        self.state = ClientState.ROUND_COMPLETE
        return {"round_id": round_id, "submission": response.data, "completion": completion.data, "metrics": checkpoint.metrics}

    def start_heartbeat(self) -> None:
        self.heartbeat.start(lambda: self.state.value)

    def stop_heartbeat(self) -> None:
        self.heartbeat.stop()

    def run_forever(self) -> None:
        self.register()
        self.start_heartbeat()
        try:
            while True:
                status = self.api.training_status()
                if not status.ok:
                    self.state = ClientState.ERROR
                    continue
                payload = status.data or {}
                current_round = int(payload.get("current_round", 0) or 0)
                if current_round > self.current_round:
                    self.participate_in_round(current_round)
                else:
                    self.state = ClientState.WAITING_FOR_ROUND
        finally:
            self.stop_heartbeat()
