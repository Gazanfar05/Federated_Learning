from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch

from server.config import settings
from server.checkpointing.checkpoint_manager import CheckpointManager
from server.core.client_manager import ClientManager
from server.core.round_manager import RoundManager
from server.core.state_manager import RuntimeState
from server.federated.anomaly_detection import flag_update
from server.federated.robust_aggregation import robust_aggregate
from server.models.diabetes_model import DiabetesMLP
from server.privacy.dp_accountant import DifferentialPrivacyAccountant
from server.storage.metrics_store import MetricsStore
from server.storage.round_store import RoundStore, RoundSubmission


class FederatedCoordinator:
    def __init__(self) -> None:
        self.settings = settings
        self.client_manager = ClientManager()
        self.round_manager = RoundManager()
        self.state = RuntimeState()
        self.metrics_store = MetricsStore()
        self.round_store = RoundStore()
        self.checkpoint_manager = CheckpointManager(self.settings.checkpoint_dir)
        np.random.seed(42)
        torch.manual_seed(42)
        self.model = DiabetesMLP()
        self.model_version = 1
        self.privacy_accountant = DifferentialPrivacyAccountant(
            epsilon_target=self.settings.dp_epsilon_target,
            delta=self.settings.dp_delta,
            clipping_norm=self.settings.dp_clipping_norm,
        )
        self.synced_clients = []
        self.anomaly_log: list[dict] = []
        self._bootstrap_known_clients()
        self._recover_checkpoint_if_present()

    def _bootstrap_known_clients(self) -> None:
        for client_id in ("hospital_01", "hospital_02", "hospital_03"):
            self.client_manager.register_client(client_id, client_id)

    def _model_vector(self) -> np.ndarray:
        flat = []
        for key in sorted(self.model.state_dict()):
            flat.append(self.model.state_dict()[key].detach().cpu().numpy().ravel())
        return np.concatenate(flat) if flat else np.array([], dtype=np.float32)

    def _vector_to_state_dict(self, vector: np.ndarray) -> dict[str, torch.Tensor]:
        state = self.model.state_dict()
        flat = np.asarray(vector, dtype=np.float32).reshape(-1)
        expected_size = sum(tensor.numel() for tensor in state.values())
        if flat.size != expected_size:
            raise ValueError(
                f"Expected {expected_size} model values, received {flat.size}."
            )
        if not np.isfinite(flat).all():
            raise ValueError("Model vector contains NaN or infinite values.")

        offset = 0
        updated: dict[str, torch.Tensor] = {}
        for key in sorted(state):
            numel = state[key].numel()
            slice_ = flat[offset : offset + numel]
            updated[key] = torch.tensor(slice_.reshape(state[key].shape), dtype=state[key].dtype)
            offset += numel
        return updated

    def register_client(self, client_id: str, certificate_identity: str = "") -> bool:
        return self.client_manager.register_client(client_id, certificate_identity)

    def authenticate_client(self, client_id: str, certificate_identity: str = "") -> bool:
        if not self.client_manager.authenticator.validate_client_id(client_id):
            return False
        if not self.client_manager.authenticator.validate_certificate_identity(client_id, certificate_identity):
            return False
        record = self.client_manager.registry.get(client_id)
        if record is None:
            return False
        record.status = "CONNECTED"
        record.connection_status = "CONNECTED"
        record.last_seen = datetime.now(timezone.utc).isoformat()
        return True

    def get_client_status(self) -> list[dict]:
        rows: list[dict] = []
        for client in self.client_manager.list_clients():
            rows.append(
                {
                    "client_id": client.client_id,
                    "certificate_identity": client.certificate_identity,
                    "status": client.status,
                    "last_seen": client.last_seen,
                    "current_round": client.current_round,
                    "submitted_updates": client.submitted_updates,
                    "connection_status": client.connection_status,
                }
            )
        return rows

    def start_round(self) -> dict:
        self.state.current_round += 1
        self.round_manager.start_round(self.state.current_round)
        self.state.running = True
        for record in self.client_manager.list_clients():
            record.current_round = self.state.current_round
            record.status = "TRAINING"
            record.connection_status = "CONNECTED"
        return {
            "status": "started",
            "round_id": self.state.current_round,
            "min_clients": self.settings.min_clients,
            "max_clients": self.settings.max_clients,
        }

    def join_training_round(self, client_id: str, round_id: int) -> dict:
        if not self.client_manager.authenticator.validate_client_id(client_id):
            raise ValueError(f"Unknown client {client_id}.")
        self.round_manager.join_round(client_id, round_id)
        record = self.client_manager.registry.get(client_id)
        if record:
            record.current_round = round_id
            record.status = "TRAINING"
        return {"client_id": client_id, "round_id": round_id, "status": "joined"}

    def get_model_snapshot(self, client_id: str) -> dict:
        if not self.client_manager.authenticator.validate_client_id(client_id):
            raise ValueError(f"Unknown client {client_id}.")
        return {
            "client_id": client_id,
            "model_version": self.model_version,
            "round_id": self.state.current_round,
            "architecture": "DiabetesMLP(input_dim=8, hidden_dim=16)",
            "parameter_count": sum(p.numel() for p in self.model.parameters()),
            "model_vector": self._model_vector().tolist(),
            "update_hash": "sha256:global_model_v" + str(self.model_version),
        }

    def submit_update(self, update_payload: dict) -> dict:
        client_id = update_payload["client_id"]
        round_id = int(update_payload["round_id"])

        def reject(reason: str) -> dict:
            return {
                "accepted": False,
                "status": "REJECTED",
                "client_id": client_id,
                "reason": reason,
            }

        if not self.client_manager.authenticator.validate_client_id(client_id):
            return reject("Unknown client identity.")

        if int(update_payload["model_version"]) != self.model_version:
            return reject("Submitted model version does not match the current global model.")

        round_state = self.round_manager.rounds.get(round_id)
        if (
            round_id != self.state.current_round
            or not self.state.running
            or round_state is None
            or round_state.status != "ACTIVE"
        ):
            return reject("The requested training round is not active.")

        existing_round = self.round_store.get(round_id)
        if existing_round and any(
            item.client_id == client_id for item in existing_round.submissions
        ):
            return reject("This client has already submitted an update for this round.")

        num_samples = int(update_payload["num_samples"])
        if num_samples < 1:
            return reject("num_samples must be positive.")

        try:
            candidate = np.asarray(
                update_payload["protected_update"], dtype=np.float32
            ).reshape(-1)
        except (TypeError, ValueError):
            return reject("Model update must be a numeric vector.")

        expected_reference = self._model_vector()
        if candidate.size != expected_reference.size:
            return reject(
                f"Expected {expected_reference.size} model values, received {candidate.size}."
            )
        if not np.isfinite(candidate).all():
            return reject("Model update contains NaN or infinite values.")

        reference_payload = update_payload.get("reference_model")
        if reference_payload is not None:
            try:
                reference = np.asarray(reference_payload, dtype=np.float32).reshape(-1)
            except (TypeError, ValueError):
                return reject("Reference model must be a numeric vector.")
            if (
                reference.shape != expected_reference.shape
                or not np.isfinite(reference).all()
                or not np.allclose(
                    reference, expected_reference, rtol=1e-4, atol=1e-5
                )
            ):
                anomaly_score = 1.0
                reason = "Client reference model does not match the current global model."
                self.anomaly_log.append({
                    "client_id": client_id,
                    "round_id": round_id,
                    "anomaly_score": anomaly_score,
                    "decision": "SUSPICIOUS",
                    "reason": reason,
                })
                return reject(reason)

        # Updates are full model vectors, so assess their distance from the
        # global model rather than applying a norm threshold to absolute weights.
        delta_norm = float(np.linalg.norm(candidate - expected_reference))
        anomaly_score = min(delta_norm, 1.0)
        suspicious = delta_norm > self.settings.anomaly_threshold
        reason = (
            "Model change exceeds the configured anomaly threshold."
            if suspicious
            else "Model change is within the configured threshold."
        )
        self.anomaly_log.append({
            "client_id": client_id,
            "round_id": round_id,
            "anomaly_score": anomaly_score,
            "decision": "SUSPICIOUS" if suspicious else "NORMAL",
            "reason": reason,
        })

        if suspicious:
            return {
                **reject(reason),
                "anomaly_score": anomaly_score,
            }

        record = self.client_manager.registry.get(client_id)
        if record is not None:
            record.status = "SUBMITTED"
            record.connection_status = "CONNECTED"
            record.submitted_updates += 1
            record.current_round = round_id

        submission = RoundSubmission(
            client_id=client_id,
            round_id=round_id,
            model_version=self.model_version,
            num_samples=num_samples,
            update_hash=str(update_payload["update_hash"]),
            protected_update=candidate.tolist(),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.round_store.add_submission(round_id, submission)
        self.round_manager.mark_submission(client_id, round_id)

        return {
            "accepted": True,
            "status": "ACCEPTED",
            "client_id": client_id,
            "anomaly_score": anomaly_score,
        }

    def complete_round(self, client_id: str, round_id: int) -> dict:
        if not self.client_manager.authenticator.validate_client_id(client_id):
            return {"status": "failed", "reason": "Unknown client."}

        if round_id != self.state.current_round or not self.state.running:
            return {
                "status": "failed",
                "round_id": round_id,
                "reason": "The requested training round is not active.",
            }

        round_record = self.round_store.get(round_id)
        if round_record is None or not round_record.submissions:
            return {"status": "completed_without_updates", "round_id": round_id}

        if len(round_record.submissions) < self.settings.min_clients:
            return {
                "status": "paused",
                "round_id": round_id,
                "reason": "Minimum client quorum not met.",
                "received_clients": len(round_record.submissions),
                "required_clients": self.settings.min_clients,
            }

        client_models = []
        sample_counts = []
        anomaly_scores = []

        for submission in round_record.submissions:
            if submission.model_version != self.model_version:
                return {
                    "status": "failed",
                    "round_id": round_id,
                    "reason": "A submission uses a stale global model version.",
                }

            client_model = DiabetesMLP()
            try:
                client_model.load_state_dict(
                    self._vector_to_state_dict(
                        np.asarray(submission.protected_update, dtype=np.float32)
                    )
                )
            except (ValueError, RuntimeError) as exc:
                return {
                    "status": "failed",
                    "round_id": round_id,
                    "reason": f"Invalid client model: {exc}",
                }

            client_models.append(client_model)
            sample_counts.append(submission.num_samples)
            anomaly_scores.append(0.1)

        aggregated_model, valid_indices = robust_aggregate(
            self.model,
            client_models,
            sample_counts,
            anomaly_scores,
            threshold=self.settings.anomaly_threshold,
        )

        if not valid_indices:
            return {
                "status": "failed",
                "round_id": round_id,
                "reason": "No client updates passed robust aggregation.",
            }

        self.model = aggregated_model
        self.model_version += 1
        self.state.model_version = self.model_version
        self.privacy_accountant.register_round(round_id, len(valid_indices))

        accepted_clients = [
            round_record.submissions[index].client_id for index in valid_indices
        ]

        # No held-out evaluation is configured yet. Do not publish invented
        # loss, accuracy, or F1 values as if they were measured.
        metrics = {
            "available": False,
            "reason": "No held-out evaluation dataset configured.",
        }
        checkpoint_dir = self.checkpoint_manager.save_checkpoint(
            round_id,
            self.model,
            {
                "model_version": self.model_version,
                "client_participation": accepted_clients,
                "metrics": metrics,
                "privacy_state": self.privacy_accountant.current_metrics(),
                "config": {
                    "num_rounds": self.settings.num_rounds,
                    "min_clients": self.settings.min_clients,
                    "max_clients": self.settings.max_clients,
                    "local_epochs": self.settings.local_epochs,
                },
            },
        )

        self.round_manager.complete_round(round_id)
        self.state.running = False

        return {
            "status": "completed",
            "round_id": round_id,
            "model_version": self.model_version,
            "checkpoint_dir": str(checkpoint_dir),
            "accepted_clients": accepted_clients,
            "metrics": metrics,
        }

    def get_training_status(self) -> dict:
        return {
            "status": "online",
            "current_round": self.state.current_round,
            "model_version": self.model_version,
            "clients_connected": len(self.client_manager.list_clients()),
            "running": self.state.running,
        }

    def monitoring_clients(self) -> list[dict]:
        return self.get_client_status()

    def monitoring_round(self) -> dict:
        round_state = self.round_manager.rounds.get(self.state.current_round)
        return {
            "round_id": self.state.current_round,
            "status": round_state.status if round_state else "INIT",
            "participants": round_state.participants if round_state else [],
            "submitted_clients": round_state.submitted_clients if round_state else [],
        }

    def monitoring_metrics(self) -> dict:
        latest_metrics = self.metrics_store.latest()
        if latest_metrics is None:
            return {"round_id": self.state.current_round, "loss": 0.0, "accuracy": 0.0, "f1_score": 0.0}
        return {
            "round_id": latest_metrics.round_id,
            "loss": latest_metrics.loss,
            "accuracy": latest_metrics.accuracy,
            "f1_score": latest_metrics.f1_score,
        }

    def monitoring_privacy(self) -> dict:
        return self.privacy_accountant.current_metrics()

    def monitoring_anomalies(self) -> list[dict]:
        return self.anomaly_log

    def recover_latest_checkpoint(self) -> dict:
        model, metadata = self.checkpoint_manager.recover_latest_checkpoint()
        if model is None or metadata is None:
            return {"status": "no_checkpoint"}
        self.model = model
        self.model_version = int(metadata.get("model_version", self.model_version))
        self.state.current_round = int(metadata.get("round_id", self.state.current_round))
        return {
            "status": "recovered",
            "round_id": self.state.current_round,
            "model_version": self.model_version,
            "checkpoint": metadata,
        }

    def _recover_checkpoint_if_present(self) -> None:
        recovered = self.checkpoint_manager.recover_latest_checkpoint()
        if recovered[0] is not None:
            self.model = recovered[0]
            metadata = recovered[1] or {}
            self.model_version = int(metadata.get("model_version", self.model_version))
            self.state.current_round = int(metadata.get("round_id", self.state.current_round))
