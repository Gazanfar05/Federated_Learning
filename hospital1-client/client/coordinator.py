from __future__ import annotations

import copy
import json
import os
import time
from pathlib import Path

import numpy as np
import torch

from client.api.authentication import authenticate_client
from client.api.server_client import ServerClient
from client.communication.protocol import build_update_payload
from client.communication.serialization import serialize_update
from client.config import CLIENT_ID, DATA_PATH, DP_CLIPPING_NORM, DP_ENABLED, DP_NOISE_MULTIPLIER, LEARNING_RATE, LOCAL_EPOCHS, ROOT_DIR
from client.privacy.differential_privacy import add_gaussian_noise
from client.privacy.gradient_clipping import clip_update
from client.security.hashing import sha256_hex
from client.security.secure_aggregation import compute_update_hash, mask_update
from client.training.dataset import prepare_local_dataset
from client.training.local_trainer import model_delta, train_local_model
from client.training.model import create_model
from client.utils.logging_config import logger
from client.utils.metrics import update_norm


def save_checkpoint(round_id: int, model: torch.nn.Module, optimizer: torch.optim.Optimizer, model_version: int):
    path = Path(ROOT_DIR) / "models" / f"local_round_{round_id:03d}.pt"
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "round_id": round_id,
            "model_version": model_version,
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "training_config": {
                "learning_rate": LEARNING_RATE,
                "epochs": LOCAL_EPOCHS,
            },
        },
        path,
    )
    return path


def run_hospital1_round(round_id: int = 1):
    logger.info("========================================")
    logger.info("HOSPITAL 1 CLIENT")
    logger.info("========================================")
    logger.info("Client ID: %s", CLIENT_ID)

    client = ServerClient()
    auth_result = authenticate_client()
    if not auth_result["ok"]:
        logger.error("Authentication failed: %s", auth_result.get("error"))
        return {"ok": False, "error": "Authentication failed"}

    logger.info("Authentication: SUCCESS ✓")

    join_response = client.join_round(round_id)
    if not join_response["ok"]:
        logger.error("Join round failed: %s", join_response.get("error"))
        return {"ok": False, "error": "Join round failed"}

    model_response = client.fetch_model(round_id)
    if not model_response["ok"]:
        logger.error("Failed to fetch global model: %s", model_response.get("error"))
        return {"ok": False, "error": "Failed to fetch global model"}

    global_model_state = model_response["data"].get("model_state")
    if not global_model_state:
        global_model_state = model_response["data"].get("global_model")
    if not global_model_state:
        logger.warning("No global model returned; using fresh local model")
        model = create_model()
    else:
        model = create_model()
        model.load_state_dict(global_model_state)

    logger.info("Round %s; Global Model v%s received ✓", round_id, round_id)

    dataset = prepare_local_dataset(DATA_PATH)
    train_ds = dataset["train"]
    local_model, train_update = train_local_model(model, train_ds, epochs=LOCAL_EPOCHS, learning_rate=LEARNING_RATE, batch_size=32)

    logger.info("Local Samples: %s", train_update["num_samples"])
    logger.info("Training loss: %.4f", train_update["training_metrics"]["training_loss"])
    logger.info("Validation accuracy: %.4f", train_update["training_metrics"]["accuracy"])

    delta = model_delta(model, local_model)
    delta_flat = {k: v.detach().cpu().numpy() for k, v in delta.items()}
    clipped_delta, clip_meta = clip_update(delta_flat, DP_CLIPPING_NORM)
    logger.info("Original norm: %.4f", clip_meta["original_norm"])
    logger.info("Clipped norm: %.4f", clip_meta["clipped_norm"])
    logger.info("Clipping applied: %s", clip_meta["clipping_applied"])

    protected_delta = clipped_delta
    privacy_meta = {"epsilon": None, "delta": 1e-5, "noise_multiplier": DP_NOISE_MULTIPLIER, "clipping_norm": DP_CLIPPING_NORM}
    if DP_ENABLED:
        protected_delta, dp_meta = add_gaussian_noise(protected_delta, DP_NOISE_MULTIPLIER, 1e-5)
        privacy_meta.update(dp_meta)
        logger.info("Differential Privacy: ENABLED")
    else:
        logger.info("Differential Privacy: DISABLED")

    def _flatten_numeric(value):
        if isinstance(value, dict):
            flattened = []
            for nested in value.values():
                flattened.extend(_flatten_numeric(nested))
            return flattened
        if isinstance(value, (list, tuple)):
            flattened = []
            for item in value:
                flattened.extend(_flatten_numeric(item))
            return flattened
        if hasattr(value, "ravel"):
            return [float(x) for x in np.asarray(value).ravel().tolist()]
        return [float(value)]

    masked_update = _flatten_numeric(protected_delta)
    raw_update = _flatten_numeric(clipped_delta)
    payload = build_update_payload(
        client_id=CLIENT_ID,
        round_id=round_id,
        model_version=round_id,
        protected_update=masked_update,
        num_samples=train_update["num_samples"],
        privacy_metadata=privacy_meta,
        update_hash=compute_update_hash({"protected_update": masked_update, "client_id": CLIENT_ID, "round_id": round_id, "model_version": round_id}),
        raw_update=raw_update,
    )
    submit_response = client.submit_update(payload)
    if not submit_response["ok"]:
        logger.error("Submission failed: %s", submit_response.get("error"))
        return {"ok": False, "error": "Submission failed"}

    completion_response = client.complete_round({"client_id": CLIENT_ID, "round_id": round_id})
    if not completion_response["ok"]:
        logger.error("Round completion failed: %s", completion_response.get("error"))
        return {"ok": False, "error": "Round completion failed"}

    save_checkpoint(round_id, local_model, torch.optim.Adam(local_model.parameters(), lr=LEARNING_RATE), round_id)
    logger.info("Update accepted ✓")
    return {"ok": True, "payload": payload, "round_id": round_id, "local_model": local_model}


def run_client_loop():
    for round_id in [1, 2, 3]:
        result = run_hospital1_round(round_id)
        if not result["ok"]:
            logger.error("Round %s failed: %s", round_id, result.get("error"))
            break
        time.sleep(1)


__all__ = ["run_hospital1_round", "run_client_loop"]
