from __future__ import annotations

import json
from pathlib import Path


if __name__ == "__main__":
    checkpoint_dir = Path(__file__).resolve().parents[1] / "checkpoints"
    round_dirs = sorted(checkpoint_dir.glob("round_*"), key=lambda p: int(p.name.split("_")[-1]))
    if not round_dirs:
        print("No checkpoints found.")
    else:
        latest = round_dirs[-1]
        metadata = json.loads((latest / "metadata.json").read_text(encoding="utf-8"))
        print(f"Latest checkpoint: {latest.name}")
        print(json.dumps(metadata, indent=2))
