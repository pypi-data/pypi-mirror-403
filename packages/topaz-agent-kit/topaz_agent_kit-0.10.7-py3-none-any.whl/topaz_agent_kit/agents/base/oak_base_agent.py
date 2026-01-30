"""
OAK framework base class implementing the BaseAgent interface.
Uses Microsoft OAK SDK for agent creation and management.
"""
import os
from typing import Any, Dict, List, Optional

from agents import Agent, Runner, set_default_openai_client, SQLiteSession, set_tracing_disabled, OpenAIChatCompletionsModel

from topaz_agent_kit.agents.base.base_agent import BaseAgent
from topaz_agent_kit.core.exceptions import AgentError
from topaz_agent_kit.utils.file_utils import FileUtils
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.utils.mcp_utils import matches_tool_patterns


class OAKBaseAgent(BaseAgent):
    """
    Base class for OAK agents using official SDK patterns.
    Handles OAK-specific initialization, tool management, and execution.
    Uses the unified architecture for model and MCP tool management.
    """
    
    def __init__(self, agent_id: str, **kwargs):
        super().__init__(agent_id, "oak", **kwargs)
        
        # Override logger with framework-specific name
        self.logger = Logger(f"OAKAgent({agent_id})")

        # OAK-specific attributes
        # self.session = SQLiteSession(agent_id)

        # Store filtered tool names for each plugin (since plugins don't support filtering)
        self._filtered_mcp_tool_names = {}

    def _initialize_agent(self):
        """Initialize OAK agent"""
        set_tracing_disabled(True)

    def _setup_environment(self):
        """Setup OAK-specific environment variables based on model preference"""
        # no specific environment setup needed for OAK

    async def _filter_mcp_tools(self) -> None:
        """Filter MCP tools for OAK framework using pattern matching"""
        try:
            self.logger.debug("Filtering MCP tools for OAK agent: {}", self.agent_id)
            if not self.tools:
                return
                
            mcp_config = self.agent_config.get("mcp", {})
            servers_config = mcp_config.get("servers", [])
            
            if not servers_config:
                # No MCP config, filter out all tools
                self.logger.debug("No MCP server configuration found, filtering out all tools")
                self.tools = []
                return
                
            # Aggregate wildcard patterns and toolkits from pipeline.yml
            all_patterns = []
            all_toolkits = []
            for server in servers_config:
                all_patterns.extend(server.get("tools", []))
                all_toolkits.extend(server.get("toolkits", []))
            # De-duplicate while preserving order
            all_patterns = list(dict.fromkeys(all_patterns))
            all_toolkits = list(dict.fromkeys(all_toolkits))
            self.logger.debug(f"Allowed tool patterns from pipeline.yml: {all_patterns}")
            self.logger.debug(f"Allowed toolkits from pipeline.yml: {all_toolkits}")
            
            # For OAK, MCP tools are now FunctionTool objects (extracted by FrameworkMCPManager)
            # We can filter them directly by checking their .name attribute
            filtered_tools = []
            self._filtered_mcp_tool_names = {}  # Clear previous filtered names
            
            for tool in self.tools:
                # Extract tool name
                tool_name = None
                if hasattr(tool, 'name'):
                    tool_name = tool.name
                elif isinstance(tool, dict) and 'name' in tool:
                    tool_name = tool['name']
                
                if tool_name:
                    # Check if tool matches patterns
                    matches = matches_tool_patterns(tool_name, all_patterns, all_toolkits)
                    if matches:
                        filtered_tools.append(tool)
                        self.logger.debug(f"Keeping OAK tool: {tool_name}")
                    else:
                        self.logger.debug(f"Filtering out OAK tool: {tool_name} (does not match patterns {all_patterns} or toolkits {all_toolkits})")
                else:
                    # Tool has no name - keep it for safety (might be a local tool or unknown type)
                    filtered_tools.append(tool)
                    self.logger.debug(f"Keeping OAK tool of unknown type: {type(tool).__name__} (no name attribute)")
            
            # Log filtered tool names for debugging
            filtered_tool_names = []
            for tool in filtered_tools:
                if hasattr(tool, 'name'):
                    filtered_tool_names.append(tool.name)
                elif isinstance(tool, dict) and 'name' in tool:
                    filtered_tool_names.append(tool['name'])
            
            self._filtered_mcp_tool_names[0] = filtered_tool_names  # Store for logging
            
            self.tools = filtered_tools
            
        except Exception as e:
            self.logger.error("Failed to filter MCP tools for OAK: {}", e)
            self.tools = []  # Clear tools on error
    
    def _extract_tool_name(self, tool_obj: Any) -> str:
        """Extract tool name from tool object"""
        if hasattr(tool_obj, 'name'):
            return tool_obj.name
        elif isinstance(tool_obj, dict) and 'name' in tool_obj:
            return tool_obj['name']
        return str(tool_obj)
    
    async def _log_tool_details(self) -> None:
        """Log filtered tool details for OAK framework"""
        if not self.tools:
            self.logger.debug("No tools attached")
            return
        
        # Extract tool names from filtered tools
        all_tool_names = []
        for tool in self.tools:
            if hasattr(tool, 'name'):
                all_tool_names.append(tool.name)
            elif isinstance(tool, dict) and 'name' in tool:
                all_tool_names.append(tool['name'])
            else:
                all_tool_names.append(type(tool).__name__)
        
        total_after = len(all_tool_names)
        
        self.logger.success(f"MCP tools count after filtering: {total_after}")
        for name in sorted(set(all_tool_names)):
            self.logger.success(f"  - {name}")

    def _create_agent(self) -> None:
        """Create OAK agent instance using official SDK"""
        try:
            self.logger.debug("Creating OAK agent with LLM: {} (type: {})", self.llm, type(self.llm))
            self.logger.debug("OAK agent instruction: {}", self.prompt["instruction"])
            
            # MCP tools are now individual FunctionTool objects (extracted by FrameworkMCPManager)
            # Combine MCP tools and local tools into a single tools list
            mcp_tools = self.tools if self.tools else []
            local_tools = self.local_tools if self.local_tools else []
            
            # Combine all tools
            all_tools = list(mcp_tools) + list(local_tools)
            
            if mcp_tools:
                self.logger.debug("Added {} MCP tool(s) (as FunctionTool wrappers)", len(mcp_tools))
            if local_tools:
                self.logger.success("Added {} local tool(s)", len(local_tools))
            
            # Create OAK agent
            # Now that MCP tools are FunctionTool objects, we can pass them via tools parameter
            agent_kwargs = {
                "name": self.agent_id,
                "model": OpenAIChatCompletionsModel(model=os.getenv("AZURE_OPENAI_MODEL"), openai_client=self.llm),
                "instructions": self.prompt["instruction"],
            }
            
            # Add all tools (MCP + local) via tools parameter
            if all_tools:
                agent_kwargs["tools"] = all_tools
                self.logger.debug(f"Added {len(all_tools)} total tool(s) ({len(mcp_tools)} MCP + {len(local_tools)} local) via tools parameter")
            
            self.agent = Agent(**agent_kwargs)
            
            self.logger.success("Created OAK agent: {}", self.name)
            self.logger.debug("Agent tools: {} tools available", len(self.tools))
            
        except Exception as e:
            raise AgentError(f"Failed to create OAK agent: {e}")
    
    def _build_multimodal_content(self, rendered_inputs: str, context: Dict[str, Any]) -> Optional[list[Dict[str, Any]]]:
        """
        Build multimodal content list for OAK Runner using ResponseInputItemParam format.
        
        OAK's Runner.run() accepts input as str | list[TResponseInputItem], where
        TResponseInputItem (ResponseInputItemParam) uses OpenAI Responses API format:
        - For EasyInputMessage: {"role": "user", "content": str | list[ResponseInputContentParam]}
        - ResponseInputContentParam can be:
          - {"type": "input_text", "text": "..."}
          - {"type": "input_image", "image_url": "..."}  # image_url is a string, not nested dict
        
        Args:
            rendered_inputs: Rendered prompt text
            context: Execution context containing user_files_data
            
        Returns:
            None if text-only (use plain string), or list of ResponseInputItemParam-compatible dicts for multimodal
        """
        content = []
        user_files_data = context.get("user_files_data", {})
        self.logger.debug("Building OAK multimodal content - user_files_data keys: {}", list(user_files_data.keys()) if user_files_data else "None")
        
        # Check if the agent's prompt template uses user_files variable
        # If not, skip file processing to avoid unnecessary data processing
        if not self._should_process_files():
            return None  # Return None to signal text-only mode
        
        # Add text content (always present)
        # OAK uses Responses API format: "input_text" not "text"
        if rendered_inputs and rendered_inputs.strip():
            content.append({"type": "input_text", "text": rendered_inputs})
        
        # Add image files from user_files_data (as base64 data URLs)
        # OAK uses Responses API format: "input_image" with "image_url" field (not "image_url" type)
        images = user_files_data.get("images", [])
        self.logger.debug("Found {} image(s) in user_files_data", len(images))
        for image_data in images:
            try:
                # Convert bytes to base64 data URL
                base64_data = FileUtils.encode_bytes_to_base64(image_data["data"])
                data_url = f"data:{image_data['metadata']['mime_type']};base64,{base64_data}"
                content.append({
                    "type": "input_image",
                    "image_url": data_url  # Direct string, not nested dict
                })
                self.logger.debug("Added image to OAK message: {}", image_data["name"])
            except Exception as e:
                self.logger.error("Failed to add image {} to OAK message: {}", image_data.get("name", "unknown"), e)
                raise  # Fail agent execution on error
        
        # Add document files from user_files_data
        # OAK vision API only supports actual images (PNG, JPEG, GIF, WEBP) - NOT PDFs/documents
        documents = user_files_data.get("documents", [])
        for doc_data in documents:
            try:
                # If document has extracted text, add as text content
                if doc_data.get("text"):
                    content.append({"type": "input_text", "text": f"\n\nDocument: {doc_data['name']}\n{doc_data['text']}"})
                    self.logger.debug("Added document text to OAK message: {}", doc_data["name"])
                else:
                    # For documents without extracted text, log and skip
                    # Vision APIs don't support PDFs/documents - only actual images
                    self.logger.warning(
                        "Skipping document {} - no extracted text available and mime_type {} not supported by vision API",
                        doc_data["name"], doc_data["metadata"]["mime_type"]
                    )
            except Exception as e:
                self.logger.error("Failed to add document {} to OAK message: {}", doc_data.get("name", "unknown"), e)
                raise  # Fail agent execution on error
        
        # Add URLs from user_files_data
        urls = user_files_data.get("urls", [])
        for url_data in urls:
            url_type = url_data.get("type")
            if url_type == "image":  # OAK primarily supports images
                try:
                    content.append({
                        "type": "input_image",
                        "image_url": url_data["url"]  # Direct string, not nested dict
                    })
                    self.logger.debug("Added image URL to OAK message: {}", url_data["url"])
                except Exception as e:
                    self.logger.error("Failed to add image URL {} to OAK message: {}", url_data.get("url", "unknown"), e)
                    raise  # Fail agent execution on error
        
        # Determine if we have multimodal content (images/document URLs)
        has_multimodal = len(content) > 1 or any(item.get("type") != "input_text" for item in content)
        
        if not has_multimodal and len(content) == 1:
            # Text-only: return None to signal we should use plain string
            # We'll handle this in _execute_agent by passing the string directly
            return None
        
        # Multimodal: return list format with content as list of dicts
        # OAK requires content to be a list when multimodal
        return [{
            "role": "user",
            "content": content  # Always a list of content dicts for multimodal
        }]

    async def _execute_agent(self, context: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute with OAK agent. This method handles the actual LLM execution.
        Generated classes can override this for custom logic, or call super() to use this implementation.
        """
        try:
            # Use pre-rendered inputs from base_agent.execute() (stored in self._rendered_inputs)
            rendered_inputs = self._rendered_inputs if hasattr(self, '_rendered_inputs') else None
            if not rendered_inputs:
                # Fallback: render if not available (shouldn't happen in normal flow)
                rendered_inputs = self._render_prompt_with_variables(self.prompt["inputs"], variables)
            self.logger.debug(f"Agent {self.agent_id} Inputs: {rendered_inputs}")
            
            # Build multimodal content
            input_items = self._build_multimodal_content(rendered_inputs, context)
            
            # OAK accepts: str | list[TResponseInputItem]
            # - String for text-only input
            # - List of message dicts for multimodal input
            if input_items is None:
                # Text-only: pass string directly
                self.logger.debug("OAK input: text-only (plain string)")
                runner_input = rendered_inputs
            else:
                # Multimodal: pass list format
                self.logger.debug("OAK input: multimodal ({} message(s))", len(input_items))
                runner_input = input_items
            
            # Execute with OAK agent
            self.logger.debug("Executing OAK workflow{}", " with multimodal content" if input_items else "")
            
            # Get max_turns from agent config (default: 10 for OAK SDK)
            max_turns = self.agent_config.get("max_turns", 10)
            
            result = await Runner.run(
                starting_agent=self.agent, 
                input=runner_input,  # String for text-only, list for multimodal
                max_turns=max_turns,  # Allow configurable max turns
                # session=self.session,
            )

            self.logger.success("OAK agent execution completed")
            
            # Return raw result - base_agent.execute() will parse it
            return result.final_output
            
        except Exception as e:
            self.logger.error("OAK agent execution failed: {}", e)
            raise AgentError(f"OAK agent execution failed: {e}")
    