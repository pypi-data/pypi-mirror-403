"""
SOP MCP Toolkit - Standard Operating Procedure reader for agents.

Provides tools for reading and navigating SOPs stored as structured
markdown files. Designed for SOP-driven agents across all pipelines.

SOP files are organized as:
    config/sop/<pipeline>/<agent>/
        ├── manifest.yml        (section registry)
        ├── overview.md
        ├── steps/
        │   ├── step_01_*.md
        │   └── step_02_*.md
        ├── scenarios/
        │   └── *.md
        └── troubleshooting.md
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from topaz_agent_kit.utils.logger import Logger


class SOPMCPTools:
    """MCP toolkit for Standard Operating Procedure operations."""

    def __init__(self, **kwargs: Any) -> None:
        self._logger = Logger("MCP.SOP")
        self._cache_size = kwargs.get("cache_size", 100)
        # In-memory caches
        self._manifests: Dict[str, Dict[str, Any]] = {}
        self._section_cache: Dict[str, str] = {}

    def _resolve_sop_path(self, project_dir: str, sop_path: str) -> Path:
        """Resolve SOP path to absolute path."""
        if os.path.isabs(sop_path):
            return Path(sop_path).parent
        return Path(project_dir) / Path(sop_path).parent

    def _load_manifest(self, manifest_path: Path) -> Dict[str, Any]:
        """Load and parse SOP manifest."""
        if not manifest_path.exists():
            raise FileNotFoundError(f"SOP manifest not found: {manifest_path}")
        with open(manifest_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _load_section_content(self, sop_dir: Path, file_path: str) -> str:
        """Load content of a specific section."""
        section_file = sop_dir / file_path
        if not section_file.exists():
            raise FileNotFoundError(f"SOP section not found: {section_file}")
        with open(section_file, "r", encoding="utf-8") as f:
            return f.read()

    def _get_cache_key(self, sop_path: str) -> str:
        """Generate cache key from SOP path."""
        return sop_path

    def _get_section_cache_key(self, sop_path: str, section_id: str) -> str:
        """Generate section cache key."""
        return f"{sop_path}:{section_id}"

    def register(self, mcp: FastMCP) -> None:
        """Register SOP tools with MCP server."""

        @mcp.tool(name="sop_initialize")
        def sop_initialize(
            project_dir: str,
            sop_path: str
        ) -> Dict[str, Any]:
            """
            Initialize SOP for an agent. Call at start of processing.

            Loads the SOP manifest and returns the overview section along with
            available sections for reference.

            Args:
                project_dir: Absolute path to project root directory
                sop_path: Relative path to SOP manifest (e.g., "config/sop/reconvoy/sop_matcher/manifest.yml")

            Returns:
                Dict with:
                  - sop_id: SOP identifier
                  - version: SOP version
                  - description: SOP description
                  - overview: Overview section content
                  - available_sections: List of available section IDs with descriptions
                  - workflow_steps: Ordered list of procedure steps
                  - error: Error message if any
            """
            self._logger.input("sop_initialize: project_dir={}, sop_path={}", project_dir, sop_path)

            try:
                # Resolve paths
                manifest_path = Path(project_dir) / sop_path
                sop_dir = manifest_path.parent

                # Load manifest
                manifest = self._load_manifest(manifest_path)

                # Cache manifest
                cache_key = self._get_cache_key(sop_path)
                self._manifests[cache_key] = {
                    "path": sop_dir,
                    "manifest": manifest
                }

                # Load overview section
                overview_content = ""
                sections = manifest.get("sections", [])
                overview_section = next(
                    (s for s in sections if s.get("id") == "overview"),
                    None
                )
                if overview_section:
                    try:
                        overview_content = self._load_section_content(
                            sop_dir, overview_section["file"]
                        )
                    except FileNotFoundError as e:
                        self._logger.warning("Overview section not found: {}", e)

                # Build available sections list
                available_sections = [
                    {
                        "id": s.get("id", ""),
                        "type": s.get("type", "reference"),
                        "description": s.get("description", ""),
                        "read_at": s.get("read_at", "on_demand")
                    }
                    for s in sections
                ]

                # Extract ordered workflow steps (procedure type only)
                workflow_steps = [
                    s["id"] for s in sections
                    if s.get("type") == "procedure"
                ]

                result = {
                    "sop_id": manifest.get("sop_id", ""),
                    "version": manifest.get("version", "1.0.0"),
                    "description": manifest.get("description", ""),
                    "overview": overview_content,
                    "available_sections": available_sections,
                    "workflow_steps": workflow_steps,
                    "error": ""
                }

                self._logger.output(
                    "sop_initialize: loaded {} sections, {} workflow steps",
                    len(sections), len(workflow_steps)
                )
                return result

            except Exception as e:
                self._logger.error("sop_initialize failed: {}", e)
                return {
                    "sop_id": "",
                    "version": "",
                    "description": "",
                    "overview": "",
                    "available_sections": [],
                    "workflow_steps": [],
                    "error": str(e)
                }

        @mcp.tool(name="sop_get_section")
        def sop_get_section(
            sop_path: str,
            section_id: str
        ) -> Dict[str, Any]:
            """
            Read a specific section from the SOP.

            Use this before performing each step to get detailed instructions.

            Args:
                sop_path: Relative path to SOP manifest (same as used in sop_initialize)
                section_id: Section to read (e.g., "step_02_find_match")

            Returns:
                Dict with:
                  - section_id: Requested section ID
                  - content: Section content (markdown)
                  - type: Section type (procedure, reference, example, troubleshooting)
                  - tools_used: List of tools referenced in this section
                  - outputs: Expected outputs from this section
                  - next_steps: Suggested next sections to read
                  - error: Error message if any
            """
            self._logger.input("sop_get_section: sop_path={}, section_id={}", sop_path, section_id)

            try:
                cache_key = self._get_cache_key(sop_path)
                if cache_key not in self._manifests:
                    return {
                        "section_id": section_id,
                        "content": "",
                        "type": "",
                        "tools_used": [],
                        "outputs": [],
                        "next_steps": [],
                        "error": "SOP not initialized. Call sop_initialize first."
                    }

                cached = self._manifests[cache_key]
                manifest = cached["manifest"]
                sop_dir = cached["path"]

                sections = manifest.get("sections", [])
                section = next(
                    (s for s in sections if s.get("id") == section_id),
                    None
                )

                if not section:
                    available = [s.get("id", "") for s in sections]
                    return {
                        "section_id": section_id,
                        "content": "",
                        "type": "",
                        "tools_used": [],
                        "outputs": [],
                        "next_steps": [],
                        "error": f"Section '{section_id}' not found. Available: {available}"
                    }

                # Check section cache
                section_cache_key = self._get_section_cache_key(sop_path, section_id)
                if section_cache_key in self._section_cache:
                    content = self._section_cache[section_cache_key]
                else:
                    content = self._load_section_content(sop_dir, section["file"])
                    # LRU-like cache management
                    if len(self._section_cache) >= self._cache_size:
                        oldest = next(iter(self._section_cache))
                        del self._section_cache[oldest]
                    self._section_cache[section_cache_key] = content

                # Find next steps (sections that depend on this one)
                next_steps = [
                    s["id"] for s in sections
                    if section_id in s.get("depends_on", [])
                ]

                result = {
                    "section_id": section_id,
                    "content": content,
                    "type": section.get("type", "reference"),
                    "tools_used": section.get("tools_used", []),
                    "outputs": section.get("outputs", []),
                    "next_steps": next_steps,
                    "error": ""
                }

                self._logger.output(
                    "sop_get_section: returned {} chars for section '{}'",
                    len(content), section_id
                )
                return result

            except Exception as e:
                self._logger.error("sop_get_section failed: {}", e)
                return {
                    "section_id": section_id,
                    "content": "",
                    "type": "",
                    "tools_used": [],
                    "outputs": [],
                    "next_steps": [],
                    "error": str(e)
                }

        @mcp.tool(name="sop_get_example")
        def sop_get_example(
            sop_path: str,
            scenario_name: str
        ) -> Dict[str, Any]:
            """
            Get an example/scenario from the SOP.

            Use when encountering a specific scenario type and want to see
            how it should be handled.

            Args:
                sop_path: Relative path to SOP manifest
                scenario_name: Scenario name (e.g., "two_way_match", "three_way_match")

            Returns:
                Dict with scenario content and metadata
            """
            self._logger.input("sop_get_example: sop_path={}, scenario={}", sop_path, scenario_name)

            # Map scenario name to section ID
            section_id = f"scenario_{scenario_name}"
            result = sop_get_section(sop_path, section_id)

            # Add scenario_name to result for clarity
            result["scenario_name"] = scenario_name

            return result

        @mcp.tool(name="sop_get_troubleshooting")
        def sop_get_troubleshooting(
            sop_path: str,
            issue: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Get troubleshooting guidance from the SOP.

            Use when encountering errors or unexpected situations.

            Args:
                sop_path: Relative path to SOP manifest
                issue: Optional specific issue to look up (searches within troubleshooting content)

            Returns:
                Dict with troubleshooting content and optionally a relevant section
            """
            self._logger.input("sop_get_troubleshooting: sop_path={}, issue={}", sop_path, issue)

            result = sop_get_section(sop_path, "troubleshooting")

            # If specific issue provided, try to find relevant section
            if issue and result.get("content"):
                lines = result["content"].split("\n")
                relevant_lines: List[str] = []
                capturing = False

                for line in lines:
                    if issue.lower() in line.lower():
                        capturing = True
                    if capturing:
                        relevant_lines.append(line)
                        # Stop at next heading if we've captured content
                        if line.startswith("##") and len(relevant_lines) > 1:
                            break

                if relevant_lines:
                    result["relevant_section"] = "\n".join(relevant_lines)
                    self._logger.output(
                        "sop_get_troubleshooting: found relevant section ({} lines)",
                        len(relevant_lines)
                    )

            return result

        @mcp.tool(name="sop_list_sections")
        def sop_list_sections(
            sop_path: str,
            section_type: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            List available SOP sections.

            Useful to see what procedures, examples, and references are available.

            Args:
                sop_path: Relative path to SOP manifest
                section_type: Optional filter by type (procedure, reference, example, troubleshooting)

            Returns:
                Dict with sections list
            """
            self._logger.input("sop_list_sections: sop_path={}, type={}", sop_path, section_type)

            try:
                cache_key = self._get_cache_key(sop_path)
                if cache_key not in self._manifests:
                    return {
                        "sections": [],
                        "error": "SOP not initialized. Call sop_initialize first."
                    }

                manifest = self._manifests[cache_key]["manifest"]
                sections = manifest.get("sections", [])

                if section_type:
                    sections = [s for s in sections if s.get("type") == section_type]

                result = {
                    "sections": [
                        {
                            "id": s.get("id", ""),
                            "type": s.get("type", "reference"),
                            "description": s.get("description", "")
                        }
                        for s in sections
                    ],
                    "error": ""
                }

                self._logger.output(
                    "sop_list_sections: returned {} sections",
                    len(result["sections"])
                )
                return result

            except Exception as e:
                self._logger.error("sop_list_sections failed: {}", e)
                return {"sections": [], "error": str(e)}

        @mcp.tool(name="sop_invalidate_cache")
        def sop_invalidate_cache(
            sop_path: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Invalidate cached SOP data. Use after SOP files have been updated.

            Args:
                sop_path: Optional specific SOP to invalidate (all if not provided)

            Returns:
                Dict with invalidation status
            """
            self._logger.input("sop_invalidate_cache: sop_path={}", sop_path)

            try:
                if sop_path:
                    cache_key = self._get_cache_key(sop_path)
                    self._manifests.pop(cache_key, None)
                    # Remove section caches for this SOP
                    prefix = f"{sop_path}:"
                    keys_to_remove = [k for k in self._section_cache if k.startswith(prefix)]
                    for k in keys_to_remove:
                        del self._section_cache[k]
                    scope = sop_path
                else:
                    self._manifests.clear()
                    self._section_cache.clear()
                    scope = "all"

                self._logger.output("sop_invalidate_cache: invalidated scope={}", scope)
                return {
                    "invalidated": True,
                    "scope": scope,
                    "error": ""
                }

            except Exception as e:
                self._logger.error("sop_invalidate_cache failed: {}", e)
                return {
                    "invalidated": False,
                    "scope": sop_path or "all",
                    "error": str(e)
                }

        @mcp.tool(name="sop_get_glossary_term")
        def sop_get_glossary_term(
            project_dir: str,
            sop_path: str,
            term_id: str
        ) -> Dict[str, Any]:
            """
            Get a glossary term definition from the pipeline-specific glossary.

            Use when you encounter a term in the SOP and need clarification on its meaning.

            Args:
                project_dir: Absolute path to project root directory
                sop_path: Relative path to SOP manifest (used to locate pipeline-specific glossary)
                term_id: Term to look up (e.g., "GBP items", "processing_status", "need_to_process")

            Returns:
                Dict with:
                  - term_id: The term that was looked up
                  - definition: The definition content (markdown)
                  - error: Error message if any
            """
            self._logger.input("sop_get_glossary_term: project_dir={}, sop_path={}, term_id={}", project_dir, sop_path, term_id)

            try:
                # Resolve glossary path: if SOP is at config/sop/reconvoy/sop_matcher/manifest.yml,
                # glossary should be at config/sop/reconvoy/glossary.md
                sop_manifest_path = Path(project_dir) / sop_path
                sop_dir = sop_manifest_path.parent.parent  # Go up from sop_matcher/ to reconvoy/
                glossary_path = sop_dir / "glossary.md"

                if not glossary_path.exists():
                    return {
                        "term_id": term_id,
                        "definition": "",
                        "error": f"Glossary not found at {glossary_path}. Expected location: config/sop/<pipeline>/glossary.md"
                    }

                # Load glossary content
                with open(glossary_path, "r", encoding="utf-8") as f:
                    glossary_content = f.read()

                # Parse glossary to find the term
                # Terms are defined as: ## <term_id>
                lines = glossary_content.split("\n")
                term_section: List[str] = []
                capturing = False
                in_term = False

                for i, line in enumerate(lines):
                    # Check if this is the term we're looking for
                    if line.startswith("## ") and term_id.lower() in line.lower():
                        capturing = True
                        in_term = True
                        term_section.append(line)
                        continue

                    # If we're capturing and hit another ## heading, stop
                    if capturing and line.startswith("## ") and not in_term:
                        break

                    if capturing:
                        term_section.append(line)
                        # Stop at next ## heading (next term)
                        if line.startswith("## ") and i > 0:
                            term_section.pop()  # Remove the heading line
                            break

                    in_term = False

                if not term_section:
                    # Try to find similar terms
                    all_terms: List[str] = []
                    for line in lines:
                        if line.startswith("## "):
                            term = line[3:].strip()
                            all_terms.append(term)

                    return {
                        "term_id": term_id,
                        "definition": "",
                        "error": f"Term '{term_id}' not found in glossary. Available terms: {', '.join(all_terms[:10])}"
                    }

                definition = "\n".join(term_section).strip()

                self._logger.output(
                    "sop_get_glossary_term: returned {} chars for term '{}'",
                    len(definition), term_id
                )
                return {
                    "term_id": term_id,
                    "definition": definition,
                    "error": ""
                }

            except Exception as e:
                self._logger.error("sop_get_glossary_term failed: {}", e)
                return {
                    "term_id": term_id,
                    "definition": "",
                    "error": str(e)
                }

        @mcp.tool(name="sop_list_glossary_terms")
        def sop_list_glossary_terms(
            project_dir: str,
            sop_path: str
        ) -> Dict[str, Any]:
            """
            List all available glossary terms for the pipeline.

            Useful to see what terms are defined and available for lookup.

            Args:
                project_dir: Absolute path to project root directory
                sop_path: Relative path to SOP manifest (used to locate pipeline-specific glossary)

            Returns:
                Dict with:
                  - terms: List of term IDs available in the glossary
                  - error: Error message if any
            """
            self._logger.input("sop_list_glossary_terms: project_dir={}, sop_path={}", project_dir, sop_path)

            try:
                # Resolve glossary path
                sop_manifest_path = Path(project_dir) / sop_path
                sop_dir = sop_manifest_path.parent.parent  # Go up from sop_matcher/ to reconvoy/
                glossary_path = sop_dir / "glossary.md"

                if not glossary_path.exists():
                    return {
                        "terms": [],
                        "error": f"Glossary not found at {glossary_path}. Expected location: config/sop/<pipeline>/glossary.md"
                    }

                # Load glossary content
                with open(glossary_path, "r", encoding="utf-8") as f:
                    glossary_content = f.read()

                # Extract all term headings (## <term>)
                terms: List[str] = []
                for line in glossary_content.split("\n"):
                    if line.startswith("## ") and not line.startswith("## " + "#"):  # ## but not ###
                        term = line[3:].strip()
                        # Skip the main title "ReconVoy Glossary"
                        if term.lower() != "enhanced reconvoy glossary":
                            terms.append(term)

                self._logger.output(
                    "sop_list_glossary_terms: returned {} terms",
                    len(terms)
                )
                return {
                    "terms": terms,
                    "error": ""
                }

            except Exception as e:
                self._logger.error("sop_list_glossary_terms failed: {}", e)
                return {
                    "terms": [],
                    "error": str(e)
                }
