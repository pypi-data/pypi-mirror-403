"""
Case Manager Module

Manages pipeline cases - tracking ALL cases (both HITL and straight-through).
Handles case creation, updates, and status transitions.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from topaz_agent_kit.core.chat_database import ChatDatabase
from topaz_agent_kit.core.case_data_extractor import CaseDataExtractor
from topaz_agent_kit.utils.logger import Logger


class CaseManager:
    """
    Manages pipeline cases in the database.
    
    This class is responsible for:
    - Creating case entries for ALL pipeline iterations
    - Extracting and storing case display data
    - Updating case status throughout the pipeline lifecycle
    - Querying cases with filters
    """
    
    # Case status constants
    STATUS_PROCESSING = "processing"
    STATUS_HITL_PENDING = "hitl_pending"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    
    def __init__(self, database: ChatDatabase):
        """
        Initialize CaseManager.
        
        Args:
            database: ChatDatabase instance for persistence
        """
        self.database = database
        self.extractor = CaseDataExtractor()
        self.logger = Logger("CaseManager")
    
    def create_case(
        self,
        pipeline_id: str,
        run_id: str,
        upstream: Dict[str, Any],
        case_config: Dict[str, Any],
        session_id: Optional[str] = None,
        case_type: Optional[str] = None,
        current_step: Optional[str] = None,
        fallback_case_id: Optional[str] = None,
        initial_status: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a new case entry.
        
        Args:
            pipeline_id: The pipeline identifier
            run_id: The current run ID
            upstream: The upstream context with agent outputs
            case_config: The case configuration for data extraction
            session_id: Optional session ID
            case_type: Optional case type (e.g., "invoice", "order")
            current_step: Optional current step/agent ID
            fallback_case_id: Fallback ID if extraction fails
            
        Returns:
            The created case_id (unique) or None if failed
        """
        # Extract case ID - returns unique case_id (e.g., BATCH-ABC12345)
        case_id = self.extractor.extract_case_id(
            upstream=upstream,
            case_config=case_config,
            fallback_id=fallback_case_id,
        )
        
        # Check if case already exists (important for deterministic case_ids like invoice_id)
        existing_case = self.get_case(case_id)
        if existing_case:
            self.logger.info(
                "Case {} already exists, reusing existing case (status: {})",
                case_id, existing_case.get("status", "unknown")
            )
            # Update case data if needed (merge new data with existing)
            # This ensures case_data is up-to-date even if case already exists
            case_data = self.extractor.extract_case_data(
                upstream=upstream,
                case_config=case_config,
            )
            existing_case_data = existing_case.get("case_data", {})
            merged_case_data = self._deep_merge_case_data(existing_case_data, case_data)
            
            # Update case data and status if initial_status was provided
            updates = {"case_data": merged_case_data}
            if initial_status:
                updates["status"] = initial_status
            if current_step:
                updates["current_step"] = current_step
            
            self.database.update_pipeline_case(case_id=case_id, updates=updates)
            return case_id
        
        # display_id is the same as case_id (kept for backwards compatibility with database)
        display_id = case_id
        
        # Extract case data for display
        case_data = self.extractor.extract_case_data(
            upstream=upstream,
            case_config=case_config,
        )
        
        # Determine case type from config if not provided
        if not case_type:
            case_type = case_config.get("case_type", pipeline_id)
        
        # Use provided initial_status, or default to processing (only needed for resume scenarios)
        status = initial_status or self.STATUS_PROCESSING
        
        success = self.database.create_pipeline_case(
            case_id=case_id,
            display_id=display_id,
            pipeline_id=pipeline_id,
            run_id=run_id,
            session_id=session_id,
            case_type=case_type,
            status=status,
            current_step=current_step,
            case_data=case_data,
        )
        
        if success:
            self.logger.info(
                "Created case {} (display: {}) for pipeline {} (run: {})",
                case_id, display_id, pipeline_id, run_id
            )
            # Add timeline entry for case creation
            self._add_timeline_entry(
                case_id=case_id,
                event_type="case_created",
                event_data={
                    "pipeline_id": pipeline_id,
                    "run_id": run_id,
                    "case_type": case_type,
                },
            )
            return case_id
        else:
            self.logger.error("Failed to create case for pipeline {}", pipeline_id)
            return None
    
    def update_case_data(
        self,
        case_id: str,
        upstream: Dict[str, Any],
        case_config: Dict[str, Any],
    ) -> bool:
        """
        Update case data with latest upstream context.
        
        IMPORTANT: This method MERGES new case_data with existing case_data,
        rather than replacing it. This ensures that pre-HITL agent outputs
        (like math_strategist, math_calculator) are preserved when updating
        after a HITL response.
        
        Args:
            case_id: The case ID to update
            upstream: The updated upstream context
            case_config: The case configuration
            
        Returns:
            True if updated successfully
        """
        # Get existing case to preserve existing case_data
        existing_case = self.get_case(case_id)
        existing_case_data = {}
        if existing_case:
            existing_case_data = existing_case.get("case_data", {})
        
        # Extract new case_data from upstream
        new_case_data = self.extractor.extract_case_data(
            upstream=upstream,
            case_config=case_config,
        )
        
        # Deep merge: new data updates existing, but doesn't remove existing fields
        # This is critical for HITL cases where pre-HITL agents might not be in
        # the final_upstream after resume (e.g., if they're in sub-pipeline structure)
        # 
        # The merge preserves:
        # - Agent outputs from existing (e.g., math_strategist, math_calculator) that aren't in new upstream
        # - _detail_view sections from existing (pre-HITL sections)
        # - Adds new agent outputs from new upstream (e.g., math_auditor)
        # - Adds new _detail_view sections from new (post-HITL sections like Audit)
        merged_case_data = self._deep_merge_case_data(existing_case_data, new_case_data)
        
        return self.database.update_pipeline_case(
            case_id=case_id,
            updates={"case_data": merged_case_data},
        )
    
    def _deep_merge_case_data(
        self,
        existing: Dict[str, Any],
        new: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Deep merge two case_data dictionaries.
        
        Strategy:
        - For dicts: Recursively merge
        - For _detail_view.sections: Merge sections by ID/title, merge fields within sections
        - For lists: Replace (new list replaces old) - except for _detail_view.sections
        - For other types: Replace (new value replaces old)
        - Existing keys not in new: Preserve (don't remove)
        
        Args:
            existing: Existing case_data
            new: New case_data to merge in
            
        Returns:
            Merged case_data
        """
        import copy
        result = copy.deepcopy(existing)
        
        for key, new_value in new.items():
            if key in result:
                existing_value = result[key]
                
                # Special handling for _detail_view.sections
                if key == "_detail_view" and isinstance(existing_value, dict) and isinstance(new_value, dict):
                    # Merge _detail_view structure
                    merged_detail_view = self._deep_merge_case_data(existing_value, new_value)
                    
                    # Special handling for sections array
                    if "sections" in existing_value and "sections" in new_value:
                        merged_sections = self._merge_detail_view_sections(
                            existing_value.get("sections", []),
                            new_value.get("sections", [])
                        )
                        merged_detail_view["sections"] = merged_sections
                    
                    result[key] = merged_detail_view
                # If both are dicts, recursively merge
                elif isinstance(existing_value, dict) and isinstance(new_value, dict):
                    result[key] = self._deep_merge_case_data(existing_value, new_value)
                else:
                    # For lists or other types, replace with new value
                    result[key] = copy.deepcopy(new_value)
            else:
                # New key, add it
                result[key] = copy.deepcopy(new_value)
        
        return result
    
    def _merge_detail_view_sections(
        self,
        existing_sections: List[Dict[str, Any]],
        new_sections: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Merge detail view sections intelligently.
        
        Strategy:
        - Merge sections by ID or title
        - If section exists in both: merge fields (preserve existing, add new)
        - If section only in existing: preserve it
        - If section only in new: add it
        
        Args:
            existing_sections: Existing sections from pre-HITL case_data
            new_sections: New sections from post-HITL case_data
            
        Returns:
            Merged sections list
        """
        import copy
        merged = []
        
        # Create a map of existing sections by ID or title
        existing_map = {}
        for section in existing_sections:
            section_id = section.get("id") or section.get("title") or ""
            if section_id:
                existing_map[section_id] = section
        
        # Process new sections
        new_map = {}
        for section in new_sections:
            section_id = section.get("id") or section.get("title") or ""
            if section_id:
                new_map[section_id] = section
        
        # Merge: existing sections that are also in new get merged
        # New sections that don't exist get added
        # Existing sections that don't exist in new get preserved
        all_section_ids = set(existing_map.keys()) | set(new_map.keys())
        
        for section_id in all_section_ids:
            existing_section = existing_map.get(section_id)
            new_section = new_map.get(section_id)
            
            if existing_section and new_section:
                # Both exist: merge fields
                merged_section = copy.deepcopy(existing_section)
                # Merge fields: preserve existing, add new fields
                existing_fields_map = {f.get("key") or f.get("label"): f for f in existing_section.get("fields", [])}
                new_fields = new_section.get("fields", [])
                
                merged_fields = []
                # Add existing fields first
                for field in existing_section.get("fields", []):
                    field_key = field.get("key") or field.get("label")
                    merged_fields.append(copy.deepcopy(field))
                
                # Add new fields that don't exist
                for field in new_fields:
                    field_key = field.get("key") or field.get("label")
                    if field_key not in existing_fields_map:
                        merged_fields.append(copy.deepcopy(field))
                    else:
                        # Field exists: update value if new value is not None
                        existing_field = existing_fields_map[field_key]
                        if field.get("value") is not None:
                            existing_field["value"] = field.get("value")
                
                merged_section["fields"] = merged_fields
                merged.append(merged_section)
            elif existing_section:
                # Only in existing: preserve it
                merged.append(copy.deepcopy(existing_section))
            elif new_section:
                # Only in new: add it
                merged.append(copy.deepcopy(new_section))
        
        return merged
    
    def update_case_status(
        self,
        case_id: str,
        status: str,
        current_step: Optional[str] = None,
    ) -> bool:
        """
        Update case status.
        
        Args:
            case_id: The case ID
            status: New status (processing, hitl_pending, completed, failed)
            current_step: Optional current step
            
        Returns:
            True if updated successfully
        """
        updates = {"status": status}
        if current_step:
            updates["current_step"] = current_step
        
        # Set completed_at if completing
        if status == self.STATUS_COMPLETED:
            updates["completed_at"] = datetime.now().isoformat()
        
        success = self.database.update_pipeline_case(case_id, updates)
        
        if success:
            self.logger.info("Updated case {} status to {}", case_id, status)
        else:
            self.logger.warning(
                "Failed to update case {} status to {}. Case may not exist in database.",
                case_id, status
            )
        
        return success
    
    def mark_hitl_pending(
        self,
        case_id: str,
        gate_id: str,
    ) -> bool:
        """
        Mark case as waiting for HITL response.
        
        Args:
            case_id: The case ID
            gate_id: The HITL gate ID
            
        Returns:
            True if updated successfully
        """
        return self.update_case_status(
            case_id=case_id,
            status=self.STATUS_HITL_PENDING,
            current_step=gate_id,
        )
    
    def mark_completed(
        self,
        case_id: str,
        final_output: Optional[Dict[str, Any]] = None,
        processing_time_ms: Optional[int] = None,
    ) -> bool:
        """
        Mark case as completed.
        
        Args:
            case_id: The case ID
            final_output: Optional final pipeline output
            processing_time_ms: Optional processing time in milliseconds
            
        Returns:
            True if updated successfully
        """
        updates = {
            "status": self.STATUS_COMPLETED,
            "completed_at": datetime.now().isoformat(),
        }
        
        if final_output is not None:
            updates["final_output"] = final_output
            
            # Also add final_output to case_data so it's displayed in the UI
            case = self.get_case(case_id)
            if case:
                case_data = case.get("case_data", {})
                case_data["final_output"] = final_output
                updates["case_data"] = case_data
                self.logger.debug(
                    "Added final_output to case_data for case {}",
                    case_id
                )
        
        if processing_time_ms is not None:
            updates["processing_time_ms"] = processing_time_ms
        
        success = self.database.update_pipeline_case(case_id, updates)
        
        if success:
            self.logger.info("Marked case {} as completed", case_id)
            # Add timeline entry for case completion
            self._add_timeline_entry(
                case_id=case_id,
                event_type="case_completed",
                event_data={
                    "completed_at": updates["completed_at"],
                    "processing_time_ms": processing_time_ms,
                },
            )
        
        return success
    
    def mark_failed(
        self,
        case_id: str,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Mark case as failed.
        
        Args:
            case_id: The case ID
            error_message: Optional error message
            
        Returns:
            True if updated successfully
        """
        updates = {"status": self.STATUS_FAILED}
        
        if error_message:
            # Store error in case_data
            case = self.get_case(case_id)
            if case:
                case_data = case.get("case_data", {})
                case_data["_error"] = error_message
                updates["case_data"] = case_data
        
        success = self.database.update_pipeline_case(case_id, updates)
        
        if success:
            self.logger.warning("Marked case {} as failed: {}", case_id, error_message or "Unknown error")
            # Add timeline entry for case failure
            self._add_timeline_entry(
                case_id=case_id,
                event_type="case_failed",
                event_data={
                    "error_message": error_message,
                    "failed_at": datetime.now().isoformat(),
                },
            )
        
        return success
    
    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        Get case by ID.
        
        Args:
            case_id: The case ID
            
        Returns:
            Case data or None if not found
        """
        return self.database.get_pipeline_case(case_id)
    
    def list_cases(
        self,
        pipeline_id: Optional[str] = None,
        status: Optional[str] = None,
        run_id: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List cases with optional filters.
        
        Args:
            pipeline_id: Filter by pipeline
            status: Filter by status
            run_id: Filter by run ID
            from_date: Filter by created_at >= from_date
            to_date: Filter by created_at <= to_date
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            List of case records
        """
        return self.database.list_pipeline_cases(
            pipeline_id=pipeline_id,
            status=status,
            run_id=run_id,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset,
        )
    
    def get_cases_by_run(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Get all cases for a specific run.
        
        Args:
            run_id: The run ID
            
        Returns:
            List of cases for this run
        """
        return self.list_cases(run_id=run_id, limit=1000)
    
    def delete_case(self, case_id: str) -> bool:
        """
        Delete a case and all associated data.
        
        Args:
            case_id: The case ID
            
        Returns:
            True if deleted successfully
        """
        success = self.database.delete_pipeline_case(case_id)
        
        if success:
            self.logger.info("Deleted case: {}", case_id)
        
        return success
    
    def delete_cases(
        self,
        pipeline_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> int:
        """
        Delete multiple cases with filters.
        
        Args:
            pipeline_id: Filter by pipeline ID (optional)
            status: Filter by status (optional)
            
        Returns:
            Number of cases deleted
        """
        deleted_count = self.database.delete_pipeline_cases(
            pipeline_id=pipeline_id,
            status=status,
        )
        
        if deleted_count > 0:
            self.logger.info("Deleted {} cases with filters: pipeline_id={}, status={}", 
                           deleted_count, pipeline_id, status)
        
        return deleted_count
    
    def case_exists(self, case_id: str) -> bool:
        """
        Check if a case exists.
        
        Args:
            case_id: The case ID
            
        Returns:
            True if case exists
        """
        return self.get_case(case_id) is not None
    
    def get_case_summary(
        self,
        pipeline_id: Optional[str] = None,
    ) -> Dict[str, int]:
        """
        Get summary counts by status.
        
        Args:
            pipeline_id: Optional filter by pipeline
            
        Returns:
            Dictionary with counts by status
        """
        # Use status constants instead of hardcoded strings
        summary = {
            self.STATUS_PROCESSING: 0,
            self.STATUS_HITL_PENDING: 0,
            self.STATUS_COMPLETED: 0,
            self.STATUS_FAILED: 0,
            "total": 0,
        }
        
        for status in [self.STATUS_PROCESSING, self.STATUS_HITL_PENDING, self.STATUS_COMPLETED, self.STATUS_FAILED]:
            cases = self.list_cases(
                pipeline_id=pipeline_id,
                status=status,
                limit=10000,  # High limit to get all
            )
            summary[status] = len(cases)
            summary["total"] += len(cases)
        
        return summary
    
    def _add_timeline_entry(
        self,
        case_id: str,
        event_type: str,
        event_data: Dict[str, Any],
    ) -> bool:
        """
        Add a timeline entry to a case's case_data.
        
        Args:
            case_id: The case ID
            event_type: Type of event (e.g., "hitl_queued", "hitl_response")
            event_data: Event-specific data
            
        Returns:
            True if updated successfully
        """
        case = self.get_case(case_id)
        if not case:
            self.logger.error("Case not found for timeline entry: {}", case_id)
            return False
        
        # Get current case_data
        case_data = case.get("case_data", {})
        
        # Initialize _timeline if it doesn't exist
        if "_timeline" not in case_data:
            case_data["_timeline"] = []
        
        # Create timeline entry
        # Use "type" to match frontend expectations (frontend looks for entry.type)
        timeline_entry = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            **event_data,
        }
        
        # Append to timeline
        case_data["_timeline"].append(timeline_entry)
        
        # Update case in database
        success = self.database.update_pipeline_case(
            case_id=case_id,
            updates={"case_data": case_data},
        )
        
        if success:
            self.logger.debug(
                "Added timeline entry to case {}: event_type={}",
                case_id, event_type
            )
        else:
            self.logger.error(
                "Failed to add timeline entry to case {}: event_type={}",
                case_id, event_type
            )
        
        return success
