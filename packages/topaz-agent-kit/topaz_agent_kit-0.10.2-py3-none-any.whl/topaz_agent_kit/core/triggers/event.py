"""
Normalized event format for all trigger types.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict


@dataclass
class TriggerEvent:
    """
    Normalized event format from any trigger source.
    
    All trigger handlers must convert their raw events to this format
    before passing to the pipeline execution system.
    """
    
    trigger_type: str
    """Type of trigger that generated this event (e.g., 'file_watcher', 'webhook', 'database')"""
    
    event_type: str
    """Type of event (e.g., 'created', 'modified', 'webhook_received', 'row_inserted')"""
    
    source: str
    """Source identifier (file path, webhook URL, table name, etc.)"""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Trigger-specific metadata (file_name, file_size, webhook_body, record_id, etc.)"""
    
    timestamp: datetime = field(default_factory=datetime.now)
    """When the event occurred"""
    
    raw_event: Any = None
    """Original event object for debugging (optional)"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "trigger_type": self.trigger_type,
            "event_type": self.event_type,
            "source": self.source,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }
