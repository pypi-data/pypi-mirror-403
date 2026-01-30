import json
from pathlib import Path
from typing import Any, Dict

from topaz_agent_kit.utils.logger import Logger


def normalize_path_for_prompt(path_value: Any) -> Any:
    """
    Normalize path values for inclusion in prompts.
    
    Converts Windows backslashes to forward slashes to prevent Azure OpenAI
    content filter violations. This is safe because:
    - Python's pathlib handles both separators correctly
    - Forward slashes work on Windows for file operations
    - Prevents content filter false positives from backslash characters
    
    Args:
        path_value: Path value (Path object, string, or other type)
        
    Returns:
        Normalized path string if it's a path, otherwise original value
    """
    if path_value is None:
        return None
    
    # Convert Path objects to strings
    if isinstance(path_value, Path):
        path_str = str(path_value)
    elif isinstance(path_value, str):
        path_str = path_value
    else:
        # Not a path-like value, return as-is
        return path_value
    
    # Normalize backslashes to forward slashes
    # This prevents Azure content filter issues on Windows
    normalized = path_str.replace('\\', '/')
    
    return normalized


class PromptLoader:
    """A class for loading and rendering prompt templates with clear separation of concerns."""
    
    def __init__(self, project_dir: Path):
        """Initialize the PromptLoader with a project directory.
        
        Args:
            project_dir: Project root directory for resolving relative paths
        """
        self.project_dir = project_dir
        self.logger = Logger("PromptLoader")
    
    def load_prompt(self, spec: Dict[str, Any] | None) -> str:
        """Load a prompt template from a spec WITHOUT rendering variables.
        
        This method only loads the template content, it does not render any variables.
        Use this when you need the raw template to render variables separately.
        
        Args:
            spec: Prompt specification containing inline, file, or jinja definitions
            
        Returns:
            Raw prompt template string
            
        spec:
          - inline: str (used verbatim)
          - file: str (path relative to project_dir)
          - jinja: str (either a file path or inline template content)
        """
        if not spec:
            self.logger.debug("No prompt spec provided, returning empty string")
            return ""
        
        # Handle nested description structure (e.g., {'description': {'jinja': 'file.jinja'}})
        if "description" in spec and isinstance(spec["description"], dict):
            self.logger.debug("Found nested description structure, using it as spec")
            spec = spec["description"]
        
        inline = spec.get("inline")
        file_path = spec.get("file")
        jinja_def = spec.get("jinja")
        
        self.logger.debug("Prompt spec: inline={}, file={}, jinja={}", 
                        bool(inline), bool(file_path), bool(jinja_def))

        # Resolve source
        source: str = ""
        if isinstance(inline, str) and inline.strip():
            self.logger.debug("Using inline prompt ({} chars)", len(inline))
            source = inline
        elif isinstance(file_path, str) and file_path.strip():
            self.logger.debug("Loading prompt from file: {}", file_path)
            source = self._read_text(file_path)
        elif isinstance(jinja_def, str) and jinja_def.strip():
            # If it looks like a file and exists, read it; else treat as inline template
            jp = Path(jinja_def)
            if jp.is_absolute():
                # Absolute path - use as is
                if jp.exists():
                    self.logger.debug("Loading Jinja template from absolute file: {}", jinja_def)
                    source = self._read_text(jinja_def)
                else:
                    self.logger.debug("Using Jinja template as inline content ({} chars)", len(jinja_def))
                    source = jinja_def
            else:
                # Relative path - resolve relative to config/ directory
                config_path = Path(self.project_dir) / "config" / jp
                
                if config_path.exists():
                    self.logger.debug("Loading Jinja template from config/: {}", jinja_def)
                    source = self._read_text(str(config_path))
                else:
                    self.logger.error("Prompt file not found in config/: {}", config_path)
                    return ""
        else:
            self.logger.debug("No valid prompt source found")
            return ""

        self.logger.debug("Loaded prompt template ({} chars)", len(source))
        return source

    def render_prompt(self, template: str, *, variables: Dict[str, Any]) -> str:
        """Render a prompt template with variables using Jinja2.
        
        This method only renders variables in an already-loaded template.
        Use this when you have a template string and want to substitute variables.
        
        Args:
            template: The prompt template string (may contain {{ variable }} placeholders)
            variables: Dictionary of variables to substitute in the template
            
        Returns:
            Rendered prompt string with variables substituted
        """
        self.logger.debug("Rendering template ({} chars) with {} variables", len(template), len(variables))
        
        if not template.strip():
            self.logger.warning("Empty template provided, returning empty string")
            return ""
        
        # Use Jinja2 template rendering
        return self._render_jinja(template, variables)

    def load_and_render_prompt(self, spec: Dict[str, Any] | None, *, data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Load a prompt template from a spec AND render variables in one step.
        
        This is a convenience method that combines load_prompt() and render_prompt().
        Use this when you want to load and render in a single operation.
        
        Args:
            spec: Prompt specification containing inline, file, or jinja definitions
            data: Variables to pass into the template environment
            context: Additional context variables
            
        Returns:
            Fully rendered prompt string with variables substituted
            
        spec:
          - inline: str (used verbatim)
          - file: str (path relative to project_dir)
          - jinja: str (either a file path or inline template content)
          - vars: mapping to pass into the template environment
          - description: dict containing nested prompt definitions
        """
        # Step 1: Load the template using load_prompt()
        template = self.load_prompt(spec)
        
        if not template.strip():
            self.logger.debug("No template loaded, returning empty string")
            return ""
        
        # Step 2: Prepare variables for rendering
        variables = {"data": data, "context": context}
        # Convenience: also expose data/context at top-level for {{ user_text }} style access
        try:
            if isinstance(data, dict):
                variables.update(data)
            if isinstance(context, dict):
                variables.update(context)
        except Exception:
            pass
        self.logger.debug("Prompt variables: {} data keys, {} context keys", len(data), len(context))

        # Step 3: Render the template using render_prompt()
        return self.render_prompt(template, variables=variables)

    def _read_text(self, file_path: str | Path) -> str:
        """Read text content from a file path."""
        p = Path(file_path)
        self.logger.info("_read_text called with: {} (is_absolute: {})", file_path, p.is_absolute())
        if not p.is_absolute():
            # Resolve relative to config/ directory
            config_path = Path(self.project_dir) / "config" / p
            self.logger.info("Checking config path: {} (exists: {})", config_path, config_path.exists())
            if config_path.exists():
                self.logger.debug("Reading prompt file from config/: {}", config_path)
                p = config_path
            else:
                self.logger.error("Prompt file not found in config/: {}", config_path)
                raise FileNotFoundError(f"Prompt file not found: {config_path}")
        else:
            self.logger.debug("Reading prompt file from absolute path: {}", p)
        try:
            content = p.read_text(encoding="utf-8")
            self.logger.debug("Successfully read prompt file: {} ({} chars)", p, len(content))
            return content
        except Exception as e:
            self.logger.error("Failed to read prompt file '{}': {}", p, e)
            return f"Error reading prompt file '{p}': {e}"

    def _render_jinja(self, template_str: str, variables: Dict[str, Any]) -> str:
        """Render Jinja2 template with variables."""
        self.logger.debug("Rendering Jinja template ({} chars) with {} variables", len(template_str), len(variables))
        try:
            from jinja2 import Environment, Undefined
            from topaz_agent_kit.utils.jinja2_filters import register_jinja2_filters

            # Normalize variables to prevent Azure content filter issues
            # 1. Normalize path variables (Windows backslashes -> forward slashes)
            # 2. Recursively serialize nested complex objects as JSON strings
            #    (prevents platform-specific repr() differences while preserving top-level dict structure for Jinja2 dot notation)
            
            def normalize_value(value: Any, is_top_level: bool = False) -> Any:
                """
                Recursively normalize a value for prompt rendering.
                
                Args:
                    value: Value to normalize
                    is_top_level: True if this is a top-level variable (preserve dict structure for dot notation)
                
                Returns:
                    Normalized value
                """
                # Handle None
                if value is None:
                    return None
                
                # Handle Path objects
                if isinstance(value, Path):
                    return normalize_path_for_prompt(value)
                
                # Handle strings - check if it's a path
                if isinstance(value, str):
                    has_backslash = '\\' in value
                    has_drive_letter = len(value) >= 2 and value[1] == ':' and value[0].isalpha()
                    if has_backslash or (has_drive_letter and ('/' in value or '\\' in value)):
                        return normalize_path_for_prompt(value)
                    return value
                
                # Handle dicts
                if isinstance(value, dict):
                    # For top-level dicts, we need to preserve structure for Jinja2 dot notation
                    # (e.g., argus_journal_extractor.extracted_entry), but also serialize nested dicts
                    if is_top_level:
                        # Recursively normalize nested values but keep as dict
                        # Nested dicts/lists will be serialized as JSON strings
                        normalized_dict = {}
                        for k, v in value.items():
                            normalized_dict[k] = normalize_value(v, is_top_level=False)
                        return normalized_dict
                    else:
                        # For nested dicts, serialize as JSON string to prevent platform-specific repr() issues
                        # This ensures consistent formatting and prevents content filter violations
                        try:
                            return json.dumps(value, ensure_ascii=False, separators=(',', ':'))
                        except (TypeError, ValueError) as e:
                            self.logger.warning("Failed to serialize nested dict as JSON, using str(): {}", e)
                            return str(value)
                
                # Handle lists
                if isinstance(value, list):
                    # For top-level lists, preserve structure but normalize items
                    if is_top_level:
                        return [normalize_value(item, is_top_level=False) for item in value]
                    else:
                        # For nested lists, serialize as JSON string
                        try:
                            return json.dumps(value, ensure_ascii=False, separators=(',', ':'))
                        except (TypeError, ValueError) as e:
                            self.logger.warning("Failed to serialize nested list as JSON, using str(): {}", e)
                            return str(value)
                
                # For other types (primitives), return as-is
                return value
            
            normalized_variables = {}
            path_keywords = ['path', 'dir', 'file', 'database']
            
            for key, value in variables.items():
                # Check if this looks like a path variable by name
                is_path_by_name = any(keyword in key.lower() for keyword in path_keywords)
                
                if is_path_by_name and isinstance(value, (str, Path)):
                    # Path variable - normalize paths
                    normalized_variables[key] = normalize_path_for_prompt(value)
                    self.logger.debug("Normalized path variable '{}'", key)
                else:
                    # Normalize value (preserve top-level dict structure for Jinja2 dot notation)
                    normalized_variables[key] = normalize_value(value, is_top_level=True)
                    if isinstance(value, dict) and not is_path_by_name:
                        self.logger.debug("Normalized dict variable '{}' (preserved structure, normalized nested values)", key)

            # Use permissive Undefined so missing variables render as empty strings
            env = Environment(undefined=Undefined, autoescape=False)
            register_jinja2_filters(env)
            tmpl = env.from_string(template_str)
            result = tmpl.render(**normalized_variables)
            self.logger.debug("Successfully rendered Jinja template ({} chars)", len(result))
            return result
        except Exception as e:
            self.logger.error("Jinja render error: {}", e)
            # Fallback: return raw template with note
            return f"[Jinja render error: {e}]\n{template_str}"
