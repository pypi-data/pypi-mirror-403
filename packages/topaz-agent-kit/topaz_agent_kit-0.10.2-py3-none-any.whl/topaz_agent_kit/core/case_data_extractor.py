"""
Case Data Extractor Module

Extracts display-relevant fields from the upstream context based on case configuration.
This creates the lightweight case_data stored in pipeline_cases table.
"""

import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from topaz_agent_kit.utils.logger import Logger


class CaseDataExtractor:
    """
    Extracts case data from upstream context based on case configuration.
    
    The case config defines which fields to extract using dot-notation paths
    like "agent_id.field_name" or "agent_id.nested.field".
    """
    
    def __init__(self):
        self.logger = Logger("CaseDataExtractor")
    
    def extract_case_id(
        self,
        upstream: Dict[str, Any],
        case_config: Dict[str, Any],
        fallback_id: Optional[str] = None,
    ) -> str:
        """
        Extract the case ID from upstream context based on config.
        
        Returns a unique case_id in format: PREFIX-UUID (e.g., BATCH-ABC12345)
        The expression/data is stored in case_data, not in the ID.
        
        Args:
            upstream: The upstream context containing all agent outputs
            case_config: The case configuration with identity settings
            fallback_id: Fallback ID to use if extraction fails (unused now, kept for compatibility)
            
        Returns:
            Unique case_id string
        """
        identity_config = case_config.get("identity", {})
        prefix = identity_config.get("prefix", "")
        uniqueness = identity_config.get("uniqueness", "uuid_suffix")
        
        # Simplified: Just use prefix + UUID (no id_source needed)
        # The expression/data is already stored in case_data, so we don't need it in the ID
        # This keeps IDs simple, URL-safe, and database-friendly: BATCH-ABC12345
        if prefix:
            base_id = prefix
        else:
            base_id = "CASE"  # Default prefix if none provided
        
        # Generate unique case_id based on uniqueness strategy
        # For uuid_suffix, this will add UUID suffix: BATCH-ABC12345
        # For invoice_id, this will use the invoice_id from current_invoice to create deterministic ID
        case_id = self._make_unique(base_id, uniqueness, upstream)
        
        self.logger.debug(
            "Extracted case ID: {} (strategy: {})",
            case_id, uniqueness
        )
        
        return case_id
    
    def _make_unique(self, display_id: str, uniqueness: str, upstream: Optional[Dict[str, Any]] = None) -> str:
        """
        Make the display_id unique based on the uniqueness strategy.
        
        Args:
            display_id: The human-readable display ID
            uniqueness: Strategy - "uuid_suffix", "timestamp", "none", "invoice_id"
            upstream: Optional upstream context for extracting invoice_id when uniqueness="invoice_id"
            
        Returns:
            Unique case_id (stored in uppercase)
        """
        # Convert display_id to uppercase for case_id
        display_id_upper = display_id.upper()
        
        if uniqueness == "uuid_suffix":
            suffix = uuid.uuid4().hex[:8].upper()
            return f"{display_id_upper}-{suffix}"
        elif uniqueness == "timestamp":
            suffix = datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:20].upper()  # Include microseconds for uniqueness
            return f"{display_id_upper}-{suffix}"
        elif uniqueness == "invoice_id":
            # Extract invoice_id from current_invoice.invoice_id in upstream
            if upstream:
                invoice_id = self._get_nested_value(upstream, "current_invoice.invoice_id")
                if invoice_id:
                    # Sanitize the invoice_id and use it as the suffix
                    sanitized_invoice_id = self._sanitize_id(str(invoice_id))
                    # Use sanitized invoice_id as suffix to create deterministic case_id
                    # This ensures the same invoice always gets the same case_id
                    return f"{display_id_upper}-{sanitized_invoice_id.upper()}"
                else:
                    self.logger.warning(
                        "uniqueness='invoice_id' specified but current_invoice.invoice_id not found in upstream. "
                        "Falling back to uuid_suffix."
                    )
                    # Fall back to uuid_suffix if invoice_id not found
                    suffix = uuid.uuid4().hex[:8].upper()
                    return f"{display_id_upper}-{suffix}"
            else:
                self.logger.warning(
                    "uniqueness='invoice_id' specified but upstream not provided. "
                    "Falling back to uuid_suffix."
                )
                # Fall back to uuid_suffix if upstream not provided
                suffix = uuid.uuid4().hex[:8].upper()
                return f"{display_id_upper}-{suffix}"
        elif uniqueness == "none":
            # No uniqueness guarantee - use at your own risk
            return display_id_upper
        else:
            # Default to uuid_suffix
            suffix = uuid.uuid4().hex[:8].upper()
            return f"{display_id_upper}-{suffix}"
    
    def _sanitize_id(self, raw_id: str) -> str:
        """
        Sanitize an ID to make it URL-safe and database-friendly.
        
        Replaces special characters with safe alternatives:
        - Spaces → underscores
        - Special chars (*, +, /, etc.) → underscores
        - Multiple underscores → single underscore
        - Trims underscores from start/end
        
        Args:
            raw_id: The raw ID string (e.g., "((4+5)* 2-5)/2 + 9** 2")
            
        Returns:
            Sanitized ID (e.g., "__4_5__2_5__2__9__2")
        """
        if not raw_id:
            return raw_id
        
        # Replace spaces with underscores
        sanitized = raw_id.replace(" ", "_")
        
        # Replace common special characters with underscores
        # Keep alphanumeric, underscores, and hyphens
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', sanitized)
        
        # Collapse multiple underscores into one
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        
        # If result is empty or too short, use a hash
        if not sanitized or len(sanitized) < 3:
            # Use first 8 chars of hash as fallback
            import hashlib
            hash_id = hashlib.md5(raw_id.encode()).hexdigest()[:8].upper()
            return hash_id
        
        return sanitized
    
    def _generate_fallback_display_id(self, prefix: str = "") -> str:
        """Generate a fallback display ID when extraction fails"""
        short_id = uuid.uuid4().hex[:6].upper()
        if prefix:
            return f"{prefix}-{short_id}"
        return f"CASE-{short_id}"
    
    def extract_case_data(
        self,
        upstream: Dict[str, Any],
        case_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Extract display-relevant data from upstream context.
        
        Args:
            upstream: The upstream context containing all agent outputs
            case_config: The case configuration defining what to extract
            
        Returns:
            Dictionary of extracted case data for display
        """
        case_data = {}
        
        # Extract detail view fields (primary - used in case detail modal)
        detail_view = case_config.get("detail_view", {})
        if detail_view:
            case_data["_detail_view"] = self._extract_detail_view_data(upstream, detail_view)
        
        # Extract list view fields (for case list display with tabs)
        list_view = case_config.get("list_view", {})
        if list_view:
            case_data["_list_view"] = self._extract_list_view_data(upstream, list_view)
        
        # Extract documents information (for Documents tab)
        documents = case_config.get("documents", [])
        if documents:
            case_data["_documents"] = self._extract_documents_data(upstream, documents)
        
        # Extract review response outcome fields (for Review Response Outcome tab)
        review_response_outcome = case_config.get("review_response_outcome", {})
        if review_response_outcome:
            case_data["_review_response_outcome"] = self._extract_detail_view_data(upstream, review_response_outcome)
        
        # Also store raw agent outputs for flexibility
        # Only include agents that are referenced in the config
        referenced_agents = self._get_referenced_agents(case_config)
        for agent_id in referenced_agents:
            if agent_id in upstream:
                case_data[agent_id] = upstream[agent_id]
        
        return case_data
    
    def extract_field(
        self,
        upstream: Dict[str, Any],
        source_path: str,
    ) -> Any:
        """
        Extract a single field from upstream using dot-notation path or expression.
        
        Supports two formats:
        1. Simple dot-notation: "agent_id.field" or "agent_id.nested.field"
        2. Ternary expression: "agent_a.field if agent_a else agent_b.field"
        
        Args:
            upstream: The upstream context
            source_path: Dot-notation path or expression string
            
        Returns:
            The extracted value or None if not found
        """
        # Check if source_path is an expression (contains ternary operator)
        if " if " in source_path and " else " in source_path:
            # Use ExpressionEvaluator to evaluate the expression
            from topaz_agent_kit.utils.expression_evaluator import evaluate_expression_value
            
            try:
                # Prepare context for expression evaluator
                # ExpressionEvaluator expects context with upstream data accessible via dot notation
                # It looks for context.upstream[agent_id] and then accesses parsed or direct fields
                context = {"upstream": upstream}
                
                # Extract agent names from expression to ensure they exist in context
                # This is important for ternary expressions like "aegis_translator.field if aegis_translator else ..."
                # where aegis_translator might not exist in upstream (skipped conditional node)
                agent_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\.'
                expression_agents = set(re.findall(agent_pattern, source_path))
                
                # Add agents from upstream to context
                for agent_id, agent_data in upstream.items():
                    if not agent_id.startswith("_"):
                        # Add agent data directly to context for expression evaluation
                        # This allows expressions to access agents directly (e.g., "aegis_translator")
                        # For simple checks like "if aegis_translator", this provides the agent object
                        if isinstance(agent_data, dict):
                            # For dict agents, add the parsed data if available
                            # This allows "if aegis_translator" to check if agent exists and has data
                            parsed = agent_data.get("parsed", agent_data)
                            context[agent_id] = parsed if parsed else None
                        else:
                            context[agent_id] = agent_data
                
                # Add missing agents (referenced in expression but not in upstream) as None
                # This allows ternary expressions to work correctly when agents are skipped
                for agent_id in expression_agents:
                    if agent_id not in context and agent_id not in upstream:
                        context[agent_id] = None
                        # Also add to upstream as None so ExpressionEvaluator can find it
                        context["upstream"][agent_id] = None
                        self.logger.debug(
                            "Added missing agent '{}' as None to context for expression evaluation",
                            agent_id
                        )
                
                # Evaluate the expression
                result = evaluate_expression_value(source_path, context)
                self.logger.debug(
                    "Evaluated expression '{}' to value: {}",
                    source_path,
                    result
                )
                return result
            except Exception as e:
                self.logger.warning(
                    "Failed to evaluate expression '{}': {}. Falling back to simple path resolution.",
                    source_path,
                    e
                )
                # Fall back to simple path resolution if expression evaluation fails
                # Extract the first path from the expression as fallback
                # e.g., "a.translated_data.invoice_data.invoice_number if a else b.invoice_data.invoice_number"
                # -> try "a.translated_data.invoice_data.invoice_number" first
                if " if " in source_path:
                    first_path = source_path.split(" if ")[0].strip()
                    return self._get_nested_value(upstream, first_path)
                return None
        else:
            # Simple dot-notation path - use existing logic
            return self._get_nested_value(upstream, source_path)
    
    def _extract_list_view_data(
        self,
        upstream: Dict[str, Any],
        list_view_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Extract fields for list view display.
        
        New structure:
        - pipeline_fields: Define pipeline-specific fields with key, field path, label, type
        - column_order: Define which columns to show and in what order (mix of common and pipeline field keys)
        
        Common fields (always available, don't need to define):
        - case_id, pipeline_id, status, hitl_gate_title, hitl_description,
          hitl_status, hitl_decision, responded_by, created_at, updated_at
        
        Also supports legacy structures for backwards compatibility.
        """
        data = {}
        
        # New structure: pipeline_fields and column_order
        pipeline_fields = list_view_config.get("pipeline_fields", [])
        column_order = list_view_config.get("column_order", [])
        
        if pipeline_fields or column_order:
            # Debug: Log what's available in upstream for common loop item keys
            for loop_key in ["current_journal", "current_invoice", "current_claim", "current_problem", "loop_item"]:
                if loop_key in upstream:
                    loop_item = upstream[loop_key]
                    if isinstance(loop_item, dict):
                        self.logger.info(
                            "Found loop item '{}' in upstream with keys: {}",
                            loop_key,
                            list(loop_item.keys())[:30]
                        )
            # Extract pipeline-specific fields
            data["pipeline_fields"] = {}
            for field_config in pipeline_fields:
                # Support both "source" and "field" keys
                source = field_config.get("source") or field_config.get("field")
                if source:
                    # Use extract_field to support expressions
                    value = self.extract_field(upstream, source)
                    key = field_config.get("key")
                    if not key:
                        # Fallback: use last part of field path as key
                        key = source.split(".")[-1] if "." in source else source
                    
                    # Debug logging for missing values
                    if value is None:
                        # Check if the parent object exists
                        if "." in source:
                            parent_path = ".".join(source.split(".")[:-1])
                            parent_value = self.extract_field(upstream, parent_path)
                            if parent_value is None:
                                self.logger.info(
                                    "Field '{}' (key: '{}') is None - parent path '{}' not found in upstream. "
                                    "Available keys in upstream: {}",
                                    source, key, parent_path,
                                    list(upstream.keys())[:20] if isinstance(upstream, dict) else "not a dict"
                                )
                            else:
                                self.logger.info(
                                    "Field '{}' (key: '{}') is None - field not found in parent '{}'. "
                                    "Parent type: {}, Parent keys: {}",
                                    source, key, parent_path,
                                    type(parent_value).__name__,
                                    list(parent_value.keys())[:20] if isinstance(parent_value, dict) else "not a dict"
                                )
                        else:
                            self.logger.info(
                                "Field '{}' (key: '{}') is None - not found in upstream. "
                                "Available keys: {}",
                                source, key,
                                list(upstream.keys())[:20] if isinstance(upstream, dict) else "not a dict"
                            )
                    
                    # Apply value mapping if specified
                    mapped_value = self._apply_value_mapping(value, field_config.get("value_mapping"))
                    
                    data["pipeline_fields"][key] = {
                        "value": mapped_value,
                        "label": field_config.get("label", ""),
                        "type": field_config.get("type", "text"),
                    }
            
            # Store column order (list of keys: common field keys or pipeline field keys)
            if column_order:
                data["column_order"] = column_order
        else:
            # Legacy support: "fields" array or "primary"/"secondary" structure
            fields = list_view_config.get("fields", [])
            if fields:
                # Simple fields array structure
                data["fields"] = []
                for field_config in fields:
                    # Support both "source" and "field" keys
                    source = field_config.get("source") or field_config.get("field")
                    if source:
                        # Use extract_field to support expressions
                        value = self.extract_field(upstream, source)
                        key = field_config.get("key", source.split(".")[-1] if "." in source else source)
                        data["fields"].append({
                            "value": value,
                            "label": field_config.get("label", ""),
                            "type": field_config.get("type", "text"),
                            "key": key,
                        })
            else:
                # Legacy primary/secondary structure
                # Primary field
                primary = list_view_config.get("primary", {})
                if primary:
                    # Support both "source" and "field" keys
                    source = primary.get("source") or primary.get("field")
                    if source:
                        value = self.extract_field(upstream, source)
                        data["primary"] = {
                            "value": value,
                            "label": primary.get("label", ""),
                            "type": primary.get("type", "text"),
                        }
                
                # Secondary fields
                secondary = list_view_config.get("secondary", [])
                data["secondary"] = []
                for field_config in secondary:
                    # Support both "source" and "field" keys
                    source = field_config.get("source") or field_config.get("field")
                    if source:
                        value = self.extract_field(upstream, source)
                        key = field_config.get("key", source.split(".")[-1] if "." in source else source)
                        data["secondary"].append({
                            "value": value,
                            "label": field_config.get("label", ""),
                            "type": field_config.get("type", "text"),
                            "key": key,
                        })
        
        return data
    
    def _extract_documents_data(
        self,
        upstream: Dict[str, Any],
        documents_config: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Extract documents information for the Documents tab.
        
        Supports:
        - Single document: field points to a file path string
        - List of documents: field points to an array of objects with file paths
        - Conditional display: condition expression to show/hide documents
        """
        from topaz_agent_kit.utils.expression_evaluator import evaluate_expression
        
        documents = []
        
        for doc_config in documents_config:
            # Evaluate condition if present
            condition = doc_config.get("condition")
            if condition:
                try:
                    context = {"upstream": upstream}
                    condition_result = evaluate_expression(condition, context)
                    if not condition_result:
                        self.logger.info(
                            "Skipping document '{}' - condition '{}' evaluated to False",
                            doc_config.get("key") or doc_config.get("label"),
                            condition
                        )
                        continue
                except Exception as e:
                    self.logger.warning(
                        "Failed to evaluate condition '{}' for document '{}': {}. Skipping document.",
                        condition,
                        doc_config.get("key") or doc_config.get("label"),
                        e
                    )
                    continue
            
            # Extract field value
            field_path = doc_config.get("field")
            if not field_path:
                continue
            
            value = self.extract_field(upstream, field_path)
            doc_type = doc_config.get("type", "pdf")
            key = doc_config.get("key", "")
            label = doc_config.get("label", self._format_label(key))
            missing_message = doc_config.get("missing_message", "Document not available")
            
            # Handle different document types
            if doc_type == "list":
                # List of documents - each item should have a file path
                if value and isinstance(value, list) and len(value) > 0:
                    item_label_field = doc_config.get("item_label_field", "type")
                    item_path_field = doc_config.get("item_path_field", "file_path")
                    
                    for idx, item in enumerate(value):
                        if not isinstance(item, dict):
                            continue
                        
                        file_path = item.get(item_path_field)
                        # Include even if file_path is missing - will show "not available" message
                        item_label = item.get(item_label_field, f"{label} {idx + 1}")
                        documents.append({
                            "key": f"{key}_{idx}",
                            "label": item_label,
                            "file_path": file_path if file_path else None,
                            "type": doc_type,
                            "missing_message": missing_message,
                        })
                else:
                    # Null, empty list, or not a list - still show the document entry with "not available" message
                    documents.append({
                        "key": key,
                        "label": label,
                        "file_path": None,
                        "type": doc_type,
                        "missing_message": missing_message,
                    })
            else:
                # Single document - value is the file path
                # Include even if value is None/empty - will show "not available" message
                documents.append({
                    "key": key,
                    "label": label,
                    "file_path": value if value and isinstance(value, str) else None,
                    "type": doc_type,
                    "missing_message": missing_message,
                })
        
        return documents
    
    def _extract_detail_view_data(
        self,
        upstream: Dict[str, Any],
        detail_view_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Extract fields for detail view display"""
        from topaz_agent_kit.utils.expression_evaluator import evaluate_expression
        
        data = {"sections": []}
        
        sections = detail_view_config.get("sections", [])
        for section_config in sections:
            # Evaluate condition if present - skip section if condition is false
            condition = section_config.get("condition")
            if condition:
                try:
                    # Log available agents in upstream for debugging
                    available_agents = [k for k in upstream.keys() if not k.startswith("_")]
                    self.logger.info(
                        "Evaluating condition '{}' for section '{}'. Available agents in upstream: {}",
                        condition,
                        section_config.get("id") or section_config.get("title") or section_config.get("name"),
                        available_agents
                    )
                    # Expression evaluator expects context with "upstream" key, not upstream directly
                    context = {"upstream": upstream}
                    condition_result = evaluate_expression(condition, context)
                    if not condition_result:
                        self.logger.info(
                            "Skipping section '{}' - condition '{}' evaluated to False. Available agents: {}",
                            section_config.get("id") or section_config.get("title") or section_config.get("name"),
                            condition,
                            available_agents
                        )
                        continue
                    else:
                        self.logger.info(
                            "Condition '{}' for section '{}' evaluated to True",
                            condition,
                            section_config.get("id") or section_config.get("title") or section_config.get("name")
                        )
                except Exception as e:
                    self.logger.warning(
                        "Failed to evaluate condition '{}' for section '{}': {}. Skipping section.",
                        condition,
                        section_config.get("id") or section_config.get("title") or section_config.get("name"),
                        e
                    )
                    continue
            
            section = {
                "id": section_config.get("id", ""),
                "title": section_config.get("title") or section_config.get("name", ""),  # Support both "title" and "name"
                "fields": [],
            }
            
            # Only use explicit fields - don't include all source_agent fields
            # source_agent is just for reference/documentation, explicit fields define what to show
            explicit_fields = section_config.get("fields", [])
            
            # If no explicit fields but source_agent is specified, include all outputs from that agent
            # (fallback for backwards compatibility)
            if not explicit_fields:
                source_agent = section_config.get("source_agent")
                if source_agent and source_agent in upstream:
                    agent_output = upstream[source_agent]
                    if isinstance(agent_output, dict):
                        for key, value in agent_output.items():
                            section["fields"].append({
                                "key": key,
                                "value": value,
                                "label": self._format_label(key),
                                "type": "auto",
                            })
            else:
                # Use only explicit fields
                for field_config in explicit_fields:
                    # Evaluate field-level condition if present
                    field_condition = field_config.get("condition")
                    if field_condition:
                        try:
                            from topaz_agent_kit.utils.expression_evaluator import evaluate_expression
                            # Context format matches section conditions
                            context = {"upstream": upstream}
                            condition_result = evaluate_expression(field_condition, context)
                            if not condition_result:
                                self.logger.info(
                                    "Skipping field '{}' - condition '{}' evaluated to False",
                                    field_config.get("label") or field_config.get("key") or field_config.get("field"),
                                    field_condition
                                )
                                continue
                        except Exception as e:
                            self.logger.warning(
                                "Failed to evaluate condition '{}' for field '{}': {}. Skipping field.",
                                field_condition,
                                field_config.get("label") or field_config.get("key") or field_config.get("field"),
                                e
                            )
                            continue
                    
                    # Support both "source" and "field" keys for field path
                    source = field_config.get("source") or field_config.get("field")
                    
                    # Special handling for entry_comparison type - construct comparison object
                    field_type = field_config.get("type", "text")
                    if field_type == "entry_comparison":
                        original_field = field_config.get("original_field")
                        corrected_field = field_config.get("corrected_field")
                        if original_field and corrected_field:
                            original_value = self.extract_field(upstream, original_field)
                            
                            # For corrected_field, support fallback logic if it contains "OR"
                            # Try each option in order until one returns a non-None value
                            if " OR " in corrected_field.upper():
                                # Split by " OR " and try each path
                                corrected_options = [f.strip() for f in corrected_field.split(" OR ") if f.strip()]
                                corrected_value = None
                                for option in corrected_options:
                                    corrected_value = self.extract_field(upstream, option)
                                    if corrected_value is not None:
                                        break
                                # If all options returned None, use original_value as fallback
                                if corrected_value is None:
                                    corrected_value = original_value
                            else:
                                corrected_value = self.extract_field(upstream, corrected_field)
                                # If corrected_value is None, fall back to original_value
                                if corrected_value is None:
                                    corrected_value = original_value
                            
                            # Only create comparison if original_value is not None
                            # (corrected_value can be None if no corrections were made, that's fine)
                            if original_value is None:
                                self.logger.debug(
                                    "Skipping entry_comparison field '{}' - original_value is None",
                                    field_config.get("label") or field_config.get("key")
                                )
                                continue
                            
                            # Construct comparison object
                            value = {
                                "original": original_value,
                                "corrected": corrected_value
                            }
                            key = field_config.get("key", "entry_comparison")
                        else:
                            # If comparison fields not specified, skip
                            self.logger.warning(
                                "entry_comparison field '{}' requires both original_field and corrected_field. Skipping.",
                                field_config.get("label") or field_config.get("key")
                            )
                            continue
                    elif source:
                        key = field_config.get("key", source.split(".")[-1])
                        # Use extract_field to support both simple paths and expressions
                        value = self.extract_field(upstream, source)
                    else:
                        # No source and not a comparison field - skip
                        continue
                    
                    # Only add field if value is not None (unless it's a boolean False, which is a valid value)
                    # This prevents showing empty fields with "—" in the UI
                    if value is None:
                        self.logger.debug(
                            "Skipping field '{}' - extracted value is None",
                            field_config.get("label") or field_config.get("key") or field_config.get("field")
                        )
                        continue
                    
                    # Apply value mapping if specified
                    mapped_value = self._apply_value_mapping(value, field_config.get("value_mapping"))
                    
                    field_data = {
                        "key": key,
                        "value": mapped_value,
                        "label": field_config.get("label", self._format_label(key)),
                        "type": field_type,
                    }
                    # Pass through UI metadata (collapsible, summary, etc.)
                    if "collapsible" in field_config:
                        field_data["collapsible"] = field_config["collapsible"]
                    if "collapsible_after" in field_config:
                        field_data["collapsible_after"] = field_config["collapsible_after"]
                    if "summary" in field_config:
                        field_data["summary"] = field_config["summary"]
                    section["fields"].append(field_data)
            
            data["sections"].append(section)
        
        return data
    
    def _get_nested_value(
        self,
        data: Dict[str, Any],
        path: str,
    ) -> Any:
        """
        Get a nested value from a dictionary using dot-notation path.
        
        Handles agent outputs that may be wrapped in "parsed" or "result" keys.
        For paths like "agent_id.field", tries:
        1. data["agent_id"]["field"] (direct)
        2. data["agent_id"]["parsed"]["field"] (parsed wrapper)
        3. data["agent_id"]["result"]["field"] (result wrapper)
        
        Args:
            data: The dictionary to extract from
            path: Dot-notation path like "agent_id.field" or "agent_id.nested.field"
            
        Returns:
            The value at the path or None if not found
        """
        if not path or not data:
            return None
        
        parts = path.split(".")
        if len(parts) < 2:
            return None
        
        agent_id = parts[0]
        field_path = parts[1:]
        
        # Get agent output from upstream
        agent_output = data.get(agent_id)
        if agent_output is None:
            return None
        
        # IMPORTANT: Try "parsed" wrapper FIRST, as it contains the normalized agent output
        # The "result" wrapper contains raw output and should only be used as fallback
        # This ensures we get the correct extracted value (e.g., math_calculator.result from parsed.result)
        # instead of the raw result wrapper
        if isinstance(agent_output, dict) and "parsed" in agent_output:
            current = agent_output["parsed"]
            for part in field_path:
                if isinstance(current, dict):
                    current = current.get(part)
                elif isinstance(current, list) and part.isdigit():
                    index = int(part)
                    if 0 <= index < len(current):
                        current = current[index]
                    else:
                        current = None
                else:
                    current = None
                
                if current is None:
                    break
            
            if current is not None:
                return current
        
        # If not found in parsed, try direct path (for backwards compatibility)
        current = agent_output
        for part in field_path:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                index = int(part)
                if 0 <= index < len(current):
                    current = current[index]
                else:
                    current = None
            else:
                current = None
            
            if current is None:
                break
        
        if current is not None:
            return current
        
        # If still not found, try "result" wrapper
        if isinstance(agent_output, dict) and "result" in agent_output:
            current = agent_output["result"]
            for part in field_path:
                if isinstance(current, dict):
                    current = current.get(part)
                elif isinstance(current, list) and part.isdigit():
                    index = int(part)
                    if 0 <= index < len(current):
                        current = current[index]
                    else:
                        current = None
                else:
                    current = None
                
                if current is None:
                    break
            
            if current is not None:
                return current
        
        # Special case: if field_path is just a single field name and agent_output is a dict,
        # check if that field exists as a top-level key (handles cases where parsed wrapper doesn't exist)
        # BUT only if we haven't already found it in parsed/result wrappers above
        # This is a fallback for edge cases where agent output structure is different
        if isinstance(agent_output, dict) and len(field_path) == 1:
            field_name = field_path[0]
            # Only check top-level if field_name exists and we haven't found it yet
            # This prevents returning wrong values when parsed wrapper exists
            if field_name in agent_output:
                # Double-check: if parsed exists and contains the field, we should have found it above
                # This is just a safety fallback
                if "parsed" not in agent_output or field_name not in agent_output.get("parsed", {}):
                    return agent_output[field_name]
        
        return None
    
    def _get_referenced_agents(
        self,
        case_config: Dict[str, Any],
    ) -> set:
        """Get all agent IDs referenced in the case config"""
        agents = set()
        
        def extract_from_source(source: str):
            if not source:
                return
            
            # Check if source is an expression (contains ternary operator)
            if " if " in source and " else " in source:
                # Extract agent names from expression
                # Match patterns like "agent_id.field" where agent_id is an identifier
                agent_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\.'
                matches = re.findall(agent_pattern, source)
                for agent_id in matches:
                    agents.add(agent_id)
            elif "." in source:
                # Simple dot-notation path
                agents.add(source.split(".")[0])
        
        # Identity
        identity = case_config.get("identity", {})
        extract_from_source(identity.get("id_source", ""))
        
        # Detail view
        detail_view = case_config.get("detail_view", {})
        for section in detail_view.get("sections", []):
            if section.get("source_agent"):
                agents.add(section["source_agent"])
            for field in section.get("fields", []):
                # Support both "field" and "source" keys (field is used in case configs)
                source = field.get("field", "") or field.get("source", "")
                extract_from_source(source)
        
        # List view
        list_view = case_config.get("list_view", {})
        # New structure: pipeline_fields
        for field_config in list_view.get("pipeline_fields", []):
            source = field_config.get("field", "") or field_config.get("source", "")
            extract_from_source(source)
        # Legacy support
        for field_config in list_view.get("fields", []):
            source = field_config.get("field", "") or field_config.get("source", "")
            extract_from_source(source)
        primary = list_view.get("primary", {})
        if primary:
            source = primary.get("field", "") or primary.get("source", "")
            extract_from_source(source)
        for field_config in list_view.get("secondary", []):
            source = field_config.get("field", "") or field_config.get("source", "")
            extract_from_source(source)
        
        # Documents
        documents = case_config.get("documents", [])
        for doc_config in documents:
            source = doc_config.get("field", "")
            extract_from_source(source)
        
        # Review response outcome (uses same structure as detail_view)
        review_response_outcome = case_config.get("review_response_outcome", {})
        for section in review_response_outcome.get("sections", []):
            if section.get("source_agent"):
                agents.add(section["source_agent"])
            for field in section.get("fields", []):
                # Support both "field" and "source" keys (field is used in case configs)
                source = field.get("field", "") or field.get("source", "")
                extract_from_source(source)
                # Also check for original_field and corrected_field (for entry_comparison type)
                original_field = field.get("original_field")
                corrected_field = field.get("corrected_field")
                if original_field:
                    extract_from_source(original_field)
                if corrected_field:
                    extract_from_source(corrected_field)
        
        return agents
    
    def _format_label(self, key: str) -> str:
        """Convert snake_case or camelCase to Title Case label"""
        # Handle snake_case
        if "_" in key:
            words = key.split("_")
        # Handle camelCase
        elif any(c.isupper() for c in key):
            words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', key)
        else:
            words = [key]
        
        return " ".join(word.capitalize() for word in words)
    
    def _apply_value_mapping(self, value: Any, value_mapping: Optional[Dict[str, str]]) -> Any:
        """Apply value mapping to transform display values.
        
        Args:
            value: The raw value to map
            value_mapping: Dictionary mapping raw values to display values
            
        Returns:
            Mapped value if mapping exists, otherwise original value
        """
        if not value_mapping or value is None:
            return value
        
        # Convert value to string for lookup (handles both string and other types)
        value_str = str(value) if value is not None else None
        
        # Check if exact match exists
        if value_str in value_mapping:
            return value_mapping[value_str]
        
        # Check case-insensitive match
        value_lower = value_str.lower() if value_str else None
        for raw_key, display_value in value_mapping.items():
            if raw_key.lower() == value_lower:
                return display_value
        
        # No mapping found, return original value
        return value