from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from server.config import settings


if __name__ == "__main__":
    Path(settings.checkpoint_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.log_dir).mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "certificates").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "metrics").mkdir(parents=True, exist_ok=True)
    print("Server directories initialized.")
