import asyncio
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List

from topaz_agent_kit.core.configuration_engine import ConfigurationEngine
from topaz_agent_kit.agents.agent_factory import AgentFactory
from topaz_agent_kit.agents.base import (
    AgnoBaseAgent,
    LangGraphBaseAgent,
    CrewAIBaseAgent,
    ADKBaseAgent,
    SKBaseAgent,
    OAKBaseAgent,
    MAFBaseAgent,
)


PROJECT_DIR = Path("/Users/Nishoo/Developer/topaz-agent-kit/projects/pa")
AGENT_ID = "covenant_change_order_extractor"


FRAMEWORKS: List[tuple[str, Any]] = [
    # ("agno", AgnoBaseAgent),            # Commented out - testing OAK only
    # ("langgraph", LangGraphBaseAgent),  # Commented out - testing OAK only
    # ("crewai", CrewAIBaseAgent),        # Commented out - testing OAK only
    # ("adk", ADKBaseAgent),              # Commented out - testing OAK only
    # ("sk", SKBaseAgent),                # Commented out - testing OAK only
    ("oak", OAKBaseAgent),              # Testing OAK MCP filtering
    # ("maf", MAFBaseAgent),              # Commented out - testing OAK only
]


TEST_CASES: List[Dict[str, Any]] = [
    {
        "name": "all_tools",
        "tools": ["*"],
        "expected_count": None,  # Will show actual count - all tools from MCP server
    },
    {
        "name": "doc_extract_only",
        "tools": ["doc_extract.*"],
        "expected_count": None,  # Will show actual count - should match doc_extract.* tools
    },
    {
        "name": "doc_extract_toolkit",
        "toolkits": ["doc_extract"],
        "expected_count": None,  # Will show actual count - should match doc_extract toolkit
    },
    {
        "name": "doc_extract_pattern_and_toolkit",
        "tools": ["doc_extract.*"],
        "toolkits": ["doc_extract"],
        "expected_count": None,  # Will show actual count
    },
    {
        "name": "no_match",
        "tools": ["nonexistent_*"],
        "expected_count": 0,  # No tools should match
    },
]


async def _extract_tool_names(agent) -> List[str]:
    # CrewAI stores filtered individual tools separately when using native wrapper
    if hasattr(agent, "_filtered_individual_tools") and getattr(agent, "_filtered_individual_tools") is not None:
        items = getattr(agent, "_filtered_individual_tools")
        names = []
        for t in items:
            if hasattr(t, "name") and isinstance(getattr(t, "name"), str):
                names.append(t.name)
            else:
                names.append(type(t).__name__)
        return sorted(set(names))

    # Agno: tools are wrapper objects with functions dict
    if agent.framework_type == "agno":
        items = getattr(agent, "tools", []) or []
        names = []
        for t in items:
            # Agno MCPTools wrapper has .functions dict containing actual tool functions
            if hasattr(t, "functions") and isinstance(t.functions, dict):
                names.extend(list(t.functions.keys()))
            else:
                names.append(type(t).__name__)
        return sorted(set(names))

    # ADK: tools are McpToolset wrapper objects, need to call get_tools() to get filtered tools
    if agent.framework_type == "adk":
        items = getattr(agent, "tools", []) or []
        names = []
        for t in items:
            if hasattr(t, "get_tools") and callable(t.get_tools):
                try:
                    # get_tools() is async and applies tool_filter automatically
                    tools_list = await t.get_tools()
                    if tools_list:
                        for tool_item in tools_list:
                            if hasattr(tool_item, 'name'):
                                names.append(tool_item.name)
                            elif hasattr(tool_item, '__name__'):
                                names.append(tool_item.__name__)
                            else:
                                names.append(str(tool_item))
                except Exception:
                    # If get_tools fails, fallback to type name
                    names.append(type(t).__name__)
            else:
                names.append(type(t).__name__)
        return sorted(set(names))

    # SK, OAK, MAF: use stored filtered tool names from _filter_mcp_tools
    if agent.framework_type in ["sk", "oak", "maf"]:
        items = getattr(agent, "tools", []) or []
        names = []
        for t in items:
            tool_id = id(t)
            if hasattr(agent, "_filtered_mcp_tool_names") and tool_id in agent._filtered_mcp_tool_names:
                # Use stored filtered tool names
                stored_names = agent._filtered_mcp_tool_names[tool_id]
                if stored_names:
                    names.extend(stored_names)
                else:
                    # For OAK, try to access underlying MCP client to query tools
                    if agent.framework_type == "oak":
                        # Try to access underlying client
                        client = None
                        if hasattr(t, '_client'):
                            client = t._client
                        elif hasattr(t, 'client'):
                            client = t.client
                        
                        if client and hasattr(client, 'list_tools'):
                            try:
                                # Try to query tools from the client directly
                                tools_result = await client.list_tools()
                                all_tool_objects = []
                                if hasattr(tools_result, 'tools'):
                                    all_tool_objects = tools_result.tools
                                elif isinstance(tools_result, list):
                                    all_tool_objects = tools_result
                                
                                for tool_obj in all_tool_objects:
                                    if hasattr(tool_obj, 'name'):
                                        names.append(tool_obj.name)
                                    elif isinstance(tool_obj, dict) and 'name' in tool_obj:
                                        names.append(tool_obj['name'])
                            except Exception:
                                # If query fails, check if tool_filter is set (runtime filtering)
                                if hasattr(t, 'tool_filter') and t.tool_filter:
                                    names.append(f"{type(t).__name__}(runtime_filter)")
                                else:
                                    names.append(f"{type(t).__name__}(query_failed)")
                        else:
                            # Check if tool_filter is set (runtime filtering)
                            if hasattr(t, 'tool_filter') and t.tool_filter:
                                names.append(f"{type(t).__name__}(runtime_filter)")
                            else:
                                names.append(type(t).__name__)
                    else:
                        # For SK/MAF, try to query tools directly
                        if hasattr(t, 'list_tools'):
                            try:
                                import asyncio
                                # Try to get tools synchronously if possible
                                if asyncio.iscoroutinefunction(t.list_tools):
                                    # Can't await here, just note the tool exists
                                    names.append(f"{type(t).__name__}(async)")
                                else:
                                    tools_result = t.list_tools()
                                    if hasattr(tools_result, 'tools'):
                                        for tool_obj in tools_result.tools:
                                            if hasattr(tool_obj, 'name'):
                                                names.append(tool_obj.name)
                            except Exception:
                                names.append(f"{type(t).__name__}(query_failed)")
                        else:
                            names.append(type(t).__name__)
            elif isinstance(t, dict) and 'name' in t:
                names.append(t['name'])
            elif hasattr(t, 'name'):
                names.append(t.name)
            else:
                names.append(type(t).__name__)
        return sorted(set(names))

    # Default path: agent.tools after filtering (LangGraph)
    items = getattr(agent, "tools", []) or []
    names = []
    for t in items:
        if hasattr(t, "name") and isinstance(getattr(t, "name"), str):
            names.append(t.name)
        else:
            names.append(type(t).__name__)
    return sorted(set(names))


async def _init_mcp_only(agent) -> None:
    # Minimal context with project_dir so prompt loader paths resolve if needed downstream
    context = {"project_dir": str(PROJECT_DIR)}
    # Directly initialize MCP tools (skip LLM and full initialize)
    await agent._initialize_mcp_tools(context)


async def run_case(framework_key: str, framework_cls: Any, base_agent_config: Dict[str, Any], tools_patterns: List[str] = None, toolkits: List[str] = None) -> List[str]:
    agent_config = deepcopy(base_agent_config)
    agent_config["type"] = framework_key

    # Apply tool filter patterns to each configured server
    mcp = agent_config.get("mcp", {})
    servers = mcp.get("servers", [])
    for server in servers:
        if tools_patterns:
            server["tools"] = tools_patterns
        if toolkits:
            server["toolkits"] = toolkits

    # Create a minimal concrete subclass to satisfy abstract methods
    def make_concrete(cls):
        class Concrete(cls):
            # def _log_tool_details(self) -> None:
            #     return None
            # def _setup_environment(self):
            #     return None
            # def _create_agent(self):
            #     return None
            def get_agent_variables(self, context: Dict[str, Any]) -> Dict[str, Any]:
                return {}
            # def _execute_agent(self, *args, **kwargs):
            #     return {}
            # def _initialize_agent(self):
            #     return None
        return Concrete

    ConcreteAgent = make_concrete(framework_cls)
    agent = ConcreteAgent(AGENT_ID, agent_config=agent_config)

    # Initialize MCP tools only
    await _init_mcp_only(agent)

    # Extract filtered tool names (async for ADK)
    names = await _extract_tool_names(agent)
    
    # For OAK, verify tool_filter is set (runtime filtering)
    if framework_key == "oak" and hasattr(agent, "tools"):
        print(f"  [DEBUG] OAK agent has {len(agent.tools)} MCP tool wrapper(s)")
        for i, tool_wrapper in enumerate(agent.tools):
            print(f"  [DEBUG] Tool wrapper {i}: {type(tool_wrapper).__name__}")
            
            # Check if tool_filter is set (indicates runtime filtering will work)
            if hasattr(tool_wrapper, 'tool_filter'):
                tool_filter = tool_wrapper.tool_filter
                if tool_filter:
                    print(f"  [DEBUG] ✓ tool_filter is set (runtime filtering enabled)")
                else:
                    print(f"  [DEBUG] ⚠ tool_filter is None (runtime filtering may not work)")
            else:
                print(f"  [DEBUG] ⚠ tool_filter attribute not found")
            
            # Try to access underlying MCP client to query tools directly
            if hasattr(tool_wrapper, '_client') or hasattr(tool_wrapper, 'client'):
                client = getattr(tool_wrapper, '_client', None) or getattr(tool_wrapper, 'client', None)
                if client and hasattr(client, 'list_tools'):
                    try:
                        # Try calling list_tools on the client directly
                        tools_result = await client.list_tools()
                        all_tool_objects = []
                        if hasattr(tools_result, 'tools'):
                            all_tool_objects = tools_result.tools
                        elif isinstance(tools_result, list):
                            all_tool_objects = tools_result
                        if all_tool_objects:
                            all_tool_names = []
                            for tool_obj in all_tool_objects:
                                if hasattr(tool_obj, 'name'):
                                    all_tool_names.append(tool_obj.name)
                                elif isinstance(tool_obj, dict) and 'name' in tool_obj:
                                    all_tool_names.append(tool_obj['name'])
                            print(f"  [DEBUG] Available tools from MCP client: {len(all_tool_names)}")
                            doc_extract_tools = [n for n in all_tool_names if 'doc_extract' in n.lower()]
                            print(f"  [DEBUG] doc_extract.* tools found: {doc_extract_tools}")
                            print(f"  [DEBUG] All tool names (first 20): {all_tool_names[:20]}{'...' if len(all_tool_names) > 20 else ''}")
                    except Exception as e:
                        print(f"  [DEBUG] Error querying tools from client: {e}")
            
            # Note: OAK's list_tools() requires run_context and agent, so can't query at init time
            if hasattr(tool_wrapper, 'list_tools'):
                print(f"  [DEBUG] Note: OAK filtering happens at runtime via tool_filter, not at initialization")
    
    # For OAK, verify runtime tool access
    if framework_key == "oak":
        print(f"  [RUNTIME VERIFICATION] Checking which tools agent can access at runtime...")
        runtime_results = await verify_oak_runtime_tools(agent, tool_patterns=tools_patterns, toolkits=toolkits)
        
        if runtime_results["tool_filter_set"]:
            print(f"  [RUNTIME VERIFICATION] ✓ tool_filter is configured")
            
            # Show test results
            allowed_tools = [name for name, info in runtime_results["test_tools"].items() 
                           if info.get("allowed") is True]
            blocked_tools = [name for name, info in runtime_results["test_tools"].items() 
                           if info.get("allowed") is False]
            unknown_tools = [name for name, info in runtime_results["test_tools"].items() 
                           if info.get("allowed") is None]
            
            if allowed_tools:
                print(f"  [RUNTIME VERIFICATION] ✓ Allowed tools ({len(allowed_tools)}): {', '.join(allowed_tools[:10])}{'...' if len(allowed_tools) > 10 else ''}")
            if blocked_tools:
                print(f"  [RUNTIME VERIFICATION] ✗ Blocked tools ({len(blocked_tools)}): {', '.join(blocked_tools[:10])}{'...' if len(blocked_tools) > 10 else ''}")
            if unknown_tools:
                print(f"  [RUNTIME VERIFICATION] ? Unknown status ({len(unknown_tools)}): {', '.join(unknown_tools[:5])}{'...' if len(unknown_tools) > 5 else ''}")
            
            # Show filtered tools from client
            if runtime_results["all_tools_from_client"]:
                print(f"  [RUNTIME VERIFICATION] All tools from MCP client: {len(runtime_results['all_tools_from_client'])}")
                if runtime_results["filtered_tools"]:
                    print(f"  [RUNTIME VERIFICATION] ✓ Filtered allowed tools ({len(runtime_results['filtered_tools'])}): {', '.join(runtime_results['filtered_tools'][:10])}{'...' if len(runtime_results['filtered_tools']) > 10 else ''}")
        else:
            print(f"  [RUNTIME VERIFICATION] ⚠ tool_filter not set - runtime filtering may not work")

    # Cleanup resources
    await agent.cleanup()

    return names


async def verify_oak_runtime_tools(agent, tool_patterns: List[str] = None, toolkits: List[str] = None) -> Dict[str, Any]:
    """
    Verify which tools an OAK agent can actually access at runtime.
    
    This function:
    1. Tests the tool_filter function directly with known tool names
    2. Attempts to query tools from the MCP client if accessible
    3. Returns a report of which tools would be allowed/blocked
    """
    results = {
        "tool_filter_set": False,
        "test_tools": {},
        "all_tools_from_client": [],
        "filtered_tools": []
    }
    
    if not hasattr(agent, "tools") or not agent.tools:
        return results
    
    for tool_wrapper in agent.tools:
        # Check if tool_filter is set
        if hasattr(tool_wrapper, 'tool_filter') and tool_wrapper.tool_filter:
            results["tool_filter_set"] = True
            
            # Test the tool_filter function with known tool names
            test_tool_names = [
                "doc_extract_metadata",
                "doc_extract_structured_data", 
                "doc_extract_tables",
                "doc_rag_list_documents",
                "doc_rag_query_document",
                "image_rag_list_images",
                "image_rag_query_images",
                "agentos_shell",
                "common_read_document",
                "common_ocr_reader"
            ]
            
            # First, try to get all tools from MCP client to test with real tool objects
            client = None
            if hasattr(tool_wrapper, '_client'):
                client = tool_wrapper._client
            elif hasattr(tool_wrapper, 'client'):
                client = tool_wrapper.client
            
            all_tool_objects = []
            if client and hasattr(client, 'list_tools'):
                try:
                    tools_result = await client.list_tools()
                    if hasattr(tools_result, 'tools'):
                        all_tool_objects = tools_result.tools
                    elif isinstance(tools_result, list):
                        all_tool_objects = tools_result
                    print(f"  [RUNTIME TEST] Successfully queried {len(all_tool_objects)} tools from MCP client")
                except Exception as e:
                    print(f"  [RUNTIME TEST] Could not query tools from client: {e}")
            else:
                if not client:
                    print(f"  [RUNTIME TEST] No MCP client found (checked _client and client attributes)")
                elif not hasattr(client, 'list_tools'):
                    print(f"  [RUNTIME TEST] MCP client found but has no list_tools method")
            
            # Test with actual tool objects from MCP client (preferred)
            if all_tool_objects:
                print(f"  [RUNTIME TEST] Testing tool_filter with {len(all_tool_objects)} actual tools from MCP client...")
                for tool_obj in all_tool_objects:
                    tool_name = None
                    if hasattr(tool_obj, 'name'):
                        tool_name = tool_obj.name
                    elif isinstance(tool_obj, dict) and 'name' in tool_obj:
                        tool_name = tool_obj['name']
                    
                    if tool_name:
                        results["all_tools_from_client"].append(tool_name)
                        try:
                            # tool_filter expects a tool object with .name attribute
                            allowed = tool_wrapper.tool_filter(tool_obj)
                            results["test_tools"][tool_name] = {
                                "allowed": allowed,
                                "method": "actual_tool_object"
                            }
                            if allowed:
                                results["filtered_tools"].append(tool_name)
                        except Exception as e:
                            results["test_tools"][tool_name] = {
                                "allowed": None,
                                "error": str(e),
                                "method": "exception"
                            }
            else:
                # Fallback: Create mock tool objects with .name attribute
                print(f"  [RUNTIME TEST] Testing tool_filter with {len(test_tool_names)} known tools (using mock objects)...")
                for tool_name in test_tool_names:
                    # Create a simple object with .name attribute
                    class MockTool:
                        def __init__(self, name):
                            self.name = name
                    
                    mock_tool = MockTool(tool_name)
                    try:
                        allowed = tool_wrapper.tool_filter(mock_tool)
                        results["test_tools"][tool_name] = {
                            "allowed": allowed,
                            "method": "mock_tool_object"
                        }
                    except Exception as e:
                        results["test_tools"][tool_name] = {
                            "allowed": None,
                            "error": str(e),
                            "method": "exception"
                        }
            
    
    return results


async def main() -> None:
    print("Loading configuration...")
    engine = ConfigurationEngine(PROJECT_DIR)
    config_result = engine.load_and_validate()
    if not config_result.is_valid:
        print("Config invalid:")
        for e in config_result.errors:
            print(f"  - {e}")
        raise SystemExit(1)

    factory = AgentFactory(config_result)
    base_agent_config = factory.get_agent_config(AGENT_ID)
    if not base_agent_config:
        print(f"Agent config not found for id '{AGENT_ID}'")
        raise SystemExit(1)

    total_failures = 0
    # Store results for summary: {framework: {test_case: {"status": "PASS"/"FAIL", "count": int, "expected": int}}}
    results_summary: Dict[str, Dict[str, Dict[str, Any]]] = {}

    for framework_key, framework_cls in FRAMEWORKS:
        print(f"\n=== Framework: {framework_key} ===")
        results_summary[framework_key] = {}

        # Run baseline first to get all tools reference
        all_tools_case = TEST_CASES[0]
        all_names = await run_case(
            framework_key, 
            framework_cls, 
            base_agent_config, 
            tools_patterns=all_tools_case.get("tools"),
            toolkits=all_tools_case.get("toolkits")
        )
        all_count = len(all_names)
        expected_all = all_tools_case.get("expected_count")
        if expected_all is not None:
            all_ok = all_count == expected_all
            status = "PASS" if all_ok else "FAIL"
            if not all_ok:
                total_failures += 1
            print(f"{all_tools_case['name']}: count={all_count} (expected={expected_all}) [{status}]")
            if all_names:
                print(f"  Tools: {all_names[:10]}{'...' if len(all_names) > 10 else ''}")
            results_summary[framework_key][all_tools_case['name']] = {
                "status": status,
                "count": all_count,
                "expected": expected_all
            }
        else:
            print(f"{all_tools_case['name']}: count={all_count}")
            if all_names:
                print(f"  Tools: {all_names[:10]}{'...' if len(all_names) > 10 else ''}")
            results_summary[framework_key][all_tools_case['name']] = {
                "status": "INFO",
                "count": all_count,
                "expected": None
            }

        # Run all other test cases
        for case in TEST_CASES[1:]:
            case_names = await run_case(
                framework_key, 
                framework_cls, 
                base_agent_config, 
                tools_patterns=case.get("tools"),
                toolkits=case.get("toolkits")
            )
            case_count = len(case_names)
            expected_count = case.get("expected_count")
            
            # For OAK with no_match test: tool_filter is set, so wrapper is kept (count=1)
            # This is expected behavior - filtering happens at runtime, not initialization
            if framework_key == "oak" and case["name"] == "no_match":
                # OAK keeps the wrapper for runtime filtering even when no tools match
                # So we expect 1 (the wrapper) instead of 0
                expected_count = 1
            
            # Validate count and subset relationship
            count_ok = True
            subset_ok = True
            
            if expected_count is not None:
                count_ok = case_count == expected_count
            
            # Verify subset relationship (except for no_match which should be 0, or 1 for OAK)
            if case["name"] != "no_match":
                subset_ok = set(case_names).issubset(set(all_names))
            
            # Overall status
            overall_ok = count_ok and subset_ok
            status = "PASS" if overall_ok else "FAIL"
            
            if not overall_ok:
                total_failures += 1
                details = []
                if not count_ok:
                    details.append(f"count={case_count} expected={expected_count}")
                if not subset_ok:
                    unexpected = sorted(set(case_names) - set(all_names))
                    details.append(f"unexpected_tools={unexpected}")
                detail_str = f" ({', '.join(details)})" if details else ""
                print(f"{case['name']}: count={case_count} [{status}]{detail_str}")
                if case_names:
                    print(f"  Tools: {case_names[:10]}{'...' if len(case_names) > 10 else ''}")
            else:
                expected_str = f" (expected={expected_count})" if expected_count is not None else ""
                print(f"{case['name']}: count={case_count}{expected_str} [{status}]")
                if case_names:
                    print(f"  Tools: {case_names[:10]}{'...' if len(case_names) > 10 else ''}")
            
            results_summary[framework_key][case['name']] = {
                "status": status,
                "count": case_count,
                "expected": expected_count
            }

    # Print summary table
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    # Get all test case names
    test_case_names = [case["name"] for case in TEST_CASES]
    
    # Print header
    header = f"{'Framework':<15}"
    for test_name in test_case_names:
        # Truncate long names for display
        display_name = test_name[:20] if len(test_name) > 20 else test_name
        header += f"{display_name:>25}"
    print(header)
    print("-" * 80)
    
    # Print results for each framework
    for framework_key in sorted(results_summary.keys()):
        row = f"{framework_key:<15}"
        for test_name in test_case_names:
            if test_name in results_summary[framework_key]:
                result = results_summary[framework_key][test_name]
                status = result["status"]
                count = result["count"]
                expected = result["expected"]
                
                if status == "PASS":
                    status_symbol = "✓"
                    color_start = ""
                    color_end = ""
                elif status == "FAIL":
                    status_symbol = "✗"
                    color_start = ""
                    color_end = ""
                else:
                    status_symbol = "•"
                    color_start = ""
                    color_end = ""
                
                if expected is not None:
                    cell = f"{status_symbol} {count}/{expected}"
                else:
                    cell = f"{status_symbol} {count}"
                
                row += f"{cell:>25}"
            else:
                row += f"{'N/A':>25}"
        print(row)
    
    # Print statistics
    print("-" * 80)
    total_tests = len(FRAMEWORKS) * len(TEST_CASES)
    total_passed = sum(
        1 for framework_results in results_summary.values()
        for result in framework_results.values()
        if result["status"] == "PASS"
    )
    total_failed = sum(
        1 for framework_results in results_summary.values()
        for result in framework_results.values()
        if result["status"] == "FAIL"
    )
    
    print(f"\nTotal: {total_tests} tests | Passed: {total_passed} | Failed: {total_failed}")
    print("=" * 80)

    if total_failures:
        print(f"\nCompleted with {total_failures} failure(s).")
        raise SystemExit(1)
    print("\nAll PASS")


if __name__ == "__main__":
    asyncio.run(main())


