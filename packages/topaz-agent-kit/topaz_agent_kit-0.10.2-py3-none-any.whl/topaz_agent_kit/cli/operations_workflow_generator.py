"""
Operations Workflow Generator - Creates simple horizontal pipeline workflow diagrams
for the Operations Dashboard header using Graphviz.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from topaz_agent_kit.utils.logger import Logger
import yaml
import subprocess


class OperationsWorkflowGenerator:
    """Generates simple horizontal pipeline workflow SVG diagrams using Graphviz."""

    def __init__(self):
        self.logger = Logger("OperationsWorkflowGenerator")

    def generate_operations_workflow(
        self, project_path: str, overwrite: bool = False
    ) -> int:
        """Generate operations workflow diagram for a project.
        
        Args:
            project_path: Path to project root directory
            overwrite: Whether to overwrite existing files
            
        Returns:
            0 on success, 1 on failure, 0 if config doesn't exist (not an error)
        """
        try:
            project_dir = Path(project_path)
            ui_manifest_path = project_dir / "config" / "ui_manifest.yml"
            
            if not ui_manifest_path.exists():
                self.logger.debug("UI manifest not found: {}", ui_manifest_path)
                return 0  # Not an error if no config
            
            # Load UI manifest
            with open(ui_manifest_path, "r", encoding="utf-8") as f:
                ui_manifest = yaml.safe_load(f)
            
            # Check if operations_workflow section exists
            workflow_config = ui_manifest.get("operations_workflow")
            if not workflow_config:
                self.logger.debug("No operations_workflow config found, skipping")
                return 0  # Not an error if not configured
            
            # Get pipeline titles from pipelines section
            pipelines = ui_manifest.get("pipelines", [])
            pipeline_title_map = {}
            for pipeline in pipelines:
                pipeline_id = pipeline.get("id")
                pipeline_title = pipeline.get("title", pipeline_id)
                if pipeline_id:
                    pipeline_title_map[pipeline_id] = pipeline_title
            
            # Generate SVG using Graphviz
            svg_path = self._generate_svg(
                project_dir, 
                workflow_config, 
                pipeline_title_map,
                overwrite
            )
            
            if svg_path:
                self.logger.success("Generated operations workflow: {}", svg_path)
                return 0
            else:
                self.logger.warning("Failed to generate operations workflow")
                return 1
                
        except Exception as e:
            self.logger.error("Failed to generate operations workflow: {}", e)
            return 1
    
    def _generate_svg(
        self, 
        project_dir: Path, 
        workflow_config: dict,
        pipeline_title_map: Dict[str, str],
        overwrite: bool
    ) -> Optional[Path]:
        """Generate SVG file from workflow config using Graphviz.
        
        Args:
            project_dir: Project root directory
            workflow_config: operations_workflow config section
            pipeline_title_map: Mapping of pipeline_id to title
            overwrite: Whether to overwrite existing file
            
        Returns:
            Path to generated SVG file, or None on failure
        """
        try:
            nodes = workflow_config.get("nodes", [])
            edges = workflow_config.get("edges", [])
            output_path = workflow_config.get("output_path", "assets/operations_workflow.svg")
            
            if not nodes:
                self.logger.warning("No nodes defined in operations_workflow config")
                return None
            
            # Normalize output path - remove .svg extension for base name
            if output_path.endswith(".svg"):
                base_name = output_path[:-4]
            else:
                base_name = output_path
            
            # Ensure it's in assets/
            if not base_name.startswith("assets/"):
                if base_name.startswith("/"):
                    base_name = base_name[1:]
                if "/" not in base_name:
                    base_name = f"assets/{base_name}"
                elif not base_name.startswith("assets/"):
                    base_name = f"assets/{base_name}"
            
            # Generate DOT file path
            dot_file = project_dir / "ui" / "static" / f"{base_name}.dot"
            svg_file = project_dir / "ui" / "static" / f"{base_name}.svg"
            
            dot_file.parent.mkdir(parents=True, exist_ok=True)
            
            if svg_file.exists() and not overwrite:
                self.logger.debug("SVG file already exists: {}", svg_file)
                return svg_file
            
            # Generate DOT content
            dot_content = self._create_dot_content(nodes, edges, pipeline_title_map)
            
            # Write DOT file
            dot_file.write_text(dot_content, encoding="utf-8")
            self.logger.debug("Generated DOT file: {}", dot_file)
            
            # Generate SVG using Graphviz
            try:
                result = subprocess.run(
                    ["dot", "-Tsvg", str(dot_file), "-o", str(svg_file)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                
                # Post-process SVG to add highlighting styles
                svg_content = svg_file.read_text(encoding="utf-8")
                svg_content = self._post_process_svg(svg_content)
                svg_file.write_text(svg_content, encoding="utf-8")
                
                self.logger.success("Generated SVG: {}", svg_file)
                return svg_file
            except subprocess.CalledProcessError as e:
                self.logger.error("Failed to generate SVG: {}", e.stderr)
                return None
            except FileNotFoundError:
                self.logger.error(
                    "Graphviz 'dot' command not found. Install with: brew install graphviz"
                )
                return None
            
        except Exception as e:
            self.logger.error("Failed to generate SVG: {}", e)
            return None
    
    def _create_dot_content(
        self,
        nodes: List[str],
        edges: List[Dict[str, str]],
        pipeline_title_map: Dict[str, str]
    ) -> str:
        """Create DOT content for the workflow diagram.
        
        Args:
            nodes: List of pipeline IDs in display order
            edges: List of edge dicts with 'from' and 'to' keys
            pipeline_title_map: Mapping of pipeline_id to display title
            
        Returns:
            DOT content as string
        """
        dot_lines = [
            'digraph operations_workflow {',
            '  rankdir=LR;',
            '  bgcolor=transparent;',
            '  node [',
            '    shape=box,',
            '    style="filled,rounded",',
            '    fillcolor="#E3F2FD",',
            '    color="#666",',
            '    fontname="Arial, sans-serif",',
            '    fontsize=12,',
            '    fontcolor="#1f2937",',
            '    penwidth=2,',
            '    width=2,',
            '    height=0.6,',
            '    fixedsize=true',
            '  ];',
            '  edge [',
            '    color="#666",',
            '    penwidth=2,',
            '    arrowsize=0.8',
            '  ];',
            '',
        ]
        
        # Add nodes with consistent styling
        # Use pipeline titles from manifest, fallback to formatted pipeline_id
        # If the title has more than 2 words, insert a line break after the 2nd word
        for node_id in nodes:
            raw_title = pipeline_title_map.get(node_id, node_id.replace('_', ' ').title())
            words = raw_title.split()
            if len(words) > 2:
                # First two words on the first line, remaining words on the second line
                # Use \\n (escaped newline) - Graphviz will interpret this as a line break
                title_for_label = " ".join(words[:2]) + "\\n" + " ".join(words[2:])
            else:
                title_for_label = raw_title

            # Only escape quotes (not backslashes) - matching graphviz_generator pattern
            # This allows \\n to remain as \n in the DOT file, which Graphviz interprets as a line break
            title_escaped = title_for_label.replace('"', '\\"')
            dot_lines.append(
                f'  "{node_id}" [label="{title_escaped}"];'
            )
        
        dot_lines.append('')
        
        # Create a chain of edges (visible or invisible) to force horizontal layout
        # This ensures all nodes appear in a single horizontal line
        # Process in order: add invisible edges first, then visible edges
        for i in range(len(nodes) - 1):
            current_node = nodes[i]
            next_node = nodes[i + 1]
            
            # Check if there's already a visible edge between these nodes
            has_edge = any(
                edge.get("from") == current_node and edge.get("to") == next_node
                for edge in edges
            )
            
            if not has_edge:
                # Add invisible edge to maintain order and force horizontal layout
                dot_lines.append(
                    f'  "{current_node}" -> "{next_node}" [style=invis, weight=100, minlen=1];'
                )
        
        # Add visible edges (connections) - these will override invisible edges where they exist
        for edge in edges:
            from_id = edge.get("from")
            to_id = edge.get("to")
            
            if from_id not in nodes or to_id not in nodes:
                continue
            
            dot_lines.append(f'  "{from_id}" -> "{to_id}";')
        
        dot_lines.append('}')
        
        return '\n'.join(dot_lines)
    
    def _post_process_svg(self, svg_content: str) -> str:
        """Post-process Graphviz-generated SVG to add highlighting styles and IDs.
        
        Args:
            svg_content: Raw SVG content from Graphviz
            
        Returns:
            Modified SVG content with highlighting styles and proper IDs
        """
        import re
        
        # Graphviz structure: <g id="covenant" class="node"><title>covenant</title>...
        # We need to:
        # 1. Add class="pipeline-node" to node groups
        # 2. Ensure id="pipeline-{node_id}" format for highlighting
        # 3. Add highlighting CSS styles with proper dark mode support
        
        # Graphviz generates node IDs as "node1", "node2", etc., and includes <title> with the node name
        # We need to:
        # 1. Add pipeline-node class to all node groups
        # 2. Replace node IDs with pipeline-{pipeline_id} based on the title
        
        # First, add pipeline-node class to all node groups
        # Pattern: <g id="node1" class="node">
        # Need to be careful with the regex to avoid breaking attributes
        node_pattern = r'<g id="([^"]+)" class="node">'
        
        def add_pipeline_class(match):
            graphviz_id = match.group(1)
            # Add pipeline-node class
            return f'<g id="{graphviz_id}" class="node pipeline-node">'
        
        svg_content = re.sub(node_pattern, add_pipeline_class, svg_content)
        
        # Then, update IDs based on title tags
        # Pattern: <g id="node1" class="node pipeline-node"><title>covenant</title>
        title_pattern = r'<g id="(node\d+)" class="node pipeline-node"[^>]*>.*?<title>([^<]+)</title>'
        
        def update_id_from_title(match):
            graphviz_id = match.group(1)
            pipeline_id = match.group(2).strip()
            # Replace the node ID with pipeline-{pipeline_id} in the opening tag
            full_match = match.group(0)
            return full_match.replace(
                f'id="{graphviz_id}"',
                f'id="pipeline-{pipeline_id}" data-graphviz-id="{graphviz_id}"'
            )
        
        svg_content = re.sub(title_pattern, update_id_from_title, svg_content, flags=re.DOTALL)
        
        # Also update path fill colors to use CSS variables for dark mode
        # Replace hardcoded fill colors in paths with CSS class-based styling
        path_pattern = r'(<path[^>]*fill=")(#[^"]+)(")'
        
        def update_path_fill(match):
            # Keep the fill attribute but let CSS override it
            return f'{match.group(1)}{match.group(2)}{match.group(3)}'
        
        # Add our custom styles for highlighting and dark mode
        highlight_styles = '''    <style type="text/css">
      .pipeline-node {
        transition: all 0.2s ease;
      }
      /* Light mode default */
      .pipeline-node path {
        fill: #E3F2FD;
        stroke: #666;
      }
      .pipeline-node text {
        fill: #1f2937;
      }
      /* Highlighted state */
      .pipeline-node.highlighted path {
        fill: hsl(var(--accent, 210 92% 56%)) !important;
        stroke: hsl(var(--accent, 210 92% 56%)) !important;
      }
      .pipeline-node.highlighted text {
        fill: white !important;
      }
      /* Dark mode support */
      .dark .pipeline-node:not(.highlighted) path {
        fill: #1f2937 !important;
        stroke: #6b7280 !important;
      }
      .dark .pipeline-node:not(.highlighted) text {
        fill: #e5e7eb !important;
      }
      /* Edge styling */
      .edge path {
        stroke: #666;
      }
      .dark .edge path {
        stroke: #6b7280 !important;
      }
      .dark .edge polygon {
        fill: #6b7280 !important;
        stroke: #6b7280 !important;
      }
    </style>'''
        
        # Insert styles before closing </defs> or after existing <style>
        if '</defs>' in svg_content:
            svg_content = svg_content.replace('</defs>', f'{highlight_styles}\n  </defs>')
        elif '<style' in svg_content:
            # Find the closing </style> tag and add after it
            svg_content = svg_content.replace('</style>', f'</style>\n{highlight_styles}')
        else:
            # No defs or style, add before </svg>
            svg_content = svg_content.replace('</svg>', f'  {highlight_styles}\n</svg>')
        
        return svg_content
