"""
ReconVoy - Pipeline-specific local tools (Phase 3 Redesign).

Goal:
- Agents should NOT directly use sqlite_query/sqlite_execute or python_execute.
- LLM can generate ideas/text, but all DB reads/writes and deterministic
  computation must go through these tools.

This toolkit is intentionally opinionated and schema-aware for the ReconVoy
database created by:
  src/topaz_agent_kit/scripts/setup_reconvoy_database.py

New Design:
- BlackLine unmatched items (input)
- US and FR books (reference only)
- UK journal entries (output)
- FX rates (book and spot)
"""

from __future__ import annotations

import ast
import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from topaz_agent_kit.local_tools.registry import pipeline_tool
from topaz_agent_kit.utils.logger import Logger

_logger = Logger("ReconVoyTools")


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


def _convert_date_to_iso(date_str: str) -> str:
    """Convert date from DD.MM.YY format to YYYY-MM-DD format.
    
    Args:
        date_str: Date in DD.MM.YY format (e.g., "14.01.26")
        
    Returns:
        Date in YYYY-MM-DD format (e.g., "2026-01-14")
        
    Note:
        Assumes YY >= 00 means 2000-2099, YY < 00 means 2100-2199
        For dates like "14.01.26", assumes 2026 (not 1926 or 2126)
    """
    try:
        parts = date_str.split(".")
        if len(parts) != 3:
            return date_str  # Return as-is if format doesn't match
        
        day, month, year_short = parts
        year_short_int = int(year_short)
        
        # Assume years 00-99 are 2000-2099
        year_full = 2000 + year_short_int
        
        return f"{year_full:04d}-{month:02s}-{day:02s}"
    except (ValueError, IndexError):
        # If conversion fails, return as-is (might already be YYYY-MM-DD)
        return date_str


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert SQLite row to dictionary."""
    return dict(row)


# ---------------------------------------------------------------------
# BlackLine Tools
# ---------------------------------------------------------------------


@pipeline_tool(toolkit="reconvoy", name="get_blackline_unmatched_items")
def get_blackline_unmatched_items(db_file: str, project_dir: str) -> Dict[str, Any]:
    """Get all unmatched BlackLine items to process.

    Returns all items where:
    - status = 'UNMATCHED'
    - processing_status IS NULL
    - source = 'GL (SAP)'

    Assigns a run_id if not already assigned.

    Args:
        db_file: Absolute path to the ReconVoy database file
        project_dir: Absolute path to project root directory

    Returns:
        Dictionary with unmatched_items list, run_id, database_path, total_unmatched
    """
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()

        # Get run_id or create new one
        cursor.execute(
            """
            SELECT DISTINCT run_id
            FROM blackline_unmatched_items
            WHERE run_id IS NOT NULL
            ORDER BY run_id DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        if row and row["run_id"]:
            run_id = row["run_id"]
        else:
            run_id = f"run-{_utc_iso()}"

        # Get all unmatched items
        cursor.execute(
            """
            SELECT *
            FROM blackline_unmatched_items
            WHERE status = 'UNMATCHED'
              AND processing_status IS NULL
              AND source = 'GL (SAP)'
            ORDER BY item_id ASC
            """
        )
        item_rows = cursor.fetchall()

        # Count total unmatched
        cursor.execute(
            """
            SELECT COUNT(*) as count
            FROM blackline_unmatched_items
            WHERE status = 'UNMATCHED'
              AND processing_status IS NULL
            """
        )
        total_row = cursor.fetchone()
        total_unmatched = total_row["count"] if total_row else 0

        items = []
        # Don't assign run_id here - it will be assigned when processing_status is set
        # This ensures run_id is only assigned to items actually being processed in the current iteration
        for item_row in item_rows:
            item = _row_to_dict(item_row)
            items.append(item)

        conn.close()

        return {
            "unmatched_items": items,
            "run_id": run_id,
            "database_path": db_file,
            "total_unmatched": total_unmatched,
            "error": "",
        }

    except Exception as e:
        _logger.error("Error getting BlackLine unmatched items: {}", e)
        return {
            "unmatched_items": [],
            "run_id": "",
            "database_path": db_file,
            "total_unmatched": 0,
            "error": str(e),
        }


@pipeline_tool(toolkit="reconvoy", name="update_blackline_processing_status")
def update_blackline_processing_status(
    db_file: str, item_id: str, processing_status: str, run_id: Optional[str] = None
) -> Dict[str, Any]:
    """Update processing_status for a BlackLine item.

    Also assigns run_id if provided and item doesn't already have one.

    Args:
        db_file: Absolute path to ReconVoy database file
        item_id: BlackLine item ID
        processing_status: New processing status ('processing', 'need_to_process', or NULL)
        run_id: Optional run_id to assign if item doesn't have one

    Returns:
        Dictionary with updated=True/False and error
    """
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()

        # If run_id is provided, check if item needs it assigned
        if run_id:
            cursor.execute(
                """
                SELECT run_id
                FROM blackline_unmatched_items
                WHERE item_id = ?
                """,
                (item_id,),
            )
            row = cursor.fetchone()
            if row and not row["run_id"]:
                # Item doesn't have run_id, assign it along with processing_status
                if processing_status:
                    cursor.execute(
                        """
                        UPDATE blackline_unmatched_items
                        SET processing_status = ?, run_id = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE item_id = ?
                        """,
                        (processing_status, run_id, item_id),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE blackline_unmatched_items
                        SET processing_status = NULL, run_id = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE item_id = ?
                        """,
                        (run_id, item_id),
                    )
            else:
                # Item already has run_id, just update processing_status
                if processing_status:
                    cursor.execute(
                        """
                        UPDATE blackline_unmatched_items
                        SET processing_status = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE item_id = ?
                        """,
                        (processing_status, item_id),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE blackline_unmatched_items
                        SET processing_status = NULL, updated_at = CURRENT_TIMESTAMP
                        WHERE item_id = ?
                        """,
                        (item_id,),
                    )
        else:
            # No run_id provided, just update processing_status
            if processing_status:
                cursor.execute(
                    """
                    UPDATE blackline_unmatched_items
                    SET processing_status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE item_id = ?
                    """,
                    (processing_status, item_id),
                )
            else:
                cursor.execute(
                    """
                    UPDATE blackline_unmatched_items
                    SET processing_status = NULL, updated_at = CURRENT_TIMESTAMP
                    WHERE item_id = ?
                    """,
                    (item_id,),
                )

        conn.commit()
        conn.close()

        return {"updated": True, "error": ""}

    except Exception as e:
        _logger.error("Error updating BlackLine processing status: {}", e)
        if conn:
            conn.rollback()
            conn.close()
        return {"updated": False, "error": str(e)}


@pipeline_tool(toolkit="reconvoy", name="update_blackline_match_status")
def update_blackline_match_status(
    db_file: str, item_id: str, match_status: str
) -> Dict[str, Any]:
    """Update status (match type) for a BlackLine item.

    Args:
        db_file: Absolute path to ReconVoy database file
        item_id: BlackLine item ID
        match_status: New match status ('two_way_match', 'three_way_match')

    Returns:
        Dictionary with updated=True/False and error
    """
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE blackline_unmatched_items
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE item_id = ?
            """,
            (match_status, item_id),
        )

        conn.commit()
        conn.close()

        return {"updated": True, "error": ""}

    except Exception as e:
        _logger.error("Error updating BlackLine match status: {}", e)
        if conn:
            conn.rollback()
            conn.close()
        return {"updated": False, "error": str(e)}


@pipeline_tool(toolkit="reconvoy", name="update_blackline_status")
def update_blackline_status(
    db_file: str, item_ids: List[str], status: str
) -> Dict[str, Any]:
    """Update processing_status for multiple BlackLine items.
    
    NOTE: This tool only updates processing_status, NOT the status field.
    The status field (two_way_match, three_way_match) should remain unchanged.
    Only processing_status should be updated to 'processed' or 'rejected'.

    Args:
        db_file: Absolute path to ReconVoy database file
        item_ids: List of BlackLine item IDs
        status: New processing_status ('processed', 'rejected')

    Returns:
        Dictionary with updated_count and error
    """
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()

        placeholders = ",".join("?" for _ in item_ids)
        # Only update processing_status, leave status field unchanged
        cursor.execute(
            f"""
            UPDATE blackline_unmatched_items
            SET processing_status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE item_id IN ({placeholders})
            """,
            [status] + item_ids,
        )

        updated_count = cursor.rowcount
        conn.commit()
        conn.close()

        return {"updated_count": updated_count, "error": ""}

    except Exception as e:
        _logger.error("Error updating BlackLine processing status: {}", e)
        if conn:
            conn.rollback()
            conn.close()
        return {"updated_count": 0, "error": str(e)}


@pipeline_tool(toolkit="reconvoy", name="find_related_blackline_items")
def find_related_blackline_items(
    db_file: str, reference_texts: List[str]
) -> Dict[str, Any]:
    """Find BlackLine items that match given reference texts (exact match only).

    Args:
        db_file: Absolute path to ReconVoy database file
        reference_texts: List of reference/description texts to match (exact match)

    Returns:
        Dictionary with matched_items list (deduplicated by item_id)
    """
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()

        matched_items_dict = {}  # Use dict to deduplicate by item_id
        for ref_text in reference_texts:
            # Exact match only (no LIKE) - matches foreign_book.reference or foreign_book.header_text
            cursor.execute(
                """
                SELECT *
                FROM blackline_unmatched_items
                WHERE status = 'UNMATCHED'
                  AND processing_status IS NULL
                  AND reference_description = ?
                """,
                (ref_text,),
            )
            for row in cursor.fetchall():
                item_dict = _row_to_dict(row)
                item_id = item_dict["item_id"]
                # Deduplicate by item_id
                if item_id not in matched_items_dict:
                    matched_items_dict[item_id] = item_dict

        matched_items = list(matched_items_dict.values())
        conn.close()

        return {"matched_items": matched_items, "error": ""}

    except Exception as e:
        _logger.error("Error finding related BlackLine items: {}", e)
        return {"matched_items": [], "error": str(e)}


@pipeline_tool(toolkit="reconvoy", name="get_blackline_items_by_status")
def get_blackline_items_by_status(
    db_file: str, processing_status: str, document_number: str | None = None
) -> Dict[str, Any]:
    """Get all BlackLine items with a specific processing_status, optionally filtered by document_number.

    Args:
        db_file: Absolute path to ReconVoy database file
        processing_status: Processing status to filter by ('processing')
        document_number: Optional document_number to filter by (ensures items from same case/scenario are grouped together)

    Returns:
        Dictionary with items list
    """
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()

        if document_number:
            cursor.execute(
                """
                SELECT *
                FROM blackline_unmatched_items
                WHERE processing_status = ?
                  AND document_number = ?
                ORDER BY item_id ASC
                """,
                (processing_status, document_number),
            )
        else:
            cursor.execute(
                """
                SELECT *
                FROM blackline_unmatched_items
                WHERE processing_status = ?
                ORDER BY item_id ASC
                """,
                (processing_status,),
            )

        items = [_row_to_dict(row) for row in cursor.fetchall()]
        conn.close()

        return {"items": items, "error": ""}

    except Exception as e:
        _logger.error("Error getting BlackLine items by status: {}", e)
        return {"items": [], "error": str(e)}


@pipeline_tool(toolkit="reconvoy", name="get_related_items_to_process")
def get_related_items_to_process(
    db_file: str, run_id: str
) -> Dict[str, Any]:
    """Get BlackLine items with 'need_to_process' status, excluding GBP items.
    
    This tool is designed for the recursive discovery loop to get items that need
    to be checked for three-way matches. GBP items are excluded because they
    already have two-way matches and don't need recursive processing.

    Args:
        db_file: Absolute path to ReconVoy database file
        run_id: Run ID to filter items for the current processing run

    Returns:
        Dictionary with related_items list (USD/EUR items with need_to_process status)
    """
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM blackline_unmatched_items
            WHERE processing_status = 'need_to_process'
              AND run_id = ?
              AND currency != 'GBP'
            ORDER BY item_id ASC
            """,
            (run_id,),
        )

        items = [_row_to_dict(row) for row in cursor.fetchall()]
        conn.close()

        _logger.info(
            "Found {} related items to process (excluding GBP) for run_id={}",
            len(items), run_id
        )

        return {"related_items": items, "error": ""}

    except Exception as e:
        _logger.error("Error getting related items to process: {}", e)
        return {"related_items": [], "error": str(e)}


@pipeline_tool(toolkit="reconvoy", name="get_blackline_item_by_id")
def get_blackline_item_by_id(
    db_file: str, item_id: str
) -> Dict[str, Any]:
    """Get a single BlackLine item by its item_id.

    Args:
        db_file: Absolute path to ReconVoy database file
        item_id: BlackLine item identifier

    Returns:
        Dictionary with item object or None if not found
    """
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM blackline_unmatched_items
            WHERE item_id = ?
            LIMIT 1
            """,
            (item_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return {"item": _row_to_dict(row), "error": ""}
        else:
            return {"item": None, "error": f"Item {item_id} not found"}

    except Exception as e:
        _logger.error("Error getting BlackLine item by ID: {}", e)
        return {"item": None, "error": str(e)}


# ---------------------------------------------------------------------
# Foreign Books Tools
# ---------------------------------------------------------------------


@pipeline_tool(toolkit="reconvoy", name="find_foreign_book_match")
def find_foreign_book_match(
    db_file: str,
    currency: str,
    reference_description: str,
    amount_foreign: float,
    target_book: Optional[str] = None,
) -> Dict[str, Any]:
    """Find matching entry in foreign books (US or FR) based on reference only.

    Args:
        db_file: Absolute path to ReconVoy database file
        currency: Currency code ('USD', 'EUR', 'GBP')
        reference_description: Reference/description from BlackLine item
        amount_foreign: Foreign amount (not used for matching, kept for backward compatibility)
        target_book: Optional target book ('us_books' or 'fr_books'). If provided, overrides currency-based selection.
                     Used for recursive discovery to check the OTHER foreign book.

    Returns:
        Dictionary with matched_entry, document_number, related_entries, and foreign_book_type
    """
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()

        # Determine which table(s) to query
        # If target_book is specified, use it (for recursive discovery to check OTHER foreign book)
        # Otherwise, use currency-based selection
        tables_to_try = []
        if target_book:
            if target_book in ["us_books", "fr_books"]:
                tables_to_try = [(target_book, target_book)]
            else:
                return {
                    "matched_entry": None,
                    "document_number": None,
                    "related_entries": [],
                    "foreign_book_type": None,
                    "error": f"Invalid target_book: {target_book}. Must be 'us_books' or 'fr_books'",
                }
        elif currency == "USD":
            tables_to_try = [("us_books", "us_books")]
        elif currency == "EUR":
            tables_to_try = [("fr_books", "fr_books")]
        elif currency == "GBP":
            # Try US books first, then FR books if no match
            tables_to_try = [("us_books", "us_books"), ("fr_books", "fr_books")]
        else:
            return {
                "matched_entry": None,
                "document_number": None,
                "related_entries": [],
                "foreign_book_type": None,
                "error": f"Unsupported currency: {currency}",
            }

        # Try each table until we find a match
        matched_row = None
        table_name = None
        for table_name, _ in tables_to_try:
            cursor.execute(
                f"""
                SELECT *
                FROM {table_name}
                WHERE (reference = ? OR header_text = ?)
                LIMIT 1
                """,
                (reference_description, reference_description),
            )
            matched_row = cursor.fetchone()
            if matched_row:
                break  # Found a match, stop trying other tables

        if not matched_row:
            conn.close()
            return {
                "matched_entry": None,
                "document_number": None,
                "related_entries": [],
                "foreign_book_type": None,
                "error": "No match found",
            }

        matched_entry = _row_to_dict(matched_row)
        document_number = matched_entry["document_number"]

        # Find all entries with same document_number
        cursor.execute(
            f"""
            SELECT *
            FROM {table_name}
            WHERE document_number = ?
            ORDER BY entry_id ASC
            """,
            (document_number,),
        )
        related_entries = [_row_to_dict(row) for row in cursor.fetchall()]

        conn.close()

        return {
            "matched_entry": matched_entry,
            "document_number": document_number,
            "related_entries": related_entries,
            "foreign_book_type": table_name,
            "error": "",
        }

    except Exception as e:
        _logger.error("Error finding foreign book match: {}", e)
        return {
            "matched_entry": None,
            "document_number": None,
            "related_entries": [],
            "foreign_book_type": None,
            "error": str(e),
        }


@pipeline_tool(toolkit="reconvoy", name="get_foreign_book_entries_by_document")
def get_foreign_book_entries_by_document(
    db_file: str, foreign_book_type: str, document_number: str
) -> Dict[str, Any]:
    """Get all entries from a foreign book with a specific document_number.

    Args:
        db_file: Absolute path to ReconVoy database file
        foreign_book_type: 'us_books' or 'fr_books'
        document_number: Document number to search for

    Returns:
        Dictionary with entries list
    """
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()

        if foreign_book_type not in ["us_books", "fr_books"]:
            return {"entries": [], "error": f"Invalid foreign_book_type: {foreign_book_type}"}

        cursor.execute(
            f"""
            SELECT *
            FROM {foreign_book_type}
            WHERE document_number = ?
            ORDER BY entry_id ASC
            """,
            (document_number,),
        )

        entries = [_row_to_dict(row) for row in cursor.fetchall()]
        conn.close()

        return {"entries": entries, "error": ""}

    except Exception as e:
        _logger.error("Error getting foreign book entries: {}", e)
        return {"entries": [], "error": str(e)}


# ---------------------------------------------------------------------
# FX Rates Tools
# ---------------------------------------------------------------------


@pipeline_tool(toolkit="reconvoy", name="get_fx_rate")
def get_fx_rate(
    db_file: str,
    rate_date: str,
    from_currency: str,
    to_currency: str,
    rate_type: str,
) -> Dict[str, Any]:
    """Get FX rate for a specific date, currency pair, and rate type.

    Args:
        db_file: Absolute path to ReconVoy database file
        rate_date: Date in YYYY-MM-DD format (or DD.MM.YY format, will be auto-converted)
        from_currency: Source currency (e.g., 'USD', 'EUR')
        to_currency: Target currency (e.g., 'GBP')
        rate_type: 'book' or 'spot'

    Returns:
        Dictionary with rate_value and error
    """
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()

        # Convert date format if needed (DD.MM.YY -> YYYY-MM-DD)
        iso_date = _convert_date_to_iso(rate_date)

        cursor.execute(
            """
            SELECT rate_value
            FROM fx_rates
            WHERE rate_date = ?
              AND from_currency = ?
              AND to_currency = ?
              AND rate_type = ?
            LIMIT 1
            """,
            (iso_date, from_currency, to_currency, rate_type),
        )
        row = cursor.fetchone()

        conn.close()

        if row:
            return {"rate_value": float(row["rate_value"]), "error": ""}
        else:
            return {
                "rate_value": None,
                "error": f"No {rate_type} rate found for {from_currency}/{to_currency} on {iso_date}",
            }

    except Exception as e:
        _logger.error("Error getting FX rate: {}", e)
        return {"rate_value": None, "error": str(e)}


# ---------------------------------------------------------------------
# UK Journal Entries Tools
# ---------------------------------------------------------------------


@pipeline_tool(toolkit="reconvoy", name="post_uk_journal_entries")
def post_uk_journal_entries(
    db_file: str,
    case_id: str,
    blackline_item_ids: List[str],
    journal_entries: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Post UK journal entries to the database.

    Args:
        db_file: Absolute path to ReconVoy database file
        case_id: Case identifier
        blackline_item_ids: List of BlackLine item IDs cleared by these journals
        journal_entries: List of journal entry dictionaries

    Returns:
        Dictionary with posted=True/False, entry_ids, and error
    """
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()
        now = _utc_iso()

        entry_ids = []
        for idx, entry in enumerate(journal_entries):
            entry_id = entry.get("entry_id") or f"UK-JE-{case_id}-{idx+1:03d}"

            cursor.execute(
                """
                INSERT INTO uk_journal_entries (
                    entry_id, company_code, scenario, gl_account, business_area,
                    assignment, document_type, document_date, posting_date,
                    reference, header_text, posting_key, document_currency,
                    amount_document_currency, amount_local_currency, local_currency,
                    tax_code, profit_center, cost_center, trading_partner,
                    clearing_doc_no, clearing_date, plant, "order", wbs_element,
                    remarks, case_id, blackline_item_ids, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry_id,
                    entry.get("company_code", "UK01"),
                    entry.get("scenario"),
                    entry.get("gl_account", ""),
                    entry.get("business_area"),
                    entry.get("assignment"),
                    entry.get("document_type", "AB"),
                    entry.get("document_date", now[:10]),
                    entry.get("posting_date", now[:10]),
                    entry.get("reference"),
                    entry.get("header_text"),
                    entry.get("posting_key"),
                    entry.get("document_currency", "GBP"),
                    entry.get("amount_document_currency", 0),
                    entry.get("amount_local_currency", entry.get("amount_local_gbp", 0)),
                    entry.get("local_currency", "GBP"),
                    entry.get("tax_code"),
                    entry.get("profit_center"),
                    entry.get("cost_center"),
                    entry.get("trading_partner"),
                    entry.get("clearing_doc_no"),
                    entry.get("clearing_date"),
                    entry.get("plant"),
                    entry.get("order"),
                    entry.get("wbs_element"),
                    entry.get("remarks"),
                    case_id,
                    json.dumps(blackline_item_ids),
                    now,
                ),
            )
            entry_ids.append(entry_id)

        conn.commit()
        conn.close()

        _logger.info(
            "Posted {} UK journal entries for case_id={}", len(entry_ids), case_id
        )

        return {"posted": True, "entry_ids": entry_ids, "error": ""}

    except Exception as e:
        _logger.error("Error posting UK journal entries: {}", e)
        if conn:
            conn.rollback()
            conn.close()
        return {"posted": False, "entry_ids": [], "error": str(e)}


# ---------------------------------------------------------------------
# Results Recording Tools
# ---------------------------------------------------------------------


@pipeline_tool(toolkit="reconvoy", name="save_reconvoy_processing_results")
def save_reconvoy_processing_results(
    db_file: str,
    item_id: str,
    run_id: str,
    route: str,
    hitl_required: bool,
    hitl_decision: Optional[str] = None,
    fx_summary: Optional[str] = None,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """Save per-item processing results for ReconVoy.

    Args:
        db_file: Absolute path to ReconVoy database file
        item_id: BlackLine item identifier
        run_id: Processing run ID
        route: Final route taken ("StraightThrough" or "HITL")
        hitl_required: Whether HITL was required
        hitl_decision: Final HITL decision (if any)
        fx_summary: Short text summary of FX / variance analysis
        error: Error message, if any
    """
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()
        now = _utc_iso()

        cursor.execute(
            """
            INSERT INTO reconvoy_results (
                open_item_id,
                run_id,
                route,
                hitl_required,
                hitl_decision,
                fx_summary,
                error,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_id,
                run_id,
                route,
                1 if hitl_required else 0,
                hitl_decision,
                fx_summary,
                error or "",
                now,
            ),
        )

        conn.commit()
        conn.close()

        return {"recorded": True, "error": ""}

    except Exception as e:
        _logger.error("Error saving ReconVoy processing results: {}", e)
        if conn:
            conn.rollback()
            conn.close()
        return {"recorded": False, "error": str(e)}


@pipeline_tool(toolkit="reconvoy", name="get_case_item_foreign_book_mappings")
def get_case_item_foreign_book_mappings(
    db_file: str,
    item_ids: List[str],
    item_discovery_results: Any,  # Can be List[Dict] or Dict wrapping a list
    related_items_discovery_results: Any,  # Can be List[Dict] or Dict wrapping a list
) -> Dict[str, Any]:
    """Get foreign book mappings for all items in a case group.
    
    This tool resolves foreign book mappings for case items by:
    1. Checking item_discovery results for direct matches
    2. Falling back to related_items_mappings from the FIRST related_items_discovery result
    3. Returns a structured mapping of item_id -> foreign_book_info
    
    Args:
        db_file: Absolute path to ReconVoy database file
        item_ids: List of BlackLine item IDs in the case group
        item_discovery_results: Accumulated list of item_discovery results (may be wrapped in {'result': ..., 'parsed': ...} or dict)
        related_items_discovery_results: Accumulated list of related_items_discovery results (may be wrapped)
    
    Returns:
        Dictionary with mappings for each item that has a foreign book match:
        {
            "mappings": {
                "<item_id>": {
                    "foreign_book_type": "us_books|fr_books",
                    "document_number": "<foreign_document_number>",
                    "source": "item_discovery|related_items_mapping"
                }
            },
            "items_with_mappings": [<list of item_ids>],
            "items_without_mappings": [<list of item_ids>],
            "error": ""
        }
    """
    try:
        mappings = {}
        items_with_mappings = []
        items_without_mappings = []
        
        # Helper to extract list from potentially wrapped format
        def _extract_list(data: Any) -> List[Any]:
            """Extract list from wrapped format or return as-is if already a list."""
            # First, try to parse string if it's a string (could be JSON or Python literal)
            if isinstance(data, str):
                # Try JSON first (double quotes) - may need multiple passes for double-encoded strings
                parsed = None
                current_data = data
                max_parse_attempts = 3
                for attempt in range(max_parse_attempts):
                    try:
                        parsed = json.loads(current_data)
                        _logger.info(
                            "get_case_item_foreign_book_mappings: Parsed JSON string (attempt {}), type: {}", 
                            attempt + 1, type(parsed).__name__
                        )
                        # If we got a string back, it might be double-encoded, try again
                        if isinstance(parsed, str) and attempt < max_parse_attempts - 1:
                            current_data = parsed
                            continue
                        # Recursively process the parsed data
                        return _extract_list(parsed)
                    except (json.JSONDecodeError, ValueError, TypeError):
                        # If JSON fails, try Python literal eval (single quotes)
                        try:
                            parsed = ast.literal_eval(current_data)
                            _logger.info(
                                "get_case_item_foreign_book_mappings: Parsed Python literal string (attempt {}), type: {}", 
                                attempt + 1, type(parsed).__name__
                            )
                            # Recursively process the parsed data
                            return _extract_list(parsed)
                        except (ValueError, SyntaxError) as e:
                            if attempt < max_parse_attempts - 1:
                                # Try next attempt with original data
                                continue
                            # All attempts failed
                            _logger.info(
                                "get_case_item_foreign_book_mappings: Failed to parse string after {} attempts. "
                                "Last error: {}. Value (first 500 chars): {}", 
                                max_parse_attempts, str(e)[:200], data[:500]
                            )
                            return []
            
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                # FIRST: Check if this is a result dict that should be wrapped in a list
                # (This must come before checking for list values, otherwise empty lists will be returned)
                # Check for item_discovery result keys
                if "blackline_item_id" in data or "matched_entry" in data or "related_entries" in data:
                    _logger.info(
                        "get_case_item_foreign_book_mappings: Found item_discovery result dict, wrapping in list. "
                        "Keys: {}", list(data.keys())[:10]
                    )
                    return [data]
                # Check for related_items_discovery result keys
                if "related_blackline_items" in data or "related_items_mappings" in data or "items_marked" in data:
                    _logger.info(
                        "get_case_item_foreign_book_mappings: Found related_items_discovery result dict, wrapping in list. "
                        "Keys: {}", list(data.keys())[:10]
                    )
                    return [data]
                # Check for common wrapper keys - these might contain lists
                for key in ["result", "parsed", "data", "items", "list"]:
                    if key in data:
                        value = data[key]
                        if isinstance(value, list):
                            return value
                        # If value is a dict, check if it contains a list
                        elif isinstance(value, dict):
                            # Check if any nested value is a list
                            for nested_value in value.values():
                                if isinstance(nested_value, list) and nested_value:  # Only return non-empty lists
                                    return nested_value
                # Check if any value is a list (OAK might wrap it)
                # BUT: Only return non-empty lists, otherwise we might return empty lists from result dicts
                for value in data.values():
                    if isinstance(value, list) and value:  # Only return non-empty lists
                        return value
                # Check if this is a wrapped result dict (has 'result' and/or 'parsed' keys)
                # and if the nested dicts contain result-like keys, wrap it in a list
                if "result" in data or "parsed" in data:
                    # Check nested dicts for result-like keys
                    for key in ["result", "parsed"]:
                        if key in data and isinstance(data[key], dict):
                            nested = data[key]
                            if ("blackline_item_id" in nested or "matched_entry" in nested or 
                                "related_blackline_items" in nested or "related_items_mappings" in nested):
                                _logger.info(
                                    "get_case_item_foreign_book_mappings: Found wrapped result dict with nested result keys, wrapping in list"
                                )
                                return [data]
                # If dict is empty or has no list values, return empty list
                _logger.info(
                    "get_case_item_foreign_book_mappings: Could not extract list from dict. "
                    "Keys: {}, Sample values: {}", 
                    list(data.keys())[:5],
                    {k: str(v)[:100] for k, v in list(data.items())[:3]}
                )
            # If it's not a list or dict, try to wrap it
            if data is not None:
                _logger.info(
                    "get_case_item_foreign_book_mappings: Unexpected data type: {}. Value: {}", 
                    type(data).__name__,
                    str(data)[:200]
                )
            return []
        
        # Helper to extract parsed result from wrapped format
        def _extract_parsed(result: Any) -> Dict[str, Any]:
            """Extract parsed result from wrapped format or return as-is."""
            if isinstance(result, dict):
                if "parsed" in result:
                    return result["parsed"]
                elif "result" in result:
                    return result["result"]
            return result
        
        # Log the raw input for debugging
        _logger.info(
            "get_case_item_foreign_book_mappings: Raw inputs - "
            "item_discovery_results type: {}, keys: {}; "
            "related_items_discovery_results type: {}, keys: {}",
            type(item_discovery_results).__name__,
            list(item_discovery_results.keys())[:10] if isinstance(item_discovery_results, dict) else "N/A",
            type(related_items_discovery_results).__name__,
            list(related_items_discovery_results.keys())[:10] if isinstance(related_items_discovery_results, dict) else "N/A"
        )
        # Log string values in detail if they're strings
        if isinstance(item_discovery_results, str):
            _logger.info(
                "get_case_item_foreign_book_mappings: item_discovery_results is string, length: {}, "
                "first 1000 chars: {}", 
                len(item_discovery_results), item_discovery_results[:1000]
            )
        if isinstance(related_items_discovery_results, str):
            _logger.info(
                "get_case_item_foreign_book_mappings: related_items_discovery_results is string, length: {}, "
                "first 1000 chars: {}", 
                len(related_items_discovery_results), related_items_discovery_results[:1000]
            )
        
        # Extract lists from potentially wrapped formats
        item_discovery_list = _extract_list(item_discovery_results)
        related_items_list = _extract_list(related_items_discovery_results)
        
        _logger.info(
            "get_case_item_foreign_book_mappings: Extracted lists - "
            "item_discovery_list length: {}, related_items_list length: {}",
            len(item_discovery_list),
            len(related_items_list)
        )
        
        if not item_discovery_list:
            _logger.info(
                "get_case_item_foreign_book_mappings: item_discovery_results is empty or not a list. "
                "Received type: {}, value (first 500 chars): {}", 
                type(item_discovery_results).__name__, 
                str(item_discovery_results)[:500]
            )
        
        if not related_items_list:
            _logger.warning(
                "get_case_item_foreign_book_mappings: related_items_discovery_results is empty or not a list. "
                "Received type: {}, value (first 500 chars): {}. "
                "This may indicate the agent passed a single item instead of the full accumulated list.",
                type(related_items_discovery_results).__name__, 
                str(related_items_discovery_results)[:500]
            )
            # Try to extract as a single dict and wrap it if it looks like a result
            if isinstance(related_items_discovery_results, str):
                try:
                    parsed = json.loads(related_items_discovery_results)
                    if isinstance(parsed, dict) and ("related_blackline_items" in parsed or "related_items_mappings" in parsed):
                        related_items_list = [parsed]
                        _logger.info(
                            "get_case_item_foreign_book_mappings: Wrapped single dict result into list for processing"
                        )
                except (json.JSONDecodeError, ValueError):
                    pass
        
        # Build a lookup map for item_discovery results by blackline_item_id
        item_discovery_map = {}
        for item_result in item_discovery_list:
            parsed = _extract_parsed(item_result)
            if isinstance(parsed, dict) and "blackline_item_id" in parsed:
                item_id = parsed["blackline_item_id"]
                item_discovery_map[item_id] = parsed
        
        # Find the FIRST related_items_discovery result that has related_items_mappings
        related_items_mappings = {}
        for related_result in related_items_list:
            parsed = _extract_parsed(related_result)
            if isinstance(parsed, dict) and "related_items_mappings" in parsed:
                mappings_data = parsed["related_items_mappings"]
                if isinstance(mappings_data, dict) and mappings_data:
                    related_items_mappings = mappings_data
                    break  # Use the first non-empty mapping
        
        # Process each item in the case group
        for item_id in item_ids:
            # First, check item_discovery results
            item_discovery = item_discovery_map.get(item_id)
            if item_discovery and item_discovery.get("matched_entry") and item_discovery.get("foreign_book_type"):
                # Direct match from item_discovery
                mappings[item_id] = {
                    "foreign_book_type": item_discovery["foreign_book_type"],
                    "document_number": item_discovery.get("document_number"),
                    "source": "item_discovery"
                }
                items_with_mappings.append(item_id)
            elif item_id in related_items_mappings:
                # Fall back to related_items_mappings
                mapping_info = related_items_mappings[item_id]
                if isinstance(mapping_info, dict) and mapping_info.get("foreign_book_type") and mapping_info.get("document_number"):
                    mappings[item_id] = {
                        "foreign_book_type": mapping_info["foreign_book_type"],
                        "document_number": mapping_info["document_number"],
                        "source": "related_items_mapping"
                    }
                    items_with_mappings.append(item_id)
                else:
                    items_without_mappings.append(item_id)
            else:
                items_without_mappings.append(item_id)
        
        # If no items have mappings, return an error
        if not items_with_mappings:
            error_msg = (
                f"No items in the current case group have foreign book mappings "
                f"(no items mapped from item_discovery or related_items_discovery). "
                f"Processed {len(item_ids)} items, found {len(item_discovery_map)} item_discovery results, "
                f"{len(related_items_mappings)} related_items_mappings."
            )
            _logger.error("get_case_item_foreign_book_mappings: {}", error_msg)
            return {
                "mappings": {},
                "items_with_mappings": [],
                "items_without_mappings": item_ids,
                "error": error_msg
            }
        
        return {
            "mappings": mappings,
            "items_with_mappings": items_with_mappings,
            "items_without_mappings": items_without_mappings,
            "error": ""
        }
    
    except Exception as e:
        _logger.error("Error getting case item foreign book mappings: {}", e)
        return {
            "mappings": {},
            "items_with_mappings": [],
            "items_without_mappings": item_ids if item_ids else [],
            "error": str(e)
        }


@pipeline_tool(toolkit="reconvoy", name="get_reconvoy_processing_statistics")
def get_reconvoy_processing_statistics(
    db_file: str, run_id: str
) -> Dict[str, Any]:
    """Get processing statistics for a specific run.

    Counts items processed by route (StraightThrough vs HITL) from reconvoy_results table.

    Args:
        db_file: Absolute path to ReconVoy database file
        run_id: Processing run ID

    Returns:
        Dictionary with item counts by route and total processed items
    """
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()

        # Count items by route
        cursor.execute(
            """
            SELECT 
                route,
                COUNT(*) as item_count
            FROM reconvoy_results
            WHERE run_id = ?
            GROUP BY route
            """,
            (run_id,),
        )
        route_counts = {row["route"]: row["item_count"] for row in cursor.fetchall()}

        # Total processed items
        cursor.execute(
            """
            SELECT COUNT(*) as total_processed
            FROM reconvoy_results
            WHERE run_id = ?
            """,
            (run_id,),
        )
        total_row = cursor.fetchone()
        total_processed = total_row["total_processed"] if total_row else 0

        # Get counts by route
        straight_through_count = route_counts.get("StraightThrough", 0)
        hitl_count = route_counts.get("HITL", 0)

        conn.close()

        return {
            "total_processed_items": total_processed,
            "straight_through_items": straight_through_count,
            "hitl_items": hitl_count,
            "error": "",
        }

    except Exception as e:
        _logger.error("Error getting ReconVoy processing statistics: {}", e)
        return {
            "total_processed_items": 0,
            "straight_through_items": 0,
            "hitl_items": 0,
            "error": str(e),
        }


@pipeline_tool(toolkit="reconvoy", name="calculate_case_fx_variance")
def calculate_case_fx_variance(
    db_file: str,
    main_item_id: str,
    mappings: Dict[str, Any],
) -> Dict[str, Any]:
    """Deterministically calculate FX variance for a case using BlackLine data only.

    This tool is designed to be called by the case matcher agent AFTER
    `get_case_item_foreign_book_mappings` has been used to build the
    `mappings` dictionary for the current case group.

    It implements the business rule:
      - total_blackline_gbp = amount_local_gbp of the MAIN case item
      - total_matched_gbp   = sum of amount_local_gbp of OTHER BlackLine items
                              in the same case that have foreign book mappings
      - variance_gbp        = total_blackline_gbp - total_matched_gbp
      - variance_percent    = (variance_gbp / total_blackline_gbp) * 100

    Args:
        db_file: Absolute path to ReconVoy database file
        main_item_id: Item ID of the main BlackLine case item
        mappings: Dictionary from `get_case_item_foreign_book_mappings.mappings`
                  mapping item_id -> {foreign_book_type, document_number, source}

    Returns:
        Dictionary with deterministic variance calculation:
        {
            "main_item": {<BlackLine main item dict>},
            "matched_items": [<BlackLine matched item dicts>],
            "total_blackline_gbp": <float>,
            "total_matched_gbp": <float>,
            "variance_gbp": <float>,
            "variance_percent": <float>,
            "error": ""
        }
    """
    conn: Optional[sqlite3.Connection] = None
    try:
        if not mappings or not isinstance(mappings, dict):
            error_msg = (
                "calculate_case_fx_variance: No mappings provided or mappings is not a dict. "
                f"Got type={type(mappings).__name__}, value={str(mappings)[:200]}"
            )
            _logger.error(error_msg)
            return {
                "main_item": None,
                "matched_items": [],
                "total_blackline_gbp": 0.0,
                "total_matched_gbp": 0.0,
                "variance_gbp": 0.0,
                "variance_percent": 0.0,
                "error": error_msg,
            }

        conn = _connect(db_file)
        cursor = conn.cursor()

        # Fetch main item
        cursor.execute(
            """
            SELECT *
            FROM blackline_unmatched_items
            WHERE item_id = ?
            LIMIT 1
            """,
            (main_item_id,),
        )
        main_row = cursor.fetchone()
        if not main_row:
            error_msg = f"calculate_case_fx_variance: Main item {main_item_id} not found in blackline_unmatched_items"
            _logger.error(error_msg)
            conn.close()
            return {
                "main_item": None,
                "matched_items": [],
                "total_blackline_gbp": 0.0,
                "total_matched_gbp": 0.0,
                "variance_gbp": 0.0,
                "variance_percent": 0.0,
                "error": error_msg,
            }

        main_item = _row_to_dict(main_row)
        if "amount_local_gbp" not in main_item:
            error_msg = (
                f"calculate_case_fx_variance: Main item {main_item_id} missing amount_local_gbp "
                f"(keys={list(main_item.keys())})"
            )
            _logger.error(error_msg)
            conn.close()
            return {
                "main_item": main_item,
                "matched_items": [],
                "total_blackline_gbp": 0.0,
                "total_matched_gbp": 0.0,
                "variance_gbp": 0.0,
                "variance_percent": 0.0,
                "error": error_msg,
            }

        total_blackline_gbp = float(main_item.get("amount_local_gbp", 0.0))

        # Collect matched items (all mapped items except the main item)
        matched_items: List[Dict[str, Any]] = []
        total_matched_gbp = 0.0

        for item_id, mapping_info in mappings.items():
            if not isinstance(item_id, str):
                continue
            if item_id == main_item_id:
                # Main item is used only for total_blackline_gbp, not for total_matched_gbp
                continue

            cursor.execute(
                """
                SELECT *
                FROM blackline_unmatched_items
                WHERE item_id = ?
                LIMIT 1
                """,
                (item_id,),
            )
            row = cursor.fetchone()
            if not row:
                _logger.error(
                    "calculate_case_fx_variance: Mapped item_id {} not found in blackline_unmatched_items. "
                    "Mapping info: {}",
                    item_id,
                    str(mapping_info)[:200],
                )
                continue

            item_dict = _row_to_dict(row)
            if "amount_local_gbp" not in item_dict:
                _logger.error(
                    "calculate_case_fx_variance: Mapped item_id {} missing amount_local_gbp. Keys: {}",
                    item_id,
                    list(item_dict.keys()),
                )
                continue

            amount_gbp = float(item_dict.get("amount_local_gbp", 0.0))
            total_matched_gbp += amount_gbp
            matched_items.append(item_dict)

        conn.close()

        # Compute variance (protect against divide-by-zero)
        variance_gbp = total_blackline_gbp - total_matched_gbp
        if total_blackline_gbp != 0:
            variance_percent = (variance_gbp / total_blackline_gbp) * 100.0
        else:
            variance_percent = 0.0

        _logger.info(
            "calculate_case_fx_variance: main_item_id={}, total_blackline_gbp={}, "
            "total_matched_gbp={}, variance_gbp={}, variance_percent={}, matched_items={}",
            main_item_id,
            total_blackline_gbp,
            total_matched_gbp,
            variance_gbp,
            variance_percent,
            [m.get("item_id") for m in matched_items],
        )

        return {
            "main_item": main_item,
            "matched_items": matched_items,
            "total_blackline_gbp": total_blackline_gbp,
            "total_matched_gbp": total_matched_gbp,
            "variance_gbp": variance_gbp,
            "variance_percent": variance_percent,
            "error": "",
        }

    except Exception as e:
        _logger.error("Error in calculate_case_fx_variance: {}", e)
        if conn:
            conn.close()
        return {
            "main_item": None,
            "matched_items": [],
            "total_blackline_gbp": 0.0,
            "total_matched_gbp": 0.0,
            "variance_gbp": 0.0,
            "variance_percent": 0.0,
            "error": str(e),
        }
