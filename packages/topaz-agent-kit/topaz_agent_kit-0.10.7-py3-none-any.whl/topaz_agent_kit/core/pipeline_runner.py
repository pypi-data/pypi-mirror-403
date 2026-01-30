import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.frameworks.framework_config_manager import FrameworkConfigManager
from topaz_agent_kit.core.configuration_engine import ConfigurationResult
from topaz_agent_kit.core.exceptions import PipelineError, PipelineStoppedByUser, HITLQueuedForAsync
from topaz_agent_kit.core.case_manager import CaseManager
from topaz_agent_kit.transport.agent_bus import AgentBus
from topaz_agent_kit.core.output_manager import OutputManager
from topaz_agent_kit.core.agent_runner import AgentRunner
from topaz_agent_kit.core.runner_compiler import RunnerCompiler
from topaz_agent_kit.utils.json_utils import JSONUtils


class PipelineRunner:
    """Config-driven DAG executor supporting sequential, parallel, optional nodes, and joins."""

    def __init__(
        self,
        pattern_config: Dict[str, Any],
        config_result: Optional[ConfigurationResult] = None,
    ) -> None:
        """Initialize PipelineRunner with pattern configuration and optional configuration result."""
        self.pattern_config = pattern_config
        self.config_result = config_result

        # Initialize logger
        self.logger = Logger("PipelineRunner")

        # Store pipeline and UI configuration for test access
        if config_result:
            self.pipeline_config = config_result.pipeline_config
            self.ui_config = config_result.ui_config
        else:
            self.pipeline_config = {}
            self.ui_config = {}

        # Initialize agent storage
        self.agents = {}

        # Initialize framework configuration manager
        self.framework_config_manager = FrameworkConfigManager()

        # Initialize output manager for intermediate and final outputs
        self.output_manager = OutputManager(self.pipeline_config)

        # Initialize agent bus for unified transport
        # Add project_dir and pipeline_dir to config for agent config file loading
        agent_bus_config = self.pipeline_config.copy()
        if config_result and hasattr(config_result, "project_dir"):
            agent_bus_config["project_dir"] = config_result.project_dir

        self.agent_bus = AgentBus(
            agents_by_id={},  # Will be populated with built agents
            config=agent_bus_config,
            emitter=None,  # Will be set in run() method when emitter is available
        )

        # Initialize agent runner for agent execution (share agent_bus and pipeline structure)
        self.agent_runner = AgentRunner(
            config_result, self.agent_bus, self._get_pipeline_structure
        )

        # Initialize runner compiler after agent_runner is created
        self.runner_compiler = RunnerCompiler(
            agent_runner=self.agent_runner,
            logger=self.logger,
            populate_upstream_context_func=None,  # Will be set by caller
            output_manager=self.output_manager,
            config_result=config_result,
        )
        # Inject pipeline_config into runner_compiler for global settings
        self.runner_compiler.pipeline_config = self.pipeline_config

        # Debug: Log orchestrator config if present
        if self.pipeline_config and "orchestrator" in self.pipeline_config:
            self.logger.info(
                "Found orchestrator config: {}", self.pipeline_config["orchestrator"]
            )
        else:
            self.logger.warning("No orchestrator config found in pipeline_config")
            self.logger.info(
                "Pipeline config keys: {}", list(self.pipeline_config.keys())
            )

        # Debug: Log what we're passing to agent bus
        self.logger.debug(
            "Agent bus config keys: {}",
            list(self.pipeline_config.keys()) if self.pipeline_config else "None",
        )
        self.logger.debug("Pattern structure: {}", self.pattern_config)
        self.logger.debug(
            "Agent bus config agents count: {}",
            len(self.pipeline_config.get("agents", [])) if self.pipeline_config else 0,
        )
        self.logger.debug(
            "Agent bus pipeline_dir: {}", agent_bus_config.get("pipeline_dir")
        )
        self.logger.debug(
            "Agent bus project_dir: {}", agent_bus_config.get("project_dir")
        )

    def _get_agent_info_from_config(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get agent information from configuration"""
        try:
            self.logger.debug("🔍 Getting agent info for: {}", node_id)

            # Try to get agent info from agent factory if available
            if hasattr(self, "agent_runner") and self.agent_runner:
                # Create context with agent_factory if available
                context = {}
                if (
                    hasattr(self.agent_runner, "config_result")
                    and self.agent_runner.config_result
                ):
                    # Get agent factory from config_result
                    from topaz_agent_kit.agents.agent_factory import AgentFactory

                    agent_factory = AgentFactory(self.agent_runner.config_result)
                    context["agent_factory"] = agent_factory

                agent_info = self.agent_runner.get_agent_info(node_id, context)
                self.logger.debug("🔍 Agent info from agent_runner: {}", agent_info)
                if agent_info:
                    return agent_info

            # Fallback: try to get from config_result directly
            if hasattr(self, "config_result") and self.config_result:
                # Look for agent config in the pipeline config
                agents = self.config_result.pipeline_config.get("agents", [])
                self.logger.debug(
                    "🔍 Available agents in config: {}",
                    [a.get("id") if isinstance(a, dict) else str(a) for a in agents],
                )
                for agent in agents:
                    if isinstance(agent, dict) and agent.get("id") == node_id:
                        agent_info = {
                            "id": node_id,
                            "run_mode": agent.get("run_mode", "local"),
                            "type": agent.get("type"),
                            "name": agent.get("name"),
                        }
                        self.logger.debug(
                            "🔍 Agent info from config_result: {}", agent_info
                        )
                        return agent_info

            self.logger.warning("🔍 No agent info found for: {}", node_id)
            return None

        except Exception as e:
            self.logger.warning("Failed to get agent info for {}: {}", node_id, e)
            return None

    def _get_pipeline_structure(self) -> Dict[str, Any]:
        """Extract pipeline structure from pattern-only configuration"""
        # Get agent IDs from the pipeline config (not from pattern)
        nodes = self.pipeline_config.get("nodes", [])

        # Extract node IDs from the nodes structure
        node_ids = []
        for node in nodes:
            if isinstance(node, dict) and "id" in node:
                node_ids.append(node["id"])
            elif isinstance(node, str):
                node_ids.append(node)

        return {"agents": node_ids, "pattern": self.pattern_config}

    def _initialize_upstream_context(self, context: Dict[str, Any]) -> None:
        """
        Initialize upstream context with user input as a pseudo-agent.
        This makes user input available to all agents through the standard upstream mechanism.
        """
        try:
            # Get user input from context
            user_text = context.get("user_text", "")

            if not user_text:
                self.logger.warning(
                    "No user_text found in context - skipping user_input initialization"
                )
                return

            # Initialize upstream context if it doesn't exist
            if "upstream" not in context:
                context["upstream"] = {}

            # Add user_input as a pseudo-agent in upstream context
            context["upstream"]["user_input"] = {
                "result": user_text,
                "parsed": {
                    "user_text": user_text,
                    # "question": user_text,
                    # "user_message": user_text,
                    # "input": user_text,
                    # "input_text": user_text,
                    # "input_message": user_text,
                    # "query": user_text,
                    # "query_text": user_text,
                    # "message": user_text,
                    # "text": user_text,
                    # "user_input": user_text
                },
            }

            self.logger.debug(
                "Initialized user_input in upstream context: {} chars", len(user_text)
            )

        except Exception as e:
            self.logger.error(
                "Failed to initialize user_input in upstream context: {}", e
            )
            # Don't fail the pipeline for user input initialization issues

    def _populate_upstream_context(
        self, node_id: str, result: Any, context: Dict[str, Any]
    ) -> None:
        """
        Populate the upstream context so downstream agents can access upstream agent results.

        This method stores agent results in the context structure that generated agents
        expect for their _get_upstream_variable methods to work properly.

        Args:
            node_id: ID of the agent that just executed
            result: Result from the agent execution
            context: Pipeline execution context
        """
        try:
            # Initialize upstream context if it doesn't exist
            if "upstream" not in context:
                context["upstream"] = {}

            # Extract the actual result content (handle different result types)
            # NOTE: AgentOutputParser.parse_agent_output() already parses outputs, so result should be a dict
            # However, if JSON parsing failed, it may have returned {"content": "<json string>"}
            if result is None:
                self.logger.warning("Agent {} returned None result", node_id)
                result_content = {}
                parsed_content = {}
            elif hasattr(result, "content"):
                # Handle objects with .content attribute (like LLM responses)
                result_content = result.content
                # Parse if it's a string
                if isinstance(result_content, str):
                    parsed_content = JSONUtils.parse_json_from_text(result_content, expect_json=False)
                else:
                    parsed_content = result_content
            elif isinstance(result, dict):
                # Check if this is a fallback from failed JSON parsing: {"content": "<json string>"}
                # If so, parse the content string
                if "content" in result and isinstance(result.get("content"), str) and len(result) == 1:
                    # This is likely a JSON parse failure fallback - try parsing the content
                    content_str = result["content"]
                    parsed_content = JSONUtils.parse_json_from_text(content_str, expect_json=False)
                    # If parsing succeeded, use the parsed dict; otherwise use original
                    # Check if we got a proper dict (not the {"content": ...} fallback)
                    if isinstance(parsed_content, dict) and (len(parsed_content) > 1 or "content" not in parsed_content):
                        # Parsing succeeded - use the parsed dict
                        result_content = parsed_content
                    else:
                        # Parsing failed again - keep original structure
                        result_content = result["content"]
                        parsed_content = result
                elif "content" in result and result.get("content"):
                    # SDK-style 'content' field (already parsed or dict)
                    result_content = result["content"]
                    parsed_content = result_content
                # Handle execute_agent structured responses (MVP-6.0 format)
                elif "result" in result and "agent" in result:
                    result_content = result["result"]
                    if isinstance(result_content, str):
                        parsed_content = JSONUtils.parse_json_from_text(result_content, expect_json=False)
                    else:
                        parsed_content = result_content
                    self.logger.debug(
                        "Extracted agent result content from structured response: {} chars",
                        len(str(result_content)),
                    )
                else:
                    # Regular dictionary result (already parsed by AgentOutputParser)
                    result_content = result
                    parsed_content = result
            else:
                # Handle string or other types
                result_content = str(result)
                # Parse string as JSON if possible
                parsed_content = JSONUtils.parse_json_from_text(result_content, expect_json=False)

            self.logger.info(
                "Using normalized agent output: {} (keys: {})",
                node_id,
                list(parsed_content.keys())
                if isinstance(parsed_content, dict)
                else "n/a",
            )
            # Log what we're about to store for observability
            self.logger.info(
                "Upstream store [{}]: type(result)={}, parsed_keys={}",
                node_id,
                type(result_content).__name__,
                list(parsed_content.keys())
                if isinstance(parsed_content, dict)
                else "n/a",
            )
            if node_id == "planner" and isinstance(parsed_content, dict):
                missing = [
                    k for k in ("expression", "steps") if k not in parsed_content
                ]
                if missing:
                    self.logger.info("Planner parsed output missing keys: {}", missing)

            # Remove content wrapping just before storing in context
            # This ensures we don't store nested {"content": {...}} structures
            def unwrap_content(data: Any) -> Any:
                """Recursively unwrap content wrapping like {"content": {...}}."""
                if isinstance(data, dict):
                    # Check if this is a content wrapper (only has "content" key)
                    if len(data) == 1 and "content" in data:
                        content_value = data["content"]
                        # Recursively unwrap nested content wrappers
                        if isinstance(content_value, dict) and len(content_value) == 1 and "content" in content_value:
                            return unwrap_content(content_value)
                        # Return the unwrapped content
                        return content_value
                    # Not a content wrapper, return as-is
                    return data
                # Not a dict, return as-is
                return data
            
            # Unwrap content from both result_content and parsed_content
            unwrapped_result = unwrap_content(result_content)
            unwrapped_parsed = unwrap_content(parsed_content)
            
            # CRITICAL: Ensure parsed_content is always a dict for downstream agents to access fields
            # If parsing failed and we got a string, try one more time with aggressive parsing
            if isinstance(unwrapped_parsed, str):
                self.logger.warning(
                    "Agent {} output is a string after parsing, attempting aggressive JSON extraction",
                    node_id
                )
                # Try aggressive parsing - this will use balanced JSON extraction
                aggressive_parsed = JSONUtils.parse_json_from_text(unwrapped_parsed, expect_json=False)
                if isinstance(aggressive_parsed, dict) and (len(aggressive_parsed) > 1 or "content" not in aggressive_parsed):
                    # Successfully extracted a dict
                    unwrapped_parsed = aggressive_parsed
                    self.logger.info(
                        "Successfully extracted dict from string output for {} (keys: {})",
                        node_id,
                        list(unwrapped_parsed.keys())
                    )
                else:
                    # Still a string or wrapped in content - this is a critical error
                    self.logger.error(
                        "Failed to parse agent {} output as JSON. Storing as error structure. Raw output: {}",
                        node_id,
                        unwrapped_parsed[:500]
                    )
                    # Store as error structure so downstream agents can at least see there was an error
                    unwrapped_parsed = {
                        "error": f"Failed to parse agent output as JSON. Raw output: {str(unwrapped_parsed)[:200]}...",
                        "raw_output": str(unwrapped_parsed)
                    }
            
            # Final validation: parsed must be a dict
            if not isinstance(unwrapped_parsed, dict):
                self.logger.error(
                    "CRITICAL: Agent {} parsed output is not a dict (type: {}). This will break downstream agents.",
                    node_id,
                    type(unwrapped_parsed).__name__
                )
                unwrapped_parsed = {
                    "error": f"Agent output parsing failed. Expected dict, got {type(unwrapped_parsed).__name__}",
                    "raw_output": str(unwrapped_parsed)
                }
            
            # Store the result in upstream context for pattern-based execution
            # In MVP-6.0, pattern execution handles the flow, so we just store the result
            context["upstream"][node_id] = {
                "result": unwrapped_result,
                "parsed": unwrapped_parsed,
            }

            # 🔎 Debug: Log raw agent output for troubleshooting expression evaluation
            try:
                raw_str = result_content if isinstance(result_content, str) else str(result_content)
                self.logger.output("Raw output [{}]: {} chars", node_id, len(raw_str))
                # For long outputs, log a small head
                self.logger.output("Raw output head [{}]: {}", node_id, raw_str[:500])
            except Exception:
                pass

            self.logger.debug(
                "Updated upstream context for {}: {} chars",
                node_id,
                len(str(result_content)),
            )

        except Exception as e:
            self.logger.error(
                "Failed to populate upstream context for {}: {}", node_id, e
            )
            # Don't fail the pipeline for context population issues

    # NOTE: Agent execution methods moved to AgentRunner class

    async def run(self, context: Dict[str, Any]) -> Any:
        """
        Execute the pipeline using pattern-only runners (sequential, parallel, loop).

        Args:
            context: Execution context containing user_text, intent, session, etc.

        Returns:
            Pipeline execution result or error response
        """

        # Attach emitter to agent bus if provided
        emitter = context.get("emitter")
        if emitter:
            self.agent_bus._emitter = emitter

            # Initialize upstream context for user input once
            self._initialize_upstream_context(context)

        # Compile and run the pattern
        # Use the already initialized runner_compiler (with pipeline_config)
        self.runner_compiler.populate_upstream_context_func = (
            self._populate_upstream_context
        )
        self.runner_compiler.gate_lookup_func = self._get_gate_config
        self.runner_compiler.pipeline_runner_gate_handler_func = (
            self._handle_gate_execution
        )

        composed = self.runner_compiler.compile(self.pattern_config, is_top_level=True)
        
        pattern_results = await composed.run(context)

        # Process final outputs if configured
        # Skip during resume scenarios where only partial pipeline execution occurs
        final_output = None
        try:
            is_resumed = context.get("_resume", {}).get("is_resumed", False)
            if emitter and self.output_manager.has_final_output() and not is_resumed:
                final_output = self.output_manager.process_final_output(
                    pattern_results, emitter
                )
                if final_output:
                    self.logger.info(
                        "Processed final output: {} chars", len(final_output)
                    )
            elif is_resumed and self.output_manager.has_final_output():
                self.logger.debug(
                    "Skipping final output processing during resume (partial pipeline execution)"
                )
        except Exception as e:
            self.logger.warning("Failed to process final output: {}", e)

        # Include final_output in pattern_results if available
        if final_output:
            if not isinstance(pattern_results, dict):
                pattern_results = {}
            pattern_results["final_output"] = final_output

        # Create case for completed sequential pipelines (if async HITL enabled and no case created yet)
        # This handles straight-through completions (no HITL gates encountered)
        # 
        # IMPORTANT: Skip case creation if we're in a loop context, as individual items should have
        # created their own cases (via HITL gates or LoopRunner._save_iteration_case). The orchestrator
        # will handle creating a summary case for the overall pipeline run if needed.
        # 
        # CRITICAL: Skip case creation if pipeline execution failed (check for errors in pattern_results)
        case_manager = context.get("case_manager")
        if case_manager and not context.get("case_id"):
            # Check if pipeline execution failed (error in pattern_results or upstream context)
            pipeline_failed = False
            if isinstance(pattern_results, dict):
                # Check for error field or _iteration_failed flag in pattern_results
                if pattern_results.get("error") or pattern_results.get("_iteration_failed"):
                    pipeline_failed = True
                    self.logger.info(
                        "Skipping pipeline-level case creation: pipeline execution failed with error: {}",
                        pattern_results.get("error") or "iteration failed"
                    )
                # Check upstream context for agent errors
                upstream = context.get("upstream", {})
                for agent_id, agent_result in upstream.items():
                    if isinstance(agent_result, dict):
                        if agent_result.get("error"):
                            pipeline_failed = True
                            self.logger.info(
                                "Skipping pipeline-level case creation: agent {} failed with error: {}",
                                agent_id, agent_result.get("error")
                            )
                            break
                    elif isinstance(agent_result, list):
                        # Check accumulated results for errors
                        for result_item in agent_result:
                            if isinstance(result_item, dict):
                                parsed = result_item.get("parsed", {})
                                if parsed.get("error"):
                                    pipeline_failed = True
                                    self.logger.info(
                                        "Skipping pipeline-level case creation: agent {} failed with error: {}",
                                        agent_id, parsed.get("error")
                                    )
                                    break
                        if pipeline_failed:
                            break
            
            if pipeline_failed:
                # Don't create case if pipeline failed
                return pattern_results
            # Check if we're in a loop context (individual items may have created cases)
            case_tracking = context.get("case_tracking") or {}
            completed_key = case_tracking.get("completed", "completed_cases")
            hitl_queued_key = case_tracking.get("hitl_queued", "hitl_queued_cases")
            completed_cases = context.get(completed_key, [])
            hitl_queued_cases = context.get(hitl_queued_key, [])
            
            # Skip case creation if we're in a loop context with individual item cases
            if completed_cases or hitl_queued_cases:
                self.logger.debug(
                    "Skipping pipeline-level case creation in PipelineRunner: loop context detected "
                    "(completed_cases: {}, hitl_queued_cases: {}). "
                    "Individual item cases exist, orchestrator will handle summary case if needed.",
                    len(completed_cases), len(hitl_queued_cases)
                )
            # Skip case creation if loop had no items to process (empty loop)
            elif isinstance(pattern_results, dict) and pattern_results.get("_loop_empty"):
                self.logger.info(
                    "Skipping pipeline-level case creation in PipelineRunner: loop had 0 iterations (no items to process)"
                )
            else:
                # Check if case_management is configured
                case_management = self.pipeline_config.get("case_management", {}) or {}
                if case_management:
                    try:
                        pipeline_id = context.get("pipeline_id") or context.get("pipeline", "unknown")
                        run_id = context.get("run_id", "")
                        session_id = context.get("session_id")
                        case_config = context.get("case_config", {})
                        upstream = context.get("upstream", {})
                        
                        # Detect "empty run" based on statistics in pattern_results / final_output
                        skip_pipeline_case_for_empty_run = False
                        stats_dicts = []
                        if isinstance(pattern_results, dict):
                            stats = pattern_results.get("statistics")
                            if isinstance(stats, dict):
                                stats_dicts.append(stats)
                            final_output_dict = pattern_results.get("final_output")
                            if isinstance(final_output_dict, dict):
                                stats_inner = final_output_dict.get("statistics")
                                if isinstance(stats_inner, dict):
                                    stats_dicts.append(stats_inner)
                        for stats in stats_dicts:
                            numeric_values = [
                                v for v in stats.values()
                                if isinstance(v, (int, float))
                            ]
                            if numeric_values and all(v == 0 for v in numeric_values):
                                skip_pipeline_case_for_empty_run = True
                                self.logger.info(
                                    "Skipping pipeline-level case creation in PipelineRunner for pipeline {} run {} "
                                    "because statistics indicate an empty run (all numeric stats are 0).",
                                    pipeline_id,
                                    run_id,
                                )
                                break

                        if skip_pipeline_case_for_empty_run:
                            # Do not create a pipeline-level straight-through case for empty runs
                            return pattern_results

                        # CRITICAL: For pipeline-level cases created here (straight-through completions),
                        # use UUID-based uniqueness to avoid conflicts with any item-specific IDs that
                        # might be present in the upstream context (e.g., from a previous loop iteration).
                        # This ensures the case ID is unique and doesn't accidentally reuse an item ID.
                        pipeline_case_config = case_config.copy()
                        original_uniqueness = None
                        if "identity" in pipeline_case_config:
                            pipeline_case_config["identity"] = pipeline_case_config["identity"].copy()
                            original_uniqueness = pipeline_case_config["identity"].get("uniqueness", "uuid_suffix")
                            # Override to UUID for pipeline-level cases (not item-level)
                            pipeline_case_config["identity"]["uniqueness"] = "uuid_suffix"
                            if original_uniqueness != "uuid_suffix":
                                self.logger.debug(
                                    "PipelineRunner: Overriding uniqueness from '{}' to 'uuid_suffix' "
                                    "for pipeline-level straight-through case (to avoid conflicts with item-specific IDs)",
                                    original_uniqueness
                                )
                        
                        # Create case with completed status
                        case_id = case_manager.create_case(
                            pipeline_id=pipeline_id,
                            run_id=run_id,
                            upstream=upstream,
                            case_config=pipeline_case_config,
                            session_id=session_id,
                            case_type="straight_through",
                            current_step="completed",
                            initial_status=CaseManager.STATUS_COMPLETED,
                        )
                        
                        if case_id:
                            self.logger.info(
                                "Created completed case {} for pipeline {} (straight-through)",
                                case_id, pipeline_id
                            )
                            context["case_id"] = case_id
                            
                            # Mark case as completed with final_output
                            final_output_for_case = None
                            if isinstance(pattern_results, dict):
                                final_output_for_case = pattern_results
                            elif pattern_results is not None:
                                final_output_for_case = {"result": pattern_results}
                            
                            if final_output_for_case:
                                case_manager.mark_completed(
                                    case_id=case_id,
                                    final_output=final_output_for_case,
                                )
                                self.logger.debug(
                                    "Marked case {} as completed with final_output",
                                    case_id
                                )
                            
                            # Track completed case for summary (if tracking is configured)
                            case_tracking_for_summary = context.get("case_tracking") or {}
                            completed_key_for_summary = case_tracking_for_summary.get("completed", "completed_cases")
                            if completed_key_for_summary not in context:
                                context[completed_key_for_summary] = []
                            context[completed_key_for_summary].append({
                                "case_id": case_id,
                                "status": "completed",
                            })
                    except Exception as e:
                        # Don't fail pipeline if case creation fails
                        self.logger.warning(
                            "Failed to create case for completed pipeline: {}", e
                        )

        return pattern_results

    def _get_gates(self) -> List[Dict[str, Any]]:
        """Get gates configuration from pipeline config"""
        try:
            gates = self.pipeline_config.get("gates", [])
            self.logger.info(
                "Loaded {} gates: {}", len(gates), [g.get("id") for g in gates]
            )
            return gates
        except Exception:
            return []

    def _get_gate_config(self, gate_id: str) -> Optional[Dict[str, Any]]:
        """Look up gate configuration by ID"""
        gates = self.pipeline_config.get("gates", [])
        for gate in gates:
            if gate.get("id") == gate_id:
                return gate
        return None

    def _load_and_render_hitl_description(
        self,
        description: Any,
        context: Dict[str, Any],
        gate_id: str,
        gate_type: str = "approval",
        populated_options: Optional[List] = None,
    ) -> str:
        """
        Load HITL description from jinja file if dict with 'jinja' key, then render with context.
        Used for both sync (hitl_request) and async (hitl_queued) HITL.
        Returns rendered string.
        """
        from pathlib import Path

        description_template = ""
        if isinstance(description, dict) and "jinja" in description:
            try:
                from topaz_agent_kit.utils.prompt_loader import PromptLoader

                project_dir = context.get("project_dir")
                if project_dir:
                    project_dir = Path(project_dir)
                    prompt_loader = PromptLoader(project_dir)
                    loaded = prompt_loader.load_prompt(description)
                    if loaded and isinstance(loaded, str):
                        description_template = loaded
                    elif loaded:
                        description_template = str(loaded)
                else:
                    self.logger.warning(
                        "No project_dir in context, cannot load HITL description from file"
                    )
            except Exception as e:
                self.logger.warning(
                    "Failed to load HITL description from file: {}, using empty string", e
                )
        elif isinstance(description, str):
            description_template = description
        elif description is not None:
            description_template = str(description)

        if not isinstance(description_template, str):
            description_template = str(description_template) if description_template else ""

        if not description_template:
            return f"HITL review required for gate: {gate_id}"

        try:
            from jinja2 import Environment, Undefined

            from topaz_agent_kit.utils.jinja2_filters import register_jinja2_filters

            class SafeUndefined(Undefined):
                def __getattr__(self, name: str) -> Any:
                    return SafeUndefined()

                def __getitem__(self, key: Any) -> Any:
                    return SafeUndefined()

                def __str__(self) -> str:
                    return ""

                def __repr__(self) -> str:
                    return ""

            def get_nested_value(data: Any, path: str, default: Any = None) -> Any:
                if not path or not isinstance(data, dict):
                    return default
                parts = path.split(".")
                value = data
                for field in parts:
                    if isinstance(value, dict) and field in value:
                        value = value[field]
                    else:
                        return default
                return value

            env = Environment(undefined=SafeUndefined, autoescape=False)
            env.filters["nested_get"] = get_nested_value
            register_jinja2_filters(env)
            tmpl = env.from_string(description_template)
            render_context = dict(context)
            upstream = context.get("upstream", {}) if isinstance(context, dict) else {}
            flat: Dict[str, Any] = {}
            if isinstance(upstream, dict):
                for agent_id, node in upstream.items():
                    if isinstance(node, list):
                        if not node:
                            continue
                        node = node[-1]
                        while isinstance(node, list):
                            if not node:
                                break
                            node = node[-1]
                        if not isinstance(node, dict):
                            continue
                    if not isinstance(node, dict):
                        continue
                    parsed = node.get("parsed")
                    if parsed is None and isinstance(node.get("result"), dict):
                        parsed = node["result"]
                    if isinstance(parsed, str):
                        try:
                            parsed = JSONUtils.parse_json_from_text(
                                parsed, expect_json=False
                            )
                        except Exception:
                            parsed = None
                    if isinstance(parsed, dict):
                        render_context.setdefault(agent_id, parsed)
                        for k, v in parsed.items():
                            flat.setdefault(k, v)
            render_context.update({k: v for k, v in flat.items() if k not in render_context})
            for key, value in context.items():
                if key.startswith("current_") and key not in render_context:
                    render_context[key] = value
            if gate_type == "selection" and populated_options:
                render_context["gate_options"] = populated_options
            out = tmpl.render(**render_context)
            return str(out) if isinstance(out, str) else (str(out) if out else "")
        except Exception as e:
            self.logger.error(
                "Failed to render HITL gate description template for gate {}: {}",
                gate_id,
                e,
            )
            if description_template:
                return description_template
            return f"HITL review required for gate: {gate_id}"

    async def _handle_gate_execution(
        self,
        context: Dict[str, Any],
        gate_id: str,
        gate_config: Dict[str, Any],
        flow_control_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute HITL gate and handle flow control decisions.

        Returns:
            result: {"decision": "approve/continue", "data": {...}, "flow_action": "continue/retry/skip/stop"}
        """
        # Get effective gate configuration with defaults
        effective_config = self._get_effective_gate_config(gate_config)

        gate_type = effective_config.get("type", "approval")
        title = effective_config.get("title", "Approval Required")
        description = effective_config.get("description", "")
        fields = effective_config.get("fields", [])
        options = effective_config.get("options", [])
        options_source = effective_config.get("options_source")  # e.g., "agent_id.key.path"
        buttons = effective_config.get("buttons", {})
        timeout_ms = int(effective_config.get("timeout_ms", 300000))
        on_timeout = effective_config.get("on_timeout", "reject")
        context_key = effective_config.get("context_key", gate_id)
        context_strategy = effective_config.get("context_strategy")  # e.g., 'append'
        preserve_feedback = effective_config.get("preserve_feedback", True)  # Default: preserve feedback for retry
        default_value = effective_config.get("default")  # For selection gates

        emitter = context.get("emitter")

        # Filter and render field-level conditions/defaults before emitting to UI
        filtered_fields = self._filter_gate_fields(fields, context)
        
        # Populate selection gate options only via explicit options_source (no heuristics)
        populated_options = self._populate_selection_options(
            options,
            context,
            gate_type,
            gate_id,
            options_source=options_source,
        )
        
        # Render default value for selection gates if it's a Jinja2 template
        if gate_type == "selection" and default_value and isinstance(default_value, str):
            try:
                from jinja2 import Environment, Undefined
                
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
                
                def get_nested_value(data: Any, path: str, default: Any = None) -> Any:
                    """Safely get nested value from dict using dot notation path."""
                    if not path or not isinstance(data, dict):
                        return default
                    parts = path.split(".")
                    value = data
                    for field in parts:
                        if isinstance(value, dict) and field in value:
                            value = value[field]
                        else:
                            return default
                    return value
                
                from topaz_agent_kit.utils.jinja2_filters import register_jinja2_filters
                
                env = Environment(undefined=SafeUndefined, autoescape=False)
                # Add custom filter for safe nested dict access
                env.filters['nested_get'] = get_nested_value
                register_jinja2_filters(env)
                # Check if it looks like a template (contains {{ or {%)
                if "{{" in default_value or "{%" in default_value:
                    tmpl = env.from_string(default_value)
                    # Build render context similar to description rendering
                    render_context = dict(context)
                    upstream = context.get("upstream", {}) if isinstance(context, dict) else {}
                    flat: Dict[str, Any] = {}
                    if isinstance(upstream, dict):
                        for agent_id, node in upstream.items():
                            # Handle accumulated loop results (list of results from multiple iterations)
                            if isinstance(node, list):
                                if not node:
                                    self.logger.debug("Upstream agent '{}' has empty list result", agent_id)
                                    continue
                                # Use the last element (most recent iteration's result)
                                node = node[-1]
                                if not isinstance(node, dict):
                                    self.logger.warning("Upstream agent '{}' list element is not a dict: {}", agent_id, type(node))
                                    continue
                            
                            if not isinstance(node, dict):
                                self.logger.warning("Upstream agent '{}' result is not a dict: {}", agent_id, type(node))
                                continue
                            
                            parsed = node.get("parsed")
                            if parsed is None:
                                # Check if there's an error or if parsing failed
                                if "error" in node:
                                    self.logger.warning("Upstream agent '{}' has error in result: {}", agent_id, node.get("error"))
                                elif "result" in node:
                                    # Try to use raw result if parsed is missing
                                    raw_result = node.get("result")
                                    self.logger.debug("Upstream agent '{}' missing 'parsed', using 'result' field (type: {})", agent_id, type(raw_result))
                                    if isinstance(raw_result, dict):
                                        parsed = raw_result
                                    else:
                                        self.logger.warning("Upstream agent '{}' 'result' field is not a dict: {}", agent_id, type(raw_result))
                                else:
                                    # Skip warning for special context variables that don't have standard agent output structure
                                    # (e.g., 'current_journal', '_loop', etc. - these are loop context variables, not agent outputs)
                                    if not (agent_id.startswith("_") or agent_id in ["current_journal", "loop_item"]):
                                        self.logger.warning("Upstream agent '{}' missing both 'parsed' and 'result' fields. Available keys: {}", agent_id, list(node.keys()))
                            
                            if isinstance(parsed, dict):
                                render_context.setdefault(agent_id, parsed)
                                # Log structure for debugging missing nested paths
                                if agent_id == "tci_document_extractor" and "extracted_data" not in parsed:
                                    self.logger.warning(
                                        "Upstream agent '{}' parsed output missing 'extracted_data' key. Available keys: {}. "
                                        "This may indicate agent execution failure or parsing error.",
                                        agent_id,
                                        list(parsed.keys())
                                    )
                                for k, v in parsed.items():
                                    flat.setdefault(k, v)
                    render_context.update({k: v for k, v in flat.items() if k not in render_context})
                    rendered_default = tmpl.render(**render_context)
                    # Strip whitespace from rendered default
                    rendered_default = rendered_default.strip() if isinstance(rendered_default, str) else rendered_default
                    # Update effective_config with rendered default
                    effective_config["default"] = rendered_default
                    default_value = rendered_default
                    self.logger.debug("Rendered default value for gate {}: '{}'", gate_id, default_value)
            except Exception as e:
                self.logger.warning("Failed to render default value for gate {}: {}, using as-is", gate_id, e)
        
        # After populating options, verify default value matches an option (for selection gates)
        if gate_type == "selection" and default_value and populated_options:
            # Check if default value matches any option
            default_matches = any(
                isinstance(opt, dict) and (opt.get("value") == default_value or opt.get("id") == default_value)
                for opt in populated_options
            )
            if not default_matches and default_value:
                self.logger.warning("Default value '{}' for gate {} does not match any option. Available option values: {}", 
                                  default_value, gate_id, [opt.get("value") if isinstance(opt, dict) else str(opt) for opt in populated_options[:5]])
                # Try to find a match by stripping whitespace
                for opt in populated_options:
                    if isinstance(opt, dict):
                        opt_value = str(opt.get("value", "")).strip()
                        if opt_value == str(default_value).strip():
                            effective_config["default"] = opt_value
                            default_value = opt_value
                            self.logger.debug("Fixed default value match by stripping whitespace: '{}'", default_value)
                            break

        # Ensure validation sees dynamically populated options for selection gates
        try:
            if gate_type == "selection":
                effective_config["options"] = populated_options or []
        except Exception:
            pass

        # =============================================================================
        # ASYNC HITL MODE CHECK (BEFORE emitting hitl_request to UI)
        # =============================================================================
        # Check if async HITL mode is enabled for this gate
        # Priority: gate-level override > pipeline-level setting > default (sync)
        gate_hitl_mode = effective_config.get("hitl_mode")
        pipeline_hitl_mode = self.pipeline_config.get("execution_settings", {}).get("hitl_mode", "sync")
        effective_hitl_mode = gate_hitl_mode or pipeline_hitl_mode
        is_async_hitl = effective_hitl_mode == "async"

        # Emit type-specific HITL request (only for SYNC mode)
        # For async mode, we skip this and emit hitl_queued event later
        if emitter and hasattr(emitter, "hitl_request") and not is_async_hitl:
            description = self._load_and_render_hitl_description(
                description, context, gate_id, gate_type, populated_options
            )
            # Get parent_pattern_id from context (set by pattern runners)
            parent_pattern_id = context.get("parent_pattern_id")
            emitter.hitl_request(
                gate_id=gate_id,
                gate_type=gate_type,
                title=title,
                description=description,
                fields=filtered_fields,
                options=populated_options,
                buttons=buttons,
                timeout_ms=timeout_ms,
                on_timeout=on_timeout,
                context_key=context_key,
                default=default_value if gate_type == "selection" else None,
                retry_target=flow_control_config.get("retry_target"),
                max_retries=flow_control_config.get("max_retries"),
                parent_pattern_id=parent_pattern_id,
            )

            # Register gate with AGUIService for backend lookup
            agui_service = context.get("agui_service")
            if agui_service and hasattr(agui_service, "create_hitl_gate"):
                # Create options list from buttons for AGUIService
                gate_options = (
                    list(buttons.keys()) if buttons else ["approve", "reject"]
                )
                agui_service.create_hitl_gate(gate_id, title, description, gate_options)

        # =============================================================================
        # ASYNC HITL HANDLING
        # =============================================================================
        # is_async_hitl was computed earlier (before hitl_request emission)
        
        if is_async_hitl:
            # Async HITL: Create checkpoint and enqueue instead of waiting
            self.logger.info(
                "Async HITL mode enabled for gate {}, creating checkpoint and queuing",
                gate_id
            )
            
            # Check if we're resuming and this gate already has a HITL response
            # This prevents creating duplicate checkpoints when resuming
            resume_info = context.get("_resume", {})
            is_resumed = resume_info.get("is_resumed", False)
            resumed_gate_id = resume_info.get("gate_id")
            resumed_loop_index = resume_info.get("loop_index")  # Get from resume_info (doesn't get overwritten)
            hitl_context = context.get("hitl", {})
            
            # Get current loop iteration (if in a loop)
            current_loop_index = context.get("loop_index")
            
            # If we're resuming and this gate already has a response, use it instead of creating a new checkpoint
            if is_resumed and gate_id in hitl_context and gate_id == resumed_gate_id:
                # If we're in a loop, verify we're on the correct iteration
                if resumed_loop_index is not None:
                    if current_loop_index != resumed_loop_index:
                        # We're resuming iteration X, but we're on iteration Y - skip this gate
                        # The LoopRunner should skip wrong iterations, but gates might be hit before that
                        self.logger.info(
                            "Resuming from checkpoint: gate {} hit on iteration {} but resuming iteration {}, skipping gate",
                            gate_id, current_loop_index, resumed_loop_index
                        )
                        return {
                            "decision": "approve",
                            "data": {},
                            "flow_action": "continue",
                        }
                
                gate_response = hitl_context[gate_id]
                decision = gate_response.get("decision", "approve")
                response_data = gate_response.get("data", {})
                
                # CRITICAL: Check if this gate's inline array has already been executed.
                # If so, return immediately to prevent re-execution (which causes cyclic loops).
                array_executed_key = f"_gate_{gate_id}_array_executed"
                if context.get(array_executed_key, False):
                    self.logger.warning(
                        "Gate {}'s inline array has already been executed on resume - returning 'continue' to prevent re-execution",
                        gate_id
                    )
                    # Return 'continue' to skip re-execution and let the loop break naturally
                    return {
                        "decision": decision,
                        "data": response_data,
                        "flow_action": "continue",
                    }
                
                self.logger.info(
                    "Resuming from checkpoint: gate {} already has HITL response (decision: {}), skipping checkpoint creation",
                    gate_id, decision
                )
                # Build result dict and determine flow_action based on decision (same as normal flow)
                result = {
                    "decision": decision,
                    "data": response_data,
                }
                # Determine flow action based on gate type and user decision (CRITICAL: don't hardcode "continue")
                flow_action = self._determine_flow_action(
                    result, gate_type, flow_control_config
                )
                
                # Handle BaseRunner objects (compiled arrays) - store in context, use marker in result
                from topaz_agent_kit.core.execution_patterns import BaseRunner
                if isinstance(flow_action, BaseRunner):
                    # Store BaseRunner in context (won't be serialized in checkpoints)
                    context_key = f"_gate_array_runner_{gate_id}"
                    context[context_key] = flow_action
                    # Mark that this gate's array will be executed (prevents re-execution)
                    array_executed_key = f"_gate_{gate_id}_array_executed"
                    context[array_executed_key] = True
                    # Store marker and gate_id in result for SequentialRunner to look up
                    result["flow_action"] = "execute_array"
                    result["_array_runner_context_key"] = context_key
                    self.logger.info(
                        "Flow action is a compiled runner (array of nodes), stored in context at '{}', will be handled by SequentialRunner. Marked {} to prevent re-execution.",
                        context_key, array_executed_key
                    )
                    return result
                
                result["flow_action"] = flow_action
                
                # CRITICAL: Handle flow_action immediately when resuming (same as normal flow)
                # This ensures rejection stops execution even when resuming from checkpoint
                
                if flow_action == "stop":
                    raise PipelineStoppedByUser(gate_id, "User rejected approval")
                elif flow_action == "retry_node":
                    # Trigger retry logic (handled by SequentialRunner)
                    result["retry_target"] = flow_control_config.get("retry_target")
                    result["max_retries"] = flow_control_config.get("max_retries", 3)
                elif flow_action == "skip_to_node":
                    # Trigger skip logic (handled by SequentialRunner)
                    result["skip_to"] = flow_control_config.get("skip_to")
                
                # Return the decision with correct flow_action (will be handled by GateRunner for other actions)
                return result
            
            # If we're resuming but this gate doesn't have a response yet, check if we're on the wrong loop iteration
            # This can happen when resuming iteration 2, but iteration 0 hits the gate first
            if is_resumed and resumed_loop_index is not None and gate_id == resumed_gate_id:
                if current_loop_index is not None and current_loop_index != resumed_loop_index:
                    # We're resuming iteration X, but we're on iteration Y - skip creating checkpoint
                    self.logger.info(
                        "Resuming from checkpoint: gate {} hit on iteration {} but resuming iteration {}, skipping checkpoint creation",
                        gate_id, current_loop_index, resumed_loop_index
                    )
                    return {
                        "decision": "approve",
                        "data": {},
                        "flow_action": "continue",
                    }
            
            # Get async HITL managers from context
            checkpoint_manager = context.get("checkpoint_manager")
            hitl_queue_manager = context.get("hitl_queue_manager")
            case_manager = context.get("case_manager")
            
            if not checkpoint_manager or not hitl_queue_manager:
                self.logger.warning(
                    "Async HITL managers not available, falling back to sync mode for gate {}",
                    gate_id
                )
            else:
                # Extract case ID and create/update case if needed
                case_id = context.get("case_id")
                
                # Create case if it doesn't exist
                # IMPORTANT: create_case will extract the case_id from case_config if available,
                # and only use fallback if extraction fails. This ensures proper format is used.
                if case_manager:
                    # Generate fallback ID only if we don't have a case_id yet
                    # This fallback will only be used if case_config extraction fails
                    fallback_case_id = None
                    if not case_id:
                        fallback_case_id = f"CASE-{context.get('run_id', 'unknown')[:8]}"
                    
                    # First, try to get existing case if we have a case_id
                    if case_id:
                        existing_case = case_manager.get_case(case_id)
                        if existing_case:
                            # Case exists - use the actual case_id from database (might have UUID suffix)
                            actual_case_id = existing_case.get("case_id", case_id)
                            if actual_case_id != case_id:
                                case_id = actual_case_id
                                context["case_id"] = case_id
                        else:
                            # Case doesn't exist - create it
                            # CRITICAL: Use _parent_pipeline_id if available (preserved by LoopRunner/PipelineStepRunner)
                            # to ensure correct parent pipeline_id is used even if sub-pipeline modified context["pipeline_id"]
                            pipeline_id = context.get("_parent_pipeline_id") or context.get("pipeline_id", "unknown")
                            actual_case_id = case_manager.create_case(
                                pipeline_id=pipeline_id,
                                run_id=context.get("run_id", ""),
                                upstream=context.get("upstream", {}),
                                case_config=context.get("case_config", {}),
                                session_id=context.get("session_id"),
                                fallback_case_id=case_id,
                                initial_status=CaseManager.STATUS_HITL_PENDING,
                            )
                            if actual_case_id:
                                case_id = actual_case_id
                                context["case_id"] = case_id
                                
                                # Add timeline entry for HITL queued
                                case_manager._add_timeline_entry(
                                    case_id=case_id,
                                    event_type="hitl_queued",
                                    event_data={
                                        "gate_id": gate_id,
                                        "queued_at": datetime.now().isoformat(),
                                    },
                                )
                    else:
                        # No case_id yet - create case (will extract from case_config or use fallback)
                        # CRITICAL: Use _parent_pipeline_id if available (preserved by LoopRunner/PipelineStepRunner)
                        # to ensure correct parent pipeline_id is used even if sub-pipeline modified context["pipeline_id"]
                        pipeline_id = context.get("_parent_pipeline_id") or context.get("pipeline_id", "unknown")
                        actual_case_id = case_manager.create_case(
                            pipeline_id=pipeline_id,
                            run_id=context.get("run_id", ""),
                            upstream=context.get("upstream", {}),
                            case_config=context.get("case_config", {}),
                            session_id=context.get("session_id"),
                            fallback_case_id=fallback_case_id,
                            initial_status=CaseManager.STATUS_HITL_PENDING,
                        )
                        # Use the actual case_id returned from create_case
                        if actual_case_id:
                            case_id = actual_case_id
                            context["case_id"] = case_id
                            
                            # Add timeline entry for HITL queued
                            case_manager._add_timeline_entry(
                                case_id=case_id,
                                event_type="hitl_queued",
                                event_data={
                                    "gate_id": gate_id,
                                    "queued_at": datetime.now().isoformat(),
                                },
                            )
                        else:
                            self.logger.warning(
                                "Failed to create case, using fallback case_id: {}", fallback_case_id
                            )
                            case_id = fallback_case_id
                            context["case_id"] = case_id
                
                # Check if there's already a pending checkpoint/queue item for this case+gate combination
                # This prevents creating duplicate checkpoints/queue items when:
                # 1. A loop hits the same gate multiple times for the same case
                # 2. A resumed pipeline hits the same gate again (before the previous checkpoint is fully processed)
                # 
                # IMPORTANT: Only check for PENDING items to avoid reusing already-processed checkpoints.
                # When resuming, if we hit the same gate again, we want to create a NEW checkpoint
                # for the new iteration, but we should NOT create duplicates if there's already a pending one.
                existing_queue_item = hitl_queue_manager.get_pending_queue_item(case_id, gate_id)
                
                # Also check for pending checkpoints (not resumed ones) to prevent duplicates
                existing_checkpoint = checkpoint_manager.get_checkpoint_by_case_gate(
                    case_id=case_id,
                    gate_id=gate_id,
                    include_resumed=False,  # Only check for pending checkpoints to prevent duplicates
                )
                
                # If we have a pending queue item, reuse it
                if existing_queue_item:
                    # Reuse existing pending queue item and checkpoint
                    queue_item_id = existing_queue_item.get("queue_item_id")
                    checkpoint_id = existing_queue_item.get("checkpoint_id")
                    self.logger.info(
                        "Reusing existing pending HITL request for case {} at gate {} (checkpoint: {}, queue: {})",
                        case_id, gate_id, checkpoint_id, queue_item_id
                    )
                # If we have a pending checkpoint but no queue item, create queue item for it
                elif existing_checkpoint and existing_checkpoint.checkpoint_id:
                    # Have pending checkpoint but no queue item - create new queue item for existing checkpoint
                    checkpoint_id = existing_checkpoint.checkpoint_id
                    priority = effective_config.get("priority", "medium")
                    queue_item_id = hitl_queue_manager.enqueue(
                        checkpoint_id=checkpoint_id,
                        case_id=case_id,
                        pipeline_id=context.get("pipeline_id", "unknown"),
                        gate_id=gate_id,
                        gate_type=gate_type,
                        gate_config=effective_config,
                        upstream=context.get("upstream", {}),
                        hitl=context.get("hitl", {}),
                        priority=priority,
                        project_dir=context.get("project_dir"),
                    )
                    if not queue_item_id:
                        self.logger.error("Failed to enqueue HITL request for gate {}", gate_id)
                        raise PipelineError(f"Failed to enqueue HITL request for gate {gate_id}")
                    self.logger.info(
                        "Reusing existing pending checkpoint {} for case {} at gate {}, created new queue item {}",
                        checkpoint_id, case_id, gate_id, queue_item_id
                    )
                else:
                    # Create new checkpoint and queue item
                    checkpoint_expiry_days = self.pipeline_config.get(
                        "execution_settings", {}
                    ).get("checkpoint_expiry_days", 7)
                    
                    # When inside a loop, use parent upstream (full context) instead of filtered loop_context upstream
                    # This ensures checkpoints store ALL agent outputs, including pre-loop agents like batch_problem_parser
                    # CRITICAL: Merge current iteration's results into checkpoint upstream
                    # _parent_upstream has accumulated results from previous iterations, but we need current iteration's results too
                    upstream_for_checkpoint = context.get("_parent_upstream") or context.get("upstream", {}).copy()
                    current_iteration_upstream = context.get("upstream", {})
                    loop_index = context.get("loop_index")
                    
                    # If we're in a loop and have current iteration's upstream, merge it into checkpoint upstream
                    if loop_index is not None and current_iteration_upstream:
                        import copy
                        upstream_for_checkpoint = copy.deepcopy(upstream_for_checkpoint)
                        for agent_id, agent_result in current_iteration_upstream.items():
                            if agent_id in upstream_for_checkpoint:
                                # Agent exists in parent upstream (accumulated results from previous iterations)
                                existing = upstream_for_checkpoint[agent_id]
                                if isinstance(existing, list):
                                    # Loop-specific agent with accumulated results
                                    # CRITICAL: For checkpoint, store ONLY the current iteration's result, not the accumulated list
                                    # When resuming, we only need this iteration's data (post-loop agents are skipped during resume)
                                    # This simplifies resumption - no need to extract from a list, just use the single result
                                    upstream_for_checkpoint[agent_id] = copy.deepcopy(agent_result)
                                    
                                    self.logger.debug(
                                        "Stored iteration {} result for {} in checkpoint upstream (single result, not accumulated list)",
                                        loop_index, agent_id
                                    )
                                else:
                                    # Pre-loop agent: keep parent upstream result (single result, shared across iterations)
                                    # Don't overwrite with current iteration's result
                                    pass
                            else:
                                # Agent only exists in current iteration (first time running in loop)
                                # Add it to checkpoint upstream
                                upstream_for_checkpoint[agent_id] = copy.deepcopy(agent_result)
                                self.logger.debug(
                                    "Added iteration {} result for new loop-specific agent {} to checkpoint upstream",
                                    loop_index, agent_id
                                )
                    
                    checkpoint_id = checkpoint_manager.create_checkpoint(
                        case_id=case_id,
                        pipeline_id=context.get("pipeline_id", "unknown"),
                        run_id=context.get("run_id", ""),
                        gate_id=gate_id,
                        gate_config=effective_config,
                        upstream=upstream_for_checkpoint,
                        hitl=context.get("hitl", {}),
                        session_id=context.get("session_id"),
                        loop_index=context.get("loop_index"),
                        loop_item=context.get("loop_item"),
                        loop_total=context.get("loop_total"),
                        loop_id=context.get("loop_id"),
                        pattern_stack=context.get("_pattern_stack"),
                        resume_point=flow_control_config.get("resume_point", "next"),
                        expiry_days=checkpoint_expiry_days,
                    )
                    
                    if not checkpoint_id:
                        self.logger.error("Failed to create checkpoint for async HITL gate {}", gate_id)
                        raise PipelineError(f"Failed to create checkpoint for async HITL gate {gate_id}")
                    
                    # Enqueue HITL request
                    priority = effective_config.get("priority", "medium")
                    queue_item_id = hitl_queue_manager.enqueue(
                        checkpoint_id=checkpoint_id,
                        case_id=case_id,
                        pipeline_id=context.get("pipeline_id", "unknown"),
                        gate_id=gate_id,
                        gate_type=gate_type,
                        gate_config=effective_config,
                        upstream=context.get("upstream", {}),
                        hitl=context.get("hitl", {}),
                        priority=priority,
                        project_dir=context.get("project_dir"),
                    )
                    
                    if not queue_item_id:
                        self.logger.error("Failed to enqueue HITL request for gate {}", gate_id)
                        raise PipelineError(f"Failed to enqueue HITL request for gate {gate_id}")
                
                # Case was created with "hitl_pending" status, but update current_step to gate_id
                if case_manager:
                    # Only update current_step since status is already correct
                    case_manager.update_case_status(case_id=case_id, status=CaseManager.STATUS_HITL_PENDING, current_step=gate_id)
                    self.logger.info("Case {} is queued for HITL at gate {}", case_id, gate_id)
                
                self.logger.info(
                    "Async HITL: Queued case {} at gate {} (checkpoint: {}, queue: {})",
                    case_id, gate_id, checkpoint_id, queue_item_id
                )
                
                # Emit hitl_queued event to UI (instead of hitl_request)
                if emitter and hasattr(emitter, "hitl_queued"):
                    # Get parent_pattern_id from context (set by pattern runners)
                    parent_pattern_id = context.get("parent_pattern_id")
                    description_for_ui = self._load_and_render_hitl_description(
                        description, context, gate_id, gate_type, populated_options
                    )
                    emitter.hitl_queued(
                        gate_id=gate_id,
                        case_id=case_id,
                        display_id=case_id,  # display_id is always same as case_id now
                        checkpoint_id=checkpoint_id,
                        queue_item_id=queue_item_id,
                        title=title,
                        description=description_for_ui,
                        gate_type=gate_type,
                        parent_pattern_id=parent_pattern_id,
                    )
                
                # Raise exception to signal loop to continue with next iteration
                raise HITLQueuedForAsync(
                    gate_id=gate_id,
                    queue_item_id=queue_item_id,
                    case_id=case_id,
                    checkpoint_id=checkpoint_id,
                )
        
        # =============================================================================
        # SYNC HITL HANDLING (Original behavior)
        # =============================================================================
        # Await user response
        waiter = context.get("options", {}).get("hitl", {}).get("wait_for_approval")
        if not callable(waiter):
            # No waiter - auto-approve for CLI mode
            result = {"decision": "approve", "data": {}}

            # Emit hitl_result event for CLI auto-approve
            if emitter and hasattr(emitter, "hitl_result"):
                emitter.hitl_result(
                    gate_id=gate_id, decision="approve", actor="system", data={}
                )
        else:
            try:
                result = await waiter(gate_id, timeout_ms)
                # CRITICAL: Ensure result is not a Future (should be resolved by waiter)
                if isinstance(result, asyncio.Future):
                    if result.done():
                        result = result.result()
                    else:
                        self.logger.error("HITL waiter returned unresolved Future for gate {}", gate_id)
                        raise PipelineError(f"HITL gate {gate_id} returned unresolved Future")
            except asyncio.TimeoutError:
                result = self._handle_gate_timeout(
                    gate_type, on_timeout, filtered_fields, populated_options, effective_config
                )
                if result is None:
                    raise PipelineError(f"HITL timeout for gate {gate_id}")

                # Emit hitl_result event for auto-decision due to timeout
                if emitter and hasattr(emitter, "hitl_result"):
                    emitter.hitl_result(
                        gate_id=gate_id,
                        decision=result.get("decision", "approve"),
                        actor="system",
                        data=result.get("data", {}),
                    )

        # Normalize checkbox input payloads to arrays (coerce "", null -> [], CSV -> list)
        try:
            if gate_type == "input" and isinstance(result, dict) and isinstance(result.get("data"), dict):
                field_types = {f.get("name"): f.get("type") for f in filtered_fields if isinstance(f, dict)}
                for fname, ftype in (field_types or {}).items():
                    if ftype == "checkbox" and fname in result["data"]:
                        v = result["data"].get(fname)
                        if v is None or v == "":
                            result["data"][fname] = []
                        elif isinstance(v, str):
                            coerced = None
                            try:
                                parsed = json.loads(v)
                                if isinstance(parsed, list):
                                    coerced = [str(x) for x in parsed]
                            except Exception:
                                pass
                            if coerced is None:
                                coerced = [s.strip() for s in v.split(",") if str(s).strip()]
                            result["data"][fname] = coerced
                        elif isinstance(v, (int, float)):
                            result["data"][fname] = [str(v)]
                        elif isinstance(v, dict):
                            result["data"][fname] = [
                                str(v.get("value") or v.get("id") or "")
                            ]
                        elif isinstance(v, list):
                            result["data"][fname] = [str(x) for x in v]
        except Exception:
            # Best-effort normalization only
            pass

        # For selection gates, do matching BEFORE validation
        # This ensures we can match the option even if validation would fail
        # CRITICAL: Selection matching must happen before validation because:
        # 1. Validation checks if "selection" is in data
        # 2. Matching replaces {"selection": "OPT-2"} with the complete option object
        # 3. If validation runs first and fails, matching never happens
        if gate_type == "selection":
            try:
                data = result.get("data", {})
                # CRITICAL: Extract selection value correctly - UI sends {"selection": "OPT-2"}
                # Handle both dict format {"selection": value} and direct value format
                if isinstance(data, dict):
                    selection_value = data.get("selection")
                else:
                    # If data is not a dict, it might be the selection value directly (legacy format)
                    selection_value = data
                
                # CRITICAL: Use populated_options if available (from options_source), otherwise fall back to effective_config options
                options_to_search = populated_options if populated_options else (effective_config.get("options", []) if effective_config else [])
                
                if selection_value and options_to_search:
                    # Log all available options for debugging
                    self.logger.debug("Selection gate {}: user selected value='{}' (type: {}), available options: {}", 
                                    gate_id, selection_value, type(selection_value),
                                    [(opt.get("value") if isinstance(opt, dict) else str(opt), 
                                      opt.get("label") if isinstance(opt, dict) else "N/A") 
                                     for opt in options_to_search[:10]])
                    
                    # Find the selected option - use DIRECT comparison like the old working code
                    # OLD WORKING CODE: if isinstance(opt, dict) and (opt.get("value") == selection_value or opt.get("id") == selection_value)
                    selected_option = None
                    for opt in options_to_search:
                        if isinstance(opt, dict):
                            opt_value = opt.get("value")
                            opt_id = opt.get("id")
                            # Match by value or id (case-insensitive string comparison for safety)
                            if (opt_value and str(opt_value).strip() == str(selection_value).strip()) or \
                               (opt_id and str(opt_id).strip() == str(selection_value).strip()):
                                selected_option = opt
                                self.logger.debug("Matched option: value='{}', id='{}', label='{}'", 
                                               opt_value, opt_id, opt.get("label", "N/A"))
                                break
                    
                    # Store the complete selected option object instead of just the selection value
                    if selected_option and isinstance(selected_option, dict):
                        # Replace data with the complete selected option object
                        result["data"] = selected_option
                        option_id = selected_option.get("value") or selected_option.get("id") or "unknown"
                        option_label = selected_option.get("label") or "N/A"
                        # CRITICAL: Verify the matched option's value matches what user selected
                        if str(option_id).strip() != str(selection_value).strip() and str(selected_option.get("id", "")).strip() != str(selection_value).strip():
                            self.logger.error("MATCHING ERROR in gate {}: User selected '{}' but matched option has value '{}'! This is a bug!", 
                                            gate_id, selection_value, option_id)
                        self.logger.debug("Stored complete selected option object for gate {}: option_id={}, option_label={}, keys={}", 
                                       gate_id, option_id, option_label, list(selected_option.keys()))
                    else:
                        self.logger.error("Option lookup FAILED for gate {}: selection_value='{}' (type: {}), options_count={}, available_values={}", 
                                          gate_id, selection_value, type(selection_value), 
                                          len(options_to_search) if options_to_search else 0,
                                          [opt.get("value") if isinstance(opt, dict) else str(opt) for opt in options_to_search[:10]])
                elif not selection_value:
                    self.logger.warning("Selection gate {}: No selection value found in data: {}", gate_id, data)
                elif not options_to_search:
                    self.logger.error("Selection gate {}: No options available for matching! options_source={}, populated_options_count={}, effective_config_options_count={}", 
                                      gate_id, options_source, 
                                      len(populated_options) if populated_options else 0,
                                      len(effective_config.get("options", [])) if effective_config else 0)
            except Exception as e:
                self.logger.error("Failed to extract selected option for gate {}: {}", gate_id, e, exc_info=True)

        # Validate result based on gate type (use effective_config with dynamic options)
        # CRITICAL: For selection gates, validation happens AFTER matching so it can validate
        # the complete option object instead of just {"selection": "OPT-2"}
        self._validate_gate_result(result, gate_type, effective_config)

        self.logger.debug("Gate result: {}", result)

        # Store result in context for downstream agents
        # Only store gate data in hitl if preserve_feedback is True (default) OR decision is not retry
        # This allows retried agents to access feedback when preserve_feedback=True (e.g., article_smith)
        # but skips storage when preserve_feedback=False (e.g., rate_case simple retry)
        # NOTE: context_key data (e.g., selected_options) is ALWAYS stored below for downstream agents
        # CRITICAL: Read data AFTER selection matching (line 905 may have replaced result["data"] with selected_option)
        decision = result.get("decision")
        should_preserve = preserve_feedback or decision not in ["retry", "skip"]
        
        if should_preserve:
            # CRITICAL: Use result.get("data") AFTER selection matching has completed
            # For selection gates, result["data"] should now be the complete selected_option object (not {"selection": "OPT-2"})
            hitl_data = result.get("data", {})
            context.setdefault("hitl", {})[gate_id] = {
                "decision": decision,
                "data": hitl_data,
                "gate_type": gate_type,
                "context_key": context_key,
                "context_strategy": context_strategy,
            }
            # Log what we're storing in HITL for selection gates
            if gate_type == "selection" and gate_id == "option_selection_gate":
                if isinstance(hitl_data, dict):
                    option_id = hitl_data.get("value") or hitl_data.get("id") or "unknown"
                    self.logger.debug("Stored HITL data for {}: option_id={}, data_keys={}", gate_id, option_id, list(hitl_data.keys()))
                else:
                    self.logger.warning("HITL data for {} is not a dict: {}", gate_id, hitl_data)
            self.logger.debug("Stored HITL data in context: {}", context.get("hitl", {}))
        else:
            self.logger.debug("Skipping HITL data storage for gate {} (preserve_feedback=False, decision={})", gate_id, decision)
        
        # CRITICAL: For retry decisions with preserve_feedback=false, clear context_key data
        # because we're generating new options and old selections are no longer valid
        if decision == "retry" and not preserve_feedback and context_key:
            gate_context_key = f"{gate_id}.{context_key}"
            if gate_context_key in context:
                self.logger.debug("Clearing context_key '{}' on retry (preserve_feedback=False)", gate_context_key)
                del context[gate_context_key]

        # Apply context_strategy (generic): overwrite by default; append if specified
        # CRITICAL: Store context_key data with gate prefix (e.g., option_validation_gate.selected_options)
        # for downstream agents (repeat pattern, recommender) to avoid naming conflicts with agent outputs.
        # BUT: For retry decisions with preserve_feedback=false, DON'T store old data (it's invalid for new options)
        # The new data will be stored when user submits the gate again after new options are generated
        try:
            # CRITICAL: Read data AFTER selection matching (line 901 may have replaced result["data"] with selected_option)
            data = result.get("data", {})
            
            # For selection gates, verify data is the complete option object (not just {"selection": "OPT-2"})
            if gate_type == "selection" and isinstance(data, dict):
                # If data still has "selection" key, it means matching failed or didn't run
                if "selection" in data and options_source:
                    selection_value = data.get("selection")
                    self.logger.error("CRITICAL: Selection gate {} data still contains 'selection' key after matching! selection='{}', data={}. This means option matching failed or was skipped!", 
                                     gate_id, selection_value, data)
                    # Try to match again as fallback
                    if selection_value and populated_options:
                        for opt in populated_options:
                            if isinstance(opt, dict):
                                opt_value = str(opt.get("value", "")).strip()
                                if opt_value == str(selection_value).strip():
                                    data = opt  # Replace with complete option object
                                    result["data"] = opt
                                    self.logger.warning("Fallback matching succeeded: matched '{}' to option with value '{}'", 
                                                       selection_value, opt_value)
                                    break
            
            # For retry with preserve_feedback=false, skip storing context_key (old data is invalid)
            if decision == "retry" and not preserve_feedback:
                self.logger.debug("Skipping context_key storage for retry (preserve_feedback=False, will store new data on next submission)")
            else:
                # Flatten single-field input for convenience (matches AgentRunner behavior)
                flattened_value = None
                if gate_type == "input" and isinstance(data, dict) and len(data) == 1:
                    _, flattened_value = next(iter(data.items()))
                
                # Store context_key data with gate prefix to avoid conflicts with agent outputs
                if context_key:
                    # Store at gate_id.context_key (e.g., option_validation_gate.selected_options)
                    gate_context_key = f"{gate_id}.{context_key}"
                    
                    if context_strategy == "append" and decision not in ["retry", "skip"]:
                        # Only build Q/A pairs for non-retry decisions (feedback for retried agent)
                        previous = context.get(gate_context_key)
                        if gate_type == "input" and flattened_value is not None:
                            # Use description variable (already rendered if it was a template)
                            qa_block = f"Q: {description}\nA: {flattened_value}"
                            # Dedupe: if previous ends with the same A: value, do not append again
                            if isinstance(previous, str):
                                prev_lines = [ln for ln in previous.split("\n") if ln and ln.strip()]
                                last_a = None
                                for ln in reversed(prev_lines):
                                    if ln and isinstance(ln, str) and ln.startswith("A: "):
                                        last_a = ln[3:].strip()
                                        break
                                if last_a is not None and last_a == str(flattened_value).strip():
                                    combined = previous  # skip duplicate append
                                else:
                                    combined = f"{previous}\n{qa_block}"
                            else:
                                combined = qa_block
                            context[gate_context_key] = combined
                        else:
                            appended = flattened_value if flattened_value is not None else str(data)
                            combined = f"{previous}\n{appended}" if previous else appended
                            context[gate_context_key] = combined
                    else:
                        # Overwrite (default) - Store for downstream agents with gate prefix
                        # For approval gates, store decision as boolean at gate_context_key for easier condition evaluation
                        if gate_type == "approval" and decision:
                            context[gate_context_key] = (decision.lower() == "approve")
                        else:
                            stored_value = flattened_value if flattened_value is not None else data
                            context[gate_context_key] = stored_value
                            # Log the stored value for selection gates to track what was selected
                            if gate_type == "selection" and gate_id == "option_selection_gate":
                                if isinstance(stored_value, dict):
                                    option_id = stored_value.get("value") or stored_value.get("id") or "unknown"
                                    option_label = stored_value.get("label") or "N/A"
                                    # CRITICAL: Verify stored option_id matches what was selected
                                    if "selection" in stored_value:
                                        self.logger.error("CRITICAL BUG: Stored value still contains 'selection' key! This should be the complete option object. stored_value={}", 
                                                         stored_value)
                                    self.logger.info("USER SELECTED OPTION in {}: option_id={}, option_label={}, stored at context_key={}, full_object={}", 
                                                   gate_id, option_id, option_label, gate_context_key, stored_value)
                                else:
                                    self.logger.warning("USER SELECTED OPTION in {}: value={} (NOT A DICT!), stored at context_key={}", 
                                                   gate_id, stored_value, gate_context_key)
                    self.logger.debug("Stored context_key '{}' at '{}' for downstream agents", context_key, gate_context_key)
        except Exception as e:
            self.logger.warning("Failed to apply context_strategy for gate {}: {}", gate_id, e)

        # Determine flow action based on gate type and user decision
        flow_action = self._determine_flow_action(
            result, gate_type, flow_control_config
        )
        
        # Handle BaseRunner objects (compiled arrays) - store in context, use marker in result
        from topaz_agent_kit.core.execution_patterns import BaseRunner
        if isinstance(flow_action, BaseRunner):
            # Store BaseRunner in context (won't be serialized in checkpoints)
            # Use a key that includes gate_id to avoid conflicts
            context_key = f"_gate_array_runner_{gate_id}"
            context[context_key] = flow_action
            # Store marker and gate_id in result for SequentialRunner to look up
            result["flow_action"] = "execute_array"
            result["_array_runner_context_key"] = context_key
            self.logger.info(
                "Flow action is a compiled runner (array of nodes), stored in context at '{}', will be handled by SequentialRunner",
                context_key
            )
            return result
        
        result["flow_action"] = flow_action
        
        if flow_action == "stop":
            raise PipelineStoppedByUser(gate_id, "User rejected approval")
        elif flow_action == "retry_node":
            # Trigger retry logic (handled by SequentialRunner)
            result["retry_target"] = flow_control_config.get("retry_target")
            result["max_retries"] = flow_control_config.get("max_retries", 3)
        elif flow_action == "skip_to_node":
            # Trigger skip logic (handled by SequentialRunner)
            result["skip_to"] = flow_control_config.get("skip_to")

        return result

    def _filter_gate_fields(self, fields: list, context: Dict[str, Any]) -> list:
        """Filter HITL fields based on optional 'condition' (expression) and render defaults.

        - Keeps fields with no condition
        - For fields with 'condition', evaluates using ExpressionEvaluator (same as node conditions); keeps only truthy
        - Renders 'default' when it's a Jinja2 string template
        """
        try:
            from jinja2 import Environment, Undefined
        except Exception:
            Environment = None  # type: ignore

        from topaz_agent_kit.utils.expression_evaluator import evaluate_expression
        filtered: list = []

        for field in fields or []:
            try:
                cond_expr = field.get("condition")
                keep = True
                if cond_expr:
                    # Use ExpressionEvaluator for conditions (same as node conditions)
                    try:
                        keep = evaluate_expression(cond_expr, context)
                    except Exception as e:
                        self.logger.warning("Condition evaluation failed for field {}: {}, defaulting to False", field.get("name", "unknown"), e)
                        keep = False
                if not keep:
                    continue

                # Copy field and drop condition before sending to UI
                f2 = dict(field)
                if "condition" in f2:
                    f2.pop("condition", None)

                # Render default if it's a string template
                default_val = f2.get("default")
                if isinstance(default_val, str) and Environment is not None:
                    try:
                        env = Environment(undefined=Undefined, autoescape=False)
                        tmpl = env.from_string(default_val)
                        # Build a rich render context:
                        # - root context
                        # - agent namespaces: render_context[agent_id] = upstream[agent_id].parsed
                        # - shallow merge of all parsed dicts for convenience (no overwrite)
                        render_context = dict(context)
                        upstream = context.get("upstream", {}) if isinstance(context, dict) else {}
                        flat: Dict[str, Any] = {}
                        if isinstance(upstream, dict):
                            for agent_id, node in upstream.items():
                                parsed = node.get("parsed") if isinstance(node, dict) else None
                                if isinstance(parsed, dict):
                                    # agent namespace
                                    render_context.setdefault(agent_id, parsed)
                                    # shallow flatten
                                    for k, v in parsed.items():
                                        flat.setdefault(k, v)
                        # merge flattened keys last so direct refs like {{ flights_input.* }} may resolve
                        render_context.update({k: v for k, v in flat.items() if k not in render_context})
                        rendered_default = tmpl.render(**render_context)
                        # Parse JSON string defaults for checkbox fields (multi-select)
                        if f2.get("type") == "checkbox" and isinstance(rendered_default, str):
                            try:
                                import json
                                parsed = json.loads(rendered_default)
                                if isinstance(parsed, list):
                                    f2["default"] = parsed
                                else:
                                    f2["default"] = rendered_default
                            except (json.JSONDecodeError, ValueError):
                                # Not JSON, use as-is
                                f2["default"] = rendered_default
                        else:
                            f2["default"] = rendered_default
                    except Exception:
                        # Leave default as-is on render failure
                        pass

                # Populate field options dynamically for select/checkbox/radio fields
                if f2.get("type") in ["select", "checkbox", "radio"]:
                    field_options = f2.get("options", [])
                    options_source = f2.get("options_source")
                    # Populate only via explicit options_source; no heuristics
                    populated_field_options = self._populate_field_options(
                        field_options, context, f2.get("name", ""), options_source=options_source
                    )
                    if populated_field_options:
                        f2["options"] = populated_field_options

                filtered.append(f2)
            except Exception as e:
                # On any failure, conservatively include the field as-is
                self.logger.warning("Error filtering field {}: {}, including as-is", field.get("name", "unknown"), e)
                f2 = dict(field)
                f2.pop("condition", None)
                filtered.append(f2)

        return filtered

    def _populate_selection_options(self, options: list, context: Dict[str, Any], gate_type: str, gate_id: str = None, options_source: str = None) -> list:
        """Populate selection gate options from explicit options_source only.
        
        Also filters options based on optional 'condition' expressions (similar to field filtering).
        """
        if gate_type != "selection":
            return options or []

        from topaz_agent_kit.utils.expression_evaluator import evaluate_expression

        # Prefer explicit options_source if provided
        try:
            if options_source and isinstance(options_source, str) and "." in options_source:
                parts = options_source.split(".")
                agent_id = parts[0]
                field_path = parts[1:]
                upstream = context.get("upstream", {})
                if agent_id in upstream:
                    node_data = upstream[agent_id]
                    # Handle accumulated loop results (list of results from multiple iterations)
                    if isinstance(node_data, list):
                        if not node_data:
                            self.logger.debug("Upstream agent '{}' has empty list result", agent_id)
                            node_data = None
                        else:
                            # Use the last element (most recent iteration's result)
                            node_data = node_data[-1]
                            if not isinstance(node_data, dict):
                                self.logger.warning("Upstream agent '{}' list element is not a dict: {}", agent_id, type(node_data))
                                node_data = None
                    
                    if node_data is None:
                        value = None
                    elif isinstance(node_data, dict):
                        value = node_data.get("parsed") if "parsed" in node_data else node_data
                    else:
                        value = node_data
                    
                    if value is not None:
                        for field in field_path:
                            if isinstance(value, dict) and field in value:
                                value = value[field]
                            else:
                                value = None
                                break
                    
                    if isinstance(value, list):
                        # Filter dynamic options from options_source if they have conditions
                        filtered = []
                        for opt in value:
                            if isinstance(opt, dict):
                                cond_expr = opt.get("condition")
                                if cond_expr:
                                    try:
                                        if not evaluate_expression(cond_expr, context):
                                            continue
                                    except Exception as e:
                                        self.logger.warning("Condition evaluation failed for option {}: {}, skipping", opt.get("value", "unknown"), e)
                                        continue
                                # Remove condition before sending to UI
                                opt_copy = dict(opt)
                                opt_copy.pop("condition", None)
                                filtered.append(opt_copy)
                            else:
                                filtered.append(opt)
                        return filtered
        except Exception:
            pass

        # If options are already provided, use them (static options)
        # Filter static options based on their conditions
        if options and len(options) > 0:
            filtered = []
            for opt in options:
                if not isinstance(opt, dict):
                    filtered.append(opt)
                    continue
                    
                cond_expr = opt.get("condition")
                keep = True
                if cond_expr:
                    try:
                        keep = evaluate_expression(cond_expr, context)
                    except Exception as e:
                        self.logger.warning("Condition evaluation failed for option {}: {}, skipping", opt.get("value", "unknown"), e)
                        keep = False
                
                if not keep:
                    continue
                
                # Copy option and remove condition before sending to UI
                opt_copy = dict(opt)
                opt_copy.pop("condition", None)
                
                # Render description if it contains Jinja2 templates
                if "description" in opt_copy and isinstance(opt_copy["description"], str):
                    try:
                        from jinja2 import Environment, Undefined
                        env = Environment(undefined=Undefined, autoescape=False)
                        if "{{" in opt_copy["description"] or "{%" in opt_copy["description"]:
                            # Build render context similar to gate description rendering
                            render_context = dict(context)
                            upstream = context.get("upstream", {}) if isinstance(context, dict) else {}
                            flat: Dict[str, Any] = {}
                            if isinstance(upstream, dict):
                                for agent_id, node in upstream.items():
                                    parsed = node.get("parsed") if isinstance(node, dict) else None
                                    if isinstance(parsed, dict):
                                        render_context.setdefault(agent_id, parsed)
                                        for k, v in parsed.items():
                                            flat.setdefault(k, v)
                            render_context.update(flat)
                            tmpl = env.from_string(opt_copy["description"])
                            opt_copy["description"] = tmpl.render(**render_context)
                    except Exception as e:
                        self.logger.warning("Failed to render option description template: {}, using original", e)
                        # Keep original description on render failure
                        pass
                
                filtered.append(opt_copy)
            
            return filtered

        # No options_source and no static options -> do not populate
        return []

    def _populate_field_options(self, field_options: list, context: Dict[str, Any], field_name: str, options_source: str = None) -> list:
        """Populate field options from explicit options_source only."""
        # Prefer explicit options_source if provided
        try:
            if options_source and isinstance(options_source, str) and "." in options_source:
                parts = options_source.split(".")
                agent_id = parts[0]
                field_path = parts[1:]
                upstream = context.get("upstream", {})
                if agent_id in upstream:
                    node_data = upstream[agent_id]
                    value = node_data.get("parsed") if isinstance(node_data, dict) else node_data
                    for field in field_path:
                        if isinstance(value, dict) and field in value:
                            value = value[field]
                        else:
                            value = None
                            break
                    if isinstance(value, list):
                        return value
        except Exception:
            pass

        # No options_source -> do not populate; use whatever field_options already has
        return field_options

    def _handle_gate_timeout(
        self,
        gate_type: str,
        on_timeout: str,
        fields: List[Dict],
        options: List[Dict],
        gate_config: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Handle gate timeout based on gate type and timeout policy"""
        if on_timeout == "approve":
            if gate_type == "approval":
                return {"decision": "approve", "data": {}}
            elif gate_type == "input":
                # Use field defaults or provide empty defaults for required fields
                data = {}
                for field in fields:
                    if "default" in field:
                        data[field["name"]] = field["default"]
                    elif field.get("required", False):
                        # Provide empty default for required fields without explicit defaults
                        if field.get("type") == "textarea":
                            data[field["name"]] = ""
                        elif field.get("type") == "select":
                            # Use first option as default
                            options = field.get("options", [])
                            data[field["name"]] = options[0]["value"] if options else ""
                        else:
                            data[field["name"]] = ""
                return {"decision": "continue", "data": data}
            elif gate_type == "selection":
                # Use default option
                default_option = next(
                    (
                        opt
                        for opt in options
                        if opt.get("value") == options[0].get("default")
                    ),
                    options[0] if options else None,
                )
                if default_option:
                    return {
                        "decision": "continue",
                        "data": {"selection": default_option["value"]},
                    }
                return {"decision": "continue", "data": {}}
        elif on_timeout == "reject":
            return None  # Will raise PipelineError
        elif on_timeout == "skip":
            return {"decision": "continue", "data": {}}
        elif on_timeout == "default":
            if gate_type == "selection":
                # Use the gate's default field, not the first option's default
                default_value = gate_config.get("default")
                if default_value:
                    default_option = next(
                        (opt for opt in options if opt.get("value") == default_value),
                        None,
                    )
                    if default_option:
                        return {
                            "decision": "continue",
                            "data": {"selection": default_option["value"]},
                        }
                # Fallback to first option if no default specified
                if options:
                    return {
                        "decision": "continue",
                        "data": {"selection": options[0]["value"]},
                    }
            return {"decision": "continue", "data": {}}

        return None

    def _get_default_buttons_for_gate_type(self, gate_type: str) -> Dict[str, Any]:
        """Get default button configuration for gate types"""
        defaults = {
            "approval": {
                "approve": {"label": "Approve", "description": "Approve and continue"},
                "reject": {"label": "Reject", "description": "Reject and stop"},
            },
            "input": {
                "continue": {
                    "label": "Continue",
                    "description": "Continue without input",
                },
                "retry": {
                    "label": "Retry with Input",
                    "description": "Retry with provided input",
                },
            },
            "selection": {
                "submit": {
                    "label": "Submit",
                    "description": "Submit selection and continue",
                }
            },
        }
        return defaults.get(gate_type, {})

    def _get_default_actions_for_gate_type(self, gate_type: str) -> Dict[str, str]:
        """Get default action configuration for gate types"""
        defaults = {
            "approval": {"on_approve": "continue", "on_reject": "stop"},
            "input": {"on_continue": "continue", "on_retry": "retry_node"},
            "selection": {"on_submit": "continue"},
        }
        return defaults.get(gate_type, {})

    def _get_effective_gate_config(self, gate_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get effective gate configuration with defaults applied"""
        gate_type = gate_config.get("type", "approval")

        # Start with the original config
        effective_config = gate_config.copy()

        # Apply default buttons if not specified
        if "buttons" not in effective_config:
            self.logger.debug(
                f"No custom buttons found for gate, applying defaults for type: {gate_type}"
            )
            effective_config["buttons"] = self._get_default_buttons_for_gate_type(
                gate_type
            )
        else:
            self.logger.info(
                f"Using custom buttons for gate: {effective_config.get('buttons')}"
            )

        return effective_config

    def _validate_gate_result(
        self, result: Dict[str, Any], gate_type: str, gate_config: Dict[str, Any]
    ) -> None:
        """Validate gate result based on gate type"""
        if not isinstance(result, dict):
            raise ValueError(f"Gate result must be a dict, got {type(result)}")

        decision = result.get("decision", "").lower()
        data = result.get("data", {})

        # Validate required fields for input gates (except retry/continue decisions)
        if gate_type == "input" and decision not in ["retry", "continue"]:
            for field in gate_config.get("fields", []):
                if field.get("required") and field["name"] not in data:
                    raise ValueError(
                        f"Required field '{field['name']}' missing from input gate result"
                    )

        # Validate selection data for selection gates
        elif gate_type == "selection":
            # NOTE: Validation for selection gates is minimal because matching logic (which runs BEFORE validation)
            # already handles all the heavy lifting:
            # 1. Matching finds the option from available options
            # 2. Matching replaces {"selection": "OPT-2"} with the complete option object
            # 3. Matching logs errors if it can't find the option
            # 
            # Validation here is just a sanity check that matching succeeded (data should be the complete option object)
            # If matching failed, it would have already logged an error, so we just verify the structure is correct
            if "selection" in data:
                # Matching didn't run or failed - this is unexpected since matching runs before validation
                # Log a warning but don't fail (matching already logged the error)
                selection_value = data.get("selection")
                self.logger.warning(
                    "Selection gate validation: data still contains 'selection' key after matching. "
                    "This indicates matching failed or didn't run. selection_value='{}', data={}",
                    selection_value, data
                )
                # Don't raise exception - matching already logged the error, and we want to continue
                # so downstream agents can handle the error gracefully
            elif "value" in data or "id" in data:
                # Matching succeeded - data is the complete option object
                # This is the expected state after matching
                self.logger.debug("Selection gate validation: option object structure is valid (has value='{}' or id='{}')", 
                                 data.get("value"), data.get("id"))
            else:
                # Neither selection key nor option object structure - this is unexpected
                # But don't fail hard - just log a warning
                self.logger.warning(
                    "Selection gate validation: data has unexpected structure. "
                    "Expected either 'selection' (before matching) or 'value'/'id' (after matching), "
                    "but got: data={}",
                    data
                )
                # Don't raise exception - let downstream agents handle gracefully

    def _determine_flow_action(
        self,
        result: Dict[str, Any],
        gate_type: str,
        flow_control_config: Dict[str, Any],
    ) -> Any:
        """Determine flow action based on gate result and config.
        
        Returns:
            str: Simple flow action ("continue", "stop", "skip_to_node", "retry_node")
            BaseRunner: Compiled runner for array of nodes (SequentialRunner)
        """
        decision = result.get("decision", "").lower()

        self.logger.info(
            "Determining flow action: decision='{}', flow_control_config={}",
            decision,
            flow_control_config,
        )

        # Generic button action handling: on_<button_name>
        action_key = f"on_{decision}"
        if action_key in flow_control_config:
            action = flow_control_config[action_key]
            self.logger.info("Found action key '{}' -> '{}'", action_key, action)
            # If action is a BaseRunner (compiled array), store it in context and return marker
            # This avoids serialization issues when result dict is stored in checkpoints
            from topaz_agent_kit.core.execution_patterns import BaseRunner
            if isinstance(action, BaseRunner):
                # Store BaseRunner in context under a special key (won't be serialized in checkpoints)
                # Use a key that includes the gate_id to avoid conflicts
                context_key = f"_gate_array_runner_{gate_type}_{decision}"
                # Note: We can't access context here, so we'll store the action_key
                # SequentialRunner will need to look it up from the gate's flow_control_config
                # For now, return the BaseRunner directly - it should only exist in memory during execution
                # If serialization is needed, we'll need a different approach
                return action
            return action

        # Default action if no specific button action is defined
        self.logger.info(
            "No action key '{}' found, using default 'continue'", action_key
        )
        return "continue"
