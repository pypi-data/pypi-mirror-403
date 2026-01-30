"""
Memory Configuration Loader for AgentOS.

Loads memory configuration from pipeline.yml and agent.yml files,
merges them based on inheritance settings, and provides structured
memory configuration for agents.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

try:
    import yaml
except ImportError:
    yaml = None

from topaz_agent_kit.utils.logger import Logger


@dataclass
class MemorySchema:
    """Configuration for a memory file schema."""
    file: str
    format: str  # "jsonl", "json", "markdown"
    write_mode: str = "overwrite"  # "append", "overwrite"
    readonly: bool = False
    structure: Dict[str, Any] = field(default_factory=dict)  # Simple structure definition
    instructions: Optional[Dict[str, str]] = None  # Optional custom instructions (read, write)


@dataclass
class MemoryDirectory:
    """Configuration for a memory directory."""
    path: str
    description: str
    readonly: bool = False
    auto_index: bool = True
    bootstrap: bool = True  # Create on init
    template_source: Optional[str] = None  # Template source path (e.g., "config/memory/shared/pipeline/reply_wizard/email_templates/")
    schemas: Dict[str, MemorySchema] = field(default_factory=dict)  # File schemas for this directory


@dataclass
class PathMapping:
    """Virtual path to actual path mapping configuration."""
    prefix: str
    type: str  # "pipeline_shared", "agent_memory", "agent_workspace", etc.
    base: str  # Template like "{pipeline_id}/agents/{agent_id}/memory" or "{pipeline_id}/shared"


@dataclass
class MemoryConfig:
    """Complete memory configuration for an agent."""
    inherit: bool = True
    directories: List[MemoryDirectory] = field(default_factory=list)
    shared_directories: List[MemoryDirectory] = field(default_factory=list)
    global_directories: List[MemoryDirectory] = field(default_factory=list)
    path_mappings: Dict[str, PathMapping] = field(default_factory=dict)
    prompt_section: Optional[Dict[str, Any]] = None  # inline/file/jinja spec


class MemoryConfigLoader:
    """Loads and merges memory configuration from YAML files."""
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.logger = Logger("MemoryConfigLoader")
        self._global_memory_cache: Optional[List[MemoryDirectory]] = None
    
    def load_global_memory_config(self) -> List[MemoryDirectory]:
        """
        Load global memory configuration from config/memory/memory.yml.
        
        Returns:
            List of global memory directories, or empty list if not configured
        """
        # Use cache if available
        if self._global_memory_cache is not None:
            return self._global_memory_cache
        
        global_dirs = []
        memory_config_path = self.project_dir / "config" / "memory" / "memory.yml"
        
        if not memory_config_path.exists():
            # No global memory config - return empty list
            self._global_memory_cache = []
            return global_dirs
        
        if yaml is None:
            self.logger.warning("PyYAML not available, cannot load global memory config")
            self._global_memory_cache = []
            return global_dirs
        
        try:
            with memory_config_path.open("r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            
            memory_config = config.get("memory", {})
            global_config = memory_config.get("global", {})
            global_dirs = self._parse_directories(
                global_config.get("directories", [])
            )
            
            self.logger.debug("Loaded {} global memory directories", len(global_dirs))
            self._global_memory_cache = global_dirs
            return global_dirs
        except Exception as e:
            self.logger.warning("Failed to load global memory config from {}: {}", memory_config_path, e)
            self._global_memory_cache = []
            return global_dirs
    
    def load_agent_memory_config(
        self,
        agent_config: Dict[str, Any],
        pipeline_config: Optional[Dict[str, Any]] = None,
        pipeline_id: Optional[str] = None,
        agent_id: str = "default"
    ) -> Optional[MemoryConfig]:
        """
        Load memory configuration for an agent.
        
        Args:
            agent_config: Agent YAML configuration
            pipeline_config: Pipeline YAML configuration (optional)
            pipeline_id: Pipeline identifier
            agent_id: Agent identifier
            
        Returns:
            MemoryConfig if memory is configured, None otherwise
        """
        agent_memory = agent_config.get("memory")
        if not agent_memory:
            # No memory config = memory not enabled
            return None
        
        # Load pipeline shared memory
        pipeline_shared = []
        if pipeline_config:
            pipeline_memory = pipeline_config.get("memory", {})
            pipeline_shared_config = pipeline_memory.get("shared", {})
            pipeline_shared = self._parse_directories(
                pipeline_shared_config.get("directories", [])
            )
        
        # Load global memory (always available to all agents)
        global_directories = self.load_global_memory_config()
        
        # Load agent memory
        inherit = agent_memory.get("inherit", True)
        agent_dirs = self._parse_directories(
            agent_memory.get("directories", [])
        )
        
        # Merge based on inheritance
        if inherit and pipeline_shared:
            shared_directories = pipeline_shared
        else:
            shared_directories = []
        
        # Load path mappings (merge pipeline + agent)
        path_mappings = self._load_path_mappings(
            agent_memory,
            pipeline_config.get("memory", {}) if pipeline_config else {},
            pipeline_id,
            agent_id
        )
        
        # Load prompt section config
        prompt_section = agent_memory.get("prompt_section")
        
        return MemoryConfig(
            inherit=inherit,
            directories=agent_dirs,
            shared_directories=shared_directories,
            global_directories=global_directories,
            path_mappings=path_mappings,
            prompt_section=prompt_section
        )
    
    def _parse_directories(self, dir_configs: List[Dict[str, Any]]) -> List[MemoryDirectory]:
        """Parse directory configurations."""
        directories = []
        for dir_config in dir_configs:
            # Parse schemas if present
            schemas = {}
            if "schemas" in dir_config:
                for schema_name, schema_config in dir_config["schemas"].items():
                    schemas[schema_name] = MemorySchema(
                        file=schema_config["file"],
                        format=schema_config.get("format", "json"),
                        write_mode=schema_config.get("write_mode", "overwrite"),
                        readonly=schema_config.get("readonly", False),
                        structure=schema_config.get("structure", {}),
                        instructions=schema_config.get("instructions")
                    )
            
            directories.append(MemoryDirectory(
                path=dir_config["path"],
                description=dir_config.get("description", ""),
                readonly=dir_config.get("readonly", False),
                auto_index=dir_config.get("auto_index", True),
                bootstrap=dir_config.get("bootstrap", True),
                template_source=dir_config.get("template_source"),
                schemas=schemas
            ))
        return directories
    
    def _load_path_mappings(
        self,
        agent_memory: Dict[str, Any],
        pipeline_memory: Dict[str, Any],
        pipeline_id: Optional[str],
        agent_id: str
    ) -> Dict[str, PathMapping]:
        """Load and merge path mappings from config."""
        mappings = {}
        
        # Default path mappings
        defaults = {
            "/shared": PathMapping(
                prefix="/shared",
                type="pipeline_shared",
                base=f"{pipeline_id}/shared" if pipeline_id else "default/shared"
            ),
            "/global": PathMapping(
                prefix="/global",
                type="global_shared",
                base="global_shared"
            ),
            "/memory": PathMapping(
                prefix="/memory",
                type="agent_memory",
                base=f"{pipeline_id}/agents/{agent_id}/memory" if pipeline_id else f"default/agents/{agent_id}/memory"
            ),
            "/workspace": PathMapping(
                prefix="/workspace",
                type="agent_workspace",
                base=f"{pipeline_id}/agents/{agent_id}/workspace" if pipeline_id else f"default/agents/{agent_id}/workspace"
            )
        }
        
        # Load from pipeline config
        pipeline_mappings = pipeline_memory.get("path_mappings", {})
        for prefix, mapping_config in pipeline_mappings.items():
            mappings[prefix] = PathMapping(
                prefix=prefix,
                type=mapping_config.get("type", "pipeline_shared"),
                base=mapping_config.get("base", "").format(
                    pipeline_id=pipeline_id or "default"
                )
            )
        
        # Load from agent config (overrides pipeline)
        agent_mappings = agent_memory.get("path_mappings", {})
        for prefix, mapping_config in agent_mappings.items():
            mappings[prefix] = PathMapping(
                prefix=prefix,
                type=mapping_config.get("type", "agent_memory"),
                base=mapping_config.get("base", "").format(
                    pipeline_id=pipeline_id or "default",
                    agent_id=agent_id
                )
            )
        
        # Merge with defaults (config overrides defaults)
        final_mappings = {**defaults, **mappings}
        return final_mappings
