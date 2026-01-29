"""
Tool Response Wrapper - Auto-converts unstructured responses to structured format.

This module provides utilities to automatically wrap tool responses that return
unstructured data (strings, numbers, JSON strings) into structured dict format
for frameworks like MAF that require structured responses.

This utility works for both:
- MCP tools (via FastMCP server)
- Local tools (via pipeline_tool decorator)
"""

import json
import inspect
from typing import Any, Callable, Dict, Union, TYPE_CHECKING
from functools import wraps
from topaz_agent_kit.utils.logger import Logger

if TYPE_CHECKING:
    from fastmcp import FastMCP

logger = Logger("Utils.ToolResponseWrapper")


def is_unstructured_response(value: Any) -> bool:
    """
    Check if a response value is unstructured (should be wrapped in a dict).
    
    Unstructured responses include:
    - Plain strings (including JSON strings)
    - Numbers (int, float)
    - Booleans
    - None
    
    Structured responses (don't need wrapping):
    - Dicts
    - Lists
    - Objects with dict-like structure
    
    Args:
        value: The response value to check
        
    Returns:
        True if the value is unstructured and should be wrapped
    """
    # Dicts and lists are already structured
    if isinstance(value, dict):
        return False
    if isinstance(value, list):
        return False
    
    # Primitives (str, int, float, bool, None) are unstructured
    if isinstance(value, (str, int, float, bool)) or value is None:
        return True
    
    # Everything else (objects, etc.) - assume structured
    return False


def wrap_unstructured_response(value: Any, tool_name: str = "unknown") -> Dict[str, Any]:
    """
    Wrap an unstructured response into a structured dict format.
    
    Handles:
    - Plain strings -> {"result": "string"}
    - JSON strings -> Parse and return as dict (if valid JSON)
    - Numbers -> {"result": number}
    - Booleans -> {"result": bool}
    - None -> {"result": None}
    
    Args:
        value: The unstructured response value
        tool_name: Name of the tool (for logging)
        
    Returns:
        Dict with structured response format
    """
    # If already structured, return as-is
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        return {"result": value}
    
    # Handle strings (including JSON strings)
    if isinstance(value, str):
        # Try to parse as JSON first (for tools that return JSON strings)
        if value.strip().startswith(('{', '[')):
            try:
                parsed = json.loads(value)
                # If it parsed to a dict, return it directly (already structured)
                if isinstance(parsed, dict):
                    logger.debug("Tool {} returned JSON string, parsed to dict", tool_name)
                    return parsed
                # If it parsed to a list, wrap it
                if isinstance(parsed, list):
                    logger.debug("Tool {} returned JSON string (list), wrapped in dict", tool_name)
                    return {"result": parsed}
            except (json.JSONDecodeError, ValueError):
                # Not valid JSON, treat as plain string
                pass
        
        # Plain string - wrap it
        logger.debug("Tool {} returned plain string, wrapping in dict", tool_name)
        return {"result": value}
    
    # Handle numbers and booleans
    if isinstance(value, (int, float, bool)) or value is None:
        logger.debug("Tool {} returned primitive type {}, wrapping in dict", tool_name, type(value).__name__)
        return {"result": value}
    
    # For other types, try to convert to dict or wrap
    try:
        if hasattr(value, '__dict__'):
            # Object with __dict__ - convert to dict
            return dict(value.__dict__)
    except Exception:
        pass
    
    # Last resort: wrap as string representation
    logger.warning("Tool {} returned unknown type {}, wrapping as string", tool_name, type(value).__name__)
    return {"result": str(value)}


def wrap_tool_response(func: Callable, tool_name: str = None) -> Callable:
    """
    Wrap a tool function to automatically convert unstructured responses to structured format.
    
    This wrapper:
    1. Executes the original tool function
    2. Checks if the response is unstructured
    3. If unstructured, wraps it in a dict
    4. Returns the structured response
    
    Works for both sync and async functions.
    
    Args:
        func: The tool function to wrap
        tool_name: Optional tool name (defaults to function name)
        
    Returns:
        Wrapped function that returns structured responses
    """
    if tool_name is None:
        tool_name = getattr(func, '__name__', 'unknown_tool')
    
    # Check if function is async
    is_async = inspect.iscoroutinefunction(func)
    
    if is_async:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            if is_unstructured_response(result):
                return wrap_unstructured_response(result, tool_name)
            return result
        return async_wrapper
    else:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if is_unstructured_response(result):
                return wrap_unstructured_response(result, tool_name)
            return result
        return sync_wrapper


def patch_fastmcp_tool_decorator(mcp_server: "FastMCP") -> None:
    """
    Patch FastMCP's tool decorator to automatically wrap unstructured responses.
    
    This function modifies the FastMCP instance's tool decorator to automatically
    convert unstructured responses (strings, numbers, JSON strings) to structured
    dict format. This ensures MAF compatibility without modifying individual tools.
    
    Usage:
        from fastmcp import FastMCP
        from topaz_agent_kit.utils.tool_response_wrapper import patch_fastmcp_tool_decorator
        
        mcp = FastMCP(name="my-server")
        patch_fastmcp_tool_decorator(mcp)  # Patch before registering tools
        
        @mcp.tool(name="my_tool")
        def my_tool() -> str:
            return "result"  # Will be auto-wrapped to {"result": "result"}
    
    Args:
        mcp_server: The FastMCP server instance to patch
    """
    original_tool = mcp_server.tool
    
    def structured_tool(name: str = None, **kwargs):
        """Wrapper around FastMCP's tool decorator that auto-structures responses"""
        def decorator(func: Callable):
            # Wrap the function to convert responses
            tool_name = name or getattr(func, '__name__', 'unknown_tool')
            wrapped_func = wrap_tool_response(func, tool_name=tool_name)
            
            # Apply the original FastMCP decorator to the wrapped function
            return original_tool(name=name, **kwargs)(wrapped_func)
        return decorator
    
    # Replace the tool method with our wrapper
    mcp_server.tool = structured_tool
    logger.info("Patched FastMCP tool decorator to auto-structure responses")
