"""Framework-specific MCP integration management"""

import copy
import json
import traceback
from typing import List, Any, Dict

from topaz_agent_kit.core.exceptions import MCPError
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.frameworks.framework_config_manager import FrameworkConfigManager

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StreamableHttpConnection
from crewai_tools import MCPServerAdapter
from semantic_kernel.connectors.mcp import MCPStreamableHttpPlugin
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from agents.mcp import MCPServerStreamableHttp, MCPServerStreamableHttpParams
from agent_framework import MCPStreamableHTTPTool

class FrameworkMCPManager:
    """Framework-specific MCP integration management"""
    
    _logger = Logger("FrameworkMCPManager")
    
    @classmethod
    async def create_framework_mcp_tools(cls, framework: str, mcp_url: str, **config) -> List[Any]:
        """Create MCP tools appropriate for the specified framework"""
        
        cls._logger.info("Creating MCP tools for {} framework: {}", framework, mcp_url)
        
        # Get framework-specific MCP integration details
        framework_config = FrameworkConfigManager()
        mcp_integration = framework_config.get_mcp_integration(framework)
        
        if framework == "agno":
            return cls._create_agno_mcp_tools(mcp_url, mcp_integration, **config)
        elif framework == "langgraph":
            return await cls._create_langgraph_mcp_tools(mcp_url, mcp_integration, **config)
        elif framework == "crewai":
            return await cls._create_crewai_mcp_tools(mcp_url, mcp_integration, **config)
        elif framework == "sk":
            return await cls._create_sk_mcp_tools(mcp_url, mcp_integration, **config)
        elif framework == "adk":
            return await cls._create_adk_mcp_tools(mcp_url, mcp_integration, **config)
        elif framework == "oak":
            return await cls._create_oak_mcp_tools(mcp_url, mcp_integration, **config)
        elif framework == "maf":
            return await cls._create_maf_mcp_tools(mcp_url, mcp_integration, **config)
        else:
            raise ValueError(f"Unsupported framework: {framework}")
    
    @classmethod
    async def connect_framework_mcp_tools(cls, mcp_tools: List[Any]) -> None:
        """Connect and initialize MCP tools asynchronously"""
        for tool in mcp_tools:
            try:
                if hasattr(tool, 'connect'):
                    await tool.connect()
                    cls._logger.success("Connected MCP tool: {}", type(tool).__name__)
                
                if hasattr(tool, 'initialize'):
                    await tool.initialize()
                    cls._logger.success("Initialized MCP tool: {}", type(tool).__name__)
                    
            except Exception as e:
                cls._logger.warning("Failed to connect/initialize MCP tool: {}", e)
    
    @classmethod
    async def cleanup_framework_mcp_tools(cls, mcp_tools: List[Any]) -> None:
        """Cleanup and close MCP tools asynchronously"""
        # Track cleaned up MCP servers to avoid duplicate cleanup
        cleaned_servers = set()
        
        for tool in mcp_tools:
            try:
                # Check if this is an OAK FunctionTool with attached MCP server
                if hasattr(tool, '_mcp_server'):
                    server = tool._mcp_server
                    server_id = id(server)
                    if server_id not in cleaned_servers:
                        if hasattr(server, 'close'):
                            await server.close()
                        elif hasattr(server, 'disconnect'):
                            await server.disconnect()
                        elif hasattr(server, 'cleanup'):
                            await server.cleanup()
                        cleaned_servers.add(server_id)
                        cls._logger.info("Cleaned up OAK MCP server from FunctionTool")
                # Check if this is our MCPToolsWrapper (LangGraph/CrewAI)
                elif hasattr(tool, 'cleanup') and hasattr(tool, '_mcp_client'):
                    # This is our wrapper, use its cleanup method
                    tool.cleanup()
                    cls._logger.info("Cleaned up MCP tools wrapper: {}", type(tool).__name__)
                elif hasattr(tool, 'close'):
                    await tool.close()
                    cls._logger.info("Closed MCP tool: {}", type(tool).__name__)
                elif hasattr(tool, 'disconnect'):
                    await tool.disconnect()
                    cls._logger.info("Disconnected MCP tool: {}", type(tool).__name__)
                elif hasattr(tool, 'cleanup'):
                    await tool.cleanup()
                    cls._logger.info("Cleaned up MCP tool: {}", type(tool).__name__)
                    
            except Exception as e:
                cls._logger.warning("Failed to cleanup MCP tool: {}", e)
    
    @classmethod
    def _create_agno_mcp_tools(cls, mcp_url: str, mcp_integration: Dict[str, Any], **config) -> List[Any]:
        """Create Agno MCP tools using framework configuration"""
        try:
            transport = mcp_integration.get("transport", "streamable-http")
            tool_class = mcp_integration.get("tool_class", "agno.tools.mcp.MCPTools")
            params_class = mcp_integration.get("params_class", "agno.tools.mcp.StreamableHTTPClientParams")
            timeout = mcp_integration.get("timeout", 300)

            # Import required classes
            tool_module, tool_name = tool_class.rsplit(".", 1)
            tool_module_obj = __import__(tool_module, fromlist=[tool_name])
            tool_class_obj = getattr(tool_module_obj, tool_name)
            
            params_module, params_name = params_class.rsplit(".", 1)
            params_module_obj = __import__(params_module, fromlist=[params_name])
            params_class_obj = getattr(params_module_obj, params_name)
            
            # Create MCP tools with timeout configuration
            server_params = params_class_obj(url=mcp_url, timeout=timeout)        
            
            mcp_tools = tool_class_obj(
                transport=transport,
                server_params=server_params,
                timeout_seconds=timeout
            )
            
            cls._logger.success("Created Agno MCPTools with {} transport", transport)
            return [mcp_tools]
            
        except Exception as e:
            cls._logger.error("Failed to create Agno MCPTools: {}", e)
            raise MCPError(f"Failed to create Agno MCPTools: {e}")
    
    @classmethod
    async def _create_langgraph_mcp_tools(cls, mcp_url: str, mcp_integration: Dict[str, Any], **config) -> List[Any]:
        """Create LangGraph MCP tools using langchain-mcp-adapters"""
        try:
            # Extract transport type from integration config
            transport = mcp_integration.get("transport", "streamable-http")
            timeout = mcp_integration.get("timeout")
            cls._logger.info("Using transport: {} for MCP server: {}", transport, mcp_url)
            
            # Configure MCP client for the server using proper connection types
            # For now, we'll use a single server configuration
            # This can be extended to support multiple servers later
            server_config = {
                "mcp_server": StreamableHttpConnection(
                    transport="streamable_http",
                    url=mcp_url,
                    timeout=timeout  
                )
            }
            
            cls._logger.info("Server config: {}", server_config)
            
            # Create MCP client
            mcp_client = MultiServerMCPClient(server_config)
            cls._logger.success("MCP client created successfully")
            
            # Get tools as LangChain BaseTool instances
            tools = await mcp_client.get_tools()
            
            cls._logger.success("Created LangGraph MCP tools using langchain-mcp-adapters: {} tools", len(tools))
            
            # Create a wrapper that holds both tools and MCP client for cleanup
            # This ensures we can properly cleanup the MCP client later
            class MCPToolsWrapper:
                def __init__(self, tools_list, mcp_client_instance):
                    self.tools = tools_list
                    self._mcp_client = mcp_client_instance
                
                def __len__(self):
                    return len(self.tools)
                
                def __getitem__(self, index):
                    return self.tools[index]
                
                def __iter__(self):
                    return iter(self.tools)
                
                def __contains__(self, item):
                    return item in self.tools
                
                async def cleanup(self):
                    """Cleanup MCP client resources"""
                    try:
                        if hasattr(self._mcp_client, 'close'):
                            await self._mcp_client.close()
                        elif hasattr(self._mcp_client, 'disconnect'):
                            await self._mcp_client.disconnect()
                        cls._logger.info("Cleaned up LangGraph MCP client")
                    except Exception as e:
                        cls._logger.warning("Failed to cleanup LangGraph MCP client: {}", e)
            
            # Return the wrapper instead of raw tools
            return MCPToolsWrapper(tools, mcp_client)
            
        except ImportError as e:
            cls._logger.error("langchain-mcp-adapters not available: {}", e)
            cls._logger.error("Install with: uv add langchain-mcp-adapters")
            raise MCPError("langchain-mcp-adapters package required for LangGraph MCP integration")
        except Exception as e:
            cls._logger.error("Failed to create LangGraph MCP tools: {}", e)
            cls._logger.error("Full error details: {}", str(e))
            cls._logger.error("Traceback: {}", traceback.format_exc())
            raise MCPError(f"Failed to create LangGraph MCP tools: {e}")
    
    @classmethod
    async def _create_crewai_mcp_tools(cls, mcp_url: str, mcp_integration: Dict[str, Any], **config) -> List[Any]:
        """Create CrewAI MCP tools using native MCPServerAdapter"""
        try:    
            cls._logger.info("Using CrewAI MCPServerAdapter: {}", mcp_url)
            timeout = mcp_integration.get("timeout", 300)  # Default to 300 seconds if not specified

            # Create server parameters as a dictionary (CrewAI expects this format)
            # MCP library expects "streamable-http" (with hyphen), not "streamable_http" (with underscore)
            # MCPServerAdapter accepts either a dict (single server) or list of dicts (multiple servers)
            server_params = {
                "url": mcp_url,
                "transport": "streamable-http",
                "timeout": timeout,
            }
            
            cls._logger.info("Created CrewAI native MCP server parameters for {}", mcp_url)
            
            # Create adapter and return tools directly (following working example pattern)
            # MCPServerAdapter has a .tools property that returns the list of tools
            # The adapter manages its own lifecycle internally
            adapter = MCPServerAdapter(server_params)
            
            # Access .tools property to get the list of tools
            # This initializes the adapter and fetches tools from the MCP server
            tools = adapter.tools
            
            cls._logger.success("Created CrewAI MCPServerAdapter and extracted {} tools", len(tools))
            
            # Return tools directly as a list (similar to LangGraph pattern)
            # The base agent will filter these tools based on patterns
            return tools
            
        except ImportError as e:
            cls._logger.error("crewai-tools not available or missing MCP support: {}", e)
            cls._logger.error("Install with: uv add 'crewai-tools[mcp]'")
            raise MCPError("crewai-tools package with MCP support required for CrewAI MCP integration")
        except Exception as e:
            cls._logger.error("Failed to create CrewAI native MCP tools: {}", e)
            raise MCPError(f"Failed to create CrewAI native MCP tools: {e}")
    
    @classmethod
    async def _create_sk_mcp_tools(cls, mcp_url: str, mcp_integration: Dict[str, Any], **config) -> List[Any]:
        """Create MCP tools for SK framework using plugin-based integration"""
        cls._logger.info("Creating SK MCP tools for mcp_url: {}", mcp_url)
        
        try:
            # Create the plugin (no explicit initialization needed)
            plugin = MCPStreamableHttpPlugin(
                name="sk_mcp_plugin",
                description="SK MCP Plugin",
                url=mcp_url, 
                timeout=mcp_integration.get("timeout", 300),
            )
            
            # Return the plugin wrapper
            return [plugin]
            
        except Exception as e:
            cls._logger.error("Failed to create SK MCP tools: {}", e)
            raise MCPError(f"Failed to create SK MCP tools: {e}")
    
    @classmethod
    async def _create_adk_mcp_tools(cls, mcp_url: str, mcp_integration: Dict[str, Any], **config) -> List[Any]:
        """Create MCP tools for ADK framework using streamable HTTP connection"""
        cls._logger.info("Creating ADK MCP tools for mcp_url: {}", mcp_url)
        
        try:
            # Create connection parameters
            connection_params = StreamableHTTPConnectionParams(
                url=mcp_url,
                timeout=mcp_integration.get("timeout", 300)
            )
            
            # Create MCP toolset (ADK manages sessions internally; no explicit initialize)
            mcp_toolset = McpToolset(connection_params=connection_params)
            
            cls._logger.success("ADK MCP toolset created successfully")
            
            # Return the toolset wrapper
            return [mcp_toolset]
            
        except ImportError as e:
            cls._logger.error("ADK MCP tools not available: {}", e)
            cls._logger.error("Ensure google-adk-tools is installed with MCP support")
            raise MCPError("ADK MCP tools package required for ADK MCP integration")
        except Exception as e:
            cls._logger.error("Failed to create ADK MCP tools: {}", e)
            raise MCPError(f"Failed to create ADK MCP tools: {e}")
    
    @classmethod
    async def _create_oak_mcp_tools(cls, mcp_url: str, mcp_integration: Dict[str, Any], **config) -> List[Any]:
        """Create MCP tools for OAK framework by extracting individual tools and creating wrapper functions"""
        cls._logger.info("Creating OAK MCP tools for mcp_url: {}", mcp_url)
        
        try:
            from agents import FunctionTool, RunContextWrapper
            from typing import Any as TypingAny
            import json
            
            # Create connection parameters
            connection_params = MCPServerStreamableHttpParams(
                url=mcp_url,
                timeout=mcp_integration.get("timeout", 300)
            )
            
            # Create MCP server connection
            mcp_server = MCPServerStreamableHttp(
                params=connection_params,
                client_session_timeout_seconds=mcp_integration.get("timeout", 300)
            )
            
            # Connect to the MCP server
            if hasattr(mcp_server, 'connect'):
                await mcp_server.connect()
                cls._logger.info("Connected to MCP server")
            
            # Query tools from the MCP server
            tools_result = await mcp_server.list_tools()
            
            # Extract tool objects from result
            all_tool_objects = []
            if hasattr(tools_result, 'tools'):
                all_tool_objects = tools_result.tools
            elif isinstance(tools_result, list):
                all_tool_objects = tools_result
            
            cls._logger.info("Extracted {} tools from MCP server", len(all_tool_objects))
            
            # Debug: Log first tool object structure
            if all_tool_objects:
                first_tool = all_tool_objects[0]
                cls._logger.debug("First tool object type: {}, attributes: {}", 
                                 type(first_tool).__name__,
                                 dir(first_tool) if hasattr(first_tool, '__dict__') else 'N/A')
            
            # Create wrapper functions for each tool
            wrapped_tools = []
            for tool_obj in all_tool_objects:
                # Extract tool name, description, and schema
                tool_name = None
                tool_description = ""
                tool_input_schema = {}
                
                # Try to extract from object attributes first
                if hasattr(tool_obj, 'name'):
                    tool_name = tool_obj.name
                    if hasattr(tool_obj, 'description'):
                        tool_description = tool_obj.description
                    if hasattr(tool_obj, 'inputSchema'):
                        tool_input_schema = tool_obj.inputSchema
                    elif hasattr(tool_obj, 'input_schema'):
                        tool_input_schema = tool_obj.input_schema
                # Try dict-like access
                elif isinstance(tool_obj, dict):
                    tool_name = tool_obj.get('name')
                    tool_description = tool_obj.get('description', '')
                    tool_input_schema = tool_obj.get('inputSchema', tool_obj.get('input_schema', {}))
                # Try get() method (for dict-like objects)
                elif hasattr(tool_obj, 'get'):
                    tool_name = tool_obj.get('name')
                    tool_description = tool_obj.get('description', '')
                    tool_input_schema = tool_obj.get('inputSchema', tool_obj.get('input_schema', {}))
                
                if not tool_name:
                    cls._logger.warning("Skipping tool object with no name: {}", type(tool_obj).__name__)
                    continue
                
                # Create an invoke handler that matches FunctionTool's expected signature
                # Signature: async def handler(ctx: RunContextWrapper[Any], args: str) -> str
                def create_invoke_handler(tool_name_capture: str, server_capture: Any):
                    """Create an invoke handler for an MCP tool"""
                    async def handler(ctx: RunContextWrapper[TypingAny], args: str) -> str:
                        """Handler function that calls the MCP server"""
                        try:
                            # Parse JSON args string
                            parsed_args = json.loads(args)
                            
                            # Call MCP server - use call_tool method
                            result = await server_capture.call_tool(tool_name_capture, parsed_args)
                            
                            # Extract content from result if it's a structured response
                            if hasattr(result, 'content'):
                                if isinstance(result.content, list) and len(result.content) > 0:
                                    # Get text content if available
                                    content_item = result.content[0]
                                    if hasattr(content_item, 'text'):
                                        return content_item.text
                                    elif isinstance(content_item, str):
                                        return content_item
                                    elif isinstance(content_item, dict):
                                        return json.dumps(content_item)
                                elif isinstance(result.content, str):
                                    return result.content
                                else:
                                    return json.dumps(result.content) if isinstance(result.content, (dict, list)) else str(result.content)
                            elif isinstance(result, str):
                                return result
                            elif isinstance(result, (dict, list)):
                                return json.dumps(result)
                            else:
                                return str(result)
                        except Exception as e:
                            cls._logger.error("Error calling MCP tool {}: {}", tool_name_capture, e)
                            raise
                    
                    return handler
                
                # Create the invoke handler
                invoke_handler = create_invoke_handler(tool_name, mcp_server)
                
                # Convert MCP inputSchema to FunctionTool's params_json_schema format
                # Note: OAK's FunctionTool (Pydantic) doesn't accept ANY additionalProperties for object types (neither true nor false)
                
                def clean_schema(schema: Any) -> Any:
                    """Recursively remove additionalProperties from schema (Pydantic's FunctionTool doesn't accept it for object types)"""
                    if not isinstance(schema, dict):
                        return schema
                    
                    cleaned = {}
                    for key, value in schema.items():
                        if key == 'additionalProperties':
                            # Skip ALL additionalProperties - OAK's FunctionTool (Pydantic) doesn't accept it for object types
                            # Whether it's true, false, or a schema object, we must remove it
                            continue
                        elif key in ('properties', 'items', 'allOf', 'anyOf', 'oneOf', 'definitions', '$defs'):
                            # Recursively clean nested schemas
                            if isinstance(value, dict):
                                cleaned[key] = {k: clean_schema(v) for k, v in value.items()}
                            elif isinstance(value, list):
                                cleaned[key] = [clean_schema(item) if isinstance(item, (dict, list)) else item for item in value]
                            else:
                                cleaned[key] = value
                        elif isinstance(value, dict):
                            # Recursively clean any other nested objects
                            cleaned[key] = clean_schema(value)
                        elif isinstance(value, list):
                            # Recursively clean list items
                            cleaned[key] = [clean_schema(item) if isinstance(item, (dict, list)) else item for item in value]
                        else:
                            cleaned[key] = value
                    return cleaned
                
                params_json_schema = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
                
                if tool_input_schema:
                    # Convert to dict if it's a Pydantic model or other object
                    if hasattr(tool_input_schema, 'model_dump'):
                        tool_input_schema = tool_input_schema.model_dump()
                    elif hasattr(tool_input_schema, 'dict'):
                        tool_input_schema = tool_input_schema.dict()
                    elif not isinstance(tool_input_schema, dict):
                        cls._logger.warning("Tool {} has unexpected inputSchema type: {}", tool_name, type(tool_input_schema))
                        tool_input_schema = {}
                    
                    # MCP schema might be in different formats, try to extract properties
                    if isinstance(tool_input_schema, dict):
                        if 'properties' in tool_input_schema:
                            # Standard JSON schema format - clean recursively
                            cleaned_schema = clean_schema(tool_input_schema)
                            params_json_schema['properties'] = cleaned_schema.get('properties', {})
                            params_json_schema['required'] = cleaned_schema.get('required', [])
                            # Only include additionalProperties if it's True
                            if cleaned_schema.get('additionalProperties') is True:
                                params_json_schema['additionalProperties'] = True
                        elif 'type' in tool_input_schema and tool_input_schema['type'] == 'object':
                            # Already in correct format - clean recursively
                            params_json_schema = clean_schema(tool_input_schema)
                        else:
                            # Unknown format, use as properties directly (clean first)
                            cls._logger.debug("Tool {} has unexpected schema format, using as properties", tool_name)
                            params_json_schema['properties'] = clean_schema(tool_input_schema) if isinstance(tool_input_schema, dict) else tool_input_schema
                else:
                    # No schema provided - create empty schema (tool will accept any args)
                    cls._logger.debug("Tool {} has no inputSchema, using empty schema", tool_name)
                
                # Final cleanup: ensure params_json_schema doesn't have ANY additionalProperties (Pydantic rejects all for object types)
                # Deep clean the schema recursively
                params_json_schema = clean_schema(copy.deepcopy(params_json_schema))
                
                # Create FunctionTool with correct API
                try:
                    # Final validation: ensure no additionalProperties exists anywhere (Pydantic rejects all additionalProperties for object types)
                    # Use JSON serialization to catch any remaining instances
                    schema_str = json.dumps(params_json_schema)
                    if '"additionalProperties"' in schema_str:
                        # Aggressive cleanup: parse JSON string, remove ALL additionalProperties (true, false, or schema objects), rebuild
                        try:
                            # Parse the JSON string to get a clean dict
                            parsed = json.loads(schema_str)
                            # Recursively remove ALL additionalProperties (regardless of value)
                            def aggressive_clean(obj):
                                if isinstance(obj, dict):
                                    cleaned = {}
                                    for k, v in obj.items():
                                        if k == 'additionalProperties':
                                            continue  # Skip ALL additionalProperties (true, false, or schema objects)
                                        # Recursively clean nested structures
                                        if isinstance(v, (dict, list)):
                                            cleaned[k] = aggressive_clean(v)
                                        else:
                                            cleaned[k] = v
                                    return cleaned
                                elif isinstance(obj, list):
                                    return [aggressive_clean(item) if isinstance(item, (dict, list)) else item for item in obj]
                                return obj
                            params_json_schema = aggressive_clean(parsed)
                        except Exception as e:
                            cls._logger.warning("Failed to perform aggressive cleanup via JSON parse for {}: {}", tool_name, e)
                    
                    function_tool = FunctionTool(
                        name=tool_name,
                        description=tool_description or f"MCP tool: {tool_name}",
                        params_json_schema=params_json_schema,
                        on_invoke_tool=invoke_handler
                    )
                    wrapped_tools.append(function_tool)
                    cls._logger.debug("Created wrapper for MCP tool: {}", tool_name)
                except Exception as e:
                    cls._logger.warning("Failed to create FunctionTool for {}: {}", tool_name, str(e))
                    continue
            
            cls._logger.success("Created {} OAK MCP tool wrappers", len(wrapped_tools))
            
            # Store reference to MCP server for cleanup (attach to first tool or create a wrapper)
            if wrapped_tools:
                # Attach server reference to first tool for cleanup
                wrapped_tools[0]._mcp_server = mcp_server
            
            return wrapped_tools
            
        except ImportError as e:
            cls._logger.error("OAK MCP tools not available: {}", e)
            raise MCPError("OAK MCP tools package required for OAK MCP integration")
        except Exception as e:
            cls._logger.error("Failed to create OAK MCP tools: {}", e)
            cls._logger.error("Traceback: {}", traceback.format_exc())
            raise MCPError(f"Failed to create OAK MCP tools: {e}")

    @classmethod
    async def _create_maf_mcp_tools(cls, mcp_url: str, mcp_integration: Dict[str, Any], **config) -> List[Any]:
        """Create MCP tools for MAF framework using streamable HTTP connection"""
        cls._logger.info("Creating MAF MCP tools for mcp_url: {}", mcp_url)
        
        try:    
            mcp_tools = MCPStreamableHTTPTool(
                name="maf_mcp_tools",
                url=mcp_url,
                timeout=mcp_integration.get("timeout", 300)
            )
            
            cls._logger.success("MAF MCP tools created successfully")
            return [mcp_tools]
            
        except ImportError as e:
            cls._logger.error("MAF MCP tools not available: {}", e)
            raise MCPError("agent_framework package required for MAF MCP integration")
        except Exception as e:
            cls._logger.error("Failed to create MAF MCP tools: {}", e)
            raise MCPError(f"Failed to create MAF MCP tools: {e}")