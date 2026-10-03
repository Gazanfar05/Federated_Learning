"""Compatibility package for launching the nested project from the workspace root."""

from pathlib import Path

_project_server = Path(__file__).resolve().parent.parent / "secure-federated-learning" / "server"
__path__ = [str(_project_server)]