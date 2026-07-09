# coding=utf-8
"""Trigger package (Stage 8).

Migrates ``apps/trigger`` to an arq-backed scheduled/event trigger system while
keeping the legacy ``event_trigger`` / ``event_trigger_task`` tables:

  * ``base.BaseTrigger``     — trigger abstraction (support/deploy/undeploy/execute).
  * ``manager.TriggerManager``— loads active triggers/tasks from PG and dispatches
                               linked tasks via per-source_type handlers.
  * ``scheduled``            — builds arq cron specs from ``trigger_setting``
                               (replacing Celery beat ``PeriodicTask``).
"""
from app.trigger.base import BaseTrigger
from app.trigger.manager import TriggerManager, execute_trigger, manager, register_handler

__all__ = [
    "BaseTrigger",
    "TriggerManager",
    "manager",
    "register_handler",
    "execute_trigger",
]
