"""
Registry for trigger handlers.
"""

from pathlib import Path
from typing import Dict, Optional, Type

from topaz_agent_kit.core.triggers.base import BaseTriggerHandler
from topaz_agent_kit.utils.logger import Logger


class TriggerRegistry:
    """
    Registry for trigger handler classes.
    
    Allows registration of new trigger types without modifying core code.
    """
    
    _handlers: Dict[str, Type[BaseTriggerHandler]] = {}
    
    @classmethod
    def register(cls, trigger_type: str, handler_class: Type[BaseTriggerHandler]) -> None:
        """
        Register a trigger handler class.
        
        Args:
            trigger_type: Type identifier (e.g., 'file_watcher', 'webhook')
            handler_class: Handler class that implements BaseTriggerHandler
        """
        if trigger_type in cls._handlers:
            logger = Logger("TriggerRegistry")
            logger.warning(
                "Overriding existing trigger handler for type: {}",
                trigger_type
            )
        cls._handlers[trigger_type] = handler_class
    
    @classmethod
    def get_handler(
        cls,
        trigger_type: str,
        pipeline_id: str,
        config: Dict,
        logger: Logger,
        project_dir: Optional[Path] = None,
    ) -> BaseTriggerHandler:
        """
        Create handler instance for trigger type.
        
        Args:
            trigger_type: Type identifier
            pipeline_id: Pipeline ID
            config: Trigger configuration
            logger: Logger instance
            
        Returns:
            Handler instance
            
        Raises:
            ValueError: If trigger type is not registered
        """
        if trigger_type not in cls._handlers:
            raise ValueError(
                f"Unknown trigger type: {trigger_type}. "
                f"Registered types: {list(cls._handlers.keys())}"
            )
        
        handler_class = cls._handlers[trigger_type]
        # Pass project_dir if handler accepts it (file_watcher does)
        import inspect
        sig = inspect.signature(handler_class.__init__)
        if 'project_dir' in sig.parameters:
            return handler_class(pipeline_id, config, logger, project_dir=project_dir)
        else:
            return handler_class(pipeline_id, config, logger)
    
    @classmethod
    def is_registered(cls, trigger_type: str) -> bool:
        """Check if trigger type is registered."""
        return trigger_type in cls._handlers
    
    @classmethod
    def get_registered_types(cls) -> list[str]:
        """Get list of registered trigger types."""
        return list(cls._handlers.keys())
