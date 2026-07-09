# coding=utf-8
"""Trigger abstraction (mirrors ``apps/trigger/handler/base_trigger.py``)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseTrigger(ABC):
    """A trigger fires a task (workflow / tool) on a schedule or an event."""

    @abstractmethod
    def support(self, trigger: Any, **kwargs) -> bool:
        """Whether this handler supports the given trigger row."""

    @abstractmethod
    def deploy(self, trigger: Any, **kwargs) -> None:
        """Activate the trigger (e.g. register a cron job)."""

    @abstractmethod
    def undeploy(self, trigger: Any, **kwargs) -> None:
        """Deactivate the trigger."""

    @staticmethod
    @abstractmethod
    def execute(trigger: Any, **kwargs) -> Any:
        """Run the trigger's linked tasks."""
