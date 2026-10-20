"""OpenFL 1.9 component wrappers that inject lifecycle event capture."""

from __future__ import annotations

from typing import Any

from openfl.callbacks import Callback
from openfl.component.aggregator import Aggregator
from openfl.component.collaborator import Collaborator

from src.openfl_event_callback import OpenFLLifecycleCallback


def _callback_list(callbacks: Any) -> list[Callback]:
    if callbacks is None:
        return []
    if isinstance(callbacks, list):
        return list(callbacks)
    if isinstance(callbacks, Callback):
        return [callbacks]
    raise TypeError("callbacks must be a Callback, list, or None")


class EventAggregator(Aggregator):
    """Aggregator wrapper preserving configured callbacks and adding capture."""

    def __init__(
        self,
        *args: Any,
        callbacks: Any = None,
        workspace_dir: Any = None,
        event_log_file: str | None = None,
        **kwargs: Any,
    ) -> None:
        callback_list = _callback_list(callbacks)
        callback_list.append(
            OpenFLLifecycleCallback(
                role="aggregator",
                workspace_dir=workspace_dir,
                event_log_file=event_log_file,
            )
        )
        super().__init__(*args, callbacks=callback_list, **kwargs)


class EventCollaborator(Collaborator):
    """Collaborator wrapper preserving configured callbacks and adding capture."""

    def __init__(
        self,
        *args: Any,
        callbacks: Any = None,
        workspace_dir: Any = None,
        event_log_file: str | None = None,
        **kwargs: Any,
    ) -> None:
        collaborator_id = kwargs.get("collaborator_name")
        if collaborator_id is None and args:
            collaborator_id = args[0]
        callback_list = _callback_list(callbacks)
        callback_list.append(
            OpenFLLifecycleCallback(
                role="collaborator",
                collaborator_id=collaborator_id,
                workspace_dir=workspace_dir,
                event_log_file=event_log_file,
            )
        )
        super().__init__(*args, callbacks=callback_list, **kwargs)
