"""
Schema Instruction Generator for AgentOS Memory.

Auto-generates read/write instructions from memory schemas.
"""

from typing import Dict, Optional
from topaz_agent_kit.core.agentos.memory_config import MemorySchema, MemoryDirectory
from topaz_agent_kit.utils.logger import Logger


class SchemaInstructionGenerator:
    """Generates instructions for memory schemas."""
    
    def __init__(self):
        self.logger = Logger("SchemaInstructionGenerator")
    
    def generate_instructions(self, directory: MemoryDirectory) -> Dict[str, str]:
        """
        Generate instructions for all schemas in a directory.
        
        Returns:
            Dictionary mapping schema names to instruction text
        """
        instructions = {}
        
        for schema_name, schema in directory.schemas.items():
            schema_instructions = self._generate_schema_instructions(directory, schema_name, schema)
            if schema_instructions:
                instructions[schema_name] = schema_instructions
        
        return instructions
    
    def _generate_schema_instructions(self, directory: MemoryDirectory, schema_name: str, schema: MemorySchema) -> Optional[str]:
        """Generate instructions for a single schema."""
        # If custom instructions provided, use those
        if schema.instructions:
            read_inst = schema.instructions.get("read", "")
            write_inst = schema.instructions.get("write", "")
            if read_inst or write_inst:
                parts = []
                if read_inst:
                    parts.append(f"**Read**: {read_inst}")
                if write_inst and not directory.readonly:
                    parts.append(f"**Write**: {write_inst}")
                return "\n".join(parts)
        
        # Auto-generate instructions
        file_path = f"{directory.path.rstrip('/')}/<identifier>/{schema.file}"
        
        if schema.format == "jsonl":
            read_inst = f"`agentos_shell(command='cat {file_path}')` - Read all records (one JSON object per line)"
            if schema.write_mode == "append":
                write_inst = f"`agentos_shell(command='echo \"<single_line_json>\" >> {file_path}')` - Append new record (use `>>` to preserve history)"
            else:
                write_inst = f"`agentos_shell(command='echo \"<single_line_json>\" > {file_path}')` - Write records (overwrites existing)"
        elif schema.format == "json":
            read_inst = f"`agentos_shell(command='cat {file_path}')` - Read JSON file"
            if schema.write_mode == "append":
                write_inst = f"`agentos_shell(command='echo \"<json>\" >> {file_path}')` - Append to JSON (requires parsing existing, appending, then writing back)"
            else:
                write_inst = f"`agentos_shell(command='echo \"<json>\" > {file_path}')` - Write JSON file (overwrites existing)"
        else:  # markdown or other
            read_inst = f"`agentos_shell(command='cat {file_path}')` - Read file"
            if schema.write_mode == "append":
                write_inst = f"`agentos_shell(command='echo \"<content>\" >> {file_path}')` - Append to file"
            else:
                write_inst = f"`agentos_shell(command='echo \"<content>\" > {file_path}')` - Write file (overwrites existing)"
        
        parts = [f"**Read**: {read_inst}"]
        if not directory.readonly and not schema.readonly:
            parts.append(f"**Write**: {write_inst}")
        
        return "\n".join(parts)
    
    def format_schema_documentation(self, directory: MemoryDirectory) -> str:
        """Format schema documentation for prompt inclusion."""
        if not directory.schemas:
            return ""
        
        lines = [f"\n### File Schemas for {directory.path}:"]
        
        for schema_name, schema in directory.schemas.items():
            lines.append(f"\n**{schema_name}** (`{schema.file}`):")
            lines.append(f"- Format: {schema.format}")
            lines.append(f"- Write mode: {schema.write_mode}")
            if schema.structure:
                lines.append("- Structure:")
                self._format_structure(lines, schema.structure, indent="  ")
            
            instructions = self._generate_schema_instructions(directory, schema_name, schema)
            if instructions:
                lines.append(f"- Instructions: {instructions}")
        
        return "\n".join(lines)
    
    def _format_structure(self, lines: list, structure: Dict, indent: str = ""):
        """Recursively format structure definition."""
        for key, value in structure.items():
            if isinstance(value, dict):
                lines.append(f"{indent}- {key}: (object)")
                self._format_structure(lines, value, indent + "  ")
            elif isinstance(value, list):
                lines.append(f"{indent}- {key}: (array)")
            else:
                lines.append(f"{indent}- {key}: {value}")
