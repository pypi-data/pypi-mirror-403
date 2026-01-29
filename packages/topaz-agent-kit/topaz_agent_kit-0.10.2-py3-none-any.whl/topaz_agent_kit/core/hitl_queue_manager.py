"""
HITL Queue Manager Module

Manages the Human-in-the-Loop queue for async HITL processing.
Handles enqueuing, listing, and responding to HITL requests.
"""

import uuid
from typing import Any, Dict, List, Optional

from topaz_agent_kit.core.chat_database import ChatDatabase
from topaz_agent_kit.utils.logger import Logger


class HITLQueueManager:
    """
    Manages the HITL queue for async processing.
    
    Responsibilities:
    - Enqueue HITL requests with rendered descriptions
    - List queue items with filters
    - Submit user responses
    - Manage queue priorities
    """
    
    # Priority levels
    PRIORITY_HIGH = "high"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_LOW = "low"
    
    # Status values
    STATUS_PENDING = "pending"
    STATUS_RESPONDED = "responded"
    STATUS_FAILED = "failed"
    STATUS_EXPIRED = "expired"
    STATUS_CANCELLED = "cancelled"
    
    def __init__(self, database: ChatDatabase):
        """
        Initialize HITLQueueManager.
        
        Args:
            database: ChatDatabase instance for persistence
        """
        self.database = database
        self.logger = Logger("HITLQueueManager")
    
    def enqueue(
        self,
        checkpoint_id: str,
        case_id: str,
        pipeline_id: str,
        gate_id: str,
        gate_type: str,
        gate_config: Dict[str, Any],
        upstream: Dict[str, Any],
        hitl: Dict[str, Any],
        priority: str = "medium",
        project_dir: Optional[str] = None,
    ) -> Optional[str]:
        """
        Add a new HITL request to the queue.
        
        Args:
            checkpoint_id: The checkpoint ID for resumption
            case_id: The case identifier
            pipeline_id: The pipeline identifier
            gate_id: The HITL gate identifier
            gate_type: Type of gate (approval, input, selection)
            gate_config: The gate configuration
            upstream: Upstream context for template rendering
            hitl: Previous HITL decisions for template rendering
            priority: Queue priority (high, medium, low)
            
        Returns:
            The queue_item_id or None if failed
        """
        queue_item_id = f"q-{uuid.uuid4().hex[:12]}"
        
        # Render title and description from templates
        title = self._render_template(
            gate_config.get("title", f"Review Required: {gate_id}"),
            upstream=upstream,
            hitl=hitl,
        )
        
        # Get description - can be:
        # 1. Inline string (directly in YAML): "description: | ..."
        # 2. File reference (dict with jinja key): "description: {jinja: 'path/to/file.jinja'}"
        # 3. Legacy "description_template" key (for backwards compatibility)
        # 4. JSON string representation of dict (if stored as string)
        description_source = gate_config.get("description") or gate_config.get("description_template", "")
        
        # Handle description that might be a dict with "jinja" key pointing to a file
        # First, try to parse if it's a JSON string (handles case where it's stored as string)
        if isinstance(description_source, str):
            # Try to parse as JSON in case it's a string representation of a dict
            # This handles cases where the description was stored as JSON string
            try:
                import json
                # Check if it looks like JSON (starts with { or [)
                if description_source.strip().startswith(("{", "[")):
                    parsed = json.loads(description_source)
                    if isinstance(parsed, dict) and "jinja" in parsed:
                        self.logger.debug("Parsed description from JSON string: {}", parsed)
                        description_source = parsed
            except (json.JSONDecodeError, ValueError, TypeError):
                # Not JSON, continue with string (might be a Jinja template string)
                pass
        
        # Handle dict with "jinja" key pointing to a file
        if isinstance(description_source, dict) and "jinja" in description_source:
            # Load template from file using PromptLoader
            jinja_path = description_source.get("jinja", "unknown")
            self.logger.debug("Loading HITL description from file: {}", jinja_path)
            try:
                from pathlib import Path
                from topaz_agent_kit.utils.prompt_loader import PromptLoader
                # Use provided project_dir or try to get from upstream context
                if not project_dir:
                    project_dir = upstream.get("project_dir")
                if project_dir:
                    project_dir = Path(project_dir)
                    prompt_loader = PromptLoader(project_dir)
                    loaded_description = prompt_loader.load_prompt(description_source)
                    if not loaded_description:
                        self.logger.warning("Failed to load HITL description from file: {} (file not found or empty)", jinja_path)
                        description_source = ""
                    else:
                        # Ensure loaded_description is a string
                        description_source = str(loaded_description) if loaded_description else ""
                        self.logger.debug("Successfully loaded HITL description from file: {} (length: {})", jinja_path, len(description_source))
                else:
                    self.logger.warning("No project_dir available, cannot load HITL description from file: {}. Available keys in upstream: {}", 
                                      jinja_path, list(upstream.keys()) if isinstance(upstream, dict) else "N/A")
                    # Don't set to empty string - keep the dict so we can try to render it later
                    # But we need a string for _render_template, so use empty string as fallback
                    description_source = ""
            except Exception as e:
                self.logger.warning("Failed to load HITL description from file {}: {}, using empty string", jinja_path, e, exc_info=True)
                description_source = ""
        elif not isinstance(description_source, str):
            # Convert to string if it's not already (shouldn't happen, but be safe)
            # This handles cases where description_source is still a dict (shouldn't happen after above checks)
            self.logger.warning("Description source is not a string or dict with jinja key: {} (type: {}), converting to string", 
                              description_source, type(description_source).__name__)
            description_source = str(description_source) if description_source else ""
        
        # Render the description template (works for both inline strings and loaded file content)
        # Both are Jinja2 templates that need to be rendered with context
        # Only render if we have a non-empty string (empty string means template loading failed)
        if description_source:
            try:
                description = self._render_template(
                    description_source,
                    upstream=upstream,
                    hitl=hitl,
                )
                # Ensure description is a string and not a dict representation
                if not isinstance(description, str):
                    self.logger.warning("Rendered description is not a string (type: {}), converting", type(description).__name__)
                    description = str(description) if description else ""
                
                # Safety check: If description looks like a JSON dict (starts with {), it means rendering failed
                # and we got the raw template string. Try to detect and handle this.
                if description.strip().startswith("{") and '"jinja"' in description:
                    self.logger.warning("Description appears to be unrendered dict string: {}. This indicates template loading/rendering failed.", 
                                      description[:100])
                    # Try to extract the jinja path for better error message
                    try:
                        import json
                        parsed = json.loads(description)
                        if isinstance(parsed, dict) and "jinja" in parsed:
                            jinja_path = parsed.get("jinja", "unknown")
                            description = f"HITL review required for gate: {gate_id}\n\n(Template file not found or failed to render: {jinja_path})"
                    except:
                        description = f"HITL review required for gate: {gate_id}\n\n(Template rendering failed)"
            except Exception as e:
                self.logger.error("Failed to render HITL description template: {}", e, exc_info=True)
                description = f"HITL review required for gate: {gate_id}\n\n(Template rendering error: {str(e)})"
        else:
            # Template loading failed - use a fallback message
            description = f"HITL review required for gate: {gate_id}"
            self.logger.warning("Using fallback description for gate {} (template loading failed)", gate_id)
        
        # Get options for selection gates
        # Options can come from:
        # 1. gate_config["options"] - populated from options_source (e.g., aegis_decision_router.dynamic_options)
        # 2. gate_config["actions"] - static options defined in pipeline YAML (legacy/fallback)
        options = None
        if gate_type == "selection":
            # Prefer populated options from options_source, fall back to static actions
            options = gate_config.get("options") or gate_config.get("actions", [])
        
        # Store full gate_config (including buttons) for Review tab
        success = self.database.create_hitl_queue_item(
            queue_item_id=queue_item_id,
            checkpoint_id=checkpoint_id,
            case_id=case_id,
            pipeline_id=pipeline_id,
            gate_id=gate_id,
            gate_type=gate_type,
            title=title,
            description=description,
            options=options,
            gate_config=gate_config,  # Store full gate configuration
            priority=priority,
        )
        
        if success:
            self.logger.info(
                "Enqueued HITL request {} for case {} (gate: {}, priority: {})",
                queue_item_id, case_id, gate_id, priority
            )
            return queue_item_id
        else:
            self.logger.error(
                "Failed to enqueue HITL request for case {} at gate {}",
                case_id, gate_id
            )
            return None
    
    def get_queue_item(self, queue_item_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a queue item by ID.
        
        Args:
            queue_item_id: The queue item ID
            
        Returns:
            Queue item data or None if not found
        """
        return self.database.get_hitl_queue_item(queue_item_id)
    
    def get_queue_item_by_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a queue item by checkpoint ID.
        
        Args:
            checkpoint_id: The checkpoint ID
            
        Returns:
            Queue item data or None if not found
        """
        return self.database.get_hitl_queue_item_by_checkpoint(checkpoint_id)
    
    def list_queue(
        self,
        pipeline_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List queue items with optional filters.
        
        Args:
            pipeline_id: Filter by pipeline
            status: Filter by status
            priority: Filter by priority
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            List of queue items
        """
        return self.database.list_hitl_queue(
            pipeline_id=pipeline_id,
            status=status,
            priority=priority,
            limit=limit,
            offset=offset,
        )
    
    def list_pending(
        self,
        pipeline_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        List pending queue items.
        
        Args:
            pipeline_id: Filter by pipeline
            limit: Maximum number of results
            
        Returns:
            List of pending queue items
        """
        return self.list_queue(
            pipeline_id=pipeline_id,
            status=self.STATUS_PENDING,
            limit=limit,
        )
    
    def get_pending_queue_item(
        self,
        case_id: str,
        gate_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get a pending queue item for a specific case and gate.
        
        This is useful to check if there's already a pending HITL request
        for this case+gate combination before creating a new one.
        
        Args:
            case_id: The case identifier
            gate_id: The gate identifier
            
        Returns:
            Queue item data or None if not found
        """
        return self.database.get_pending_queue_item_by_case_gate(case_id, gate_id)
    
    def get_queue_item_by_case_gate(
        self,
        case_id: str,
        gate_id: str,
        include_responded: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Get a queue item for a specific case and gate combination.
        
        This is useful to prevent duplicate queue item creation when:
        - A loop hits the same gate multiple times for the same case
        - A resumed pipeline hits the same gate again
        
        Args:
            case_id: The case identifier
            gate_id: The gate identifier
            include_responded: If True, include responded queue items (for duplicate prevention)
            
        Returns:
            Queue item data or None if not found
        """
        return self.database.get_queue_item_by_case_gate(
            case_id=case_id,
            gate_id=gate_id,
            include_responded=include_responded,
        )
    
    def submit_response(
        self,
        queue_item_id: str,
        decision: str,
        response_data: Optional[Dict[str, Any]] = None,
        responded_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Submit a user response to a queue item.
        
        Args:
            queue_item_id: The queue item ID
            decision: The user's decision (e.g., "approve", "reject", action ID)
            response_data: Additional response data
            responded_by: User who responded
            
        Returns:
            Dictionary with success status and checkpoint_id for resumption
        """
        # Get the queue item first
        queue_item = self.get_queue_item(queue_item_id)
        
        if not queue_item:
            self.logger.error("Queue item not found: {}", queue_item_id)
            return {"success": False, "error": "Queue item not found"}
        
        if queue_item.get("status") != self.STATUS_PENDING:
            self.logger.warning(
                "Queue item {} has status {}, cannot respond",
                queue_item_id, queue_item.get("status")
            )
            return {
                "success": False,
                "error": f"Queue item already has status: {queue_item.get('status')}"
            }
        
        # Update the queue item
        success = self.database.update_hitl_queue_response(
            queue_item_id=queue_item_id,
            decision=decision,
            response_data=response_data,
            responded_by=responded_by,
        )
        
        if success:
            self.logger.info(
                "Response submitted for queue item {}: decision={}",
                queue_item_id, decision
            )
            return {
                "success": True,
                "queue_item_id": queue_item_id,
                "checkpoint_id": queue_item["checkpoint_id"],
                "case_id": queue_item["case_id"],
                "decision": decision,
            }
        else:
            self.logger.error(
                "Failed to submit response for queue item {}",
                queue_item_id
            )
            return {"success": False, "error": "Failed to update queue item"}
    
    def cancel_queue_item(self, queue_item_id: str) -> bool:
        """
        Cancel a queue item (mark as cancelled).
        
        Args:
            queue_item_id: The queue item ID
            
        Returns:
            True if cancelled successfully
        """
        success = self.database.update_hitl_queue_response(
            queue_item_id=queue_item_id,
            decision="cancelled",
        )
        
        if success:
            self.logger.info("Cancelled queue item: {}", queue_item_id)
        
        return success
    
    def reset_queue_item_for_retry(self, queue_item_id: str) -> Dict[str, Any]:
        """
        Reset a failed or responded queue item back to pending status for retry.
        
        Args:
            queue_item_id: The queue item ID to reset
            
        Returns:
            Dictionary with success status
        """
        queue_item = self.get_queue_item(queue_item_id)
        if not queue_item:
            return {"success": False, "error": "Queue item not found"}
        
        current_status = queue_item.get("status")
        if current_status not in [self.STATUS_RESPONDED, self.STATUS_FAILED]:
            return {
                "success": False,
                "error": f"Cannot retry queue item with status: {current_status}. Only 'responded' or 'failed' items can be retried.",
            }
        
        # Reset status to pending and clear response data
        success = self.database.update_hitl_queue_item_status(
            queue_item_id=queue_item_id,
            status=self.STATUS_PENDING,
            clear_response=True,
        )
        
        if success:
            self.logger.info(
                "Reset queue item {} from {} to pending for retry",
                queue_item_id, current_status
            )
            return {
                "success": True,
                "queue_item_id": queue_item_id,
                "previous_status": current_status,
                "message": f"Queue item {queue_item_id} reset to pending. You can now retry the response.",
            }
        else:
            return {
                "success": False,
                "error": "Failed to reset queue item status",
            }
    
    def delete_queue_item(self, queue_item_id: str) -> bool:
        """
        Delete a queue item.
        
        Args:
            queue_item_id: The queue item ID
            
        Returns:
            True if deleted successfully
        """
        success = self.database.delete_hitl_queue_item(queue_item_id)
        
        if success:
            self.logger.info("Deleted queue item: {}", queue_item_id)
        
        return success
    
    def get_queue_count(
        self,
        pipeline_id: Optional[str] = None,
        status: str = "pending",
    ) -> int:
        """
        Get count of queue items.
        
        Args:
            pipeline_id: Filter by pipeline
            status: Filter by status
            
        Returns:
            Count of matching items
        """
        return self.database.get_hitl_queue_count(
            pipeline_id=pipeline_id,
            status=status,
        )
    
    def get_queue_summary(
        self,
        pipeline_id: Optional[str] = None,
    ) -> Dict[str, int]:
        """
        Get summary counts by status and priority.
        
        Args:
            pipeline_id: Optional filter by pipeline
            
        Returns:
            Dictionary with counts
        """
        summary = {
            "pending": 0,
            "pending_high": 0,
            "pending_medium": 0,
            "pending_low": 0,
            "responded": 0,
            "total": 0,
        }
        
        # Get pending by priority
        for priority in ["high", "medium", "low"]:
            items = self.list_queue(
                pipeline_id=pipeline_id,
                status=self.STATUS_PENDING,
                priority=priority,
                limit=10000,
            )
            summary[f"pending_{priority}"] = len(items)
            summary["pending"] += len(items)
            summary["total"] += len(items)
        
        # Get responded
        responded = self.list_queue(
            pipeline_id=pipeline_id,
            status=self.STATUS_RESPONDED,
            limit=10000,
        )
        summary["responded"] = len(responded)
        summary["total"] += len(responded)
        
        return summary
    
    def _render_template(
        self,
        template_str: str,
        upstream: Dict[str, Any],
        hitl: Dict[str, Any],
    ) -> str:
        """
        Render a Jinja2 template with context.
        
        Args:
            template_str: The template string
            upstream: Upstream context
            hitl: HITL context
            
        Returns:
            Rendered string
        """
        if not template_str:
            return ""
        
        try:
            from jinja2 import Environment, Undefined
            from topaz_agent_kit.utils.jinja2_filters import register_jinja2_filters
            
            class SafeUndefined(Undefined):
                """Custom Undefined class that returns empty string instead of raising errors."""
                def __getattr__(self, name: str) -> Any:
                    return SafeUndefined()
                
                def __getitem__(self, key: Any) -> Any:
                    return SafeUndefined()
                
                def __str__(self) -> str:
                    return ""
                
                def __repr__(self) -> str:
                    return ""
            
            env = Environment(undefined=SafeUndefined, autoescape=False)
            register_jinja2_filters(env)
            template = env.from_string(template_str)
            
            # Build context similar to pipeline_runner.py for consistency
            # Flatten parsed outputs so agent_id.field works directly
            render_context = {}
            flat: Dict[str, Any] = {}
            
            if isinstance(upstream, dict):
                for agent_id, node in upstream.items():
                    # Handle accumulated loop results (list of results from multiple iterations)
                    if isinstance(node, list):
                        if not node:
                            continue
                        # Use the last element (most recent iteration's result)
                        node = node[-1]
                        # Handle nested lists
                        while isinstance(node, list):
                            if not node:
                                break
                            node = node[-1]
                        if not isinstance(node, dict):
                            continue
                    
                    if not isinstance(node, dict):
                        continue
                    
                    # Get parsed output (normalized agent output)
                    parsed = node.get("parsed")
                    if parsed is None:
                        # Fallback to result if parsed is missing
                        if "result" in node and isinstance(node.get("result"), dict):
                            parsed = node["result"]
                        else:
                            continue
                    
                    # If parsed is a string, try to parse it as JSON
                    if isinstance(parsed, str):
                        try:
                            from topaz_agent_kit.utils.json_utils import JSONUtils
                            parsed = JSONUtils.parse_json_from_text(parsed, expect_json=False)
                        except Exception:
                            parsed = None
                    
                    if isinstance(parsed, dict):
                        # Add agent namespace: render_context[agent_id] = parsed
                        render_context[agent_id] = parsed
                        # Also flatten for convenience: render_context["field"] = value
                        for k, v in parsed.items():
                            if k not in render_context:
                                flat[k] = v
            
            # Update render context with flattened values
            render_context.update({k: v for k, v in flat.items() if k not in render_context})
            
            # Add upstream and hitl for explicit access
            render_context["upstream"] = upstream
            render_context["hitl"] = hitl
            
            # Add loop items (any key starting with "current_")
            if isinstance(upstream, dict):
                for key, value in upstream.items():
                    if key.startswith("current_") and key not in render_context:
                        render_context[key] = value
            
            # CRITICAL FIX: Scan template for expressions that reference agents
            # This ensures that when Jinja2 evaluates expressions like
            # "{{aegis_translator.translated_data.invoice_data.invoice_number if aegis_translator else ...}}"
            # all referenced agents exist in the render context (even if None)
            # This is especially important for conditional nodes that may be skipped
            import re
            # Find all Jinja2 expressions in the template: {{ ... }}
            jinja_expr_pattern = r'\{\{([^}]+)\}\}'
            expressions = re.findall(jinja_expr_pattern, template_str)
            
            for expr in expressions:
                # Check if expression contains ternary operator (if/else)
                if ' if ' in expr and ' else ' in expr:
                    # Extract agent names from the expression
                    # Match patterns like "agent_id.field" where agent_id is an identifier
                    agent_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z0-9_.]+)'
                    matches = re.findall(agent_pattern, expr)
                    for agent_id, _ in matches:
                        # If agent is not in render_context, add it as None
                        # This allows ternary expressions to evaluate correctly
                        # when the agent was skipped (e.g., conditional step)
                        if agent_id not in render_context:
                            render_context[agent_id] = None
                            self.logger.debug(
                                "Added missing agent '{}' as None to HITL render context for template expression evaluation",
                                agent_id
                            )
            
            return template.render(**render_context)
            
        except Exception as e:
            self.logger.warning(
                "Failed to render template, returning raw: {}",
                str(e)
            )
            return template_str
