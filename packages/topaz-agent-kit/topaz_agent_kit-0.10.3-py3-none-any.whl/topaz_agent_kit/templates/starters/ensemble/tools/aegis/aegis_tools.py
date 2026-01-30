"""
Aegis - Pipeline-specific local tools.

Goal:
- Agents should NOT directly use sqlite_query/sqlite_execute or python_execute.
- LLM can generate ideas/text, but all DB reads/writes and deterministic computation must go through these tools.

This toolkit is intentionally opinionated and schema-aware for the Aegis database created by:
  src/topaz_agent_kit/scripts/setup_aegis_database.py
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from topaz_agent_kit.local_tools.registry import pipeline_tool
from topaz_agent_kit.utils.logger import Logger

_logger = Logger("AegisTools")


# ---------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------

def _validate_db_file(db_file: str) -> None:
    """Validate database file path."""
    if not db_file:
        raise ValueError("db_file is required")
    if not os.path.exists(db_file):
        raise FileNotFoundError(f"Database file not found: {db_file}")
    if not os.path.isfile(db_file):
        raise ValueError(f"db_file is not a file: {db_file}")


def _connect(db_file: str) -> sqlite3.Connection:
    """Connect to SQLite database with row factory."""
    _validate_db_file(db_file)
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn


def _utc_iso() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalize_evidence_type(db_type: str) -> str:
    """Normalize evidence type from database format to display format.
    
    Converts database format (lowercase with underscores) to display format
    (Title Case with hyphens) for consistency with evidence validator expectations.
    
    Args:
        db_type: Evidence type from database (e.g., "timesheet", "completion_certificate")
    
    Returns:
        Normalized evidence type (e.g., "Timesheet", "Completion-Cert")
    """
    type_mapping = {
        "timesheet": "Timesheet",
        "completion_certificate": "Completion-Cert",
        "vessel_log": "Vessel-Log",
        "equipment_log": "Equipment-Log"
    }
    return type_mapping.get(db_type.lower(), db_type)


# ---------------------------------------------------------------------
# Database Query Tools
# ---------------------------------------------------------------------

@pipeline_tool(toolkit="aegis", name="get_pending_invoices")
def get_pending_invoices(
    db_file: str,
    project_dir: str
) -> Dict[str, Any]:
    """Get all pending invoices with their associated evidence documents.
    
    Args:
        db_file: Absolute path to the database file
        project_dir: Absolute path to project root directory
    
    Returns:
        Dictionary with pending_invoices list, total_pending_count, and run_id
    """
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()
        
        # Query pending invoices
        cursor.execute("""
            SELECT invoice_id, invoice_file_path, status, document_language, submitted_at, created_at
            FROM incoming_invoices
            WHERE status = 'pending'
            ORDER BY created_at ASC
        """)
        
        invoices = []
        for row in cursor.fetchall():
            invoice_id = row["invoice_id"]
            
            # Query evidence documents for this invoice
            cursor.execute("""
                SELECT evidence_id, invoice_id, evidence_file_path, evidence_type, document_language, submitted_at
                FROM evidence_documents
                WHERE invoice_id = ?
                ORDER BY evidence_type
            """, (invoice_id,))
            
            evidence_docs = []
            for ev_row in cursor.fetchall():
                # Normalize evidence_type from database format to display format
                # Database stores: "timesheet", "completion_certificate", etc.
                # Display format: "Timesheet", "Completion-Cert", etc.
                normalized_type = _normalize_evidence_type(ev_row["evidence_type"])
                evidence_docs.append({
                    "evidence_id": ev_row["evidence_id"],
                    "evidence_file_path": ev_row["evidence_file_path"],
                    "evidence_type": normalized_type,
                    "document_language": ev_row["document_language"] if ev_row["document_language"] else None,
                    "submitted_at": ev_row["submitted_at"] if ev_row["submitted_at"] else None
                })
            
            invoices.append({
                "invoice_id": invoice_id,
                "invoice_file_path": row["invoice_file_path"],
                "status": row["status"],
                "document_language": row["document_language"] if row["document_language"] else None,
                "submitted_at": row["submitted_at"] if row["submitted_at"] else None,
                "created_at": row["created_at"],
                "evidence_documents": evidence_docs
            })
        
        conn.close()
        
        # Generate run_id
        run_id = f"run-{_utc_iso()}"
        
        return {
            "pending_invoices": invoices,
            "total_pending_count": len(invoices),
            "run_id": run_id,
            "error": ""
        }
    
    except Exception as e:
        _logger.error("Error getting pending invoices: {}", e)
        return {
            "pending_invoices": [],
            "total_pending_count": 0,
            "run_id": "",
            "error": str(e)
        }


@pipeline_tool(toolkit="aegis", name="get_sow_retention_info")
def get_sow_retention_info(
    db_file: str,
    sow_id: str
) -> Dict[str, Any]:
    """Get SOW retention information.
    
    Args:
        db_file: Absolute path to the database file
        sow_id: Statement of Work ID
    
    Returns:
        Dictionary with sow_id, retention_percentage, and error
    """
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()
        
        # Try both sow_id and sow_number (invoices may contain sow_number)
        cursor.execute("""
            SELECT sow_id, sow_number, retention_percentage
            FROM statements_of_work
            WHERE sow_id = ? OR sow_number = ?
        """, (sow_id, sow_id))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {
                "sow_id": sow_id,
                "retention_percentage": None,
                "error": f"SOW {sow_id} not found"
            }
        
        return {
            "sow_id": row["sow_id"],
            "retention_percentage": float(row["retention_percentage"]) if row["retention_percentage"] else 0.0,
            "error": ""
        }
    
    except Exception as e:
        _logger.error("Error getting SOW retention info: {}", e)
        return {
            "sow_id": sow_id,
            "retention_percentage": None,
            "error": str(e)
        }


@pipeline_tool(toolkit="aegis", name="get_sow_ld_info")
def get_sow_ld_info(
    db_file: str,
    sow_id: str
) -> Dict[str, Any]:
    """Get SOW LD information and late milestones.
    
    Args:
        db_file: Absolute path to the database file
        sow_id: Statement of Work ID
    
    Returns:
        Dictionary with sow_id, ld_applicable, ld_rate_per_day, late_milestones list, and error
    """
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()
        
        # Get SOW LD info - try both sow_id and sow_number (invoices may contain sow_number)
        cursor.execute("""
            SELECT sow_id, sow_number, ld_applicable, ld_rate_per_day
            FROM statements_of_work
            WHERE sow_id = ? OR sow_number = ?
        """, (sow_id, sow_id))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return {
                "sow_id": sow_id,
                "ld_applicable": False,
                "ld_rate_per_day": None,
                "late_milestones": [],
                "error": f"SOW {sow_id} not found"
            }
        
        ld_applicable = bool(row["ld_applicable"])
        ld_rate_per_day = float(row["ld_rate_per_day"]) if row["ld_rate_per_day"] else None
        
        # Get late milestones (actual_date > planned_date)
        # Use the actual sow_id from the row we found (not the input parameter which might be sow_number)
        actual_sow_id = row["sow_id"]
        cursor.execute("""
            SELECT milestone_id, milestone_name, planned_date, actual_date
            FROM milestones
            WHERE sow_id = ? AND actual_date IS NOT NULL AND planned_date IS NOT NULL
                AND actual_date > planned_date
            ORDER BY planned_date
        """, (actual_sow_id,))
        
        late_milestones = []
        for m_row in cursor.fetchall():
            late_milestones.append({
                "milestone_id": m_row["milestone_id"],
                "milestone_name": m_row["milestone_name"],
                "planned_date": m_row["planned_date"],
                "actual_date": m_row["actual_date"]
            })
        
        conn.close()
        
        return {
            "sow_id": row["sow_id"],
            "ld_applicable": ld_applicable,
            "ld_rate_per_day": ld_rate_per_day,
            "late_milestones": late_milestones,
            "error": ""
        }
    
    except Exception as e:
        _logger.error("Error getting SOW LD info: {}", e)
        return {
            "sow_id": sow_id,
            "ld_applicable": False,
            "ld_rate_per_day": None,
            "late_milestones": [],
            "error": str(e)
        }


@pipeline_tool(toolkit="aegis", name="get_evidence_requirements")
def get_evidence_requirements(
    db_file: str,
    sow_reference: str
) -> Dict[str, Any]:
    """Get evidence requirements for a SOW.
    
    Args:
        db_file: Absolute path to the database file
        sow_reference: SOW reference (sow_number from invoice)
    
    Returns:
        Dictionary with:
        - sow_id: SOW ID (mapped from sow_reference)
        - required_evidence_types: List of required evidence types (e.g., ["Timesheet", "Completion-Cert", "Vessel-Log", "Equipment-Log"])
        - coverage_requirements: Coverage requirements description
        - work_type: Work type (e.g., "labor", "equipment", "materials", "services")
        - error: Error message if any
    """
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()
        
        # Map sow_reference (sow_number) to sow_id
        cursor.execute("""
            SELECT sow_id, sow_number
            FROM statements_of_work
            WHERE sow_number = ?
        """, (sow_reference,))
        
        sow_row = cursor.fetchone()
        if not sow_row:
            conn.close()
            return {
                "sow_id": None,
                "required_evidence_types": [],
                "coverage_requirements": None,
                "work_type": None,
                "error": f"SOW with reference '{sow_reference}' not found"
            }
        
        sow_id = sow_row["sow_id"]
        
        # Get evidence requirements for this SOW
        cursor.execute("""
            SELECT required_evidence_types, coverage_requirements, work_type
            FROM evidence_requirements
            WHERE applicable_sow_id = ?
        """, (sow_id,))
        
        req_row = cursor.fetchone()
        conn.close()
        
        if not req_row:
            # No specific requirements found - return default (all standard types)
            return {
                "sow_id": sow_id,
                "required_evidence_types": ["Timesheet", "Completion-Cert", "Vessel-Log", "Equipment-Log"],
                "coverage_requirements": None,
                "work_type": None,
                "error": ""
            }
        
        # Parse required_evidence_types (stored as JSON string or comma-separated)
        required_types = req_row["required_evidence_types"]
        if isinstance(required_types, str):
            try:
                # Try parsing as JSON first
                required_types = json.loads(required_types)
            except json.JSONDecodeError:
                # If not JSON, treat as comma-separated string
                required_types = [t.strip() for t in required_types.split(",") if t.strip()]
        
        return {
            "sow_id": sow_id,
            "required_evidence_types": required_types if isinstance(required_types, list) else [],
            "coverage_requirements": req_row["coverage_requirements"],
            "work_type": req_row["work_type"],
            "error": ""
        }
    
    except Exception as e:
        _logger.error("Error getting evidence requirements: {}", e)
        return {
            "sow_id": None,
            "required_evidence_types": [],
            "coverage_requirements": None,
            "work_type": None,
            "error": str(e)
        }


@pipeline_tool(toolkit="aegis", name="get_milestone_cap_info")
def get_milestone_cap_info(
    db_file: str,
    milestone_id: Optional[str] = None,
    sow_id: Optional[str] = None
) -> Dict[str, Any]:
    """Get milestone cap information and total billed amount.
    
    Args:
        db_file: Absolute path to the database file
        milestone_id: Milestone ID (primary lookup, optional)
        sow_id: Optional SOW ID for fallback lookup
    
    Returns:
        Dictionary with milestone_id, milestone_name, milestone_cap_amount, total_billed_amount, and error
    """
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()
        
        # Normalize empty strings to None for proper handling
        milestone_id = milestone_id.strip() if milestone_id and milestone_id.strip() else None
        sow_id = sow_id.strip() if sow_id and sow_id.strip() else None
        
        # Get milestone cap info
        if milestone_id:
            cursor.execute("""
                SELECT milestone_id, milestone_name, milestone_cap_amount, sow_id
                FROM milestones
                WHERE milestone_id = ?
            """, (milestone_id,))
        elif sow_id:
            # Try both sow_id and sow_number (invoices may contain sow_number)
            cursor.execute("""
                SELECT m.milestone_id, m.milestone_name, m.milestone_cap_amount, m.sow_id
                FROM milestones m
                JOIN statements_of_work s ON m.sow_id = s.sow_id
                WHERE m.sow_id = ? OR s.sow_number = ?
                ORDER BY m.planned_date DESC
                LIMIT 1
            """, (sow_id, sow_id))
        else:
            conn.close()
            return {
                "milestone_id": None,
                "milestone_name": None,
                "milestone_cap_amount": None,
                "total_billed_amount": 0.0,
                "error": "Either milestone_id or sow_id must be provided"
            }
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return {
                "milestone_id": milestone_id,
                "milestone_name": None,
                "milestone_cap_amount": None,
                "total_billed_amount": 0.0,
                "error": f"Milestone not found (milestone_id={milestone_id}, sow_id={sow_id})"
            }
        
        milestone_id_found = row["milestone_id"]
        milestone_cap_amount = float(row["milestone_cap_amount"]) if row["milestone_cap_amount"] else None
        sow_id_found = row["sow_id"]
        
        # Calculate total billed amount from approved historical invoices
        # NOTE: historical_invoices table has sow_id but NOT milestone_id
        # So we sum all approved invoices for the SOW that this milestone belongs to
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) as total_billed
            FROM historical_invoices
            WHERE sow_id = ? AND final_status = 'approved'
        """, (sow_id_found,))
        
        total_billed_row = cursor.fetchone()
        total_billed_amount = float(total_billed_row["total_billed"]) if total_billed_row else 0.0
        
        conn.close()
        
        return {
            "milestone_id": milestone_id_found,
            "milestone_name": row["milestone_name"],
            "milestone_cap_amount": milestone_cap_amount,
            "total_billed_amount": total_billed_amount,
            "error": ""
        }
    
    except Exception as e:
        _logger.error("Error getting milestone cap info: {}", e)
        return {
            "milestone_id": milestone_id,
            "milestone_name": None,
            "milestone_cap_amount": None,
            "total_billed_amount": 0.0,
            "error": str(e)
        }


@pipeline_tool(toolkit="aegis", name="get_po_line_item")
def get_po_line_item(
    db_file: str,
    po_number: str,
    po_line_number: Optional[str] = None,
    item_code: Optional[str] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Get PO line item details including WBS assignment.
    
    This tool looks up PO line items and returns WBS information for WBS inheritance.
    Matching is done in priority order: po_line_number > item_code > description (fuzzy).
    
    Args:
        db_file: Absolute path to the database file
        po_number: PO number (required)
        po_line_number: PO line number (optional, primary matching method)
        item_code: Item code for matching if line number not available (optional)
        description: Description for fuzzy matching if line number and item code not available (optional)
    
    Returns:
        Dictionary with:
        - po_number: PO number
        - po_line_number: PO line number
        - wbs_id: WBS ID assigned to this PO line item
        - role: Role (for Labor PO lines, optional)
        - rate: Rate (for Labor PO lines, optional)
        - item_code: Item code
        - description: Description
        - quantity: Quantity
        - unit_price: Unit price
        - total: Total amount
        - error: Error message if any
    """
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()
        
        # Normalize empty strings to None
        po_line_number = po_line_number.strip() if po_line_number and po_line_number.strip() else None
        item_code = item_code.strip() if item_code and item_code.strip() else None
        description = description.strip() if description and description.strip() else None
        
        # Priority 1: Match by po_line_number if provided
        if po_line_number:
            # Parse po_line_number: if it's in format "PO-XXXX-XXXX-N", extract just the numeric part
            # Database stores line_number as INTEGER, but invoice PDF may display as "PO-2026-1016-2"
            parsed_line_number = po_line_number
            try:
                # Try to extract numeric part if po_line_number contains PO prefix
                # Format: "PO-YYYY-NNNN-N" -> extract last "N"
                if po_line_number.startswith(po_number + "-"):
                    # Format: "PO-2026-1016-2" where "PO-2026-1016" is the PO number
                    parts = po_line_number.split("-")
                    if len(parts) >= 3:
                        # Last part should be the line number
                        parsed_line_number = int(parts[-1])
                elif po_line_number.isdigit():
                    # Already a number
                    parsed_line_number = int(po_line_number)
                else:
                    # Try to extract any trailing number
                    match = re.search(r'(\d+)$', po_line_number)
                    if match:
                        parsed_line_number = int(match.group(1))
                    else:
                        parsed_line_number = po_line_number
            except (ValueError, AttributeError):
                # If parsing fails, use original value (will fail in SQL but that's expected)
                parsed_line_number = po_line_number
            except Exception:
                # Fallback to original value on any other error
                parsed_line_number = po_line_number
            
            cursor.execute("""
                SELECT po_number, line_number, item_code, description, quantity, unit_price, total,
                       wbs_id, role, rate, material_category
                FROM po_line_items
                WHERE po_number = ? AND line_number = ?
            """, (po_number, parsed_line_number))
            row = cursor.fetchone()
            if row:
                conn.close()
                return {
                    "po_number": row["po_number"],
                    "po_line_number": row["line_number"],
                    "wbs_id": row["wbs_id"],
                    "role": row["role"],
                    "rate": float(row["rate"]) if row["rate"] else None,
                    "item_code": row["item_code"],
                    "description": row["description"],
                    "quantity": float(row["quantity"]) if row["quantity"] else None,
                    "unit_price": float(row["unit_price"]) if row["unit_price"] else None,
                    "total": float(row["total"]) if row["total"] else None,
                    "material_category": row["material_category"],
                    "error": ""
                }
        
        # Priority 2: Match by item_code if provided
        if item_code:
            cursor.execute("""
                SELECT po_number, line_number, item_code, description, quantity, unit_price, total,
                       wbs_id, role, rate, material_category
                FROM po_line_items
                WHERE po_number = ? AND item_code = ?
                LIMIT 1
            """, (po_number, item_code))
            row = cursor.fetchone()
            if row:
                conn.close()
                return {
                    "po_number": row["po_number"],
                    "po_line_number": row["line_number"],
                    "wbs_id": row["wbs_id"],
                    "role": row["role"],
                    "rate": float(row["rate"]) if row["rate"] else None,
                    "item_code": row["item_code"],
                    "description": row["description"],
                    "quantity": float(row["quantity"]) if row["quantity"] else None,
                    "unit_price": float(row["unit_price"]) if row["unit_price"] else None,
                    "total": float(row["total"]) if row["total"] else None,
                    "material_category": row["material_category"],
                    "error": ""
                }
        
        # Priority 3: Fuzzy match by description (simple contains match for now)
        if description:
            cursor.execute("""
                SELECT po_number, line_number, item_code, description, quantity, unit_price, total,
                       wbs_id, role, rate, material_category
                FROM po_line_items
                WHERE po_number = ? AND description LIKE ?
                LIMIT 1
            """, (po_number, f"%{description}%"))
            row = cursor.fetchone()
            if row:
                conn.close()
                return {
                    "po_number": row["po_number"],
                    "po_line_number": row["line_number"],
                    "wbs_id": row["wbs_id"],
                    "role": row["role"],
                    "rate": float(row["rate"]) if row["rate"] else None,
                    "item_code": row["item_code"],
                    "description": row["description"],
                    "quantity": float(row["quantity"]) if row["quantity"] else None,
                    "unit_price": float(row["unit_price"]) if row["unit_price"] else None,
                    "total": float(row["total"]) if row["total"] else None,
                    "material_category": row["material_category"],
                    "error": ""
                }
        
        # No match found
        conn.close()
        return {
            "po_number": po_number,
            "po_line_number": po_line_number,
            "wbs_id": None,
            "role": None,
            "rate": None,
            "item_code": item_code,
            "description": description,
            "quantity": None,
            "unit_price": None,
            "total": None,
            "material_category": None,
            "error": f"PO line item not found (po_number={po_number}, po_line_number={po_line_number}, item_code={item_code})"
        }
    
    except Exception as e:
        _logger.error("Error getting PO line item: {}", e)
        return {
            "po_number": po_number,
            "po_line_number": po_line_number,
            "wbs_id": None,
            "role": None,
            "rate": None,
            "item_code": item_code,
            "description": description,
            "quantity": None,
            "unit_price": None,
            "total": None,
            "material_category": None,
            "error": str(e)
        }


@pipeline_tool(toolkit="aegis", name="get_wbs_budget_info")
def get_wbs_budget_info(
    db_file: str,
    wbs_id: str
) -> Dict[str, Any]:
    """Get WBS budget allocation and total billed amount.
    
    Args:
        db_file: Absolute path to the database file
        wbs_id: WBS ID (required)
    
    Returns:
        Dictionary with:
        - wbs_id: WBS ID
        - budget_allocation: Budget allocated for this WBS
        - total_billed_so_far: Sum of all approved invoices for this WBS
        - remaining_budget: Remaining budget (budget_allocation - total_billed_so_far)
        - error: Error message if any
    """
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()
        
        # Get WBS budget allocation
        cursor.execute("""
            SELECT wbs_id, budget_allocation
            FROM work_breakdown_structure
            WHERE wbs_id = ?
        """, (wbs_id,))
        wbs_row = cursor.fetchone()
        
        if not wbs_row:
            conn.close()
            return {
                "wbs_id": wbs_id,
                "budget_allocation": None,
                "total_billed_so_far": 0.0,
                "remaining_budget": None,
                "error": f"WBS not found: {wbs_id}"
            }
        
        budget_allocation = float(wbs_row["budget_allocation"]) if wbs_row["budget_allocation"] else None
        
        # Calculate total billed from approved historical invoices
        # Note: We need to join through PO line items to get WBS association
        # Historical invoices reference PO numbers, PO line items have wbs_id
        cursor.execute("""
            SELECT COALESCE(SUM(hi.total_amount), 0) as total_billed
            FROM historical_invoices hi
            JOIN purchase_orders po ON hi.po_number = po.po_number
            JOIN po_line_items poli ON po.po_number = poli.po_number
            WHERE poli.wbs_id = ? AND hi.final_status = 'approved'
        """, (wbs_id,))
        
        total_billed_row = cursor.fetchone()
        total_billed_so_far = float(total_billed_row["total_billed"]) if total_billed_row else 0.0
        
        remaining_budget = (budget_allocation - total_billed_so_far) if budget_allocation is not None else None
        
        conn.close()
        
        return {
            "wbs_id": wbs_id,
            "budget_allocation": budget_allocation,
            "total_billed_so_far": total_billed_so_far,
            "remaining_budget": remaining_budget,
            "error": ""
        }
    
    except Exception as e:
        _logger.error("Error getting WBS budget info: {}", e)
        return {
            "wbs_id": wbs_id,
            "budget_allocation": None,
            "total_billed_so_far": 0.0,
            "remaining_budget": None,
            "error": str(e)
        }


@pipeline_tool(toolkit="aegis", name="get_wbs_role_rate_budget_info")
def get_wbs_role_rate_budget_info(
    db_file: str,
    wbs_id: str,
    role: str,
    rate: float
) -> Dict[str, Any]:
    """Get budget allocation and total billed for WBS+Role+Rate combination.
    
    This is used for Labor invoice validation where budget is tracked at WBS+Role+Rate level.
    
    Args:
        db_file: Absolute path to the database file
        wbs_id: WBS ID (required)
        role: Role name (e.g., "Senior Engineer", "Technician") (required)
        rate: Hourly rate (required)
    
    Returns:
        Dictionary with:
        - wbs_id: WBS ID
        - role: Role
        - rate: Rate
        - budget_allocation: Budget allocated for this WBS+Role+Rate combination
        - total_billed_so_far: Sum of all approved invoices for this combination
        - remaining_budget: Remaining budget
        - error: Error message if any
    
    Note:
        Budget allocation for WBS+Role+Rate is calculated from rate cards and WBS budget.
        Total billed is calculated from approved historical invoices that match WBS+Role+Rate.
    """
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()
        
        # Get WBS budget allocation
        cursor.execute("""
            SELECT budget_allocation
            FROM work_breakdown_structure
            WHERE wbs_id = ?
        """, (wbs_id,))
        wbs_row = cursor.fetchone()
        
        if not wbs_row:
            conn.close()
            return {
                "wbs_id": wbs_id,
                "role": role,
                "rate": rate,
                "budget_allocation": None,
                "total_billed_so_far": 0.0,
                "remaining_budget": None,
                "error": f"WBS not found: {wbs_id}"
            }
        
        wbs_budget = float(wbs_row["budget_allocation"]) if wbs_row["budget_allocation"] else None
        
        # For WBS+Role+Rate budget, we need to:
        # 1. Get rate card entries matching WBS+Role+Rate
        # 2. Calculate budget allocation from rate cards (if available)
        # 3. Calculate total billed from approved invoices matching WBS+Role+Rate
        
        # Get rate card for this WBS+Role+Rate combination
        # Note: Rate cards may be linked to SOW, and we need to find matching PO line items
        # For now, we'll calculate based on PO line items with matching WBS+Role+Rate
        cursor.execute("""
            SELECT COALESCE(SUM(poli.total), 0) as budget_allocated
            FROM po_line_items poli
            WHERE poli.wbs_id = ? AND poli.role = ? AND ABS(poli.rate - ?) < 0.01
        """, (wbs_id, role, rate))
        
        budget_row = cursor.fetchone()
        budget_allocation = float(budget_row["budget_allocated"]) if budget_row and budget_row["budget_allocated"] else None
        
        # If no PO line items found, use WBS budget as fallback (assume it's allocated for this role/rate)
        if budget_allocation is None or budget_allocation == 0:
            budget_allocation = wbs_budget  # Use WBS budget as allocation
        
        # Calculate total billed from approved historical invoices
        # Match by WBS+Role+Rate through PO line items
        cursor.execute("""
            SELECT COALESCE(SUM(hi.total_amount), 0) as total_billed
            FROM historical_invoices hi
            JOIN purchase_orders po ON hi.po_number = po.po_number
            JOIN po_line_items poli ON po.po_number = poli.po_number
            WHERE poli.wbs_id = ? AND poli.role = ? AND ABS(poli.rate - ?) < 0.01
              AND hi.final_status = 'approved'
        """, (wbs_id, role, rate))
        
        total_billed_row = cursor.fetchone()
        total_billed_so_far = float(total_billed_row["total_billed"]) if total_billed_row else 0.0
        
        remaining_budget = (budget_allocation - total_billed_so_far) if budget_allocation is not None else None
        
        conn.close()
        
        return {
            "wbs_id": wbs_id,
            "role": role,
            "rate": rate,
            "budget_allocation": budget_allocation,
            "total_billed_so_far": total_billed_so_far,
            "remaining_budget": remaining_budget,
            "error": ""
        }
    
    except Exception as e:
        _logger.error("Error getting WBS+Role+Rate budget info: {}", e)
        return {
            "wbs_id": wbs_id,
            "role": role,
            "rate": rate,
            "budget_allocation": None,
            "total_billed_so_far": 0.0,
            "remaining_budget": None,
            "error": str(e)
        }


@pipeline_tool(toolkit="aegis", name="get_historical_invoice_patterns")
def get_historical_invoice_patterns(
    db_file: str,
    vendor_id: Optional[str] = None,
    vendor_name: Optional[str] = None,
    sow_id: Optional[str] = None,
    sow_number: Optional[str] = None,
    lookback_days: int = 730
) -> Dict[str, Any]:
    """Get historical invoice patterns for anomaly detection.
    
    Args:
        db_file: Absolute path to the database file
        vendor_id: Vendor ID to filter historical invoices (optional)
        vendor_name: Vendor name to filter historical invoices (optional, will lookup vendor_id)
        sow_id: SOW ID to filter historical invoices (optional)
        sow_number: SOW number to filter historical invoices (optional, will lookup sow_id)
        lookback_days: Number of days to look back for historical data (default: 730 = 2 years)
    
    Returns:
        Dictionary with:
        - average_amount: Average invoice amount
        - min_amount: Minimum invoice amount
        - max_amount: Maximum invoice amount
        - median_amount: Median invoice amount
        - count: Number of historical invoices
        - standard_deviation: Standard deviation of amounts
        - vendor_id: Vendor ID used (if provided)
        - sow_id: SOW ID used (if provided)
        - error: Error message if any
    """
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()
        
        # Lookup vendor_id from vendor_name if provided
        if vendor_name and not vendor_id:
            cursor.execute("""
                SELECT vendor_id FROM vendors
                WHERE vendor_name = ?
            """, (vendor_name,))
            vendor_row = cursor.fetchone()
            if vendor_row:
                vendor_id = vendor_row["vendor_id"]
        
        # Lookup sow_id from sow_number if provided
        if sow_number and not sow_id:
            cursor.execute("""
                SELECT sow_id FROM statements_of_work
                WHERE sow_number = ?
            """, (sow_number,))
            sow_row = cursor.fetchone()
            if sow_row:
                sow_id = sow_row["sow_id"]
        
        # Build query based on provided filters
        conditions = []
        params = []
        
        if vendor_id:
            conditions.append("vendor_id = ?")
            params.append(vendor_id)
        
        if sow_id:
            conditions.append("sow_id = ?")
            params.append(sow_id)
        
        # Filter by date (lookback_days)
        from datetime import datetime, timedelta
        cutoff_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        conditions.append("invoice_date >= ?")
        params.append(cutoff_date)
        
        # Only include approved invoices for pattern analysis
        conditions.append("final_status = 'approved'")
        
        where_clause = " AND ".join(conditions) if conditions else "final_status = 'approved'"
        
        # Get statistical data
        # Note: where_clause is used 3 times (main query + 2 subqueries), so we need params * 3
        query = f"""
            SELECT 
                COUNT(*) as count,
                AVG(total_amount) as avg_amount,
                MIN(total_amount) as min_amount,
                MAX(total_amount) as max_amount,
                (SELECT total_amount 
                 FROM historical_invoices 
                 WHERE {where_clause}
                 ORDER BY total_amount 
                 LIMIT 1 OFFSET (SELECT COUNT(*) FROM historical_invoices WHERE {where_clause}) / 2) as median_amount
            FROM historical_invoices
            WHERE {where_clause}
        """
        
        cursor.execute(query, params * 3)  # params used 3 times (main query + 2 subqueries)
        row = cursor.fetchone()
        
        if not row or row["count"] == 0:
            conn.close()
            return {
                "average_amount": 0.0,
                "min_amount": 0.0,
                "max_amount": 0.0,
                "median_amount": 0.0,
                "count": 0,
                "standard_deviation": 0.0,
                "vendor_id": vendor_id,
                "sow_id": sow_id,
                "error": f"No historical invoices found (vendor_id={vendor_id}, vendor_name={vendor_name}, sow_id={sow_id}, sow_number={sow_number}, lookback_days={lookback_days})"
            }
        
        count = row["count"]
        avg_amount = float(row["avg_amount"]) if row["avg_amount"] else 0.0
        min_amount = float(row["min_amount"]) if row["min_amount"] else 0.0
        max_amount = float(row["max_amount"]) if row["max_amount"] else 0.0
        median_amount = float(row["median_amount"]) if row["median_amount"] else 0.0
        
        # Calculate standard deviation
        std_query = f"""
            SELECT 
                SQRT(AVG((total_amount - ?) * (total_amount - ?))) as std_dev
            FROM historical_invoices
            WHERE {where_clause}
        """
        cursor.execute(std_query, [avg_amount, avg_amount] + params)
        std_row = cursor.fetchone()
        std_dev = float(std_row["std_dev"]) if std_row and std_row["std_dev"] else 0.0
        
        conn.close()
        
        return {
            "average_amount": round(avg_amount, 2),
            "min_amount": round(min_amount, 2),
            "max_amount": round(max_amount, 2),
            "median_amount": round(median_amount, 2),
            "count": count,
            "standard_deviation": round(std_dev, 2),
            "vendor_id": vendor_id,
            "sow_id": sow_id,
            "error": ""
        }
    
    except Exception as e:
        _logger.error("Error getting historical invoice patterns: {}", e)
        return {
            "average_amount": 0.0,
            "min_amount": 0.0,
            "max_amount": 0.0,
            "median_amount": 0.0,
            "count": 0,
            "standard_deviation": 0.0,
            "vendor_id": vendor_id,
            "sow_id": sow_id,
            "error": str(e)
        }


@pipeline_tool(toolkit="aegis", name="get_anomaly_thresholds")
def get_anomaly_thresholds(
    db_file: str,
    metric_type: str = "amount_spike",
    vendor_id: Optional[str] = None,
    vendor_name: Optional[str] = None
) -> Dict[str, Any]:
    """Get anomaly detection thresholds for a specific metric type.
    
    Args:
        db_file: Absolute path to the database file
        metric_type: Type of metric (e.g., "amount_spike", "quantity_variance", "frequency_anomaly")
        vendor_id: Vendor ID for vendor-specific threshold (optional)
        vendor_name: Vendor name for vendor-specific threshold (optional, will lookup vendor_id)
    
    Returns:
        Dictionary with:
        - threshold_id: Threshold ID
        - metric_type: Metric type
        - vendor_id: Vendor ID (None for global)
        - baseline_value: Baseline value for the metric
        - variance_percentage: Allowed variance percentage (e.g., 50.0 means 50% above baseline is threshold)
        - lookback_days: Number of days to look back
        - is_global: Whether this is a global threshold (True) or vendor-specific (False)
        - error: Error message if any
    """
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()
        
        # Lookup vendor_id from vendor_name if provided
        if vendor_name and not vendor_id:
            cursor.execute("""
                SELECT vendor_id FROM vendors
                WHERE vendor_name = ?
            """, (vendor_name,))
            vendor_row = cursor.fetchone()
            if vendor_row:
                vendor_id = vendor_row["vendor_id"]
        
        # Try vendor-specific threshold first, then fall back to global
        if vendor_id:
            cursor.execute("""
                SELECT threshold_id, metric_type, vendor_id, baseline_value, 
                       variance_percentage, lookback_days
                FROM anomaly_thresholds
                WHERE metric_type = ? AND vendor_id = ?
                LIMIT 1
            """, (metric_type, vendor_id))
            row = cursor.fetchone()
            
            if row:
                conn.close()
                return {
                    "threshold_id": row["threshold_id"],
                    "metric_type": row["metric_type"],
                    "vendor_id": row["vendor_id"],
                    "baseline_value": float(row["baseline_value"]) if row["baseline_value"] else 0.0,
                    "variance_percentage": float(row["variance_percentage"]) if row["variance_percentage"] else 50.0,
                    "lookback_days": int(row["lookback_days"]) if row["lookback_days"] else 90,
                    "is_global": False,
                    "error": ""
                }
        
        # Fall back to global threshold
        cursor.execute("""
            SELECT threshold_id, metric_type, vendor_id, baseline_value, 
                   variance_percentage, lookback_days
            FROM anomaly_thresholds
            WHERE metric_type = ? AND vendor_id IS NULL
            LIMIT 1
        """, (metric_type,))
        row = cursor.fetchone()
        
        if row:
            conn.close()
            return {
                "threshold_id": row["threshold_id"],
                "metric_type": row["metric_type"],
                "vendor_id": None,
                "baseline_value": float(row["baseline_value"]) if row["baseline_value"] else 0.0,
                "variance_percentage": float(row["variance_percentage"]) if row["variance_percentage"] else 50.0,
                "lookback_days": int(row["lookback_days"]) if row["lookback_days"] else 90,
                "is_global": True,
                "error": ""
            }
        
        # No threshold found
        conn.close()
        return {
            "threshold_id": None,
            "metric_type": metric_type,
            "vendor_id": vendor_id,
            "baseline_value": 0.0,
            "variance_percentage": 50.0,  # Default fallback
            "lookback_days": 90,  # Default fallback
            "is_global": False,
            "error": f"No threshold found for metric_type={metric_type}, vendor_id={vendor_id}"
        }
    
    except Exception as e:
        _logger.error("Error getting anomaly thresholds: {}", e)
        return {
            "threshold_id": None,
            "metric_type": metric_type,
            "vendor_id": vendor_id,
            "baseline_value": 0.0,
            "variance_percentage": 50.0,  # Default fallback
            "lookback_days": 90,  # Default fallback
            "is_global": False,
            "error": str(e)
        }


@pipeline_tool(toolkit="aegis", name="get_payment_patterns")
def get_payment_patterns(
    db_file: str,
    vendor_id: Optional[str] = None,
    vendor_name: Optional[str] = None,
    lookback_days: int = 365
) -> Dict[str, Any]:
    """Get payment pattern analysis for anomaly detection.
    
    Args:
        db_file: Absolute path to the database file
        vendor_id: Vendor ID to filter payment history (optional)
        vendor_name: Vendor name to filter payment history (optional, will lookup vendor_id)
        lookback_days: Number of days to look back for payment data (default: 365 = 1 year)
    
    Returns:
        Dictionary with:
        - total_payments: Total number of payments
        - on_time_payments: Number of on-time payments
        - late_payments: Number of late payments
        - average_payment_delay_days: Average delay in days for late payments
        - payment_frequency_days: Average days between payments
        - total_payment_amount: Total amount paid
        - average_payment_amount: Average payment amount
        - payment_methods: Dictionary of payment methods and counts
        - vendor_id: Vendor ID used (if provided)
        - error: Error message if any
    """
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()
        
        # Lookup vendor_id from vendor_name if provided
        if vendor_name and not vendor_id:
            cursor.execute("""
                SELECT vendor_id FROM vendors
                WHERE vendor_name = ?
            """, (vendor_name,))
            vendor_row = cursor.fetchone()
            if vendor_row:
                vendor_id = vendor_row["vendor_id"]
        
        # Build query based on provided filters
        conditions = []
        params = []
        
        if vendor_id:
            conditions.append("vendor_id = ?")
            params.append(vendor_id)
        
        # Filter by date (lookback_days)
        from datetime import datetime, timedelta
        cutoff_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        conditions.append("payment_date >= ?")
        params.append(cutoff_date)
        
        # Only include completed payments
        conditions.append("payment_status = 'completed'")
        
        where_clause = " AND ".join(conditions) if conditions else "payment_status = 'completed'"
        
        # Get payment statistics
        query = f"""
            SELECT 
                COUNT(*) as total_payments,
                SUM(payment_amount) as total_amount,
                AVG(payment_amount) as avg_amount
            FROM payment_history
            WHERE {where_clause}
        """
        
        cursor.execute(query, params)
        row = cursor.fetchone()
        
        if not row or row["total_payments"] == 0:
            conn.close()
            return {
                "total_payments": 0,
                "on_time_payments": 0,
                "late_payments": 0,
                "average_payment_delay_days": 0.0,
                "payment_frequency_days": 0.0,
                "total_payment_amount": 0.0,
                "average_payment_amount": 0.0,
                "payment_methods": {},
                "vendor_id": vendor_id,
                "error": f"No payment history found (vendor_id={vendor_id}, vendor_name={vendor_name}, lookback_days={lookback_days})"
            }
        
        total_payments = row["total_payments"]
        total_amount = float(row["total_amount"]) if row["total_amount"] else 0.0
        avg_amount = float(row["avg_amount"]) if row["avg_amount"] else 0.0
        
        # Get payment methods distribution
        method_query = f"""
            SELECT payment_method, COUNT(*) as count
            FROM payment_history
            WHERE {where_clause}
            GROUP BY payment_method
        """
        cursor.execute(method_query, params)
        method_rows = cursor.fetchall()
        payment_methods = {row["payment_method"]: row["count"] for row in method_rows}
        
        # Get on-time vs late payments by joining with historical_invoices
        timing_conditions = ["ph.payment_status = 'completed'", "ph.payment_date >= ?"]
        timing_params = [cutoff_date]
        if vendor_id:
            timing_conditions.insert(0, "ph.vendor_id = ?")
            timing_params.insert(0, vendor_id)
        
        timing_where = " AND ".join(timing_conditions)
        timing_query = f"""
            SELECT 
                SUM(CASE WHEN ph.payment_date <= DATE(hi.invoice_date, '+30 days') THEN 1 ELSE 0 END) as on_time,
                SUM(CASE WHEN ph.payment_date > DATE(hi.invoice_date, '+30 days') THEN 1 ELSE 0 END) as late,
                AVG(CASE WHEN ph.payment_date > DATE(hi.invoice_date, '+30 days') 
                    THEN JULIANDAY(ph.payment_date) - JULIANDAY(DATE(hi.invoice_date, '+30 days')) ELSE NULL END) as avg_delay
            FROM payment_history ph
            JOIN historical_invoices hi ON ph.invoice_id = hi.invoice_number
            WHERE {timing_where}
        """
        
        cursor.execute(timing_query, timing_params)
        timing_row = cursor.fetchone()
        
        on_time_payments = int(timing_row["on_time"]) if timing_row and timing_row["on_time"] else 0
        late_payments = int(timing_row["late"]) if timing_row and timing_row["late"] else 0
        avg_delay_days = float(timing_row["avg_delay"]) if timing_row and timing_row["avg_delay"] else 0.0
        
        conn.close()
        
        return {
            "total_payments": total_payments,
            "on_time_payments": on_time_payments,
            "late_payments": late_payments,
            "average_payment_delay_days": round(avg_delay_days, 2),
            "payment_frequency_days": 0.0,  # Would need window functions or separate calculation
            "total_payment_amount": round(total_amount, 2),
            "average_payment_amount": round(avg_amount, 2),
            "payment_methods": payment_methods,
            "vendor_id": vendor_id,
            "error": ""
        }
    
    except Exception as e:
        _logger.error("Error getting payment patterns: {}", e)
        return {
            "total_payments": 0,
            "on_time_payments": 0,
            "late_payments": 0,
            "average_payment_delay_days": 0.0,
            "payment_frequency_days": 0.0,
            "total_payment_amount": 0.0,
            "average_payment_amount": 0.0,
            "payment_methods": {},
            "vendor_id": vendor_id,
            "error": str(e)
        }


# ---------------------------------------------------------------------
# Database Write Tools
# ---------------------------------------------------------------------

@pipeline_tool(toolkit="aegis", name="save_processing_results")
def save_processing_results(
    db_file: str,
    invoice_id: str,
    status: str,
    processing_status: str,
    final_decision: str,
    decision_rationale: str,
    straight_through_eligible: bool,
    requires_human_review: bool,
    run_id: Optional[str] = None,
    validation_results: Optional[List[Dict[str, Any]]] = None,
    exceptions: Optional[List[Dict[str, Any]]] = None,
    hitl_decision: Optional[str] = None,
    hitl_response_data: Optional[Dict[str, Any]] = None,
    extracted_invoice_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Save invoice processing results to database.
    
    This tool handles all database writes for invoice processing:
    - Updates incoming_invoices table
    - Inserts into invoice_processing_status table
    - Inserts into validation_results table
    - Inserts into exceptions table
    - Inserts into clarification_requests table (if applicable)
    - Inserts into finance_adjustments table (if applicable)
    
    Args:
        db_file: Absolute path to the database file
        invoice_id: Invoice ID
        status: Invoice status (approved, rejected, needs_clarification, approved_with_adjustment)
        processing_status: Processing status (completed, in_review, etc.)
        final_decision: Final decision (approve, reject, request_clarification, etc.)
        decision_rationale: Rationale for the decision
        straight_through_eligible: Whether invoice was eligible for straight-through processing
        requires_human_review: Whether invoice required human review
        run_id: Processing run ID (optional)
        validation_results: List of validation result dictionaries (optional)
        exceptions: List of exception dictionaries (optional)
        hitl_decision: HITL decision (optional)
        hitl_response_data: HITL response data (optional)
        extracted_invoice_data: Extracted invoice data from invoice extractor (optional, used to get vendor_name and invoice_number)
    
    Returns:
        Dictionary with records_updated, records_inserted, status, and error
    """
    conn = None
    try:
        # Normalize hitl_response_data - handle empty string from OAK parsing
        if hitl_response_data == "" or (isinstance(hitl_response_data, str) and not hitl_response_data.strip()):
            hitl_response_data = None
        
        # Normalize extracted_invoice_data - handle empty string from OAK parsing
        if extracted_invoice_data == "" or (isinstance(extracted_invoice_data, str) and not extracted_invoice_data.strip()):
            extracted_invoice_data = None
        
        conn = _connect(db_file)
        cursor = conn.cursor()
        records_updated = 0
        records_inserted = 0
        current_time = _utc_iso()
        
        # 1. Update incoming_invoices table
        cursor.execute("""
            UPDATE incoming_invoices
            SET status = ?, updated_at = ?
            WHERE invoice_id = ?
        """, (status, current_time, invoice_id))
        records_updated += cursor.rowcount
        
        # Get invoice details for clarification_requests and finance_adjustments
        # Note: incoming_invoices table doesn't have vendor_id or invoice_number
        # These need to be looked up from extracted data or vendors table
        vendor_id = None
        invoice_number = None
        vendor_name = None
        
        # First, try to get vendor_name and invoice_number from extracted_invoice_data
        if extracted_invoice_data:
            vendor_name = extracted_invoice_data.get("vendor_name")
            invoice_number = extracted_invoice_data.get("invoice_number")
        
        # Fallback: Try to get from hitl_response_data if available
        if not vendor_name and hitl_response_data:
            vendor_name = hitl_response_data.get("vendor_name")
        if not invoice_number and hitl_response_data:
            invoice_number = hitl_response_data.get("invoice_number")
        
        # Fallback: Try to get from validation_results
        if not invoice_number and validation_results:
            for vr in validation_results:
                if "invoice_number" in vr:
                    invoice_number = vr["invoice_number"]
                    break
                # Also check details field which might contain extracted data
                if "details" in vr and isinstance(vr["details"], str):
                    try:
                        details_json = json.loads(vr["details"])
                        if "invoice_number" in details_json:
                            invoice_number = details_json["invoice_number"]
                        if "vendor_name" in details_json and not vendor_name:
                            vendor_name = details_json["vendor_name"]
                    except (json.JSONDecodeError, TypeError):
                        pass
        
        # Lookup vendor_id from vendor_name if we have it
        if vendor_name:
            cursor.execute("""
                SELECT vendor_id FROM vendors
                WHERE vendor_name = ?
            """, (vendor_name,))
            vendor_row = cursor.fetchone()
            if vendor_row:
                vendor_id = vendor_row["vendor_id"]
        
        # 2. Insert into invoice_processing_status
        cursor.execute("""
            INSERT INTO invoice_processing_status (
                status_id, invoice_id, run_id, processing_status, final_decision,
                decision_rationale, straight_through_eligible, requires_human_review,
                processed_at, decision_made_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid4()), invoice_id, run_id, processing_status, final_decision,
            decision_rationale, straight_through_eligible, requires_human_review,
            current_time, current_time
        ))
        records_inserted += 1
        
        # 3. Insert validation results
        if validation_results:
            for vr in validation_results:
                # Map to actual schema columns
                validation_type = vr.get("validator_name", "")
                validation_status = "passed" if vr.get("validation_passed", False) else "failed"
                validation_details = json.dumps({
                    "issues_found": vr.get("issues_found", []),
                    "details": vr.get("details", "")
                })
                
                cursor.execute("""
                    INSERT INTO validation_results (
                        validation_id, invoice_id, validation_type, validation_status,
                        validation_details, validated_at, validated_by_agent
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid4()), invoice_id,
                    validation_type,
                    validation_status,
                    validation_details,
                    current_time,
                    validation_type  # Use validator_name as validated_by_agent
                ))
                records_inserted += 1
        
        # 4. Insert exceptions
        if exceptions:
            for exc in exceptions:
                # Map to actual schema columns
                exception_type = exc.get("exception_type", "")
                exception_description = exc.get("exception_details", "")
                # Determine category from exception type
                exception_category = "validation" if exception_type in ["rate_violation", "wbs_budget_exceeded", "abnormal_spike"] else "compliance"
                
                cursor.execute("""
                    INSERT INTO exceptions (
                        exception_id, invoice_id, exception_type, exception_category,
                        exception_description, severity, detected_at, detected_by_agent
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid4()), invoice_id,
                    exception_type,
                    exception_category,
                    exception_description,
                    exc.get("severity", "medium"),
                    current_time,
                    "aegis_exception_detector"  # Agent that detected the exception
                ))
                records_inserted += 1
        
        # 5. Handle HITL decision-based inserts
        # Note: Decision values come from option values (e.g., "request_clarification", "apply_retention")
        # not from option labels (e.g., "Request Clarification", "Apply Retention")
        if hitl_decision:
            # Normalize decision to lowercase for comparison (handles both label and value formats)
            decision_lower = hitl_decision.lower() if isinstance(hitl_decision, str) else ""
            
            if decision_lower in ["request_evidence", "request evidence", "request_clarification", "request clarification"]:
                # Insert into clarification_requests
                if "evidence" in decision_lower:
                    request_type = "evidence_request"
                else:
                    request_type = "clarification"
                
                # Extract user input text from hitl_response_data
                # For input gates, all field values are in hitl_response_data dict
                # For selection gates, specific fields might be in hitl_response_data
                required_info = ""
                requested_evidence = ""
                
                if hitl_response_data:
                    # Try to get specific fields first
                    required_info = hitl_response_data.get("required_information", "") or hitl_response_data.get("required_info", "") or hitl_response_data.get("clarification_text", "") or ""
                    requested_evidence = hitl_response_data.get("requested_evidence_types", "") or hitl_response_data.get("evidence_types", "") or ""
                    
                    # If no specific fields found, extract all text fields (for input gates)
                    # Combine all text/textarea fields into required_information
                    if not required_info and isinstance(hitl_response_data, dict):
                        text_fields = []
                        # Common field names that might contain user input
                        text_field_names = [
                            "notes", "comments", "message", "description", "details",
                            "required_information", "required_info", "clarification_text",
                            "feedback", "response", "input", "text"
                        ]
                        
                        for field_name in text_field_names:
                            if field_name in hitl_response_data:
                                value = hitl_response_data[field_name]
                                if value and isinstance(value, str) and value.strip():
                                    text_fields.append(f"{field_name}: {value}")
                        
                        # Also check for any other string values that look like user input
                        # (skip internal fields like "selection", "decision", etc.)
                        skip_fields = {"selection", "decision", "notes", "responded_by", "responded_at"}
                        for key, value in hitl_response_data.items():
                            if key not in skip_fields and isinstance(value, str) and value.strip() and len(value) > 10:
                                # Likely user input if it's a string longer than 10 chars
                                if key not in text_field_names:  # Don't duplicate
                                    text_fields.append(f"{key}: {value}")
                        
                        if text_fields:
                            required_info = "\n\n".join(text_fields)
                    
                    # Extract evidence types if available
                    if not requested_evidence:
                        # Check for evidence-related fields
                        evidence_fields = [
                            "requested_evidence_types", "evidence_types", "missing_evidence",
                            "evidence_list", "required_evidence"
                        ]
                        for field_name in evidence_fields:
                            if field_name in hitl_response_data:
                                value = hitl_response_data[field_name]
                                if value:
                                    if isinstance(value, list):
                                        requested_evidence = ", ".join(str(v) for v in value)
                                    else:
                                        requested_evidence = str(value)
                                    break
                
                cursor.execute("""
                    INSERT INTO clarification_requests (
                        request_id, invoice_id, vendor_id, invoice_number,
                        request_type, required_information, requested_evidence_types,
                        status, requested_date, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid4()), invoice_id, vendor_id, invoice_number,
                    request_type, required_info, requested_evidence,
                    "pending", current_time, current_time, current_time
                ))
                records_inserted += 1
            
            elif decision_lower in ["apply_retention", "apply retention", "apply_ld", "apply ld", "apply_liquidated_damages"]:
                # Insert into finance_adjustments
                if "retention" in decision_lower:
                    adjustment_type = "retention"
                else:
                    adjustment_type = "liquidated_damages"
                
                # Extract adjustment details from response_data or validation results
                adjustment_amount = 0.0
                adjustment_reason = ""
                original_amount = 0.0
                adjusted_amount = 0.0
                
                if hitl_response_data:
                    # Try to get specific numeric fields
                    try:
                        adjustment_amount = float(hitl_response_data.get("adjustment_amount", 0.0) or 0.0)
                    except (ValueError, TypeError):
                        adjustment_amount = 0.0
                    
                    try:
                        original_amount = float(hitl_response_data.get("original_invoice_amount", 0.0) or 0.0)
                    except (ValueError, TypeError):
                        original_amount = 0.0
                    
                    try:
                        adjusted_amount = float(hitl_response_data.get("adjusted_invoice_amount", 0.0) or 0.0)
                    except (ValueError, TypeError):
                        adjusted_amount = 0.0
                    
                    # Extract adjustment reason - try multiple field names
                    adjustment_reason = (
                        hitl_response_data.get("adjustment_reason", "") or
                        hitl_response_data.get("reason", "") or
                        hitl_response_data.get("notes", "") or
                        hitl_response_data.get("comments", "") or
                        ""
                    )
                    
                    # If no specific reason field found, extract all text fields (for input gates)
                    if not adjustment_reason and isinstance(hitl_response_data, dict):
                        text_fields = []
                        # Common field names that might contain user input
                        text_field_names = [
                            "notes", "comments", "message", "description", "details",
                            "adjustment_reason", "reason", "feedback", "response"
                        ]
                        
                        for field_name in text_field_names:
                            if field_name in hitl_response_data:
                                value = hitl_response_data[field_name]
                                if value and isinstance(value, str) and value.strip():
                                    text_fields.append(f"{field_name}: {value}")
                        
                        # Also check for any other string values that look like user input
                        skip_fields = {"selection", "decision", "adjustment_amount", "original_invoice_amount", 
                                     "adjusted_invoice_amount", "responded_by", "responded_at"}
                        for key, value in hitl_response_data.items():
                            if key not in skip_fields and isinstance(value, str) and value.strip() and len(value) > 10:
                                if key not in text_field_names:  # Don't duplicate
                                    text_fields.append(f"{key}: {value}")
                        
                        if text_fields:
                            adjustment_reason = "\n\n".join(text_fields)
                
                # Get SOW ID from invoice if available
                cursor.execute("""
                    SELECT sow_id FROM incoming_invoices WHERE invoice_id = ?
                """, (invoice_id,))
                invoice_sow_row = cursor.fetchone()
                sow_id = invoice_sow_row["sow_id"] if invoice_sow_row else None
                
                # Get milestone_id if available from validation results
                milestone_id = None
                if validation_results:
                    for vr in validation_results:
                        if "milestone_id" in vr:
                            milestone_id = vr["milestone_id"]
                            break
                
                cursor.execute("""
                    INSERT INTO finance_adjustments (
                        adjustment_id, invoice_id, vendor_id, invoice_number,
                        adjustment_type, adjustment_amount, adjustment_reason,
                        original_invoice_amount, adjusted_invoice_amount,
                        retention_percentage, ld_rate_per_day, ld_days,
                        milestone_id, sow_id, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid4()), invoice_id, vendor_id, invoice_number,
                    adjustment_type, adjustment_amount, adjustment_reason,
                    original_amount, adjusted_amount,
                    None, None, None,  # These would be populated from validation results if needed
                    milestone_id, sow_id, "pending", current_time, current_time
                ))
                records_inserted += 1
        
        conn.commit()
        conn.close()
        
        return {
            "records_updated": records_updated,
            "records_inserted": records_inserted,
            "status": "success",
            "error": ""
        }
    
    except Exception as e:
        _logger.error("Error saving processing results: {}", e)
        if conn:
            conn.rollback()
            conn.close()
        return {
            "records_updated": 0,
            "records_inserted": 0,
            "status": "error",
            "error": str(e)
        }
