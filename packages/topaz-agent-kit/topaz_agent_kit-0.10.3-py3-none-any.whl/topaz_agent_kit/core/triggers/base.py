"""
Base class for all trigger handlers.
"""

import asyncio
import inspect
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional

from topaz_agent_kit.core.triggers.event import TriggerEvent
from topaz_agent_kit.utils.logger import Logger


class BaseTriggerHandler(ABC):
    """
    Abstract base class for all trigger handlers.
    
    Each trigger type (file_watcher, webhook, database, etc.) must implement
    this interface to provide event-driven pipeline execution.
    """
    
    def __init__(self, pipeline_id: str, config: Dict[str, Any], logger: Logger):
        """
        Initialize trigger handler.
        
        Args:
            pipeline_id: ID of the pipeline this trigger is for
            config: Trigger-specific configuration from pipeline.yml
            logger: Logger instance
        """
        self.pipeline_id = pipeline_id
        self.config = config
        self.logger = logger
        self._callback: Callable[[TriggerEvent], None] = None
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
    
    async def start(self, callback: Callable[[TriggerEvent], None]) -> None:
        """
        Start monitoring for events.
        
        Args:
            callback: Function to call when an event is detected.
                     Callback receives a normalized TriggerEvent.
                     Can be sync or async.
        """
        # Store callback and event loop for async callback handling
        self._callback = callback
        try:
            self._event_loop = asyncio.get_running_loop()
        except RuntimeError:
            # No event loop running, will handle sync callbacks only
            self._event_loop = None
        await self._start_impl()
    
    @abstractmethod
    async def _start_impl(self) -> None:
        """Implementation-specific start logic."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop monitoring for events."""
        pass
    
    @abstractmethod
    def normalize_event(self, raw_event: Any) -> TriggerEvent:
        """
        Convert trigger-specific event to normalized TriggerEvent format.
        
        Args:
            raw_event: Raw event from the trigger source
            
        Returns:
            Normalized TriggerEvent
        """
        pass
    
    def _handle_event(self, raw_event: Any) -> None:
        """
        Internal method to handle raw events.
        
        Normalizes the event and calls the callback.
        Handles both sync and async callbacks.
        
        Args:
            raw_event: Raw event from trigger source
        """
        try:
            normalized_event = self.normalize_event(raw_event)
            if not self._callback:
                return
            
            # Check if callback is async
            if inspect.iscoroutinefunction(self._callback):
                # Async callback - schedule it in the event loop
                if self._event_loop and self._event_loop.is_running():
                    # Schedule in the running event loop
                    asyncio.run_coroutine_threadsafe(
                        self._callback(normalized_event),
                        self._event_loop
                    )
                else:
                    # No event loop available, log error
                    self.logger.error(
                        "Cannot execute async callback for pipeline {}: no event loop available",
                        self.pipeline_id
                    )
            else:
                # Sync callback - call directly
                self._callback(normalized_event)
        except Exception as e:
            self.logger.error(
                "Error handling trigger event for pipeline {}: {}",
                self.pipeline_id, e
            )
