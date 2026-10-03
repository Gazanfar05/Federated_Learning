from __future__ import annotations

from functools import lru_cache

from server.config import settings
from server.core.coordinator import FederatedCoordinator


@lru_cache(maxsize=1)
def get_coordinator() -> FederatedCoordinator:
    return FederatedCoordinator()


def get_settings():
    return settings
