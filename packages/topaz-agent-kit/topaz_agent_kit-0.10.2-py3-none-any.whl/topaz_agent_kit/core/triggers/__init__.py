"""
Event trigger system for pipelines.

Provides extensible trigger handlers for event-driven pipeline execution.
Supports multiple trigger types: file_watcher, webhook, database, scheduled, etc.
"""

from topaz_agent_kit.core.triggers.event import TriggerEvent
from topaz_agent_kit.core.triggers.base import BaseTriggerHandler
from topaz_agent_kit.core.triggers.registry import TriggerRegistry

# Import file_watcher to register the handler
from topaz_agent_kit.core.triggers import file_watcher  # noqa: F401

__all__ = ["TriggerEvent", "BaseTriggerHandler", "TriggerRegistry"]
