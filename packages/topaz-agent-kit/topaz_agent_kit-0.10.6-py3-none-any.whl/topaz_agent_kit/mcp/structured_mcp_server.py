"""
Structured MCP Server - Auto-converts unstructured tool responses to structured format.

This module provides a wrapper around McpServerApp that automatically wraps all tool
responses to ensure they return structured (dict) format for frameworks like MAF.
"""

from topaz_agent_kit.mcp.framework import McpServerApp
from topaz_agent_kit.utils.tool_response_wrapper import patch_fastmcp_tool_decorator
from topaz_agent_kit.utils.logger import Logger

logger = Logger("MCP.StructuredServer")


class StructuredMcpServerApp(McpServerApp):
    """
    MCP Server App that automatically wraps tool responses to structured format.
    
    This extends McpServerApp to automatically convert unstructured responses
    (strings, numbers, JSON strings) to structured dict format for MAF compatibility.
    
    Usage:
        # Instead of:
        app = McpServerApp(name="my-server", host="localhost", port=8050)
        
        # Use:
        app = StructuredMcpServerApp(name="my-server", host="localhost", port=8050)
        # All tools registered after this will have their responses auto-structured
    """
    
    def __init__(self, name: str, host: str, port: int, auto_structure_responses: bool = True):
        """
        Initialize structured MCP server.
        
        Args:
            name: Server name
            host: Server host
            port: Server port
            auto_structure_responses: If True, automatically wrap unstructured responses (default: True)
        """
        super().__init__(name, host, port)
        self.auto_structure_responses = auto_structure_responses
        
        if auto_structure_responses:
            # Patch the FastMCP tool decorator to auto-wrap responses
            patch_fastmcp_tool_decorator(self.server)
            logger.info("Structured MCP server initialized with auto-response wrapping enabled")
