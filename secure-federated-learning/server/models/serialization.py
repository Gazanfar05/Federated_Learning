from __future__ import annotations

import numpy as np
import torch


def state_dict_to_serialized_bytes(state_dict: dict[str, torch.Tensor]) -> bytes:
    """Convert a state_dict to deterministic, safe flat bytes.

    This avoids Python object pickling and makes the update format compatible with
    a client/server protocol that can be serialized as JSON or base64.
    """
    flat = []
    for key in sorted(state_dict):
        flat.append(state_dict[key].detach().cpu().numpy().ravel())
    full = np.concatenate(flat) if flat else np.array([], dtype=np.float32)
    return full.astype(np.float32).tobytes()


def serialized_bytes_to_state_dict(raw: bytes, template: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    """Reconstruct a state_dict from raw bytes using a template state_dict."""
    flat = np.frombuffer(raw, dtype=np.float32)
    result: dict[str, torch.Tensor] = {}
    offset = 0
    for key in sorted(template):
        tensor = template[key]
        count = int(np.prod(tensor.shape))
        slice_ = flat[offset : offset + count]
        if slice_.size != count:
            raise ValueError(f"Insufficient data for tensor {key!r}.")
        result[key] = torch.tensor(slice_.reshape(tensor.shape), dtype=tensor.dtype)
        offset += count
    return result


def tensor_to_flat_list(tensor: torch.Tensor) -> list[float]:
    return tensor.detach().cpu().numpy().astype(float).ravel().tolist()


def flat_list_to_tensor(values: list[float], shape: tuple[int, ...]) -> torch.Tensor:
    arr = np.asarray(values, dtype=np.float32).reshape(shape)
    return torch.tensor(arr)
