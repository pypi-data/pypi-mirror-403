"""
Covenant Context Manager - Local tools for contract lifecycle management.

Provides tools for:
- Contract ID extraction from file paths
- Contract file operations
- Contract artifact management (read/write JSON artifacts)
- Contract report management (write markdown reports)
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from topaz_agent_kit.local_tools.registry import pipeline_tool
from topaz_agent_kit.utils.logger import Logger

_logger = Logger("CovenantContextManager")


# ---------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------

def _validate_contract_id(contract_id: str) -> None:
    """Validate contract ID format."""
    if not contract_id:
        raise ValueError("contract_id is required")
    if not re.match(r"^CONTRACT-\d{4}-\d{3}$", contract_id):
        raise ValueError(f"Invalid contract_id format: {contract_id}. Expected format: CONTRACT-YYYY-XXX")


def _resolve_path(base_path: str, relative_path: str) -> Path:
    """Resolve absolute path from base and relative path."""
    if not base_path:
        raise ValueError("base_path is required")
    base = Path(base_path)
    if not base.is_absolute():
        raise ValueError(f"base_path must be absolute: {base_path}")
    
    path = base / relative_path
    return path.resolve()


# ---------------------------------------------------------------------
# Contract ID Extraction
# ---------------------------------------------------------------------

@pipeline_tool(toolkit="covenant", name="extract_contract_id_from_path")
def extract_contract_id_from_path(file_path: str) -> str:
    """Extract contract_id from file path.
    
    Supports multiple path patterns:
    - pre_contract/CONTRACT-2025-318/file.txt → CONTRACT-2025-318
    - draft_contracts/CONTRACT-2025-318_draft_v1.pdf → CONTRACT-2025-318
    - signed_contracts/CONTRACT-2025-318_signed.pdf → CONTRACT-2025-318
    - artifacts/CONTRACT-2025-318/file.json → CONTRACT-2025-318
    
    Args:
        file_path: File path (absolute or relative)
    
    Returns:
        Contract ID in format CONTRACT-YYYY-XXX
    
    Raises:
        ValueError: If contract_id cannot be extracted
    """
    try:
        path = Path(file_path)
        
        # Pattern 1: Directory structure (pre_contract/CONTRACT-2025-318/file.txt)
        # Look for CONTRACT-YYYY-XXX in path components
        for part in path.parts:
            match = re.match(r"^(CONTRACT-\d{4}-\d{3})", part)
            if match:
                contract_id = match.group(1)
                _logger.debug("Extracted contract_id from path component: {}", contract_id)
                return contract_id
        
        # Pattern 2: Filename (CONTRACT-2025-318_draft_v1.pdf)
        filename = path.name
        match = re.match(r"^(CONTRACT-\d{4}-\d{3})", filename)
        if match:
            contract_id = match.group(1)
            _logger.debug("Extracted contract_id from filename: {}", contract_id)
            return contract_id
        
        # Pattern 3: Search in full path string
        match = re.search(r"(CONTRACT-\d{4}-\d{3})", str(path))
        if match:
            contract_id = match.group(1)
            _logger.debug("Extracted contract_id from path string: {}", contract_id)
            return contract_id
        
        raise ValueError(f"Could not extract contract_id from path: {file_path}")
    
    except Exception as e:
        _logger.error("Error extracting contract_id from path {}: {}", file_path, e)
        raise ValueError(f"Failed to extract contract_id: {e}")


# ---------------------------------------------------------------------
# Contract File Operations
# ---------------------------------------------------------------------

@pipeline_tool(toolkit="covenant", name="get_contract_files")
def get_contract_files(
    contract_id: str,
    directory: str,
    project_dir: str
) -> List[str]:
    """Get all files for a contract in a specific directory.
    
    Args:
        contract_id: Contract ID (e.g., CONTRACT-2025-318)
        directory: Directory name (e.g., "pre_contract", "draft_contracts", "signed_contracts", "change_orders")
        project_dir: Absolute path to project root directory
    
    Returns:
        List of absolute file paths
    """
    try:
        _validate_contract_id(contract_id)
        
        # Resolve directory path
        if directory == "pre_contract":
            dir_path = _resolve_path(project_dir, f"data/covenant/pre_contract/{contract_id}")
        elif directory == "draft_contracts":
            dir_path = _resolve_path(project_dir, "data/covenant/draft_contracts")
        elif directory == "signed_contracts":
            dir_path = _resolve_path(project_dir, "data/covenant/signed_contracts")
        elif directory == "change_orders":
            dir_path = _resolve_path(project_dir, "data/covenant/change_orders")
        elif directory == "historical_wbs":
            dir_path = _resolve_path(project_dir, "data/covenant/historical_wbs")
        else:
            raise ValueError(f"Unknown directory: {directory}")
        
        if not dir_path.exists():
            _logger.warning("Directory does not exist: {}", dir_path)
            return []
        
        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {dir_path}")
        
        # Get all files (not directories)
        files = []
        for item in dir_path.iterdir():
            if item.is_file():
                # For draft_contracts, signed_contracts, and change_orders, filter by contract_id
                if directory in ["draft_contracts", "signed_contracts", "change_orders"]:
                    if contract_id in item.name:
                        files.append(str(item))
                else:
                    # For pre_contract and historical_wbs, include all files
                    files.append(str(item))
        
        _logger.debug("Found {} files in {} for contract {}", len(files), directory, contract_id)
        return sorted(files)
    
    except Exception as e:
        _logger.error("Error getting contract files for {} in {}: {}", contract_id, directory, e)
        raise


@pipeline_tool(toolkit="covenant", name="list_contract_artifacts")
def list_contract_artifacts(
    contract_id: str,
    project_dir: str
) -> List[str]:
    """List all artifact files for a contract.
    
    Args:
        contract_id: Contract ID (e.g., CONTRACT-2025-318)
        project_dir: Absolute path to project root directory
    
    Returns:
        List of artifact filenames
    """
    try:
        _validate_contract_id(contract_id)
        
        artifacts_dir = _resolve_path(project_dir, f"data/covenant/artifacts/{contract_id}")
        
        if not artifacts_dir.exists():
            _logger.debug("Artifacts directory does not exist: {}", artifacts_dir)
            return []
        
        artifacts = []
        for item in artifacts_dir.iterdir():
            if item.is_file():
                artifacts.append(item.name)
        
        _logger.debug("Found {} artifacts for contract {}", len(artifacts), contract_id)
        return sorted(artifacts)
    
    except Exception as e:
        _logger.error("Error listing artifacts for {}: {}", contract_id, e)
        raise


# ---------------------------------------------------------------------
# Contract Artifact Operations
# ---------------------------------------------------------------------

@pipeline_tool(toolkit="covenant", name="read_contract_artifact")
def read_contract_artifact(
    contract_id: str,
    artifact_name: str,
    project_dir: str
) -> Dict[str, Any]:
    """Read a contract artifact JSON file.
    
    Args:
        contract_id: Contract ID (e.g., CONTRACT-2025-318)
        artifact_name: Artifact filename (e.g., "pre_contract_summary_v1.json")
        project_dir: Absolute path to project root directory
    
    Returns:
        Dictionary containing artifact data
    
    Raises:
        FileNotFoundError: If artifact file does not exist
        ValueError: If artifact file is invalid JSON
    """
    try:
        _validate_contract_id(contract_id)
        
        artifact_path = _resolve_path(project_dir, f"data/covenant/artifacts/{contract_id}/{artifact_name}")
        
        if not artifact_path.exists():
            _logger.warning("Artifact file does not exist: {}", artifact_path)
            raise FileNotFoundError(f"Artifact not found: {artifact_name} for contract {contract_id}")
        
        with open(artifact_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        _logger.debug("Read artifact {} for contract {}", artifact_name, contract_id)
        return data
    
    except FileNotFoundError:
        raise
    except json.JSONDecodeError as e:
        _logger.error("Invalid JSON in artifact {}: {}", artifact_path, e)
        raise ValueError(f"Invalid JSON in artifact {artifact_name}: {e}")
    except Exception as e:
        _logger.error("Error reading artifact {} for {}: {}", artifact_name, contract_id, e)
        raise


@pipeline_tool(toolkit="covenant", name="write_contract_artifact")
def write_contract_artifact(
    contract_id: str,
    artifact_name: str,
    content: Dict[str, Any],
    project_dir: str
) -> bool:
    """Write a contract artifact JSON file.
    
    Args:
        contract_id: Contract ID (e.g., CONTRACT-2025-318)
        artifact_name: Artifact filename (e.g., "pre_contract_summary_v1.json")
        content: Dictionary containing artifact data
        project_dir: Absolute path to project root directory
    
    Returns:
        True if successful
    
    Raises:
        ValueError: If content cannot be serialized to JSON
        OSError: If file cannot be written
    """
    try:
        _validate_contract_id(contract_id)
        
        artifacts_dir = _resolve_path(project_dir, f"data/covenant/artifacts/{contract_id}")
        
        # Create directory if it doesn't exist
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        artifact_path = artifacts_dir / artifact_name
        
        # Write JSON file
        with open(artifact_path, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        
        _logger.debug("Wrote artifact {} for contract {}", artifact_name, contract_id)
        return True
    
    except (TypeError, ValueError) as e:
        _logger.error("Error serializing artifact {}: {}", artifact_name, e)
        raise ValueError(f"Failed to serialize artifact {artifact_name}: {e}")
    except OSError as e:
        _logger.error("Error writing artifact {}: {}", artifact_path, e)
        raise
    except Exception as e:
        _logger.error("Error writing artifact {} for {}: {}", artifact_name, contract_id, e)
        raise


@pipeline_tool(toolkit="covenant", name="write_contract_report")
def write_contract_report(
    contract_id: str,
    report_name: str,
    report_content: str,
    project_dir: str
) -> str:
    """Write a contract report markdown file.
    
    The tool automatically constructs the path: data/covenant/reports/{contract_id}_{report_name}.md
    
    Args:
        contract_id: Contract ID (e.g., CONTRACT-2025-318)
        report_name: Report name (e.g., "pre_contract_synthesis_report")
        report_content: Markdown content of the report
        project_dir: Absolute path to project root directory
    
    Returns:
        Absolute path to the saved report file
    
    Raises:
        ValueError: If contract_id is invalid
        OSError: If file cannot be written
    """
    try:
        _validate_contract_id(contract_id)
        
        reports_dir = _resolve_path(project_dir, "data/covenant/reports")
        
        # Create directory if it doesn't exist
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Construct filename: {contract_id}_{report_name}.md
        filename = f"{contract_id}_{report_name}.md"
        report_path = reports_dir / filename
        
        # Write markdown file
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        _logger.debug("Wrote report {} for contract {}: {}", report_name, contract_id, report_path)
        return str(report_path)
    
    except ValueError:
        raise
    except OSError as e:
        _logger.error("Error writing report {}: {}", report_path, e)
        raise
    except Exception as e:
        _logger.error("Error writing report {} for {}: {}", report_name, contract_id, e)
        raise


@pipeline_tool(toolkit="covenant", name="read_file")
def read_file(file_path: str) -> str:
    """Read text content from a file path.
    
    This tool reads arbitrary text files (e.g., markdown, text files) from absolute file paths.
    Use this for reading historical WBS files or other reference documents that are not contract artifacts.
    
    Args:
        file_path: Absolute file path to read
    
    Returns:
        File content as string
    
    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If file cannot be read as text
    """
    try:
        path = Path(file_path)
        
        if not path.exists():
            _logger.warning("File does not exist: {}", file_path)
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        # Read file as text
        content = path.read_text(encoding="utf-8")
        
        _logger.debug("Read file {} ({} chars)", file_path, len(content))
        return content
    
    except FileNotFoundError:
        raise
    except UnicodeDecodeError as e:
        _logger.error("Failed to decode file {} as UTF-8: {}", file_path, e)
        raise ValueError(f"File is not valid UTF-8 text: {file_path}")
    except Exception as e:
        _logger.error("Error reading file {}: {}", file_path, e)
        raise
