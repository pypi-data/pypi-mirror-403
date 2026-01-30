"""
Checkpoint Manager Module

Manages pipeline checkpoints for async HITL resumption.
Handles serialization, compression, and restoration of full pipeline state.
"""

import json
import uuid
import zlib
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from topaz_agent_kit.core.chat_database import ChatDatabase
from topaz_agent_kit.utils.logger import Logger


@dataclass
class PipelineCheckpoint:
    """
    Complete pipeline state at the moment of HITL trigger.
    
    This captures everything needed to resume pipeline execution:
    - All upstream agent outputs
    - Loop context (if in a loop)
    - Previous HITL decisions
    - Pattern stack for nested patterns
    - Resume point information
    """
    
    # Identification
    checkpoint_id: str
    case_id: str
    pipeline_id: str
    run_id: str
    session_id: Optional[str]
    
    # Gate information
    gate_id: str
    gate_config: Dict[str, Any]
    
    # Full upstream context - ALL agent outputs
    upstream: Dict[str, Any]
    
    # Previous HITL decisions
    hitl: Dict[str, Any]
    
    # Loop context (if applicable)
    loop_index: Optional[int] = None
    loop_item: Optional[Any] = None
    loop_total: Optional[int] = None
    loop_id: Optional[str] = None
    
    # Pattern context (for nested patterns)
    pattern_stack: Optional[List[Dict[str, Any]]] = None
    
    # Resume point - which step to continue from
    resume_point: Optional[str] = None
    
    # Timestamps
    created_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        # Use custom serialization to handle non-serializable objects (e.g., BaseRunner)
        return self._to_dict_safe(self)
    
    @staticmethod
    def _to_dict_safe(obj: Any) -> Any:
        """Recursively convert object to dict, filtering out non-serializable objects"""
        from topaz_agent_kit.core.execution_patterns import BaseRunner
        
        if isinstance(obj, BaseRunner):
            # Skip BaseRunner objects - they should not be serialized
            return None
        elif isinstance(obj, dict):
            return {k: PipelineCheckpoint._to_dict_safe(v) for k, v in obj.items() 
                    if not isinstance(v, BaseRunner)}
        elif isinstance(obj, (list, tuple)):
            return [PipelineCheckpoint._to_dict_safe(item) for item in obj 
                    if not isinstance(item, BaseRunner)]
        elif hasattr(obj, '__dict__'):
            # For dataclasses and other objects
            return {k: PipelineCheckpoint._to_dict_safe(v) for k, v in obj.__dict__.items() 
                    if not isinstance(v, BaseRunner)}
        else:
            return obj
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineCheckpoint":
        """Create from dictionary"""
        return cls(**data)


class CheckpointManager:
    """
    Manages pipeline checkpoints for async HITL.
    
    Responsibilities:
    - Create checkpoints capturing full pipeline state
    - Serialize with compression for efficient storage
    - Restore checkpoints for pipeline resumption
    - Handle checkpoint expiration
    """
    
    DEFAULT_EXPIRY_DAYS = 7
    
    def __init__(self, database: ChatDatabase):
        """
        Initialize CheckpointManager.
        
        Args:
            database: ChatDatabase instance for persistence
        """
        self.database = database
        self.logger = Logger("CheckpointManager")
    
    def create_checkpoint(
        self,
        case_id: str,
        pipeline_id: str,
        run_id: str,
        gate_id: str,
        gate_config: Dict[str, Any],
        upstream: Dict[str, Any],
        hitl: Dict[str, Any],
        session_id: Optional[str] = None,
        loop_index: Optional[int] = None,
        loop_item: Optional[Any] = None,
        loop_total: Optional[int] = None,
        loop_id: Optional[str] = None,
        pattern_stack: Optional[List[Dict[str, Any]]] = None,
        resume_point: Optional[str] = None,
        expiry_days: Optional[int] = None,
    ) -> Optional[str]:
        """
        Create a new checkpoint for async HITL resumption.
        
        Args:
            case_id: The case identifier
            pipeline_id: The pipeline identifier
            run_id: The current run ID
            gate_id: The HITL gate that triggered this checkpoint
            gate_config: The gate configuration
            upstream: Full upstream context (ALL agent outputs)
            hitl: Previous HITL decisions
            session_id: Optional session ID
            loop_index: Current loop iteration (if in loop)
            loop_item: Current loop item (if in loop)
            loop_total: Total loop iterations (if in loop)
            loop_id: Loop identifier (if in loop)
            pattern_stack: Pattern execution stack (for nested patterns)
            resume_point: Step to resume from after HITL
            expiry_days: Days until checkpoint expires
            
        Returns:
            The checkpoint_id or None if failed
        """
        checkpoint_id = f"chk-{uuid.uuid4().hex[:12]}"
        
        # Sanitize upstream and hitl to remove any BaseRunner objects before creating checkpoint
        # BaseRunner objects are stored in context but should not be serialized
        from topaz_agent_kit.core.execution_patterns import BaseRunner
        upstream_safe = self._sanitize_for_serialization(upstream)
        hitl_safe = self._sanitize_for_serialization(hitl)
        
        # Create checkpoint dataclass
        checkpoint = PipelineCheckpoint(
            checkpoint_id=checkpoint_id,
            case_id=case_id,
            pipeline_id=pipeline_id,
            run_id=run_id,
            session_id=session_id,
            gate_id=gate_id,
            gate_config=gate_config,
            upstream=upstream_safe,
            hitl=hitl_safe,
            loop_index=loop_index,
            loop_item=loop_item,
            loop_total=loop_total,
            loop_id=loop_id,
            pattern_stack=pattern_stack,
            resume_point=resume_point,
            created_at=datetime.now().isoformat(),
        )
        
        # Serialize and compress
        checkpoint_data = self._serialize_checkpoint(checkpoint)
        
        # Calculate expiry
        days = expiry_days or self.DEFAULT_EXPIRY_DAYS
        expires_at = (datetime.now() + timedelta(days=days)).isoformat()
        
        # Store in database
        success = self.database.create_checkpoint(
            checkpoint_id=checkpoint_id,
            case_id=case_id,
            pipeline_id=pipeline_id,
            run_id=run_id,
            gate_id=gate_id,
            checkpoint_data=checkpoint_data,
            resume_point=resume_point or "next",
            expires_at=expires_at,
        )
        
        if success:
            self.logger.info(
                "Created checkpoint {} for case {} at gate {} (expires: {})",
                checkpoint_id, case_id, gate_id, expires_at
            )
            return checkpoint_id
        else:
            self.logger.error(
                "Failed to create checkpoint for case {} at gate {}",
                case_id, gate_id
            )
            return None
    
    def get_checkpoint(self, checkpoint_id: str) -> Optional[PipelineCheckpoint]:
        """
        Get and deserialize a checkpoint.
        
        Args:
            checkpoint_id: The checkpoint ID
            
        Returns:
            PipelineCheckpoint or None if not found
        """
        record = self.database.get_checkpoint(checkpoint_id)
        
        if not record:
            self.logger.warning("Checkpoint not found: {}", checkpoint_id)
            return None
        
        # Check if expired
        if record.get("expires_at"):
            expires_at = datetime.fromisoformat(record["expires_at"])
            if datetime.now() > expires_at:
                self.logger.warning("Checkpoint {} has expired", checkpoint_id)
                self.mark_expired(checkpoint_id)
                return None
        
        # Check status
        if record.get("status") != "pending":
            self.logger.warning(
                "Checkpoint {} has status {}, not pending",
                checkpoint_id, record.get("status")
            )
            return None
        
        # Deserialize
        checkpoint = self._deserialize_checkpoint(record["checkpoint_data"])
        
        if checkpoint:
            self.logger.debug("Loaded checkpoint: {}", checkpoint_id)
        
        return checkpoint
    
    def get_checkpoint_by_case(self, case_id: str) -> Optional[PipelineCheckpoint]:
        """
        Get the latest pending checkpoint for a case.
        
        Args:
            case_id: The case ID
            
        Returns:
            PipelineCheckpoint or None if not found
        """
        record = self.database.get_checkpoint_by_case(case_id)
        
        if not record:
            return None
        
        return self.get_checkpoint(record["checkpoint_id"])
    
    def get_checkpoint_by_case_gate(
        self,
        case_id: str,
        gate_id: str,
        include_resumed: bool = False,
    ) -> Optional[PipelineCheckpoint]:
        """
        Get the latest checkpoint for a case and gate combination.
        
        This is useful to prevent duplicate checkpoint creation when:
        - A loop hits the same gate multiple times for the same case
        - A resumed pipeline hits the same gate again
        
        Args:
            case_id: The case identifier
            gate_id: The gate identifier
            include_resumed: If True, include resumed checkpoints (for duplicate prevention)
            
        Returns:
            PipelineCheckpoint or None if not found
        """
        record = self.database.get_checkpoint_by_case_gate(
            case_id=case_id,
            gate_id=gate_id,
            include_resumed=include_resumed,
        )
        
        if not record:
            return None
        
        # Check if expired
        if record.get("expires_at"):
            expires_at = datetime.fromisoformat(record["expires_at"])
            if datetime.now() > expires_at:
                self.logger.debug(
                    "Checkpoint {} for case {} gate {} has expired",
                    record["checkpoint_id"], case_id, gate_id
                )
                return None
        
        # Deserialize
        checkpoint = self._deserialize_checkpoint(record["checkpoint_data"])
        
        if checkpoint:
            self.logger.debug(
                "Found existing checkpoint {} for case {} gate {}",
                record["checkpoint_id"], case_id, gate_id
            )
        
        return checkpoint
    
    def mark_resumed(self, checkpoint_id: str) -> bool:
        """
        Mark checkpoint as resumed (used).
        
        Args:
            checkpoint_id: The checkpoint ID
            
        Returns:
            True if updated successfully
        """
        success = self.database.update_checkpoint_status(
            checkpoint_id=checkpoint_id,
            status="resumed",
            resumed_at=datetime.now().isoformat(),
        )
        
        if success:
            self.logger.info("Marked checkpoint {} as resumed", checkpoint_id)
        
        return success
    
    def mark_expired(self, checkpoint_id: str) -> bool:
        """
        Mark checkpoint as expired.
        
        Args:
            checkpoint_id: The checkpoint ID
            
        Returns:
            True if updated successfully
        """
        success = self.database.update_checkpoint_status(
            checkpoint_id=checkpoint_id,
            status="expired",
        )
        
        if success:
            self.logger.info("Marked checkpoint {} as expired", checkpoint_id)
        
        return success
    
    def list_pending_checkpoints(
        self,
        pipeline_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List pending checkpoints.
        
        Args:
            pipeline_id: Optional filter by pipeline
            
        Returns:
            List of checkpoint records (metadata only, not full data)
        """
        return self.database.list_pending_checkpoints(
            pipeline_id=pipeline_id,
            include_expired=False,
        )
    
    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Delete a checkpoint.
        
        Args:
            checkpoint_id: The checkpoint ID
            
        Returns:
            True if deleted successfully
        """
        success = self.database.delete_checkpoint(checkpoint_id)
        
        if success:
            self.logger.info("Deleted checkpoint: {}", checkpoint_id)
        
        return success
    
    def cleanup_expired(self) -> int:
        """
        Clean up expired checkpoints.
        
        Returns:
            Number of checkpoints cleaned up
        """
        expired = self.database.list_pending_checkpoints(include_expired=True)
        
        cleaned = 0
        now = datetime.now()
        
        for record in expired:
            expires_at_str = record.get("expires_at")
            if expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str)
                if now > expires_at:
                    self.mark_expired(record["checkpoint_id"])
                    cleaned += 1
        
        if cleaned > 0:
            self.logger.info("Cleaned up {} expired checkpoints", cleaned)
        
        return cleaned
    
    def _sanitize_for_serialization(self, obj: Any) -> Any:
        """Recursively remove BaseRunner objects from data structures before serialization"""
        from topaz_agent_kit.core.execution_patterns import BaseRunner
        
        if isinstance(obj, BaseRunner):
            # Remove BaseRunner objects - they should not be serialized
            return None
        elif isinstance(obj, dict):
            return {k: self._sanitize_for_serialization(v) for k, v in obj.items() 
                    if not isinstance(v, BaseRunner)}
        elif isinstance(obj, (list, tuple)):
            return [self._sanitize_for_serialization(item) for item in obj 
                    if not isinstance(item, BaseRunner)]
        else:
            return obj
    
    def _serialize_checkpoint(self, checkpoint: PipelineCheckpoint) -> bytes:
        """
        Serialize and compress checkpoint data.
        
        Args:
            checkpoint: The checkpoint to serialize
            
        Returns:
            Compressed bytes
        """
        # Convert to JSON
        json_str = json.dumps(checkpoint.to_dict(), default=str)
        
        # Compress with zlib
        compressed = zlib.compress(json_str.encode("utf-8"), level=6)
        
        self.logger.debug(
            "Serialized checkpoint: {} bytes -> {} bytes ({}% reduction)",
            len(json_str), len(compressed),
            round((1 - len(compressed) / len(json_str)) * 100, 1)
        )
        
        return compressed
    
    def _deserialize_checkpoint(self, data: bytes) -> Optional[PipelineCheckpoint]:
        """
        Decompress and deserialize checkpoint data.
        
        Args:
            data: Compressed checkpoint bytes
            
        Returns:
            PipelineCheckpoint or None if failed
        """
        try:
            # Decompress
            json_str = zlib.decompress(data).decode("utf-8")
            
            # Parse JSON
            checkpoint_dict = json.loads(json_str)
            
            # Create dataclass
            return PipelineCheckpoint.from_dict(checkpoint_dict)
            
        except (zlib.error, json.JSONDecodeError, TypeError, KeyError) as e:
            self.logger.error("Failed to deserialize checkpoint: {}", e)
            return None
