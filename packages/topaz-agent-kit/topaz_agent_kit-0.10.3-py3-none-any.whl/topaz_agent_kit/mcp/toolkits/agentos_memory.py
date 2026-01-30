"""
AgentOS Memory MCP Toolkit - Filesystem-based memory for agents.

Provides a single `agentos_shell` tool that enables agents to use Unix-like
commands (ls, cat, grep, echo, semgrep) in a secure, sandboxed environment
with auto-indexing for semantic search.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import yaml
from contextvars import ContextVar

from fastmcp import FastMCP

from topaz_agent_kit.core.agentos import SafeKernel, MemoryConfigLoader
from topaz_agent_kit.utils.logger import Logger

# Context variable to store the current agent_id when tools are called
# This allows the framework to inject agent_id automatically
# Framework should set this when agents execute: _current_agent_id.set(agent_id)
_current_agent_id: ContextVar[Optional[str]] = ContextVar('_current_agent_id', default=None)

# Export function for framework to set agent_id in context
def set_current_agent_id(agent_id: Optional[str]) -> None:
    """Set the current agent_id in context for auto-injection into MCP tools.
    
    Args:
        agent_id: Agent identifier to set, or None to clear the context.
    """
    _current_agent_id.set(agent_id)


class AgentOSMemoryMCPTools:
    """MCP toolkit for AgentOS filesystem-based memory."""

    def __init__(self, data_root: str = "./data/agentos", project_dir: Optional[str] = None, **_: Any) -> None:
        """
        Initialize AgentOS Memory toolkit.
        
        Args:
            data_root: Root directory for AgentOS data storage.
            project_dir: Optional project directory for loading memory configs.
        """
        self._logger = Logger("MCP.AgentOSMemory")
        self.data_root = Path(data_root).resolve()
        self.project_dir = Path(project_dir) if project_dir else None
        self._kernels: Dict[str, SafeKernel] = {}
        self._memory_config_loader = MemoryConfigLoader(self.project_dir) if self.project_dir else None
        self._logger.info("AgentOSMemoryMCPTools initialized with data_root={}, project_dir={}", self.data_root, self.project_dir)

    def _load_agent_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Load agent configuration from YAML file."""
        if not self.project_dir:
            return None
        
        try:
            agent_config_path = self.project_dir / "config" / "agents" / f"{agent_id}.yml"
            if not agent_config_path.exists():
                self._logger.debug("Agent config not found: {}", agent_config_path)
                return None
            
            with open(agent_config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self._logger.warning("Failed to load agent config for {}: {}", agent_id, e)
            return None
    
    def _load_pipeline_config(self, pipeline_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Load pipeline configuration from YAML file.
        
        Args:
            pipeline_id: Optional pipeline ID to load specific pipeline config.
                        If None, loads main pipeline.yml.
        """
        if not self.project_dir:
            return None
        
        try:
            # If pipeline_id is provided, try to load individual pipeline config
            if pipeline_id:
                pipeline_config_path = self.project_dir / "config" / "pipelines" / f"{pipeline_id}.yml"
                if pipeline_config_path.exists():
                    with open(pipeline_config_path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                        self._logger.debug("Loaded individual pipeline config: {}", pipeline_config_path)
                        return config
                else:
                    self._logger.debug("Individual pipeline config not found: {}", pipeline_config_path)
            
            # Fallback to main pipeline.yml
            pipeline_config_path = self.project_dir / "config" / "pipeline.yml"
            if not pipeline_config_path.exists():
                self._logger.debug("Pipeline config not found: {}", pipeline_config_path)
                return None
            
            with open(pipeline_config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self._logger.warning("Failed to load pipeline config: {}", e)
            return None
    
    def _get_pipeline_id_from_context(self, agent_id: str) -> Optional[str]:
        """Try to determine pipeline_id by searching pipeline configs for this agent."""
        if not self.project_dir:
            return None
        
        try:
            # Load main pipeline config
            main_pipeline_config = self._load_pipeline_config()
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
                                node_id = node.get("id")
                                config_file = node.get("config_file")
                                # Extract agent_id from config_file (e.g., "agents/reply_context_wizard.yml" -> "reply_context_wizard")
                                if config_file:
                                    agent_id_from_file = Path(config_file).stem
                                    if agent_id_from_file == agent_id:
                                        # Extract pipeline_id from pipeline filename (e.g., "pipelines/reply_wizard.yml" -> "reply_wizard")
                                        pipeline_id = pipeline_file.stem
                                        self._logger.debug("Found pipeline_id '{}' for agent '{}'", pipeline_id, agent_id)
                                        return pipeline_id
                            elif isinstance(node, str) and node == agent_id:
                                # Direct agent_id match
                                pipeline_id = pipeline_file.stem
                                self._logger.debug("Found pipeline_id '{}' for agent '{}' (direct match)", pipeline_id, agent_id)
                                return pipeline_id
                    except Exception as e:
                        self._logger.debug("Failed to load pipeline file {}: {}", pipeline_file, e)
                        continue
            
            # Check if single-pipeline structure (has "nodes" key directly)
            elif "nodes" in main_pipeline_config:
                nodes = main_pipeline_config.get("nodes", [])
                for node in nodes:
                    if isinstance(node, dict):
                        node_id = node.get("id")
                        config_file = node.get("config_file")
                        if config_file:
                            agent_id_from_file = Path(config_file).stem
                            if agent_id_from_file == agent_id:
                                # For single pipeline, try to get pipeline_id from config or use default
                                # Check if pipeline.yml has an "id" field
                                pipeline_id = main_pipeline_config.get("id")
                                if not pipeline_id:
                                    # Try to infer from filename or use "default"
                                    pipeline_id = "default"
                                self._logger.debug("Found pipeline_id '{}' for agent '{}' (single pipeline)", pipeline_id, agent_id)
                                return pipeline_id
                    elif isinstance(node, str) and node == agent_id:
                        pipeline_id = main_pipeline_config.get("id", "default")
                        self._logger.debug("Found pipeline_id '{}' for agent '{}' (single pipeline, direct match)", pipeline_id, agent_id)
                        return pipeline_id
            
            self._logger.debug("Could not determine pipeline_id for agent '{}'", agent_id)
            return None
            
        except Exception as e:
            self._logger.warning("Failed to determine pipeline_id for agent {}: {}", agent_id, e)
            return None

    def _get_kernel(
        self,
        agent_id: str = "default",
        pipeline_id: Optional[str] = None
    ) -> SafeKernel:
        """
        Get or create SafeKernel instance for an agent.
        
        Args:
            agent_id: Agent identifier.
            pipeline_id: Pipeline identifier for shared memory.
            
        Returns:
            SafeKernel instance for this agent.
        """
        cache_key = f"{agent_id}:{pipeline_id or 'default'}"
        
        if cache_key not in self._kernels:
            self._logger.debug("Creating new SafeKernel for agent={}, pipeline={}", agent_id, pipeline_id)
            
            # Load memory config if available
            memory_config = None
            if self._memory_config_loader:
                agent_config = self._load_agent_config(agent_id)
                # Load pipeline config with pipeline_id to get the correct individual pipeline file
                pipeline_config = self._load_pipeline_config(pipeline_id=pipeline_id)
                
                if agent_config:
                    memory_config = self._memory_config_loader.load_agent_memory_config(
                        agent_config=agent_config,
                        pipeline_config=pipeline_config,
                        pipeline_id=pipeline_id,
                        agent_id=agent_id
                    )
                    if memory_config:
                        self._logger.info("Loaded memory config for agent {}: {} directories, {} shared, {} global", 
                                        agent_id, len(memory_config.directories), len(memory_config.shared_directories), len(memory_config.global_directories))
            
            self._kernels[cache_key] = SafeKernel(
                data_root=str(self.data_root),
                agent_id=agent_id,
                pipeline_id=pipeline_id,
                enable_audit_log=True,
                memory_config=memory_config,
                project_dir=self.project_dir,
            )
        
        return self._kernels[cache_key]

    def register(self, mcp: FastMCP) -> None:
        """Register AgentOS memory tools with MCP server."""

        @mcp.tool(name="agentos_shell")
        def agentos_shell(
            command: str,
            agent_id: Optional[str] = None,
            pipeline_id: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Execute a shell command in the agent's secure filesystem environment.
            
            This tool provides a Unix-like shell interface with commands like:
            - Navigation: ls, cd, pwd
            - File Reading: cat, head, tail
            - Search: grep, find, semgrep (semantic search)
            - File Operations: echo (with > and >> redirection), mkdir, touch
            - Utilities: tree, wc
            
            Files written to /memory/ are automatically indexed for semantic search.
            
            Args:
                command: Shell command to execute (e.g., "ls /memory", "cat /memory/note.md").
                agent_id: Agent identifier (optional, auto-detected from context if not provided).
                pipeline_id: Optional pipeline identifier for shared memory (auto-detected from agent config if not provided).
            
            Returns:
                Dict with:
                  - success: bool indicating if command succeeded
                  - output: command output string
                  - error: error message if any, else empty string
            """
            if not command:
                return {
                    "success": False,
                    "output": "",
                    "error": "Command cannot be empty"
                }
            
            try:
                # Resolve agent_id: use provided value, or try context variable, or default
                if not agent_id:
                    context_agent_id = _current_agent_id.get()
                    if context_agent_id:
                        agent_id = context_agent_id
                        self._logger.debug("Auto-detected agent_id '{}' from context variable", agent_id)
                    else:
                        agent_id = "default"
                        self._logger.warning(
                            "agent_id not provided in tool call and not available in context variable - using 'default'. "
                            "This indicates the framework is not injecting agent_id into tool calls. "
                            "For proper operation, agent_id should be passed as a tool parameter."
                        )
                
                # Resolve pipeline_id: use provided value, or try to detect from agent config
                if not pipeline_id:
                    pipeline_id = self._get_pipeline_id_from_context(agent_id)
                    if pipeline_id:
                        self._logger.debug("Auto-detected pipeline_id '{}' for agent '{}'", pipeline_id, agent_id)
                    else:
                        # Only warn if agent_id is not "default" (meaning we have a real agent but couldn't find pipeline)
                        if agent_id != "default":
                            self._logger.warning(
                                "pipeline_id not provided in tool call and could not be auto-detected for agent '{}' - using None. "
                                "This may indicate the agent is not part of a pipeline or pipeline config is missing. "
                                "For proper operation, pipeline_id should be passed as a tool parameter.",
                                agent_id
                            )
                        pipeline_id = None  # Will be None if not found
                
                # Always log the resolved values (even if None/default)
                # Note: In ideal operation, agent_id should never be "default" and pipeline_id should be set for pipeline agents
                self._logger.input(
                    "agentos_shell INPUT: command={}, agent_id={}, pipeline_id={}",
                    command,
                    agent_id,
                    pipeline_id or "default"
                )
                
                kernel = self._get_kernel(agent_id=agent_id, pipeline_id=pipeline_id)
                output = kernel.run_shell_command(command)
                
                # Check if output indicates an error
                success = not output.startswith("Error [")
                
                result = {
                    "success": success,
                    "output": output,
                    "error": "" if success else output
                }
                
                # Log actual result (truncate if too long for readability)
                output_preview = output[:500] + "..." if len(output) > 500 else output
                error_preview = result["error"][:500] + "..." if result["error"] and len(result["error"]) > 500 else result["error"]
                
                if success:
                    self._logger.output(
                        "agentos_shell OUTPUT: success=true, output={}",
                        output_preview
                    )
                else:
                    self._logger.output(
                        "agentos_shell OUTPUT: success=false, error={}",
                        error_preview
                    )
                
                return result
                
            except Exception as exc:
                error_msg = f"Error [INTERNAL]: {str(exc)}"
                self._logger.error("agentos_shell failed: {}", exc)
                return {
                    "success": False,
                    "output": "",
                    "error": error_msg
                }
