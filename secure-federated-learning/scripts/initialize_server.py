from __future__ import annotations

from pathlib import Path

from server.config import settings


if __name__ == "__main__":
    Path(settings.checkpoint_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.log_dir).mkdir(parents=True, exist_ok=True)
    Path("certificates").mkdir(parents=True, exist_ok=True)
    Path("metrics").mkdir(parents=True, exist_ok=True)
    print("Server directories initialized.")
