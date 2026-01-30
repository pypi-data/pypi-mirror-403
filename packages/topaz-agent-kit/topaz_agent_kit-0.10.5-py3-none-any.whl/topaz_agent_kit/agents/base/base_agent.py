"""
Minimal agent interface that all agents must implement.
This provides the contract for agent orchestration while allowing framework-specific implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

from topaz_agent_kit.utils.json_utils import JSONUtils
from topaz_agent_kit.utils.prompt_loader import PromptLoader
from topaz_agent_kit.core.agentos.memory_config import MemoryConfigLoader
from topaz_agent_kit.frameworks.framework_config_manager import FrameworkConfigManager
from topaz_agent_kit.frameworks.framework_model_factory import FrameworkModelFactory
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.core.exceptions import AgentError
from topaz_agent_kit.frameworks.framework_mcp_manager import FrameworkMCPManager
from topaz_agent_kit.utils.agent_output_parser import AgentOutputParser
from topaz_agent_kit.local_tools.loader import LocalToolLoader
from topaz_agent_kit.local_tools.framework_adapter import FrameworkToolAdapter

class BaseAgent(ABC):
    """
    Minimal interface that all agents must implement.
    Framework-specific base classes inherit from this and provide framework-specific implementations.
    """
    
    def __init__(self, agent_id: str, agent_type: str, **kwargs):
        # Add logger for base class
        self.logger = Logger(f"BaseAgent({agent_id})")

        # Agent instance
        self.agent = None
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.framework_type = agent_type
        self.agent_config = kwargs.get("agent_config", {})
        # MCP config can come from kwargs or agent_config
        self.mcp_config = kwargs.get("mcp_config") or self.agent_config.get("mcp", {})
        
        # Common attributes for all agents
        self.name = self.agent_config.get("name", agent_id)
        self.model_preference = self.agent_config.get("model")
        self.llm = None
        self.tools = []
        self.local_tools = []  # Pipeline-specific local tools (separate from MCP tools)
        self.project_dir = ""

        # Prompt configuration
        self.prompt = ""
        self._prompt_spec = self.agent_config.get("prompt")
        self._prompt_loader = None  # Will be initialized when project_dir is available

        self._initialized = False
    
    @abstractmethod
    async def _filter_mcp_tools(self) -> None:
        """Framework-specific MCP tool filtering logic"""
        pass

    @abstractmethod
    async def _log_tool_details(self) -> None:
        """Framework-specific tool detail logging"""
        pass
    
    @abstractmethod
    def _setup_environment(self):
        """
        Setup framework-specific environment
        
        Args:
            project_dir: Project directory
        """
        pass

    @abstractmethod
    def _create_agent(self):
        """Create framework-specific agent"""
        pass

    @abstractmethod
    def get_agent_variables(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get agent-specific variables for prompt population."""
        pass

    @abstractmethod
    def _execute_agent(self, context: Dict[str, Any]):
        """
        Execute framework-specific agent

        Args:
            context: Execution context
        """
        pass

    @abstractmethod
    def _initialize_agent(self):
        """Initialize framework-specific agent"""
        pass

    def is_initialized(self) -> bool:
        """Check if agent has been initialized"""
        return self._initialized
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get basic agent information"""
        return {
            "id": self.agent_id,
            "type": self.agent_type,
            "initialized": self._initialized
        } 

    async def initialize(self, context: Dict[str, Any]) -> None:
        """Initialize the agent with context"""
        # Always update pipeline_id from context (even if already initialized)
        # This ensures memory section has correct pipeline_id
        pipeline_id_from_context = context.get("pipeline_id") or context.get("pipeline")
        old_pipeline_id = getattr(self, '_pipeline_id', None)
        
        if pipeline_id_from_context:
            self._pipeline_id = pipeline_id_from_context
            self.logger.debug("Updated _pipeline_id for agent {}: {}", self.agent_id, self._pipeline_id)
        
        # If pipeline_id changed and agent is already initialized, we need to re-inject memory section
        pipeline_id_changed = old_pipeline_id != getattr(self, '_pipeline_id', None)
        
        # Skip if already fully initialized (agent created)
        # This prevents re-initialization on subsequent requests for remote agents
        if self._initialized and self.agent is not None:
            # If pipeline_id changed, re-inject memory section
            if pipeline_id_changed and hasattr(self, 'prompt') and isinstance(self.prompt, dict):
                self.logger.debug("Agent {} already initialized but pipeline_id changed, re-injecting memory section", self.agent_id)
                self._inject_memory_section()
            else:
                self.logger.debug("Agent {} already initialized, skipping re-initialization", self.agent_id)
            return
        
        try:
            self.logger.debug("Initializing {} agent with context keys: {}", self.agent_type, list(context.keys()))
            self.logger.debug("Agent config: {}", self.agent_config)
            self.logger.debug("Model preference: {}", self.model_preference)
            
            self.project_dir = context.get("project_dir")
            if self.project_dir:
                self.project_dir = Path(self.project_dir)
                self.logger.info("Project directory from context: {}", self.project_dir)
            else:
                self.logger.error("No project_dir in context or parameter")
                raise AgentError("No project_dir in context or parameter")
            
            # Store pipeline_id from context for memory section injection (if not already set above)
            if not hasattr(self, '_pipeline_id') or self._pipeline_id is None:
                self._pipeline_id = pipeline_id_from_context
            
            # Initialize prompt loader
            self._prompt_loader = PromptLoader(self.project_dir)
            
            # Setup environment
            load_dotenv(self.project_dir / ".env")
            self._setup_environment()

            # Load prompt
            if self._prompt_spec:
                self.logger.info("Loading prompt for agent {}...", self.agent_id)
                if self.agent_type != "crewai":
                    self.prompt = self._load_prompt(self._prompt_spec)
                    
                    # Inject memory section if memory is configured
                    self._inject_memory_section()
                    
                    self.logger.success("Loaded prompt - instruction: {} chars, inputs: {} chars", len(self.prompt["instruction"]), len(self.prompt["inputs"]))
            else:
                self.logger.warning("No prompt specified")
                raise AgentError("No prompt specified")
            
            # Initialize LLM using unified factory
            self.logger.info("Starting LLM initialization with unified factory...")
            self._initialize_llm(context)
            self.logger.success("LLM initialization completed")
            
            # Initialize MCP tools using unified manager
            self.logger.info("Starting MCP tools initialization with unified manager...")
            await self._initialize_mcp_tools(context)
            self.logger.success("MCP tools initialization completed")

            # Initialize local tools (pipeline-specific)
            self.logger.info("Starting local tools initialization...")
            await self._initialize_local_tools(context)
            self.logger.success("Local tools initialization completed")

            # Initialize agent for any framework-specific initialization
            self.logger.info("Starting {} agent framework-specific initialization...", self.agent_type)
            self._initialize_agent()
            self._initialized = True
            self.logger.success(f"{self.agent_type} agent initialized successfully")

            # Create agent instance
            self.logger.debug(f"Creating {self.agent_type} agent...")
            self._create_agent()
            self.logger.success(f"{self.agent_type} agent created successfully")
            
        except Exception as e:
            self.logger.error(f"{self.agent_type} agent initialization failed: {e}")
            raise AgentError(f"{self.agent_type} agent initialization failed: {e}")

    def _load_prompt(self, prompt_spec: Dict[str, Any]) -> Dict[str, str]:
        """Load prompt template with instruction and inputs sections"""
        try:
            result = {}
            self.logger.debug("Using prompt format with instruction/inputs sections")
            
            # Load instruction prompt template (without rendering variables)
            instruction_spec = prompt_spec["instruction"]
            result["instruction"] = self._prompt_loader.load_prompt(instruction_spec)
            
            # Load inputs prompt template (without rendering variables)
            inputs_spec = prompt_spec["inputs"]
            result["inputs"] = self._prompt_loader.load_prompt(inputs_spec)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to load prompt: {e}")
            raise AgentError(f"Prompt loading failed: {e}")
    
    def _get_nested_value(self, data: Any, path: str) -> Any:
        """
        Get a nested value from a dictionary using dot notation path.
        
        Args:
            data: Dictionary or value to traverse
            path: Dot-separated path (e.g., "rfp_data.evaluation_criteria")
            
        Returns:
            Value at the path if found, None otherwise
        """
        if not path or not isinstance(data, dict):
            return None
        
        parts = path.split(".")
        value = data
        
        for field in parts:
            if isinstance(value, dict) and field in value:
                value = value[field]
            else:
                return None
        
        return value
    
    def _resolve_array_indexed_variable(self, parsed_data: dict, var_name: str, context: Dict[str, Any], agent_id: str) -> Any:
        """
        Resolve a variable that includes array indexing (e.g., "supplier_response_paths[supplier_loop.index]").
        
        Args:
            parsed_data: The parsed data dictionary to search in
            var_name: Variable name that may include array indexing
            context: Execution context for evaluating index expressions
            agent_id: Agent ID for logging purposes
            
        Returns:
            The resolved value if found, None otherwise
        """
        if '[' not in var_name or ']' not in var_name:
            return None
        
        # Extract base field name and index expression
        bracket_start = var_name.find('[')
        bracket_end = var_name.find(']')
        if bracket_start >= bracket_end:
            return None
        
        base_field = var_name[:bracket_start]
        index_expr = var_name[bracket_start + 1:bracket_end]
        
        # Get the base field value
        base_value = None
        if base_field in parsed_data:
            base_value = parsed_data[base_field]
        else:
            # Try nested path for base field
            base_value = self._get_nested_value(parsed_data, base_field)
        
        if base_value is None or not isinstance(base_value, list):
            return None
        
        # Evaluate index expression from context
        index_value = None
        if '.' in index_expr:
            # Nested path like "supplier_loop.index"
            # First try direct context access (e.g., context["supplier_loop"]["index"])
            index_value = self._get_nested_value(context, index_expr)
            # If not found, try accessing through variables (for loop context)
            if index_value is None:
                parts = index_expr.split('.')
                if len(parts) == 2:
                    obj_name, field_name = parts
                    obj = context.get(obj_name)
                    if isinstance(obj, dict) and field_name in obj:
                        index_value = obj[field_name]
                    # Also try accessing from base variables (which includes loop context)
                    # This handles cases where loop context is added to variables dict
                    if index_value is None:
                        base_vars = self._get_base_agent_variables(context)
                        if obj_name in base_vars:
                            obj = base_vars[obj_name]
                            if isinstance(obj, dict) and field_name in obj:
                                index_value = obj[field_name]
        else:
            # Simple variable name
            index_value = context.get(index_expr)
            # Also try from base variables
            if index_value is None:
                base_vars = self._get_base_agent_variables(context)
                index_value = base_vars.get(index_expr)
        
        if index_value is None or not isinstance(index_value, int):
            self.logger.warning("Could not evaluate index expression '{}' for '{}' in agent '{}' (got: {}). Context keys: {}", index_expr, base_field, agent_id, index_value, list(context.keys())[:10])
            return None
        
        # Access list at index
        if 0 <= index_value < len(base_value):
            self.logger.debug("Found array-indexed variable '{}' in agent '{}' parsed data: {}", var_name, agent_id, base_value[index_value])
            return base_value[index_value]
        else:
            self.logger.warning("Index {} out of range for '{}' in agent '{}' (list length: {})", index_value, base_field, agent_id, len(base_value))
            return None
    
    def _strip_jinja_filters(self, var_name: str) -> str:
        """
        Strip Jinja2 filters from variable names before lookup.
        
        This method safely strips Jinja2 filters (e.g., | default([]) | tojson) from variable names
        so they can be looked up in the context. The filters are preserved in the prompt template
        and will be applied by Jinja2 during rendering.
        
        Examples:
        - "problems | default([]) | tojson" -> "problems"
        - "field | default('N/A')" -> "field"
        - "agent.field | upper" -> "agent.field"
        - "nested.path.field | default([])" -> "nested.path.field"
        - "simple_field" -> "simple_field" (no change)
        
        Safety: Only strips filters if pipe is followed by whitespace (standard Jinja2 syntax).
        This prevents false positives if a field name legitimately contains '|' (extremely rare).
        
        Args:
            var_name: Variable name that may include Jinja filters
            
        Returns:
            Variable name with filters stripped (whitespace trimmed)
        """
        # Strip whitespace first
        var_name = var_name.strip()
        
        # Check if this looks like a Jinja filter expression
        # Standard Jinja syntax: "variable | filter" (pipe followed by whitespace)
        # We check for " | " (pipe with spaces) to avoid false positives
        # Edge case: "variable|filter" (no spaces) is also valid Jinja, so check for any pipe
        if '|' in var_name:
            # Split on pipe and take the first part (the variable name)
            # This handles: "field | filter1 | filter2" -> "field"
            # Also handles nested paths: "agent.field | default([])" -> "agent.field"
            # Also handles: "field|filter" -> "field" (edge case with no spaces)
            parts = var_name.split('|', 1)
            base_var = parts[0].strip()
            
            # Safety check: If the "filter" part doesn't look like a filter (e.g., no parentheses,
            # no common filter names), this might be a false positive. However, since field names
            # with '|' are extremely rare and not recommended, we'll proceed with stripping.
            # The worst case is that a variable lookup fails, which will be logged and handled gracefully.
            return base_var
        
        return var_name
    
    def _get_upstream_variable(self, context: Dict[str, Any], agent_name: str, var_name: str) -> Any:
        """
        Get a variable from upstream agent output.
        Always uses parsed data for reliable extraction.
        Supports nested paths using dot notation (e.g., "rfp_data.evaluation_criteria").
        
        Args:
            context: Execution context
            agent_name: ID of the upstream agent, or "auto" to search all
            var_name: Name of the variable to extract (can be nested like "rfp_data.evaluation_criteria", may include Jinja filters)
            
        Returns:
            Variable value if found, None otherwise
        """
        try:
            # CRITICAL: Strip Jinja filters from var_name before lookup
            # Filters like "problems | default([]) | tojson" should be stripped to "problems"
            # The filters will be applied by Jinja2 when rendering the prompt
            var_name = self._strip_jinja_filters(var_name)
            
            if agent_name == "auto":
                # 🆕 FIXED: Search through ALL upstream agents, not just direct parents
                upstream_context = context.get("upstream", {})
                
                # Search through all agents in upstream context
                for agent_id, agent_data in upstream_context.items():
                    # Skip the current agent itself
                    if agent_id == self.agent_id:
                        continue
                    
                    # Handle accumulated loop results (list of results from multiple iterations)
                    # When accumulate_results is true, upstream context contains lists instead of single dicts
                    if isinstance(agent_data, list):
                        # Get the current iteration's result (last element in the list)
                        if not agent_data:
                            continue  # Skip empty lists
                        
                        # IMPORTANT: For dot-notation paths, try the FIRST element first (for pre-loop agents),
                        # then the LAST element (for loop-specific agents).
                        first_element = agent_data[0]
                        last_element = agent_data[-1]
                        
                        # Handle nested lists in both elements
                        while isinstance(first_element, list):
                            if not first_element:
                                break
                            first_element = first_element[0]
                        while isinstance(last_element, list):
                            if not last_element:
                                break
                            last_element = last_element[-1]
                        
                        # Try first element first (for pre-loop agents with dot-notation paths)
                        if isinstance(first_element, dict):
                            if "parsed" in first_element and isinstance(first_element["parsed"], dict):
                                parsed_data = first_element["parsed"]
                                if isinstance(parsed_data, dict):
                                    # Check if field exists in first element
                                    if var_name in parsed_data:
                                        self.logger.debug(
                                            "Found variable '{}' in agent '{}' first element (pre-loop agent)",
                                            var_name, agent_id
                                        )
                                        return parsed_data[var_name]
                                    # Try nested path
                                    nested_value = self._get_nested_value(parsed_data, var_name)
                                    if nested_value is not None:
                                        self.logger.debug(
                                            "Found nested variable '{}' in agent '{}' first element (pre-loop agent)",
                                            var_name, agent_id
                                        )
                                        return nested_value
                        
                        # Fallback to last element (for loop-specific agents or if first element doesn't have the field)
                        # Use the last element (most recent iteration's result)
                        agent_data = last_element
                        # Ensure we have a dict after extracting from list(s)
                        if not isinstance(agent_data, dict):
                            continue  # Skip non-dict results
                    
                    # Try to get the variable from this agent's output
                    if isinstance(agent_data, dict):
                        # Try parsed data first
                        if "parsed" in agent_data:
                            parsed_data = agent_data["parsed"]
                            # If parsed_data is a string, try to parse it as JSON
                            if isinstance(parsed_data, str):
                                try:
                                    parsed_data = JSONUtils.parse_json_from_text(parsed_data, expect_json=False)
                                except Exception as e:
                                    self.logger.debug("Failed to parse JSON string from agent '{}': {}", agent_id, e)
                                    parsed_data = None
                            
                            if isinstance(parsed_data, dict):
                                # Handle array indexing (e.g., "supplier_response_paths[supplier_loop.index]")
                                array_indexed_value = self._resolve_array_indexed_variable(parsed_data, var_name, context, agent_id)
                                if array_indexed_value is not None:
                                    return array_indexed_value
                                
                                # Try direct key first (for backward compatibility)
                                if var_name in parsed_data:
                                    self.logger.debug("Found variable '{}' in agent '{}' parsed data: {}", var_name, agent_id, parsed_data[var_name])
                                    return parsed_data[var_name]
                                # Try nested path
                                nested_value = self._get_nested_value(parsed_data, var_name)
                                if nested_value is not None:
                                    self.logger.debug("Found nested variable '{}' in agent '{}' parsed data", var_name, agent_id)
                                    return nested_value
                        
                        # Try raw data with JSON parsing
                        if "result" in agent_data:
                            result = JSONUtils.extract_variable_from_output(agent_data["result"], var_name)
                            if result is not None:
                                self.logger.debug("Found variable '{}' in agent '{}' raw data: {}", var_name, agent_id, result)
                                return result
                
                self.logger.warning("Variable '{}' not found in any upstream agent", var_name)
                return None
            else:
                # Get from specific upstream agent
                # The upstream context structure is: context["upstream"][agent_name]
                upstream_context = context.get("upstream", {})
                parent_output = upstream_context.get(agent_name, {})
                
                # CRITICAL: If agent_name not found in upstream, check top-level context for alias
                # This handles enhanced repeat patterns where instance results are stored under instance IDs
                # (e.g., enhanced_math_repeater_file_reader_0) but accessed via base agent ID alias
                # (e.g., enhanced_math_repeater_file_reader) in top-level context
                if not parent_output and agent_name in context:
                    # Check if this is an alias (dict with parsed output structure)
                    alias_data = context[agent_name]
                    if isinstance(alias_data, dict):
                        # This is likely an alias - use it as the parent output
                        parent_output = {"parsed": alias_data}
                        self.logger.debug(
                            "Using agent ID alias '{}' from top-level context (for enhanced repeat pattern)",
                            agent_name
                        )
                
                if not parent_output:
                    self.logger.warning("Upstream agent '{}' not found in context or upstream", agent_name)
                    return None
                
                # Handle accumulated loop results (list of results from multiple iterations)
                # When accumulate_results is true, upstream context contains lists instead of single dicts
                if isinstance(parent_output, list):
                    # Get the current iteration's result (last element in the list)
                    # During loop execution, the list contains results from previous iterations
                    # For the current iteration, we want the most recent result
                    if not parent_output:
                        self.logger.warning("Upstream agent '{}' has empty accumulated results", agent_name)
                        return None
                    
                    # IMPORTANT: For dot-notation paths (e.g., batch_problem_parser.problems),
                    # try the FIRST element first (for pre-loop agents), then the LAST element (for loop-specific agents).
                    # Pre-loop agents (like batch_problem_parser) have their original result in the first element,
                    # while loop-specific agents have their latest result in the last element.
                    first_element = parent_output[0]
                    last_element = parent_output[-1]
                    
                    # Handle nested lists in both elements
                    while isinstance(first_element, list):
                        if not first_element:
                            break
                        first_element = first_element[0]
                    while isinstance(last_element, list):
                        if not last_element:
                            break
                        last_element = last_element[-1]
                    
                    # Log for debugging pre-loop agent access
                    self.logger.debug(
                        "Agent '{}' is a list ({} items). For dot-notation path '{}', trying first element (pre-loop) then last element (loop-specific)",
                        agent_name, len(parent_output), var_name
                    )
                    
                    # Try first element first (for pre-loop agents with dot-notation paths)
                    # Also try first element for loop-specific agents when accessing nested fields
                    # (e.g., reconvoy_related_items_discovery.related_items_mappings[item_id] needs first element's mapping)
                    if isinstance(first_element, dict):
                        # Try to find the field in first element
                        if "parsed" in first_element and isinstance(first_element["parsed"], dict):
                            parsed_data = first_element["parsed"]
                            if isinstance(parsed_data, dict):
                                # Check if field exists in first element
                                if var_name in parsed_data:
                                    self.logger.debug(
                                        "Found variable '{}' in agent '{}' first element (pre-loop agent)",
                                        var_name, agent_name
                                    )
                                    return parsed_data[var_name]
                                # Try nested path
                                nested_value = self._get_nested_value(parsed_data, var_name)
                                if nested_value is not None:
                                    self.logger.debug(
                                        "Found nested variable '{}' in agent '{}' first element (pre-loop agent or nested field access)",
                                        var_name, agent_name
                                    )
                                    return nested_value
                                # SPECIAL CASE: For nested paths like "related_items_mappings[item_id]",
                                # if the nested path contains a key that might be in a dict (like mappings),
                                # check if the base field exists and is a dict, then try to find the key in it
                                if '.' in var_name:
                                    parts = var_name.split('.')
                                    base_field = parts[0]
                                    if base_field in parsed_data and isinstance(parsed_data[base_field], dict):
                                        # This is a nested dict access - return the whole dict so Jinja2 can access [item_id]
                                        self.logger.debug(
                                            "Found base field '{}' in agent '{}' first element - returning dict for nested access",
                                            base_field, agent_name
                                        )
                                        return parsed_data[base_field]
                        # Also try result field if parsed didn't have it
                        if "result" in first_element:
                            result_data = first_element["result"]
                            if isinstance(result_data, dict):
                                if var_name in result_data:
                                    self.logger.debug(
                                        "Found variable '{}' in agent '{}' first element result (pre-loop agent)",
                                        var_name, agent_name
                                    )
                                    return result_data[var_name]
                                nested_value = self._get_nested_value(result_data, var_name)
                                if nested_value is not None:
                                    self.logger.debug(
                                        "Found nested variable '{}' in agent '{}' first element result (pre-loop agent)",
                                        var_name, agent_name
                                    )
                                    return nested_value
                        # Try direct access (if first_element itself is the parsed data)
                        if var_name in first_element:
                            self.logger.debug(
                                "Found variable '{}' in agent '{}' first element directly (pre-loop agent)",
                                var_name, agent_name
                            )
                            return first_element[var_name]
                        nested_value = self._get_nested_value(first_element, var_name)
                        if nested_value is not None:
                            self.logger.debug(
                                "Found nested variable '{}' in agent '{}' first element directly (pre-loop agent)",
                                var_name, agent_name
                            )
                            return nested_value
                    
                    # For dot-notation paths, if first element lookup failed, log a warning
                    # but still try last element as fallback (might be a loop-specific agent)
                    if '.' in var_name:
                        self.logger.warning(
                            "Variable '{}' not found in agent '{}' first element (pre-loop agent), trying last element as fallback",
                            var_name, agent_name
                        )
                    
                    # Fallback to last element (for loop-specific agents or if first element doesn't have the field)
                    # Use the last element (most recent iteration's result)
                    parent_output = last_element
                    # Ensure we have a dict after extracting from list(s)
                    if not isinstance(parent_output, dict):
                        self.logger.warning("Upstream agent '{}' accumulated result is not a dict: {}", agent_name, type(parent_output))
                        return None
                
                # Try parsed data first (preferred - structured output)
                if isinstance(parent_output, dict) and "parsed" in parent_output:
                    parsed_data = parent_output["parsed"]
                    # If parsed_data is a string, try to parse it as JSON
                    if isinstance(parsed_data, str):
                        try:
                            parsed_data = JSONUtils.parse_json_from_text(parsed_data, expect_json=False)
                        except Exception as e:
                            self.logger.debug("Failed to parse JSON string from agent '{}': {}", agent_name, e)
                            parsed_data = None
                    
                    if isinstance(parsed_data, dict):
                        # Handle array indexing (e.g., "supplier_response_paths[supplier_loop.index]")
                        array_indexed_value = self._resolve_array_indexed_variable(parsed_data, var_name, context, agent_name)
                        if array_indexed_value is not None:
                            return array_indexed_value
                        
                        # Try direct key first (for backward compatibility)
                        if var_name in parsed_data:
                            self.logger.debug("Found variable '{}' in agent '{}' parsed data: {}", var_name, agent_name, parsed_data[var_name])
                            return parsed_data[var_name]
                        # Try nested path
                        nested_value = self._get_nested_value(parsed_data, var_name)
                        if nested_value is not None:
                            self.logger.debug("Found nested variable '{}' in agent '{}' parsed data", var_name, agent_name)
                            return nested_value
                
                # Fallback to raw data with JSON parsing
                if isinstance(parent_output, dict) and "result" in parent_output:
                    result = JSONUtils.extract_variable_from_output(parent_output["result"], var_name)
                    if result is not None:
                        self.logger.debug("Found variable '{}' in agent '{}' raw data: {}", var_name, agent_name, result)
                        return result
                
                self.logger.warning("Variable '{}' not found in upstream agent '{}'", var_name, agent_name)
                return None
                
        except Exception as e:
            self.logger.error("Error getting upstream variable {} from {}: {}", var_name, agent_name, e)
            return None
    
    def _get_variable_from_context(self, context: Dict[str, Any], var_name: str) -> Any:
        """
        Get a variable from context with fallback logic.
        First checks main context (for standalone agents), then upstream context (for pipeline agents).
        Now supports agent_id.variable_name format.
        
        Args:
            context: Execution context
            var_name: Name of the variable to extract (can be 'variable_name' or 'agent_id.variable_name')
            
        Returns:
            Variable value if found, None otherwise
        """
        try:
            # Handle prefixed variables (agent_id.variable_name or gate_id.context_key.field)
            if '.' in var_name:
                parts = var_name.split('.', 1)  # Split only on first '.'
                agent_id = parts[0]
                field_name = parts[1]
                
                # CRITICAL: Strip Jinja filters from field_name before lookup
                # Filters like "problems | default([]) | tojson" should be stripped to "problems"
                # The filters will be applied by Jinja2 when rendering the prompt
                field_name_clean = self._strip_jinja_filters(field_name)
                
                # Check if this is a multi-part path (3+ parts, e.g., gate_id.context_key.field)
                # For multi-part paths, try root context first (pipeline_runner stores gate data there)
                if '.' in field_name_clean:
                    # Multi-part path - try root context first (for HITL gate data)
                    # Example: option_selection_gate.selected_option_id.value
                    # First try the full path in root context
                    var_name_clean = f"{agent_id}.{field_name_clean}"
                    if var_name_clean in context:
                        value = context[var_name_clean]
                        # If it's a dict, try to navigate the nested path
                        if isinstance(value, dict):
                            nested_value = self._get_nested_value(value, field_name_clean)
                            if nested_value is not None:
                                return nested_value
                        return value
                    
                    # If full path not found, try to get the base object (gate_id.context_key)
                    # and then navigate to the nested field
                    base_path = f"{agent_id}.{field_name_clean.split('.')[0]}"  # e.g., option_selection_gate.selected_option_id
                    if base_path in context:
                        base_value = context[base_path]
                        # Navigate to the nested field (e.g., .value)
                        remaining_path = '.'.join(field_name_clean.split('.')[1:])  # e.g., value
                        if isinstance(base_value, dict):
                            nested_value = self._get_nested_value(base_value, remaining_path)
                            if nested_value is not None:
                                return nested_value
                        elif hasattr(base_value, remaining_path):
                            return getattr(base_value, remaining_path)
                
                # CRITICAL: Check HITL data first (for gate variables like argus_review.decision)
                # HITL data is stored in context["hitl"][gate_id] with structure:
                # {"decision": "modify_and_approve", "data": {...}, "responded_at": ...}
                hitl = context.get("hitl", {})
                if isinstance(hitl, dict) and agent_id in hitl:
                    gate_data = hitl[agent_id]
                    if isinstance(gate_data, dict):
                        # Check if field_name is directly in gate_data (e.g., "decision")
                        if field_name_clean in gate_data:
                            self.logger.debug("Found HITL variable '{}' in gate '{}'", field_name_clean, agent_id)
                            return gate_data[field_name_clean]
                        # Try nested path (e.g., "data.selection")
                        nested_value = self._get_nested_value(gate_data, field_name_clean)
                        if nested_value is not None:
                            self.logger.debug("Found nested HITL variable '{}' in gate '{}'", field_name_clean, agent_id)
                            return nested_value
                
                # CRITICAL: Check root context for loop items before checking upstream
                # Loop items (e.g., current_invoice, current_claim) are stored in root context
                # as plain dicts, not wrapped in parsed/result like agent outputs
                if agent_id in context and isinstance(context[agent_id], dict):
                    # This is likely a loop item stored in root context
                    if field_name_clean in context[agent_id]:
                        self.logger.debug("Found variable '{}' in root context loop item '{}'", field_name_clean, agent_id)
                        return context[agent_id][field_name_clean]
                    # Try nested path for loop items
                    nested_value = self._get_nested_value(context[agent_id], field_name_clean)
                    if nested_value is not None:
                        self.logger.debug("Found nested variable '{}' in root context loop item '{}'", field_name_clean, agent_id)
                        return nested_value
                
                # Try to get from specific upstream agent (using cleaned field name)
                upstream_value = self._get_upstream_variable(context, agent_id, field_name_clean)
                if upstream_value is not None:
                    return upstream_value
                
                # Fallback: try as simple variable (backward compatibility)
                # This handles cases where someone uses "context.something" format
                if var_name in context:
                    return context[var_name]
                
                return None
            
            # Original logic for simple variables (backward compatible)
            # First, check main context (for standalone agents with additional_context)
            if var_name in context:
                value = context[var_name]
                return value
            
            # Check HITL results if available (these are added by _get_base_agent_variables)
            hitl_results = context.get("hitl_results", {})
            if var_name in hitl_results:
                value = hitl_results[var_name]
                self.logger.info("Found HITL variable '{}' = '{}' (type: {})", var_name, value, type(value))
                return value
            else:
                self.logger.debug("HITL variable '{}' not found in hitl_results: {}", var_name, list(hitl_results.keys()))
            
            # Check if var_name is an agent_id in upstream context (for accessing full agent output)
            upstream_context = context.get("upstream", {})
            if var_name in upstream_context:
                agent_data = upstream_context[var_name]
                # Handle accumulated loop results (list of results from multiple iterations)
                # When accessing as a simple variable (not agent_id.field), return the whole list
                # so downstream agents can iterate over all accumulated results
                if isinstance(agent_data, list):
                    if not agent_data:
                        return None
                    # Extract parsed content from each item if it exists
                    # This ensures tools receive clean data structures without wrapper dicts
                    # Handle nested lists (from nested loops) by recursively extracting
                    def extract_parsed_recursive(item: Any) -> Any:
                        """Recursively extract parsed content from nested structures."""
                        if isinstance(item, list):
                            # Nested list - recursively extract from each element
                            return [extract_parsed_recursive(sub_item) for sub_item in item]
                        elif isinstance(item, dict):
                            # If item has "parsed" key, extract it; otherwise use the whole item
                            if "parsed" in item and isinstance(item["parsed"], dict):
                                return item["parsed"]
                            else:
                                return item
                        else:
                            # Not a dict or list, return as-is
                            return item
                    
                    extracted_list = [extract_parsed_recursive(item) for item in agent_data]
                    self.logger.info(
                        "Found agent '{}' in upstream context as accumulated list ({} items), returning extracted parsed content",
                        var_name, len(extracted_list)
                    )
                    return extracted_list
                
                # Return parsed data if available, otherwise return the whole agent_data dict
                if isinstance(agent_data, dict):
                    if "parsed" in agent_data and isinstance(agent_data["parsed"], dict):
                        self.logger.debug("Found agent '{}' in upstream context, returning parsed data", var_name)
                        return agent_data["parsed"]
                    else:
                        self.logger.debug("Found agent '{}' in upstream context, returning raw data", var_name)
                        return agent_data
            
            # Fallback to upstream context (for pipeline agents) - search for field name
            upstream_value = self._get_upstream_variable(context, 'auto', var_name)
            if upstream_value is not None:
                return upstream_value

            return None
            
        except Exception as e:
            self.logger.error("Error getting variable {} from context: {}", var_name, e)
            return None
    
    def _resolve_input_variable(self, context: Dict[str, Any], var_spec: str) -> Any:
        """
        Resolve input variable that may be:
        - Simple: 'variable_name'
        - Prefixed: 'agent_id.variable_name'
        - Expression: 'agent_id.field if condition else default'
        - Array-indexed: 'agent_id.array[index]' or 'agent_id.array[loop_context.index]'
        
        Uses existing ExpressionEvaluator class (no duplication).
        For array-indexed variables, uses custom resolver.
        
        Args:
            context: Execution context
            var_spec: Variable specification (simple name, prefixed, expression, or array-indexed)
        
        Returns:
            Resolved variable value
        """
        try:
            # Check if this is an array-indexed variable (e.g., supplier_response_paths[supplier_loop.index])
            # IMPORTANT: Only treat as array-indexed if brackets come BEFORE any filter (|) character.
            # Filter expressions like "agent_id.field | default([]) | tojson" should NOT be parsed as array-indexed.
            has_pipe = '|' in var_spec
            pipe_pos = var_spec.find('|') if has_pipe else len(var_spec)
            
            if '[' in var_spec and ']' in var_spec and '.' in var_spec:
                # Try to resolve as array-indexed variable first
                # Format: agent_id.field[index_expr]
                bracket_start = var_spec.find('[')
                bracket_end = var_spec.find(']')
                # Only treat as array-indexed if brackets come BEFORE any pipe (filter expression)
                if bracket_start < bracket_end and bracket_start < pipe_pos:
                    base_path = var_spec[:bracket_start]
                    index_expr = var_spec[bracket_start + 1:bracket_end]
                    
                    # Get the base array
                    base_value = self._get_variable_from_context(context, base_path)
                    if base_value is not None and isinstance(base_value, list):
                        # Resolve the index expression
                        index_value = None
                        if '.' in index_expr:
                            # Nested path like "supplier_loop.index"
                            index_value = self._get_nested_value(context, index_expr)
                            if index_value is None:
                                # Try accessing through variables (for loop context)
                                parts = index_expr.split('.')
                                if len(parts) == 2:
                                    obj_name, field_name = parts
                                    obj = context.get(obj_name)
                                    if isinstance(obj, dict) and field_name in obj:
                                        index_value = obj[field_name]
                                    # Also try from base variables
                                    if index_value is None:
                                        base_vars = self._get_base_agent_variables(context)
                                        if obj_name in base_vars:
                                            obj = base_vars[obj_name]
                                            if isinstance(obj, dict) and field_name in obj:
                                                index_value = obj[field_name]
                        else:
                            # Simple variable name
                            index_value = context.get(index_expr)
                            if index_value is None:
                                base_vars = self._get_base_agent_variables(context)
                                index_value = base_vars.get(index_expr)
                        
                        if index_value is not None and isinstance(index_value, int):
                            if 0 <= index_value < len(base_value):
                                self.logger.debug("Resolved array-indexed variable '{}' = {}", var_spec, base_value[index_value])
                                return base_value[index_value]
                            else:
                                self.logger.warning("Index {} out of range for array '{}' (length: {})", index_value, base_path, len(base_value))
                        else:
                            self.logger.warning("Could not resolve index expression '{}' for '{}' (got: {})", index_expr, var_spec, index_value)
            
            # Check if this is a Jinja2 filter expression (contains |)
            if '|' in var_spec:
                # Use Jinja2 template rendering for filter expressions
                from jinja2 import Template, Environment, Undefined
                env = Environment(undefined=Undefined, autoescape=False)
                # Register custom filters if needed
                from topaz_agent_kit.utils.jinja2_filters import register_jinja2_filters
                register_jinja2_filters(env)
                
                # Build render context with upstream data flattened
                render_context = dict(context)
                upstream = context.get("upstream", {})
                if isinstance(upstream, dict):
                    # Add agent namespaces: render_context[agent_id] = upstream[agent_id].parsed
                    # Track which agents were present before loops (pre-loop agents)
                    # These should use the first element for dot-notation access in templates
                    upstream_before_loop = set(context.get("_upstream_before_loop", set()))
                    
                    for agent_id, node_data in upstream.items():
                        # Handle accumulated results (lists from loops with accumulate_results=true)
                        if isinstance(node_data, list):
                            if not node_data:
                                continue
                            
                            # For pre-loop agents (agents that existed before the loop started),
                            # use the first element for dot-notation access (e.g., batch_problem_parser.problems)
                            # For loop-specific agents, keep the full list structure for iteration
                            if agent_id in upstream_before_loop:
                                # Pre-loop agent: extract first element for dot-notation access
                                first_element = node_data[0]
                                # Handle nested lists
                                while isinstance(first_element, list):
                                    if not first_element:
                                        break
                                    first_element = first_element[0]
                                
                                # Extract parsed data if available
                                if isinstance(first_element, dict):
                                    parsed = first_element.get("parsed", first_element)
                                    if isinstance(parsed, dict):
                                        render_context[agent_id] = parsed
                                        self.logger.debug(
                                            "Added pre-loop agent '{}' first element parsed data to render context (from list with {} items)",
                                            agent_id, len(node_data)
                                        )
                                    else:
                                        render_context[agent_id] = first_element
                                else:
                                    render_context[agent_id] = first_element
                            else:
                                # Loop-specific agent: keep the list structure for iteration
                                # Extract parsed content from each item (similar to _get_variable_from_context)
                                def extract_parsed_recursive(item: Any) -> Any:
                                    """Recursively extract parsed content from nested structures."""
                                    if isinstance(item, list):
                                        return [extract_parsed_recursive(sub_item) for sub_item in item]
                                    elif isinstance(item, dict):
                                        if "parsed" in item and isinstance(item["parsed"], dict):
                                            return item["parsed"]
                                        else:
                                            return item
                                    else:
                                        return item
                                
                                extracted_list = [extract_parsed_recursive(item) for item in node_data]
                                render_context[agent_id] = extracted_list
                                self.logger.debug(
                                    "Added accumulated list '{}' to render context ({} items, extracted parsed content)",
                                    agent_id, len(extracted_list)
                                )
                        elif isinstance(node_data, dict):
                            # Check if this is a pipeline step result (has 'nodes' key)
                            if "nodes" in node_data:
                                # Pipeline step result: add the full structure
                                # Templates can access: agent_id.nodes.node_id.parsed.field
                                render_context[agent_id] = node_data
                                self.logger.debug(
                                    "Added pipeline step result '{}' to render context (has nodes structure)",
                                    agent_id
                                )
                            else:
                                # Regular agent result: add parsed data for convenience (agent_id.field access)
                                parsed = node_data.get("parsed", {})
                                if isinstance(parsed, dict):
                                    render_context[agent_id] = parsed
                                    # Also flatten for convenience
                                    for k, v in parsed.items():
                                        if k not in render_context:
                                            render_context[k] = v
                
                # Add base agent variables to render context (ensures consistency with _get_variable_from_context)
                # This ensures that variables like 'reconvoy_item_discovery' are available with extracted parsed content
                base_vars = self._get_base_agent_variables(context)
                for var_name, var_value in base_vars.items():
                    # Only add if not already in render_context (upstream data takes precedence)
                    if var_name not in render_context:
                        render_context[var_name] = var_value
                
                # Add HITL gate data to render context
                hitl = context.get("hitl", {})
                for gate_id, gate_data in hitl.items():
                    render_context[gate_id] = gate_data
                
                # Wrap in {{}} if not already wrapped
                template_str = var_spec if var_spec.startswith("{{") and var_spec.endswith("}}") else f"{{{{{var_spec}}}}}"
                tmpl = env.from_string(template_str)
                result = tmpl.render(**render_context)
                # Try to convert to appropriate type
                try:
                    # Try to parse as number if it looks like one
                    if result.replace('.', '', 1).replace('-', '', 1).isdigit():
                        return float(result) if '.' in result else int(result)
                    return result
                except (ValueError, AttributeError):
                    return result
            
            # Try to evaluate as expression first (ExpressionEvaluator will raise ValueError if invalid)
            from topaz_agent_kit.utils.expression_evaluator import evaluate_expression_value
            result = evaluate_expression_value(var_spec, context)
            # Log if expression evaluated to None (might indicate a problem)
            if result is None and ('if' in var_spec and 'else' in var_spec):
                self.logger.debug(
                    "Expression '{}' evaluated to None. This might indicate that both branches of the ternary expression failed to resolve.",
                    var_spec
                )
            return result
        except ValueError:
            # Not an expression or expression evaluation failed - fall back to variable resolution
            return self._get_variable_from_context(context, var_spec)
        except Exception as e:
            self.logger.warning("Error resolving input variable '{}': {}", var_spec, e)
            # For ternary expressions, try to provide more helpful error message
            if 'if' in var_spec and 'else' in var_spec:
                self.logger.warning(
                    "Ternary expression '{}' failed to evaluate. Check that the variables in both branches are available in the context.",
                    var_spec
                )
            return None
    
    def _expand_loop_variable(self, context: Dict[str, Any], list_var_name: str, loop_var_name: str) -> Dict[str, Any]:
        """
        Expand a loop variable to show values for each iteration in the INPUTS tab.
        
        This method is called at RUNTIME (not code generation time) to dynamically expand
        loop variables based on the actual list length. The iteration count is only known
        at runtime when the upstream agent results are available.
        
        For a loop like {% for eval_result in requirements_evaluator_list %}, this method:
        1. Gets the list variable from context (e.g., "rfp_rsp_eval_requirements_evaluator")
        2. Expands it dynamically to show loop_var[0], loop_var[1], etc. for each iteration
        3. The number of iterations is determined by the actual list length at runtime
        
        For a loop like {% for instance_id, solver_data in math_repeater_solver_instances.items() %}, this method:
        1. Gets the dictionary variable from context (e.g., "math_repeater_solver_instances")
        2. Expands the VALUE variable (solver_data) to show solver_data[0], solver_data[1], etc.
        3. The values are extracted from the dictionary in order
        
        Example (list):
            If rfp_rsp_eval_requirements_evaluator = [result1, result2] at runtime,
            this returns: {"eval_result[0]": result1, "eval_result[1]": result2}
        
        Example (dictionary):
            If math_repeater_solver_instances = {"solver_0": data1, "solver_1": data2} at runtime,
            this returns: {"solver_data[0]": data1, "solver_data[1]": data2}
        
        Args:
            context: Execution context (contains upstream agent results)
            list_var_name: Name of the list/dict variable (e.g., "rfp_rsp_eval_requirements_evaluator" or "math_repeater_solver_instances")
                          This is the actual upstream agent variable, not the Jinja2 local variable
            loop_var_name: Name of the loop variable (e.g., "eval_result" or "solver_data")
            
        Returns:
            Dictionary with keys like "loop_var[0]", "loop_var[1]", etc., mapping to each iteration's value
            The number of keys depends on the actual list/dict length at runtime
        """
        try:
            # Get the list/dict variable from context at RUNTIME
            # The length is only known at runtime when upstream agents have executed
            # First try from variables dict (which includes upstream agent data)
            base_vars = self._get_base_agent_variables(context)
            list_value = base_vars.get(list_var_name)
            
            # If not found, try getting it directly from context
            if list_value is None:
                list_value = self._get_variable_from_context(context, list_var_name)
            
            # Also check context directly for _instances dictionaries (for remote agents)
            if list_value is None and list_var_name in context:
                list_value = context[list_var_name]
            
            if list_value is None:
                self.logger.warning(
                    "List/dict variable '{}' not found for loop variable '{}'. Available keys in base_vars: {}, context keys: {}",
                    list_var_name,
                    loop_var_name,
                    sorted(base_vars.keys()),
                    sorted(context.keys()) if isinstance(context, dict) else "N/A"
                )
                return {}
            
            # Handle dictionaries (for .items() patterns)
            if isinstance(list_value, dict):
                # Extract values from dictionary in order
                # For .items() patterns, we expand the VALUE variable (e.g., solver_data)
                # The values are extracted in the order they appear in the dictionary
                dict_values = list(list_value.values())
                expanded = {}
                for index, item in enumerate(dict_values):
                    key = f"{loop_var_name}[{index}]"
                    expanded[key] = item
                self.logger.debug("Expanded loop variable '{}' from dict '{}': {} iterations (runtime expansion)", loop_var_name, list_var_name, len(expanded))
                return expanded
            
            # Handle lists (for regular loops)
            # Ensure it's a list
            if not isinstance(list_value, list):
                # If it's a single item, wrap it in a list
                list_value = [list_value]
            
            # Expand dynamically based on actual list length at runtime
            # This is where the iteration count is determined - it's not known at code generation time
            expanded = {}
            for index, item in enumerate(list_value):
                key = f"{loop_var_name}[{index}]"
                expanded[key] = item
            
            self.logger.debug("Expanded loop variable '{}' from list '{}': {} iterations (runtime expansion)", loop_var_name, list_var_name, len(expanded))
            return expanded
            
        except Exception as e:
            self.logger.error("Error expanding loop variable '{}' from '{}': {}", loop_var_name, list_var_name, e)
            return {}
    
    def _validate_mcp_servers(self) -> List[Dict[str, Any]]:
        """
        Validate MCP server configurations from self.agent_config.
        Returns list of valid servers or empty list if validation fails.
        """
        try:
            mcp_config = self.agent_config.get("mcp", {})
            
            # NEW: MCP is enabled by presence of config, not enabled flag
            if not mcp_config:
                self.logger.info("No MCP configuration found, skipping MCP tools initialization")
                return []
            
            servers = mcp_config.get("servers", [])
            if not servers:
                self.logger.warning("MCP config present but no servers configured, skipping MCP tools initialization")
                return []
            
            # Validate each server configuration
            valid_servers = []
            for i, server in enumerate(servers):
                server_url = server.get("url")
                toolkits = server.get("toolkits", [])
                tools = server.get("tools", [])
                
                if not server_url:
                    self.logger.warning(f"Server {i+1} missing URL, skipping")
                    continue
                    
                if not toolkits:
                    self.logger.warning(f"Server {i+1} ({server_url}) missing toolkits, skipping")
                    continue
                    
                if not tools:
                    self.logger.warning(f"Server {i+1} ({server_url}) missing tools, skipping")
                    continue
                
                valid_servers.append(server)
                self.logger.debug(f"Server {i+1} validated: {server_url} with {len(toolkits)} toolkits, {len(tools)} tools")
            
            if not valid_servers:
                self.logger.error("No valid MCP server configurations found, skipping MCP tools initialization")
                return []
            
            return valid_servers
            
        except Exception as e:
            self.logger.error("Error validating MCP servers: {}", e)
            return []
    
    async def _initialize_mcp_tools(self, context: Dict[str, Any]) -> None:
        """Common MCP tools initialization logic"""
        try:
            valid_servers = self._validate_mcp_servers()
            if not valid_servers:
                self.tools = []
                self._original_mcp_tools = []
                return
            
            # Create MCP tools for all valid servers
            all_tools = []
            for server in valid_servers:
                server_url = server["url"]
                self.logger.info(f"Creating MCP tools for server: {server_url}")
                
                server_tools = await FrameworkMCPManager.create_framework_mcp_tools(
                    framework=self.framework_type,  # Use self.framework_type
                    mcp_url=server_url
                )
                await FrameworkMCPManager.connect_framework_mcp_tools(server_tools)
                all_tools.extend(server_tools)
            
            # Note: Agent context (agent_id/pipeline_id) is injected via LLM instructions
            # in the memory prompt section. The LLM will automatically pass these parameters
            # when calling agentos_shell, making this solution work for both local and remote agents.
            
            self.tools = all_tools
            # Store original tools before filtering for cleanup
            self._original_mcp_tools = all_tools.copy()
            self.logger.debug(f"Created {len(self.tools)} MCP tools from {len(valid_servers)} servers")
            
            # Framework-specific filtering
            await self._filter_mcp_tools()
            
            # Framework-specific tool detail logging
            await self._log_tool_details()
            
        except Exception as e:
            self.logger.error("Failed to initialize MCP tools: {}", e)
            self.tools = []
            self._original_mcp_tools = []
    
    async def _initialize_local_tools(self, context: Dict[str, Any]) -> None:
        """Load and adapt pipeline-specific local tools."""
        try:
            # Check if agent has local_tools configuration
            local_tools_config = self.agent_config.get("local_tools")
            if not local_tools_config:
                self.logger.debug("No local_tools configuration found")
                self.local_tools = []
                return
            
            # Get pipeline_id from context if available
            pipeline_id = context.get("pipeline_id")
            
            # Load tool specs
            loader = LocalToolLoader(self.project_dir, self.logger)
            tool_specs = loader.load_for_agent(self.agent_config, pipeline_id=pipeline_id)
            
            if not tool_specs:
                self.logger.debug("No local tools matched patterns")
                self.local_tools = []
                return
            
            # Adapt tools for framework
            adapter = FrameworkToolAdapter(self.framework_type, self.logger)
            adapted_tools = adapter.adapt_tools(tool_specs)
            self.local_tools = adapted_tools
            
            # For frameworks that use self.tools directly (agno, langgraph, adk, maf),
            # merge local tools into self.tools
            # For frameworks that handle tools separately (crewai, sk, oak),
            # local_tools is kept separate and merged in _create_agent()
            if self.framework_type in ["agno", "langgraph", "adk", "maf"]:
                self.tools = list(self.tools) + list(adapted_tools)
                self.logger.info(
                    "Merged {} local tools into self.tools (total: {} tools)",
                    len(adapted_tools),
                    len(self.tools)
                )
            else:
                self.logger.info(
                    "Loaded {} local tools ({} specs -> {} adapted)",
                    len(adapted_tools),
                    len(tool_specs),
                    len(adapted_tools)
                )
            
            # Log tool names (already logged by loader, but log here too for consistency)
            if tool_specs:
                tool_names = [spec.name for spec in tool_specs]
                for name in sorted(tool_names):
                    self.logger.debug("  - {}", name)
            
        except ValueError as e:
            # Configuration error - log and continue without local tools
            self.logger.warning("Invalid local_tools configuration: {}", e)
            self.local_tools = []
        except ImportError as e:
            # Module import error - log and continue without local tools
            self.logger.warning("Failed to import local tool modules: {}", e)
            self.local_tools = []
        except Exception as e:
            # Other errors - log and continue without local tools
            self.logger.error("Failed to initialize local tools: {}", e)
            self.local_tools = []
    
    def _validate_variables(self, variables: Dict[str, Any]) -> None:
        """Simple validation to catch unknown variables that require user input"""
        for key, value in variables.items():
            if value == "VARIABLE_REQUIRES_USER_INPUT":
                raise AgentError(
                    f"Variable '{key}' requires user input. "
                    "Please check the generated code for required fixes. "
                    "This variable was detected by Prompt Variables Intelligence Engine but its value source is unclear."
                )
    
    def _get_input_template(self) -> Optional[str]:
        """Get input template based on framework type"""
        if self.framework_type == "crewai":
            # CrewAI uses task.description
            if hasattr(self, 'task_description') and self.task_description:
                return self.task_description
            else:
                # Fallback: try loading from prompt spec
                task_spec = self._prompt_spec.get("task")
                if task_spec:
                    return self._prompt_loader.load_prompt(spec=task_spec.get("description"))
                return None
        else:
            # Other frameworks use prompt["inputs"]
            if isinstance(self.prompt, dict) and "inputs" in self.prompt:
                return self.prompt["inputs"]
            return None
    
    def _get_instruction_prompt(self) -> Optional[str]:
        """Get instruction prompt template based on framework type.
        
        Returns the static instruction prompt (not rendered with variables).
        For CrewAI, combines role, goal, and backstory into a single instruction.
        For other frameworks, returns the instruction section from prompt.
        
        Returns:
            Optional[str]: Instruction prompt template, or None if not available
        """
        if self.framework_type == "crewai":
            # CrewAI uses role, goal, backstory - combine them
            parts = []
            if hasattr(self, 'role') and self.role:
                # Ensure role is a string (not dict) - convert if needed
                role_str = str(self.role) if not isinstance(self.role, str) else self.role
                parts.append(f"Role: {role_str}")
            if hasattr(self, 'goal') and self.goal:
                # Ensure goal is a string (not dict) - convert if needed
                goal_str = str(self.goal) if not isinstance(self.goal, str) else self.goal
                parts.append(f"Goal: {goal_str}")
            if hasattr(self, 'backstory') and self.backstory:
                # Ensure backstory is a string (not dict) - convert if needed
                backstory_str = str(self.backstory) if not isinstance(self.backstory, str) else self.backstory
                parts.append(f"Backstory: {backstory_str}")
            
            if parts:
                instruction = "\n\n".join(parts)
                return instruction
            self.logger.warning(f"CrewAI instruction prompt is empty - no role/goal/backstory found (has role: {hasattr(self, 'role')}, has goal: {hasattr(self, 'goal')}, has backstory: {hasattr(self, 'backstory')})")
            return None
        else:
            # Other frameworks use prompt["instruction"]
            if isinstance(self.prompt, dict) and "instruction" in self.prompt:
                return self.prompt["instruction"]
            return None

    def _inject_memory_section(self) -> None:
        """Inject memory system section into agent instruction prompt."""
        if not isinstance(self.prompt, dict) or "instruction" not in self.prompt:
            self.logger.debug("Agent {} prompt not ready for memory injection", self.agent_id)
            return
        
        # Check if agent has memory config
        memory_config_dict = self.agent_config.get("memory")
        if not memory_config_dict:
            # No memory config = no injection
            self.logger.debug("Agent {} has no memory config, skipping memory injection", self.agent_id)
            return
        
        # Check if agent has agentos_shell tool
        # MCP is enabled if config exists (no need for explicit enabled flag)
        has_agentos_tool = False
        if self.mcp_config:
            self.logger.debug("Agent {} has MCP config, checking for agentos_shell tool", self.agent_id)
            servers = self.mcp_config.get("servers", [])
            for server in servers:
                tools = server.get("tools", [])
                if "agentos_shell" in tools:
                    has_agentos_tool = True
                    self.logger.debug("Agent {} has agentos_shell tool in server {}", self.agent_id, server.get("url", "unknown"))
                    break
        else:
            self.logger.debug("Agent {} has no MCP config", self.agent_id)
        
        if not has_agentos_tool:
            # Agent doesn't use agentos_shell = no memory injection
            self.logger.debug("Agent {} does not have agentos_shell tool, skipping memory injection", self.agent_id)
            return
        
        # Load memory config
        try:
            memory_loader = MemoryConfigLoader(self.project_dir)
            
            # Load pipeline config for shared memory
            pipeline_config = None
            pipeline_config_path = self.project_dir / "config" / "pipeline.yml"
            if pipeline_config_path.exists():
                import yaml
                with open(pipeline_config_path, 'r', encoding='utf-8') as f:
                    pipeline_config = yaml.safe_load(f)
            
            # Get pipeline_id from stored context (set in initialize())
            pipeline_id = getattr(self, '_pipeline_id', None)
            
            # If pipeline_id is not set, try to auto-detect it using the same logic as MCP tool
            if not pipeline_id and self.project_dir:
                pipeline_id = self._detect_pipeline_id_from_config()
                if pipeline_id:
                    self.logger.debug("Auto-detected pipeline_id '{}' for agent '{}' from config", pipeline_id, self.agent_id)
                    self._pipeline_id = pipeline_id  # Store it for future use
            
            memory_config = memory_loader.load_agent_memory_config(
                agent_config=self.agent_config,
                pipeline_config=pipeline_config,
                pipeline_id=pipeline_id,
                agent_id=self.agent_id
            )
            
            if not memory_config:
                return
            
            # Generate memory section with agent_id and pipeline_id for LLM instructions
            self.logger.debug("Generating memory section for agent {} with pipeline_id: {}", self.agent_id, pipeline_id)
            memory_section = self._generate_memory_section(memory_config, agent_id=self.agent_id, pipeline_id=pipeline_id)
            
            # Add memory section separately after the instruction
            # This keeps the memory section distinct from the main prompt
            instruction = self.prompt["instruction"]
            
            # Check if user provided custom memory section marker in the instruction
            if "{{agentos_memory_section}}" in instruction:
                # Replace marker with generated section (user explicitly requested injection point)
                self.prompt["instruction"] = instruction.replace("{{agentos_memory_section}}", memory_section)
                self.logger.info("Injected memory section at custom marker for agent {}", self.agent_id)
                # Verify replacement worked
                if "{{agentos_memory_section}}" in self.prompt["instruction"]:
                    self.logger.error("CRITICAL: Marker {{agentos_memory_section}} still present after replacement for agent {}!", self.agent_id)
            else:
                # Append memory section separately after the instruction
                # This keeps it as a distinct section that doesn't modify the original instruction
                self.prompt["instruction"] = instruction + "\n\n" + memory_section
                self.logger.info("Appended memory section separately after instruction for agent {}", self.agent_id)
        
        except Exception as e:
            self.logger.warning("Failed to inject memory section for agent {}: {}", self.agent_id, e)
    
    def _detect_pipeline_id_from_config(self) -> Optional[str]:
        """Try to determine pipeline_id by searching pipeline configs for this agent.
        
        Uses the same logic as MCP tool's auto-detection.
        """
        if not self.project_dir:
            return None
        
        try:
            import yaml
            # Load main pipeline config
            pipeline_config_path = self.project_dir / "config" / "pipeline.yml"
            if not pipeline_config_path.exists():
                return None
            
            with open(pipeline_config_path, 'r', encoding='utf-8') as f:
                main_pipeline_config = yaml.safe_load(f)
            
            if not main_pipeline_config:
                return None
            
            # Check if multi-pipeline structure (has "pipelines" key)
            if "pipelines" in main_pipeline_config:
                pipelines = main_pipeline_config.get("pipelines", [])
                for pipeline_ref in pipelines:
                    if not isinstance(pipeline_ref, dict):
                        continue
                    
                    config_file = pipeline_ref.get("config_file")
                    if not config_file:
                        continue
                    
                    # Load individual pipeline config
                    pipeline_file = self.project_dir / "config" / config_file
                    if not pipeline_file.exists():
                        continue
                    
                    try:
                        with open(pipeline_file, 'r', encoding='utf-8') as f:
                            pipeline_config = yaml.safe_load(f)
                        
                        # Check if agent is in this pipeline's nodes
                        nodes = pipeline_config.get("nodes", [])
                        for node in nodes:
                            if isinstance(node, dict):
                                config_file = node.get("config_file")
                                # Extract agent_id from config_file (e.g., "agents/reply_context_wizard.yml" -> "reply_context_wizard")
                                if config_file:
                                    agent_id_from_file = Path(config_file).stem
                                    if agent_id_from_file == self.agent_id:
                                        # Extract pipeline_id from pipeline filename
                                        pipeline_id = pipeline_file.stem
                                        self.logger.debug("Found pipeline_id '{}' for agent '{}'", pipeline_id, self.agent_id)
                                        return pipeline_id
                            elif isinstance(node, str) and node == self.agent_id:
                                # Direct agent_id match
                                pipeline_id = pipeline_file.stem
                                self.logger.debug("Found pipeline_id '{}' for agent '{}' (direct match)", pipeline_id, self.agent_id)
                                return pipeline_id
                    except Exception as e:
                        self.logger.debug("Failed to load pipeline file {}: {}", pipeline_file, e)
                        continue
            
            # Check if single-pipeline structure (has "nodes" key directly)
            elif "nodes" in main_pipeline_config:
                nodes = main_pipeline_config.get("nodes", [])
                for node in nodes:
                    if isinstance(node, dict):
                        config_file = node.get("config_file")
                        if config_file:
                            agent_id_from_file = Path(config_file).stem
                            if agent_id_from_file == self.agent_id:
                                # For single pipeline, try to get pipeline_id from config or use default
                                pipeline_id = main_pipeline_config.get("id")
                                if not pipeline_id:
                                    pipeline_id = "default"
                                self.logger.debug("Found pipeline_id '{}' for agent '{}' (single pipeline)", pipeline_id, self.agent_id)
                                return pipeline_id
                    elif isinstance(node, str) and node == self.agent_id:
                        pipeline_id = main_pipeline_config.get("id", "default")
                        self.logger.debug("Found pipeline_id '{}' for agent '{}' (single pipeline, direct match)", pipeline_id, self.agent_id)
                        return pipeline_id
            
            self.logger.debug("Could not determine pipeline_id for agent '{}'", self.agent_id)
            return None
            
        except Exception as e:
            self.logger.warning("Failed to determine pipeline_id for agent {}: {}", self.agent_id, e)
            return None

    def _generate_tool_parameters_section(self, agent_id: str, pipeline_id: Optional[str] = None) -> str:
        """Generate the tool parameters section that must be included in all agentos_shell calls.
        
        This is centralized here to avoid duplication across templates.
        """
        pipeline_param = f', pipeline_id="{pipeline_id}"' if pipeline_id else ""
        return f"""### IMPORTANT: Tool Parameters
**You MUST always include the following parameters when calling `agentos_shell`:**
- `agent_id`: "{agent_id}" (your agent identifier)
{f'- `pipeline_id`: "{pipeline_id}" (your pipeline identifier)' if pipeline_id else ''}

**Example:** `agentos_shell(command="ls /", agent_id="{agent_id}"{pipeline_param})`

"""

    def _generate_memory_section(self, memory_config, agent_id: str, pipeline_id: Optional[str] = None) -> str:
        """Generate memory section from config."""
        # Load default template or user custom template
        if memory_config.prompt_section:
            # User provided custom template
            template_content = self._prompt_loader.load_prompt(memory_config.prompt_section)
        else:
            # Use default template
            default_template_path = Path(__file__).parent.parent.parent / "core" / "agentos" / "prompt_template.jinja"
            if default_template_path.exists():
                template_content = default_template_path.read_text(encoding="utf-8")
            else:
                self.logger.warning("Default memory prompt template not found: {}", default_template_path)
                return ""
        
        # Generate schema documentation
        from topaz_agent_kit.core.agentos.schema_instructions import SchemaInstructionGenerator
        schema_generator = SchemaInstructionGenerator()
        
        schema_docs = []
        for dir_config in memory_config.directories:
            if dir_config.schemas:
                schema_docs.append(schema_generator.format_schema_documentation(dir_config))
        for dir_config in (memory_config.shared_directories or []):
            if dir_config.schemas:
                schema_docs.append(schema_generator.format_schema_documentation(dir_config))
        
        # Prepare variables for rendering
        memory_vars = {
            "memory": {
                "directories": [
                    {
                        "path": dir.path,
                        "description": dir.description,
                        "readonly": dir.readonly
                    }
                    for dir in memory_config.directories
                ],
                "shared_directories": [
                    {
                        "path": dir.path,
                        "description": dir.description,
                        "readonly": dir.readonly
                    }
                    for dir in (memory_config.shared_directories or [])
                ],
                "schema_documentation": "\n".join(schema_docs) if schema_docs else None
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id
        }
        
        # Render template
        rendered_content = self._prompt_loader.render_prompt(template_content, variables=memory_vars)
        
        # Prepend tool parameters section if not already present
        # This ensures all templates get the required tool parameters section automatically
        tool_params_section = self._generate_tool_parameters_section(agent_id, pipeline_id)
        if "### IMPORTANT: Tool Parameters" not in rendered_content:
            return tool_params_section + rendered_content
        
        return rendered_content

    def _render_prompt_with_variables(self, prompt_template: str, variables: Dict[str, Any]) -> str:
        """Render prompt template with variables using the PromptLoader class"""
        try:
            # CRITICAL FIX: Scan template for expressions that reference agents
            # This ensures that when Jinja2 evaluates expressions like
            # "{{aegis_translator.translated_data.invoice_data if aegis_translator else ...}}"
            # all referenced agents exist in the variables dict (even if None)
            # This is especially important for conditional nodes that may be skipped
            import re
            # Find all Jinja2 expressions in the template: {{ ... }}
            jinja_expr_pattern = r'\{\{([^}]+)\}\}'
            expressions = re.findall(jinja_expr_pattern, prompt_template)
            
            for expr in expressions:
                # Check if expression contains ternary operator (if/else)
                if ' if ' in expr and ' else ' in expr:
                    # Extract agent names from the expression
                    # Match patterns like "agent_id.field" where agent_id is an identifier
                    agent_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z0-9_.]+)'
                    matches = re.findall(agent_pattern, expr)
                    for agent_id, _ in matches:
                        # If agent is not in variables, add it as None
                        # This allows ternary expressions to evaluate correctly
                        # when the agent was skipped (e.g., conditional step)
                        if agent_id not in variables:
                            variables[agent_id] = None
                            self.logger.debug(
                                "Added missing agent '{}' as None to variables for template expression evaluation",
                                agent_id
                            )
            
            # Use the PromptLoader class for rendering
            rendered = self._prompt_loader.render_prompt(prompt_template, variables=variables)
            
            # Store rendered inputs for UI display
            self._captured_rendered_inputs = rendered
            
            return rendered
        except Exception as e:
            self.logger.error("Failed to render prompt template: {}", e)
            raise AgentError(f"Failed to render prompt template: {e}")
    
    def _should_process_files(self, prompt_key: str = "inputs") -> bool:
        """
        Check if the agent's prompt template uses the user_files variable.
        This helps avoid unnecessary file processing when agents don't need files.
        
        Args:
            prompt_key: The key in self.prompt to check (default: "inputs", but CrewAI uses "task")
            
        Returns:
            bool: True if the prompt uses {{user_files}}, False otherwise
        """
        # Handle CrewAI agents: they don't use self.prompt, check task_description instead
        if self.agent_type == "crewai":
            if hasattr(self, "task_description") and isinstance(self.task_description, str):
                prompt_template = self.task_description
            else:
                # No task description available, skip file processing
                return False
        # Handle case where self.prompt is a string (shouldn't happen normally, but defensive)
        elif isinstance(self.prompt, str):
            prompt_template = self.prompt
        # Handle case where self.prompt is a dict (normal case)
        elif isinstance(self.prompt, dict):
            prompt_section = self.prompt.get(prompt_key, {})
            if isinstance(prompt_section, dict):
                prompt_template = prompt_section.get("inline", "") or prompt_section.get("file", "") or prompt_section.get("jinja", "")
            elif isinstance(prompt_section, str):
                prompt_template = prompt_section
            else:
                prompt_template = ""
        else:
            # self.prompt is None or unexpected type, skip file processing
            return False
        
        # Check for both {{user_files}} and {{ user_files }} (with/without spaces)
        uses_user_files = "{{user_files}}" in prompt_template or "{{ user_files }}" in prompt_template
        
        return uses_user_files
    
    
    async def cleanup(self) -> None:
        """cleanup method - cleanup resources and close connections"""
        try:
            self.agent = None
            # Always cleanup original tools (before filtering) to ensure all created tools are cleaned up
            tools_to_cleanup = getattr(self, '_original_mcp_tools', None) or getattr(self, 'tools', []) or []
            await FrameworkMCPManager.cleanup_framework_mcp_tools(tools_to_cleanup)
            self.logger.success("Cleaned up MCP tools")
        except Exception as e:
            self.logger.warning("Cleanup failed: {}", e)
    
    
    def _initialize_llm(self, context: Dict[str, Any]) -> None:
        """
        Initialize LLM using unified framework-aware factory.
        Reads model configuration from pipeline.yml via agent_config.
        """
        try:
            # Get model type from agent_config (pipeline.yml)
            model_type = self.agent_config.get("model")
            if not model_type:
                self.logger.error(f"Agent {self.agent_id} missing 'model' configuration in pipeline.yml")
                raise AgentError(f"Agent {self.agent_id} missing 'model' configuration in pipeline.yml")
            
            # Get configuration from unified config manager
            config_manager = FrameworkConfigManager()
            model_config = config_manager.get_model_config(
                model_type=model_type,
                framework=self.framework_type  # agno, langgraph, crewai, adk, sk, oak
            )
            
            # Create model using framework-aware factory
            self.llm = FrameworkModelFactory.get_model(
                model_type=model_type,
                framework=self.framework_type,
                **model_config
            )
            
            self.logger.success("Initialized {} {} model using unified factory", 
                            self.framework_type.title(), model_type)
            
        except Exception as e:
            self.logger.error("Failed to initialize LLM: {}", e)
            raise
    
    
    def _get_base_agent_variables(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get base variables for all agents.
        Only provides truly system-level variables that are framework-provided.
        All user input and upstream variables should be handled by generated classes.
        
        Args:
            context: Execution context
            
        Returns:
            Dictionary of variable names to values
        """
        variables = {
            # Only system-level variables that are always available
            "context": context,
            "pipeline_data": context.get("pipeline_data", {}),
        }
        
        # Add project_dir if available in context (for path resolution in prompts)
        if "project_dir" in context:
            project_dir = context["project_dir"]
            # Convert Path to string for Jinja rendering
            variables["project_dir"] = str(project_dir) if project_dir else None
        
        # Add pipeline data variables
        pipeline_data = context.get("pipeline_data", {})
        for agent_id, output in pipeline_data.items():
            variables[f"{agent_id}_output"] = output
        
        # Add common context variables that are frequently used in templates
        # Only add if not already present (to avoid overwriting values from generated agents)
        if "user_text" in context and "user_text" not in variables:
            variables["user_text"] = context["user_text"]
        
        # Add upstream agent data to variables dict so Jinja2 can evaluate expressions.
        #
        # IMPORTANT BEHAVIOR:
        # - For single-run agents, upstream[agent_id] is a dict with optional "parsed" field.
        #   We expose variables[agent_id] = parsed_dict (or the raw dict if no parsed).
        # - For loop / accumulated agents, upstream[agent_id] is a list of per-iteration results,
        #   where each element is typically a dict like {"result": ..., "parsed": {...}, ...}.
        #   For Jinja2 templates (especially comparison / aggregation agents), it is far more
        #   convenient to iterate over a list of parsed dicts. So here we flatten the list to:
        #       variables[agent_id] = [parsed_dict1, parsed_dict2, ...]
        #   falling back to the raw item when no "parsed" field exists.
        #
        # NOTE:
        # - We DO NOT modify context["upstream"] itself. All pattern runners and helper logic
        #   continue to see the original upstream structure with {"result", "parsed"} wrappers.
        #   This keeps backward compatibility for any code that inspects upstream directly.
        upstream = context.get("upstream", {})
        for agent_id, agent_data in upstream.items():
            # Handle arrays (from loop accumulated results)
            if isinstance(agent_data, list):
                # Only add if not already present (to avoid overwriting)
                if agent_id in variables:
                    continue

                # Extract parsed content recursively to handle nested lists (from nested loops)
                def extract_parsed_recursive(item: Any) -> Any:
                    """Recursively extract parsed content from nested structures."""
                    if isinstance(item, list):
                        # Nested list - recursively extract from each element
                        return [extract_parsed_recursive(sub_item) for sub_item in item]
                    elif isinstance(item, dict):
                        # If item has "parsed" key, extract it; otherwise use the whole item
                        if "parsed" in item and isinstance(item["parsed"], dict):
                            return item["parsed"]
                        else:
                            return item
                    else:
                        # Not a dict or list, return as-is
                        return item
                
                flattened_list = [extract_parsed_recursive(item) for item in agent_data]
                variables[agent_id] = flattened_list

            elif isinstance(agent_data, dict):
                # Prefer parsed data if available
                if "parsed" in agent_data and isinstance(agent_data["parsed"], dict):
                    # Only add if not already present (to avoid overwriting)
                    if agent_id not in variables:
                        variables[agent_id] = agent_data["parsed"]
                # Fallback to direct agent data
                elif agent_id not in variables:
                    variables[agent_id] = agent_data
            else:
                # Unexpected type - log warning but don't add to variables
                self.logger.warning(
                    "Unexpected upstream agent data type for '{}': {} (expected dict or list)",
                    agent_id,
                    type(agent_data),
                )
        
        # CRITICAL: Check top-level context for agent ID aliases (added by SequentialRunner for enhanced repeat patterns)
        # These aliases allow subsequent agents in a sequential pattern to access instance-specific results
        # using the base agent ID (e.g., "enhanced_math_repeater_file_reader") even though results are stored
        # under instance IDs (e.g., "enhanced_math_repeater_file_reader_0") in upstream
        # We only add aliases that look like agent IDs (contain underscores) and are dicts (parsed outputs)
        for key in context.keys():
            if key in variables:
                continue  # Already added from upstream, skip
            # Check if this looks like an agent ID alias (contains underscores, is a dict, not a system variable)
            if "_" in key and isinstance(context[key], dict) and key not in {"context", "pipeline_data", "project_dir"}:
                # Check if this key is not in upstream (meaning it's an alias, not a direct upstream entry)
                if key not in upstream:
                    # This is likely an agent ID alias - add it to variables
                    variables[key] = context[key]
                    self.logger.debug(
                        "Added agent ID alias '{}' from top-level context to variables (for enhanced repeat pattern)",
                        key
                    )
        
        # Add repeat pattern instances dictionaries (e.g., math_repeater_solver_instances)
        # These are created by RepeatPatternRunner and stored in context for downstream agents
        # Pattern: {base_agent_id}_instances = {instance_id: instance_data, ...}
        for key in context.keys():
            if key in variables:
                continue  # Already added, skip
            value = context[key]
            # Check for _instances dictionaries (created by RepeatPatternRunner)
            if key.endswith("_instances") and isinstance(value, dict):
                variables[key] = value
                self.logger.debug("Added repeat pattern instances dictionary to variables: {} ({} keys)", key, len(value))
        
        # Add loop context variables (e.g., supplier_loop, loop_iteration) to variables dict
        # These are injected by LoopRunner and RepeatPatternRunner for iteration-specific access
        # Loop context can be:
        # 1. A dict with 'index' and/or 'iteration' keys (e.g., supplier_loop = {index: 0, iteration: 1})
        # 2. Individual variables ending with _index or _iteration (e.g., supplier_loop_index, supplier_loop_iteration)
        # 3. Known loop context keys (loop_iteration, repeat_instance, etc.)
        for key in context.keys():
            if key in variables:
                continue  # Already added, skip
            value = context[key]
            # Check for loop context dict (most common case)
            if isinstance(value, dict) and ("index" in value or "iteration" in value):
                variables[key] = value
            # Check for individual index/iteration variables
            elif key.endswith("_index") or key.endswith("_iteration"):
                variables[key] = value
            # Check for known loop context keys
            elif key in ["loop_iteration", "repeat_instance"]:
                variables[key] = value
        
        # Add instance-specific variables from context (for repeat pattern instances)
        # This ensures variables from input_mapping are available for both local and remote agents
        # Called here so it works even if generated code hasn't been regenerated
        self._add_instance_context_variables(variables, context)
        
        # Add HITL gate data in nested structure for Jinja2 access (e.g., option_selection_gate.selected_option_id.value)
        # Pipeline runner stores gate data at root context as gate_id.context_key (e.g., option_selection_gate.selected_option_id)
        # We need to structure it as nested dicts so Jinja2 can access nested attributes
        hitl = context.get("hitl", {})
        if isinstance(hitl, dict):
            for gate_id, gate_data in hitl.items():
                if isinstance(gate_data, dict):
                    data = gate_data.get("data", {})
                    context_key = gate_data.get("context_key")
                    decision = gate_data.get("decision")  # Get decision field from top level
                    
                    # Create nested structure: variables[gate_id][context_key] = data
                    if gate_id not in variables:
                        variables[gate_id] = {}
                    
                    # Always include decision at top level of gate_id for direct access (e.g., argus_review.decision)
                    if decision is not None:
                        variables[gate_id]["decision"] = decision
                    
                    if context_key:
                        # Store data at nested path
                        variables[gate_id][context_key] = data
                        self.logger.debug(
                            "Added HITL gate data to variables: {}.{} = {} (type: {})",
                            gate_id,
                            context_key,
                            data,
                            type(data)
                        )
                    else:
                        # No context_key - store data directly under gate_id
                        if isinstance(data, dict):
                            variables[gate_id].update(data)
                        else:
                            variables[gate_id] = data
        
        # Also check root context for gate_id.context_key format (from pipeline_runner)
        # This handles cases where pipeline_runner stores data directly at root context
        for key in context.keys():
            if "." in key and key not in variables:
                parts = key.split(".", 1)
                gate_id = parts[0]
                context_key = parts[1]
                
                # Check if this looks like a gate ID (common pattern: ends with _gate or matches known gate IDs)
                # Only process if gate_id is not already in variables as a dict (to avoid overwriting)
                if gate_id not in variables or not isinstance(variables[gate_id], dict):
                    value = context[key]
                    if gate_id not in variables:
                        variables[gate_id] = {}
                    variables[gate_id][context_key] = value
                    self.logger.debug(
                        "Added gate data from root context to variables: {}.{} = {} (type: {})",
                        gate_id,
                        context_key,
                        value,
                        type(value)
                    )
        
        # Also check root context for gate_id.context_key format (from pipeline_runner)
        # This handles cases where pipeline_runner stores data directly at root context
        # We need to create nested structure for Jinja2 access (e.g., option_selection_gate.selected_option_id.value)
        for key in context.keys():
            if "." in key and key not in variables:
                parts = key.split(".", 1)
                gate_id = parts[0]
                remaining_path = parts[1]
                
                # Check if this looks like a gate ID (common pattern: ends with _gate)
                # Only process if gate_id is not already in variables as a dict (to avoid overwriting)
                if gate_id.endswith("_gate") or gate_id in hitl:
                    value = context[key]
                    if gate_id not in variables:
                        variables[gate_id] = {}
                    
                    # Create nested structure for the remaining path
                    # e.g., "selected_option_id.value" -> variables[gate_id]["selected_option_id"]["value"]
                    path_parts = remaining_path.split(".")
                    current = variables[gate_id]
                    for i, part in enumerate(path_parts[:-1]):
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    # Set the final value
                    current[path_parts[-1]] = value
                    self.logger.debug(
                        "Added gate data from root context to nested variables: {}.{} = {} (type: {})",
                        gate_id,
                        remaining_path,
                        value,
                        type(value)
                    )
        
        # Also add HITL results (from agent_runner._inject_hitl_variables) for backward compatibility
        hitl_results = context.get("hitl_results", {})
        if isinstance(hitl_results, dict):
            for key, value in hitl_results.items():
                # Only add if not already in variables (to avoid overwriting nested structure)
                if key not in variables:
                    variables[key] = value
        
        # Unwrap content wrapping from all variables before returning
        return self._unwrap_content_from_variables(variables)
    
    def _add_instance_context_variables(self, variables: Dict[str, Any], context: Dict[str, Any]) -> None:
        """
        Add instance-specific variables from context to variables dict.
        
        This method is called from generated get_agent_variables() methods to ensure
        instance-specific variables from input_mapping (injected by InstanceContextWrapper)
        are available for both local and remote agents.
        
        Examples of instance-specific variables:
        - problem_text, problem_index (from repeat pattern input_mapping)
        - supplier, supplier_id (from loop pattern input_mapping)
        
        Args:
            variables: Variables dict to add instance variables to (modified in place)
            context: Execution context containing instance-specific variables
        """
        # Skip system/internal variables (starting with _) and already-added variables
        system_vars = {"context", "pipeline_data", "project_dir", "emitter", "mcp_client", "user_text", "index"}
        upstream_agents = set(context.get("upstream", {}).keys())
        
        for key in context.keys():
            if key in variables:
                continue  # Already added, skip
            if key in system_vars:
                continue  # Skip system variables
            if key.startswith("_"):
                continue  # Skip internal variables (e.g., _base_agent_id, _instance_id_template)
            if key in upstream_agents:
                continue  # Skip upstream agent dicts (they're added separately)
            # Add any other variables from context that look like user variables
            # This ensures instance-specific variables from input_mapping are available
            value = context[key]
            # Only add simple types (str, int, float, bool, dict, list) - skip complex objects
            if isinstance(value, (str, int, float, bool, dict, list, type(None))):
                variables[key] = value
                self.logger.debug("Added instance-specific variable to variables: {} = {}", key, type(value).__name__)
    
    def _unwrap_content_from_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively unwrap content wrapping ({"content": ...}) from all variables.
        This ensures variables are clean before being used in Jinja2 templates.
        
        Args:
            variables: Dictionary of variable names to values
            
        Returns:
            Dictionary with content wrapping removed from all values
        """
        def unwrap_value(value: Any) -> Any:
            """Recursively unwrap content wrapping from a value."""
            if isinstance(value, dict):
                # Check if this is a content wrapper (only has "content" key)
                if len(value) == 1 and "content" in value:
                    content_value = value["content"]
                    # Recursively unwrap nested content wrappers
                    return unwrap_value(content_value)
                # Not a content wrapper, recursively unwrap all values in the dict
                return {k: unwrap_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                # Recursively unwrap all items in the list
                return [unwrap_value(item) for item in value]
            else:
                # Not a dict or list, return as-is
                return value
        
        # Unwrap all variables
        unwrapped_variables = {}
        for key, value in variables.items():
            # Skip system variables that shouldn't be unwrapped
            if key in ["context", "pipeline_data"]:
                unwrapped_variables[key] = value
            else:
                unwrapped_value = unwrap_value(value)
                # Only update if value changed (to avoid unnecessary logging)
                if unwrapped_value != value:
                    self.logger.debug("Unwrapped content from variable '{}'", key)
                unwrapped_variables[key] = unwrapped_value
        
        return unwrapped_variables
    
    def _restructure_dot_notation_variables(self, variables: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Restructure variables with dot-notation keys into nested objects for Jinja2 rendering.
        
        Converts:
          {"sot_schema_linker.schema_info": {...}, "sot_schema_linker.database_path": "..."}
        Into:
          {"sot_schema_linker": {"schema_info": {...}, "database_path": "..."}}
        
        Also handles cases where agent_id is already in variables as a list (from outer loops):
          {"sot_schema_linker": [dict1, dict2, ...]} -> {"sot_schema_linker": dict2} (last element)
        
        This allows Jinja2 templates to use {{sot_schema_linker.schema_info}} syntax.
        
        Args:
            variables: Dictionary with potentially dot-notation keys or list values
            
        Returns:
            Dictionary with nested structures for dot-notation variables
        """
        restructured = {}
        dot_notation_vars = {}
        
        # First, handle agents that are already in variables as lists (from outer loops)
        # Extract the last element so Jinja2 can access .field on them
        # BUT: Only extract if this is an agent ID that exists in upstream context as a list
        # Regular list variables (like hitl_queued_cases, completed_cases) should be kept as lists
        # Dot-notation variables (like batch_problem_parser.problems) are handled separately below
        upstream_agents = set(context.get("upstream", {}).keys())
        self.logger.debug(
            "Restructuring variables: checking {} list variables against {} upstream agents: {}",
            sum(1 for v in variables.values() if isinstance(v, list) and v and not isinstance(v, str)),
            len(upstream_agents),
            sorted(upstream_agents)
        )
        for key, value in variables.items():
            if isinstance(value, list) and value and not key.startswith('_'):
                # Only extract if this key is an agent ID in upstream context
                # This means it's an accumulated agent result from a loop
                # Regular list variables (not agent IDs) should be kept as lists
                if key in upstream_agents:
                    # IMPORTANT: Check if we have dot-notation variables for this agent (e.g., batch_problem_parser.problems)
                    # If we do, we should NOT extract the last element, because the dot-notation variables
                    # already have the correct values (resolved from first element for pre-loop agents).
                    # Instead, we'll let the dot-notation restructuring below create the nested structure.
                    has_dot_notation = any(k.startswith(f"{key}.") for k in variables.keys() if '.' in k)
                    
                    if has_dot_notation:
                        # We have dot-notation variables for this agent - skip extraction
                        # The dot-notation restructuring will create the nested structure correctly
                        self.logger.debug(
                            "Variable '{}' is in upstream agents (list with {} items) but has dot-notation variables - "
                            "skipping extraction, will use dot-notation values instead",
                            key, len(value)
                        )
                        # DON'T add to restructured - let the dot-notation restructuring create the nested structure
                        # If we add it here as a list, it will prevent the nested dict from being added later
                        # (the merge logic at line 1714 checks if it's a dict before merging)
                        # We'll add it to a set to track which keys were skipped
                        if not hasattr(self, '_skipped_for_dot_notation'):
                            self._skipped_for_dot_notation = set()
                        self._skipped_for_dot_notation.add(key)
                    else:
                        # This is an accumulated agent result - extract last element
                        self.logger.debug(
                            "Variable '{}' is in upstream agents (list with {} items) - extracting last element for Jinja2 .field access",
                            key, len(value)
                        )
                        last_item = value[-1]
                        # Handle nested lists (list of lists)
                        while isinstance(last_item, list):
                            if not last_item:
                                break
                            last_item = last_item[-1]
                        # Only replace if we got a dict (not a list)
                        if isinstance(last_item, dict):
                            restructured[key] = last_item
                            self.logger.debug("Extracted last element from accumulated agent result '{}' for Jinja2 access", key)
                        else:
                            # Keep as list if we can't extract a dict
                            restructured[key] = value
                            self.logger.debug("Kept '{}' as list (last element is not a dict: {})", key, type(last_item).__name__)
                else:
                    # This is a regular list variable (like hitl_queued_cases, completed_cases)
                    # Keep it as a list so templates can iterate over it or use filters
                    restructured[key] = value
                    self.logger.debug(
                        "Keeping list variable '{}' as-is ({} items) - not an accumulated agent result (not in upstream)",
                        key, len(value)
                    )
            elif '.' in key and not key.startswith('_'):
                # Check if this is an expression (contains 'if' and 'else') - these should be kept as-is
                # Expressions like "aegis_translator.translated_data.invoice_data if aegis_translator.translated_data else aegis_invoice_extractor.extracted_data.invoice_data"
                # are already evaluated and should be preserved as a single value, not restructured
                if ' if ' in key and ' else ' in key:
                    # This is an expression variable - keep it as-is in restructured
                    restructured[key] = value
                    self.logger.debug(
                        "Preserving expression variable '{}' as-is (not restructuring dot-notation)",
                        key
                    )
                else:
                    # This is a dot-notation variable (e.g., "sot_schema_linker.schema_info")
                    # These are handled separately below to create nested structures
                    if isinstance(value, list):
                        self.logger.debug(
                            "Dot-notation variable '{}' is a list ({} items) - will be preserved in nested structure",
                            key, len(value)
                        )
                    dot_notation_vars[key] = value
            else:
                # Regular variable, keep as-is
                restructured[key] = value
        
        # Group dot-notation variables by their base name
        # e.g., "sot_schema_linker.schema_info" and "sot_schema_linker.database_path" -> "sot_schema_linker"
        nested_objects = {}
        for dot_key, dot_value in dot_notation_vars.items():
            parts = dot_key.split('.', 1)  # Split only on first '.'
            base_name = parts[0]
            field_name = parts[1]
            
            # Create nested structure if it doesn't exist
            if base_name not in nested_objects:
                nested_objects[base_name] = {}
            
            # Handle nested paths (e.g., "current_question.question")
            if '.' in field_name:
                # Recursively build nested structure
                field_parts = field_name.split('.')
                current = nested_objects[base_name]
                for part in field_parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[field_parts[-1]] = dot_value
            else:
                # Simple field
                nested_objects[base_name][field_name] = dot_value
        
        # Add nested objects to restructured variables
        # CRITICAL: Keep BOTH the original dot-notation keys AND the nested structure
        # This ensures:
        # 1. Jinja2 can use {{sot_schema_linker.schema_info}} (nested structure)
        # 2. Inputs tab filtering can find "sot_schema_linker.schema_info" (original key)
        for base_name, nested_dict in nested_objects.items():
            # Add nested structure for Jinja2 rendering
            if base_name not in restructured:
                restructured[base_name] = nested_dict
                self.logger.debug(
                    "Created nested structure for '{}' from dot-notation variables: keys={}",
                    base_name, list(nested_dict.keys()) if isinstance(nested_dict, dict) else 'not a dict'
                )
            else:
                # Base name already exists
                # If it was skipped for dot-notation (was a list), replace it with the nested dict
                if hasattr(self, '_skipped_for_dot_notation') and base_name in getattr(self, '_skipped_for_dot_notation', set()):
                    # This was skipped earlier because it has dot-notation variables
                    # Replace the list with the nested dict structure
                    restructured[base_name] = nested_dict
                    self.logger.debug(
                        "Replaced skipped list '{}' with nested dict structure from dot-notation variables",
                        base_name
                    )
                elif isinstance(restructured[base_name], dict) and isinstance(nested_dict, dict):
                    # Both are dicts - merge them
                    restructured[base_name].update(nested_dict)
                    self.logger.debug(
                        "Merged nested dict structure for '{}' with existing dict",
                        base_name
                    )
                # If not a dict and not skipped, keep the original value (don't overwrite)
        
        # CRITICAL FIX: Ensure base agents with dot-notation variables are in restructured
        # This handles two cases:
        # 1. Dot-notation variables in dot_notation_vars (already handled above via nested_objects)
        # 2. Dot-notation variables that were already resolved (like batch_problem_parser.problems)
        #    and are in variables but NOT in dot_notation_vars
        # 3. Expression variables that reference base agents (e.g., "aegis_translator.translated_data.invoice_data if ...")
        #    IMPORTANT: For ternary expressions in Jinja2 templates, we need ALL referenced agents to exist,
        #    even if they're None (for skipped conditional steps), so Jinja2 can evaluate the condition
        import re
        for key, value in variables.items():
            # Check if this is an expression variable that references base agents
            if ' if ' in key and ' else ' in key:
                # Extract base agent names from the expression
                # Look for patterns like "agent_id.field" in the expression
                # Match agent_id.field patterns (agent_id is alphanumeric + underscore, field can have dots)
                agent_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z0-9_.]+)'
                matches = re.findall(agent_pattern, key)
                for agent_id, _ in matches:
                    # Skip if already in restructured
                    if agent_id in restructured:
                        continue
                    
                    # If agent exists in upstream, add it with its data
                    if agent_id in upstream_agents:
                        # Get the base agent from upstream
                        base_agent_value = context.get("upstream", {}).get(agent_id)
                        if isinstance(base_agent_value, list) and base_agent_value:
                            # For pre-loop agents (lists), use first element's parsed data
                            first_element = base_agent_value[0]
                            while isinstance(first_element, list):
                                if not first_element:
                                    break
                                first_element = first_element[0]
                            if isinstance(first_element, dict):
                                parsed = first_element.get("parsed", first_element)
                                if isinstance(parsed, dict):
                                    restructured[agent_id] = parsed
                                    self.logger.debug(
                                        "Added base agent '{}' to restructured from upstream (first element parsed) for expression variable access",
                                        agent_id
                                    )
                        elif isinstance(base_agent_value, dict):
                            # Regular agent result
                            parsed = base_agent_value.get("parsed", base_agent_value)
                            if isinstance(parsed, dict):
                                restructured[agent_id] = parsed
                                self.logger.debug(
                                    "Added base agent '{}' to restructured from upstream (parsed) for expression variable access",
                                    agent_id
                                )
                    else:
                        # Agent doesn't exist in upstream (e.g., skipped conditional step)
                        # Add it as None so Jinja2 can evaluate the ternary expression
                        # This allows expressions like "aegis_translator.translated_data if aegis_translator.translated_data else ..."
                        # to work correctly when aegis_translator was skipped
                        restructured[agent_id] = None
                        self.logger.debug(
                            "Added missing base agent '{}' as None to restructured for ternary expression evaluation (agent was skipped or doesn't exist)",
                            agent_id
                        )
            
            if '.' in key and not key.startswith('_'):
                # Skip expression variables (already handled above)
                if ' if ' in key and ' else ' in key:
                    continue
                    
                parts = key.split('.', 1)
                base_name = parts[0]
                field_name = parts[1]
                
                # Only process if base_name is an upstream agent
                if base_name in upstream_agents:
                    # If base_name is not in restructured yet, add it
                    if base_name not in restructured:
                        # Get the base agent from upstream
                        base_agent_value = context.get("upstream", {}).get(base_name)
                        if isinstance(base_agent_value, list) and base_agent_value:
                            # For pre-loop agents (lists), use first element's parsed data
                            first_element = base_agent_value[0]
                            while isinstance(first_element, list):
                                if not first_element:
                                    break
                                first_element = first_element[0]
                            if isinstance(first_element, dict):
                                parsed = first_element.get("parsed", first_element)
                                if isinstance(parsed, dict):
                                    restructured[base_name] = parsed
                                    self.logger.debug(
                                        "Added base agent '{}' to restructured from upstream (first element parsed) for dot-notation access",
                                        base_name
                                    )
                        elif isinstance(base_agent_value, dict):
                            # Regular agent result
                            parsed = base_agent_value.get("parsed", base_agent_value)
                            if isinstance(parsed, dict):
                                restructured[base_name] = parsed
                                self.logger.debug(
                                    "Added base agent '{}' to restructured from upstream (parsed) for dot-notation access",
                                    base_name
                                )
                    # If base_name is in restructured but the nested structure doesn't have the field,
                    # ensure the field is added (merge with nested structure if it exists)
                    elif base_name in restructured and isinstance(restructured[base_name], dict):
                        # Check if field exists in nested structure
                        if field_name not in restructured[base_name]:
                            # Field doesn't exist, add it from the resolved value
                            restructured[base_name][field_name] = value
                            self.logger.debug(
                                "Added field '{}' to existing nested structure for '{}'",
                                field_name, base_name
                            )
        
        # CRITICAL: Also keep ALL original dot-notation keys for inputs tab filtering
        # The inputs tab uses _inputs_section_variables which contains keys like "sot_schema_linker.schema_info"
        # We need to preserve these original keys so the filtering logic can find them
        for dot_key, dot_value in dot_notation_vars.items():
            # Keep the original dot-notation key so inputs tab can find it
            # This doesn't conflict with the nested structure - Jinja2 will prefer the nested structure
            if isinstance(dot_value, list):
                self.logger.debug(
                    "Preserving dot-notation variable '{}' as full list ({} items) for inputs tab and Jinja2 rendering",
                    dot_key, len(dot_value)
                )
            restructured[dot_key] = dot_value
        
        return restructured
    
    def _filter_variables_for_inputs_tab(
        self, 
        variables: Dict[str, Any], 
        context: Dict[str, Any],
        log_prefix: str = "INPUTS FILTER"
    ) -> Dict[str, Any]:
        """
        Filter variables to only show those explicitly detected from YAML configuration.
        
        This ensures the INPUTS tab only displays variables that the user explicitly
        put in their YAML file, not system variables or upstream agent dicts.
        
        Special handling for instance-specific variables from repeat pattern input_mapping:
        - These are added via _add_instance_context_variables() and are not in _inputs_section_variables
        - They should still be shown in INPUTS tab for remote agents
        
        Args:
            variables: Full variables dict from get_agent_variables()
            context: Execution context
            log_prefix: Prefix for log messages (e.g., "INPUTS FILTER" or "INPUTS FILTER REMOTE")
            
        Returns:
            Filtered variables dict containing only YAML-explicit variables
        """
        system_vars = {"context", "pipeline_data", "project_dir"}
        upstream_agents = set(context.get("upstream", {}).keys())
        
        # Get base variables to identify what was added by generated code vs base
        base_variables = self._get_base_agent_variables(context)
        
        # Log for debugging INPUTS tab filtering
        self.logger.debug(f"[{log_prefix}] All variables keys: {sorted(variables.keys())}")
        self.logger.debug(f"[{log_prefix}] Base variables keys: {sorted(base_variables.keys())}")
        self.logger.debug(f"[{log_prefix}] Upstream agents: {sorted(upstream_agents)}")
        self.logger.debug(f"[{log_prefix}] System vars to exclude: {system_vars}")
        
        # Use _inputs_section_variables if available (set by generated agent code)
        # This is the most precise way to filter - only show variables explicitly in inputs section
        if hasattr(self, '_inputs_section_variables') and self._inputs_section_variables:
            self.logger.debug(f"[{log_prefix}] Using _inputs_section_variables for filtering: {sorted(self._inputs_section_variables)}")
            # Trust the generated code - only show variables explicitly in inputs section
            # Also include instance-specific vars (from repeat pattern input_mapping)
            # These are variables in variables dict but not in base_variables (added by _add_instance_context_variables)
            instance_specific_vars = {
                k for k in variables.keys()
                if k not in base_variables
                and k not in system_vars
                and not k.startswith("_")
                and k not in upstream_agents
                and not k.endswith("_output")
                and not k.endswith("_instances")
                and isinstance(variables.get(k), (str, int, float, bool, type(None), dict, list))
            }
            self.logger.debug(f"[{log_prefix}] Instance-specific vars detected: {sorted(instance_specific_vars)}")
            filtered_variables = {
                k: v for k, v in variables.items()
                if k in self._inputs_section_variables or k in instance_specific_vars
            }
        else:
            # ERROR: _inputs_section_variables should always be set by generated agent code
            # This indicates the agent code needs to be regenerated
            self.logger.error(
                f"[{log_prefix}] _inputs_section_variables not found for agent {self.agent_id}. "
                f"This indicates the agent code needs to be regenerated. "
                f"Run: topaz-agent-kit init --starter <starter> <project_path>"
            )
            # Return empty dict to make the issue obvious - no variables will show in INPUTS tab
            # This forces the user to regenerate the agent code
            filtered_variables = {}
        
        # Log filtered results
        self.logger.debug(f"[{log_prefix}] Filtered variables keys (will show in INPUTS tab): {sorted(filtered_variables.keys())}")
        excluded_vars = set(variables.keys()) - set(filtered_variables.keys())
        self.logger.debug(f"[{log_prefix}] Excluded variables: {sorted(excluded_vars)}")
        
        return filtered_variables

    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Agent logic.

        Args:
            context: Execution context
            
        Returns:
            Output data from the agent
        """
        if not self._initialized:
            self.logger.error(f"Agent {self.agent_id} not initialized. Call initialize() first.")
            raise AgentError(f"Agent {self.agent_id} not initialized. Call initialize() first.")

        self.logger.debug("Context keys: {}", list(context.keys()))
        
        # Get variables for prompt rendering
        variables = self.get_agent_variables(context)
        
        # Unwrap content wrapping from all variables before using them
        # This ensures variables are clean before being used in Jinja2 templates
        variables = self._unwrap_content_from_variables(variables)
        
        # Restructure dot-notation variables into nested objects for Jinja2
        # e.g., "sot_schema_linker.schema_info" -> variables["sot_schema_linker"]["schema_info"]
        variables = self._restructure_dot_notation_variables(variables, context)
        
        # Simple validation to catch unknown variables that require user input
        self._validate_variables(variables)
        
        # Get input template based on framework
        input_template = self._get_input_template()
        if not input_template:
            self.logger.warning(f"No input template found for framework {self.framework_type}")
        
        # Render inputs using framework-appropriate template
        rendered_inputs = None
        if input_template:
            rendered_inputs = self._render_prompt_with_variables(input_template, variables)
        
        # Store rendered inputs for framework-specific classes to use (avoid re-rendering)
        self._rendered_inputs = rendered_inputs
        
        # Prepare agent_inputs for both local and remote agents (before execution)
        # This ensures instructions tab shows even if execution fails
        emitter = context.get("emitter")
        step_name = context.get("current_step_name")
        run_mode = context.get("run_mode", "local")
        
        # Filter to only show variables explicitly detected from YAML configuration
        filtered_variables = self._filter_variables_for_inputs_tab(variables, context, "INPUTS FILTER" if run_mode == "local" else "INPUTS FILTER REMOTE")
        
        # Get instruction prompt template (static, not rendered)
        instruction_prompt = self._get_instruction_prompt()
        
        # Prepare agent_inputs structure (used for both local step_input and remote result)
        agent_inputs = {}
        if filtered_variables:
            agent_inputs["variables"] = filtered_variables
        if rendered_inputs:
            agent_inputs["rendered_prompt"] = rendered_inputs
        if instruction_prompt:
            agent_inputs["prompt_template"] = instruction_prompt
        
        # For local agents, emit step_input directly (before execution)
        if emitter and hasattr(emitter, "step_input") and step_name and run_mode == "local":
            # Use node_id from context (set by LocalClient with instance ID) or fallback to agent_id
            # LocalClient sets context["node_id"] = recipient (the instance ID for repeat patterns)
            # This ensures INPUTS tab data is correctly associated with the instance card
            node_id = context.get("node_id", self.agent_id)
            emitter.step_input(
                step_name=step_name,
                node_id=node_id,
                inputs=agent_inputs if agent_inputs else None,
            )
        
        # Store agent_inputs for remote agents (will be added to result after execution)
        # This ensures it's available even if execution fails
        self._prepared_agent_inputs = agent_inputs
        
        # Execute agent (frameworks use self._rendered_inputs, no re-rendering needed)
        try:
            # Generated classes MUST implement _execute_agent with actual LLM execution
            raw_result = await self._execute_agent(context, variables)
            
            # Parse and validate the result using AgentOutputParser
            # This handles all framework-specific output formats consistently
            # Check if lenient parsing is enabled in agent config (for agents that may return incomplete/malformed JSON)
            lenient_parsing = self.agent_config.get("lenient_parsing", False)
            
            parsed_result = AgentOutputParser.parse_agent_output(
                raw_result,
                agent_label=f"{self.__class__.__name__}({self.agent_id})",
                agent_id=self.agent_id,
                lenient=lenient_parsing
            )
            
            # For remote agents, add agent_inputs to result for transport
            # Local agents emit step_input directly above (no need to add to result)
            if run_mode == "remote":
                # Use pre-prepared agent_inputs (created before execution)
                agent_inputs = getattr(self, "_prepared_agent_inputs", {})
                if agent_inputs:
                    parsed_result["agent_inputs"] = agent_inputs
            
            self.logger.debug(f"Successfully parsed agent output with keys: {list(parsed_result.keys())}")
            self.logger.debug(f"Agent {self.agent_id} Output: {parsed_result}")
            
            return parsed_result
            
        except Exception as e:
            self.logger.error(f"Agent {self.agent_id} execution failed: {e}")
            
            # For remote agents, still add agent_inputs to error result so instructions tab shows
            # This ensures the UI can display instructions even when execution fails
            run_mode = context.get("run_mode", "local")
            if run_mode == "remote":
                agent_inputs = getattr(self, "_prepared_agent_inputs", {})
                if agent_inputs:
                    # Create a minimal error result with agent_inputs
                    error_result = {
                        "error": str(e),
                        "agent_id": self.agent_id,
                        "agent_inputs": agent_inputs
                    }
                    # Return error result so agent_inputs can be extracted by agent_runner
                    return error_result
            
            raise