"""
Argus - Pipeline-specific local tools.

Goal:
- Agents should NOT directly use sqlite_query/sqlite_execute or python_execute.
- LLM can generate ideas/text, but all DB reads/writes and deterministic computation must go through these tools.

This toolkit is intentionally opinionated and schema-aware for the Argus database created by:
  src/topaz_agent_kit/scripts/setup_argus_database.py
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from topaz_agent_kit.local_tools.registry import pipeline_tool
from topaz_agent_kit.utils.logger import Logger

_logger = Logger("ArgusTools")


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


# ---------------------------------------------------------------------
# Database Query Tools
# ---------------------------------------------------------------------

@pipeline_tool(toolkit="argus", name="get_pending_journals")
def get_pending_journals(
    db_file: str,
    project_dir: str
) -> Dict[str, Any]:
    """Get all pending journal entries grouped by transaction_id (debit/credit pairs).
    
    Only returns entries where run_id IS NULL, excluding entries that were already
    processed in previous pipeline runs (even if they still have status='pending').
    
    Args:
        db_file: Absolute path to the database file
        project_dir: Absolute path to project root directory
    
    Returns:
        Dictionary with pending_journals list (one entry per transaction, using debit entry),
        total_count, and run_id
    """
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()
        
        # Query pending journal entries, grouped by transaction_id
        # Return one entry per transaction (using the debit entry as representative)
        # Join with credit entry to get credit GL account, assignment, and business_area
        # Only select entries where run_id IS NULL to exclude entries from previous pipeline runs
        cursor.execute("""
            SELECT DISTINCT
                debit.transaction_id,
                debit.journal_id,
                debit.company_code,
                debit.gl_account,
                debit.amount,
                debit.posting_date,
                debit.document_date,
                debit.header_text,
                debit.status,
                debit.business_area,
                debit.assignment,
                credit.gl_account AS credit_gl_account,
                credit.business_area AS credit_business_area,
                credit.assignment AS credit_assignment
            FROM journal_entries debit
            LEFT JOIN journal_entries credit 
                ON debit.transaction_id = credit.transaction_id 
                AND credit.posting_key = '50'  -- Credit entries
            WHERE debit.status = 'pending'
            AND debit.posting_key = '40'  -- Debit entries only (one per transaction)
            AND debit.run_id IS NULL  -- Only pick up entries not yet processed in any pipeline run
            -- Exclude entries that are waiting for human review (they have status != 'pending' or run_id IS NOT NULL)
            -- Entries waiting for review have status: 'needs_clarification', 'processed', or 'rejected' (not 'pending')
            ORDER BY debit.posting_date ASC, debit.transaction_id ASC
        """)
        
        journals = []
        for row in cursor.fetchall():
            journal = {
                "transaction_id": row["transaction_id"],
                "journal_id": row["journal_id"],
                "company_code": row["company_code"],
                "gl_account": row["gl_account"],
                "amount": float(row["amount"]),
                "posting_date": row["posting_date"],
                "document_date": row["document_date"] if row["document_date"] else None,
                "header_text": row["header_text"] if row["header_text"] else None,
                "status": row["status"],
                "business_area": row["business_area"] if row["business_area"] else None,
                "assignment": row["assignment"] if row["assignment"] else None,
                "credit_gl_account": row["credit_gl_account"] if row["credit_gl_account"] else None,
                "credit_business_area": row["credit_business_area"] if row["credit_business_area"] else None,
                "credit_assignment": row["credit_assignment"] if row["credit_assignment"] else None
            }
            journals.append(journal)
            
            # Log first journal entry to verify fields are populated
            if len(journals) == 1:
                _logger.info(
                    "Sample journal entry from get_pending_journals - keys: {}, "
                    "business_area: {}, assignment: {}, credit_gl_account: {}",
                    list(journal.keys()),
                    journal.get("business_area"),
                    journal.get("assignment"),
                    journal.get("credit_gl_account")
                )
        
        # Generate run_id for this processing run
        run_id = f"run-{_utc_iso()}"
        
        # CRITICAL: Update run_id on entries BEFORE returning them
        # This ensures entries waiting for async HITL are not picked up again in future runs
        # even if save_processing_results hasn't been called yet (async HITL creates checkpoints
        # and continues processing, so save_processing_results only runs after HITL decision)
        if journals:
            transaction_ids = [j["transaction_id"] for j in journals]
            placeholders = ','.join(['?' for _ in transaction_ids])
            cursor.execute(f"""
                UPDATE journal_entries
                SET run_id = ?
                WHERE transaction_id IN ({placeholders})
                AND status = 'pending'
                AND run_id IS NULL
            """, [run_id] + transaction_ids)
            conn.commit()
            _logger.info(
                "Updated run_id={} for {} pending journal entries (transactions: {})",
                run_id, len(journals), len(transaction_ids)
            )
        
        conn.close()
        
        return {
            "pending_journals": journals,
            "total_count": len(journals),
            "run_id": run_id,
            "error": ""
        }
    
    except Exception as e:
        _logger.error("Error getting pending journals: {}", e)
        return {
            "pending_journals": [],
            "total_count": 0,
            "run_id": "",
            "error": str(e)
        }


@pipeline_tool(toolkit="argus", name="get_account_classification")
def get_account_classification(
    gl_account: str,
    company_code: str,
    db_file: str
) -> Dict[str, Any]:
    """Get account classification for a GL account.
    
    Args:
        gl_account: GL account code
        company_code: Company code
        db_file: Absolute path to the database file
    
    Returns:
        Dictionary with account_type, posting_rules, normal_balance, description, and error
    """
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT gl_account, account_name, account_type, company_code, business_area, posting_rules
            FROM account_classifications
            WHERE gl_account = ? AND company_code = ?
        """, (gl_account, company_code))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {
                "gl_account": gl_account,
                "account_name": None,
                "account_type": None,
                "company_code": company_code,
                "business_area": None,
                "posting_rules": None,
                "normal_balance": None,
                "error": f"Account classification not found for GL Account {gl_account} in company {company_code}"
            }
        
        # Determine normal balance from account type
        account_type = row["account_type"].lower() if row["account_type"] else ""
        normal_balance = None
        if "asset" in account_type or "expense" in account_type:
            normal_balance = "debit"
        elif "liability" in account_type or "equity" in account_type or "revenue" in account_type:
            normal_balance = "credit"
        
        return {
            "gl_account": row["gl_account"],
            "account_name": row["account_name"],
            "account_type": row["account_type"],
            "company_code": row["company_code"],
            "business_area": row["business_area"],
            "posting_rules": row["posting_rules"],
            "normal_balance": normal_balance,
            "error": ""
        }
    
    except Exception as e:
        _logger.error("Error getting account classification: {}", e)
        return {
            "gl_account": gl_account,
            "account_name": None,
            "account_type": None,
            "company_code": company_code,
            "business_area": None,
            "posting_rules": None,
            "normal_balance": None,
            "error": str(e)
        }


@pipeline_tool(toolkit="argus", name="find_accounts_by_type")
def find_accounts_by_type(
    company_code: str,
    db_file: str,
    account_type: Optional[str] = None,
    account_name_pattern: Optional[str] = None
) -> Dict[str, Any]:
    """Find accounts by type or name pattern.
    
    Args:
        company_code: Company code
        account_type: Account type to search for (e.g., "REVENUE", "CAPITAL", "ROU_ASSET")
        account_name_pattern: Pattern to match in account name (e.g., "%Repairs%", "%Damages%")
        db_file: Absolute path to the database file
    
    Returns:
        Dictionary with accounts list and error
    """
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()
        
        # Build query based on provided filters
        query = "SELECT gl_account, account_name, account_type, company_code, posting_rules FROM account_classifications WHERE company_code = ?"
        params = [company_code]
        
        if account_type:
            query += " AND account_type = ?"
            params.append(account_type)
        
        if account_name_pattern:
            query += " AND account_name LIKE ?"
            params.append(account_name_pattern)
        
        query += " ORDER BY account_name ASC"
        
        cursor.execute(query, params)
        
        accounts = []
        for row in cursor.fetchall():
            accounts.append({
                "gl_account": row["gl_account"],
                "account_name": row["account_name"],
                "account_type": row["account_type"],
                "company_code": row["company_code"],
                "posting_rules": row["posting_rules"]
            })
        
        conn.close()
        
        return {
            "accounts": accounts,
            "count": len(accounts),
            "error": ""
        }
    
    except Exception as e:
        _logger.error("Error finding accounts: {}", e)
        return {
            "accounts": [],
            "count": 0,
            "error": str(e)
        }


@pipeline_tool(toolkit="argus", name="get_historical_patterns")
def get_historical_patterns(
    company_code: str,
    gl_account: str,
    description: Optional[str],
    db_file: str
) -> Dict[str, Any]:
    """Get historical patterns for anomaly detection.
    
    Args:
        company_code: Company code
        gl_account: GL account code
        description: Header text or description (optional, for keyword matching)
        db_file: Absolute path to the database file
    
    Returns:
        Dictionary with pattern data (avg_amount, frequency, typical descriptions) and error
    """
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()
        
        # Query historical patterns matching company_code and gl_account
        cursor.execute("""
            SELECT pattern_id, company_code, gl_account, business_area,
                   description_keywords, avg_amount, frequency_per_month,
                   last_posting_date, sample_count
            FROM historical_journal_patterns
            WHERE company_code = ? AND gl_account = ?
            ORDER BY sample_count DESC
            LIMIT 1
        """, (company_code, gl_account))
        
        row = cursor.fetchone()
        
        if not row:
            # If no pattern found, try to derive from historical journal entries
            cursor.execute("""
                SELECT 
                    AVG(amount) as avg_amount,
                    COUNT(*) as sample_count,
                    MAX(posting_date) as last_posting_date
                FROM journal_entries
                WHERE company_code = ? AND gl_account = ? AND status = 'processed'
            """, (company_code, gl_account))
            
            hist_row = cursor.fetchone()
            conn.close()
            
            if hist_row and hist_row["sample_count"] and hist_row["sample_count"] > 0:
                return {
                    "company_code": company_code,
                    "gl_account": gl_account,
                    "avg_amount": float(hist_row["avg_amount"]) if hist_row["avg_amount"] else 0.0,
                    "frequency_per_month": 0.0,  # Cannot calculate without date range
                    "last_posting_date": hist_row["last_posting_date"],
                    "sample_count": int(hist_row["sample_count"]),
                    "typical_descriptions": [],
                    "error": ""
                }
            else:
                return {
                    "company_code": company_code,
                    "gl_account": gl_account,
                    "avg_amount": 0.0,
                    "frequency_per_month": 0.0,
                    "last_posting_date": None,
                    "sample_count": 0,
                    "typical_descriptions": [],
                    "error": f"No historical patterns found for GL Account {gl_account} in company {company_code}"
                }
        
        # Parse description_keywords if stored as JSON
        typical_descriptions = []
        if row["description_keywords"]:
            try:
                typical_descriptions = json.loads(row["description_keywords"])
            except (json.JSONDecodeError, TypeError):
                # If not JSON, treat as comma-separated
                typical_descriptions = [kw.strip() for kw in row["description_keywords"].split(",") if kw.strip()]
        
        conn.close()
        
        return {
            "company_code": row["company_code"],
            "gl_account": row["gl_account"],
            "avg_amount": float(row["avg_amount"]) if row["avg_amount"] else 0.0,
            "frequency_per_month": float(row["frequency_per_month"]) if row["frequency_per_month"] else 0.0,
            "last_posting_date": row["last_posting_date"],
            "sample_count": int(row["sample_count"]) if row["sample_count"] else 0,
            "typical_descriptions": typical_descriptions,
            "error": ""
        }
    
    except Exception as e:
        _logger.error("Error getting historical patterns: {}", e)
        return {
            "company_code": company_code,
            "gl_account": gl_account,
            "avg_amount": 0.0,
            "frequency_per_month": 0.0,
            "last_posting_date": None,
            "sample_count": 0,
            "typical_descriptions": [],
            "error": str(e)
        }


@pipeline_tool(toolkit="argus", name="validate_account_usage")
def validate_account_usage(
    gl_account: str,
    description: Optional[str],
    amount: float,
    company_code: str,
    db_file: str
) -> Dict[str, Any]:
    """Validate if account usage is appropriate based on description and amount.
    
    Args:
        gl_account: GL account code
        description: Header text or description
        amount: Transaction amount
        company_code: Company code
        db_file: Absolute path to the database file
    
    Returns:
        Dictionary with is_valid, validation_reasoning, suggested_account (if invalid), and error
    """
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()
        
        # Get account classification
        cursor.execute("""
            SELECT account_name, account_type, posting_rules
            FROM account_classifications
            WHERE gl_account = ? AND company_code = ?
        """, (gl_account, company_code))
        
        account_row = cursor.fetchone()
        
        if not account_row:
            conn.close()
            return {
                "is_valid": False,
                "validation_reasoning": f"Account classification not found for GL Account {gl_account}",
                "suggested_account": None,
                "error": f"Account classification not found for GL Account {gl_account} in company {company_code}"
            }
        
        account_type = account_row["account_type"].lower() if account_row["account_type"] else ""
        account_name = account_row["account_name"] if account_row["account_name"] else ""
        posting_rules = account_row["posting_rules"] if account_row["posting_rules"] else ""
        
        # Basic validation logic
        is_valid = True
        validation_reasoning = ""
        suggested_account = None
        
        description_lower = (description or "").lower()
        
        # Parse posting_rules if available (JSON format)
        exclude_keywords = []
        try:
            if posting_rules:
                rules_dict = json.loads(posting_rules)
                exclude_keywords = rules_dict.get("exclude_keywords", [])
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass
        
        # Check for Capital/Revenue misclassification (Scenario 1)
        # Capital accounts should not be used for maintenance/repair transactions
        if "capital" in account_type:
            # Check for maintenance/repair keywords that indicate revenue/expense transactions
            maintenance_keywords = ["repairs", "maintenance", "consumables", "running", "lubricants", "filters", "equipment", "machinery", "compressor", "pump", "generator", "belts", "oil"]
            if any(keyword in description_lower for keyword in maintenance_keywords):
                is_valid = False
                validation_reasoning = f"GL Account {gl_account} ({account_name}) is a capital account but is being used for a maintenance/repair transaction. Capital accounts should not be used for revenue/expense transactions. Description: {description}"
                # Try to find a revenue/repairs account
                cursor.execute("""
                    SELECT gl_account, account_name
                    FROM account_classifications
                    WHERE company_code = ? AND (account_type LIKE '%revenue%' OR account_name LIKE '%Repairs%' OR account_name LIKE '%Maintenance%')
                    LIMIT 1
                """, (company_code,))
                rev_row = cursor.fetchone()
                if rev_row:
                    suggested_account = rev_row["gl_account"]
        
        # Check for Lease/ROU misclassification (Scenario 2)
        # ROU_ASSET accounts should not be used for damages/repairs/excess usage
        if "rou_asset" in account_type or ("rou" in account_type and "asset" in account_type):
            # Check for lease damage/repair keywords
            damage_keywords = ["repairs", "damages", "excess usage", "excess hours", "lease damages", "lease equipment damages", "damages to leased", "repairs to leased"]
            if any(keyword in description_lower for keyword in damage_keywords):
                is_valid = False
                validation_reasoning = f"GL Account {gl_account} ({account_name}) is an ROU Asset account but is being used for lease damages/repairs. ROU Asset accounts should not be used for extraordinary expenses like damages or excess usage. Description: {description}"
                # Try to find a repairs/damages expense account
                cursor.execute("""
                    SELECT gl_account, account_name
                    FROM account_classifications
                    WHERE company_code = ? AND (account_name LIKE '%Repairs%' OR account_name LIKE '%Damages%' OR account_name LIKE '%Expense%')
                    LIMIT 1
                """, (company_code,))
                exp_row = cursor.fetchone()
                if exp_row:
                    suggested_account = exp_row["gl_account"]
        
        # Check posting_rules exclude_keywords if available
        if exclude_keywords and any(keyword.lower() in description_lower for keyword in exclude_keywords):
            is_valid = False
            matching_keywords = [kw for kw in exclude_keywords if kw.lower() in description_lower]
            validation_reasoning = f"GL Account {gl_account} ({account_name}) posting rules exclude keywords: {', '.join(matching_keywords)}. Description contains excluded keywords: {description}"
            # Try to find an appropriate account based on account type
            if "capital" in account_type:
                cursor.execute("""
                    SELECT gl_account, account_name
                    FROM account_classifications
                    WHERE company_code = ? AND account_type LIKE '%revenue%'
                    LIMIT 1
                """, (company_code,))
            elif "rou_asset" in account_type or ("rou" in account_type and "asset" in account_type):
                cursor.execute("""
                    SELECT gl_account, account_name
                    FROM account_classifications
                    WHERE company_code = ? AND (account_name LIKE '%Repairs%' OR account_name LIKE '%Damages%')
                    LIMIT 1
                """, (company_code,))
            else:
                cursor.execute("""
                    SELECT gl_account, account_name
                    FROM account_classifications
                    WHERE company_code = ? AND account_type NOT LIKE ?
                    LIMIT 1
                """, (company_code, account_type))
            
            alt_row = cursor.fetchone()
            if alt_row:
                suggested_account = alt_row["gl_account"]
        
        if is_valid:
            validation_reasoning = f"Account usage appears valid. GL Account {gl_account} ({account_name}) is appropriate for this transaction type."
        
        conn.close()
        
        return {
            "is_valid": is_valid,
            "validation_reasoning": validation_reasoning,
            "suggested_account": suggested_account,
            "error": ""
        }
    
    except Exception as e:
        _logger.error("Error validating account usage: {}", e)
        return {
            "is_valid": False,
            "validation_reasoning": f"Error during validation: {str(e)}",
            "suggested_account": None,
            "error": str(e)
        }


# ---------------------------------------------------------------------
# Database Write Tools
# ---------------------------------------------------------------------

@pipeline_tool(toolkit="argus", name="apply_correction")
def apply_correction(
    db_file: str,
    transaction_id: str,
    corrected_entry: Dict[str, Any],
    run_id: Optional[str] = None
) -> Dict[str, Any]:
    """Apply correction to journal entries by marking originals as superseded and creating corrected entries.
    
    This tool:
    1. Marks original debit and credit entries as 'superseded'
    2. Creates new corrected debit and credit entries with status 'processed'
    3. Links corrected entries to originals via original_journal_id
    
    Args:
        db_file: Absolute path to the database file
        transaction_id: Transaction ID of the original entries to correct
        corrected_entry: Corrected entry structure from correction_suggestions
            Must contain: transaction_id, debit_entry (with gl_account), credit_entry (with gl_account),
            and all other fields (company_code, posting_date, document_date, header_text, reference, etc.)
        run_id: Processing run ID (optional)
    
    Returns:
        Dictionary with:
        - applied: boolean indicating success
        - original_journal_ids: list of original journal IDs (debit, credit)
        - corrected_journal_ids: list of corrected journal IDs (debit, credit)
        - corrected_transaction_id: new transaction ID for corrected entries
        - error: error message if failed
    """
    conn = None
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()
        current_time = _utc_iso()
        
        # 1. Get original entries
        # First check if transaction exists at all (any status)
        cursor.execute("""
            SELECT COUNT(*) as count, status
            FROM journal_entries
            WHERE transaction_id = ?
            GROUP BY status
        """, (transaction_id,))
        status_counts = cursor.fetchall()
        
        if not status_counts:
            return {
                "applied": False,
                "original_journal_ids": [],
                "corrected_journal_ids": [],
                "corrected_transaction_id": None,
                "error": f"Transaction {transaction_id} not found in database. This may indicate the database was reset or the transaction_id is incorrect."
            }
        
        # Check status breakdown for better error message
        status_info = {row["status"]: row["count"] for row in status_counts}
        pending_count = status_info.get("pending", 0)
        superseded_count = status_info.get("superseded", 0)
        processed_count = status_info.get("processed", 0)
        
        # IDEMPOTENCY: If entries are already superseded, check if corrected entries exist
        if pending_count == 0 and superseded_count >= 2:
            # Check if corrected entries already exist (same transaction_id, linked via original_journal_id)
            cursor.execute("""
                SELECT journal_id, transaction_id, original_journal_id, status
                FROM journal_entries
                WHERE transaction_id = ? 
                  AND original_journal_id IN (
                      SELECT journal_id FROM journal_entries 
                      WHERE transaction_id = ? AND status = 'superseded' AND original_journal_id IS NULL
                  )
                ORDER BY posting_key
            """, (transaction_id, transaction_id))
            
            corrected_entries = cursor.fetchall()
            
            if len(corrected_entries) >= 2:
                # Correction was already applied - return success with existing data
                original_journal_ids = []
                corrected_journal_ids = []
                corrected_transaction_id = None
                
                # Get original journal IDs (filter by original_journal_id IS NULL to exclude corrected entries)
                cursor.execute("""
                    SELECT journal_id FROM journal_entries
                    WHERE transaction_id = ? AND status = 'superseded' AND original_journal_id IS NULL
                    ORDER BY posting_key
                """, (transaction_id,))
                original_rows = cursor.fetchall()
                original_journal_ids = [row["journal_id"] for row in original_rows]
                
                # Get corrected journal IDs and transaction ID
                if corrected_entries:
                    corrected_transaction_id = corrected_entries[0]["transaction_id"]
                    corrected_journal_ids = [row["journal_id"] for row in corrected_entries]
                
                _logger.info(
                    "Correction already applied for transaction {} - returning existing correction data",
                    transaction_id
                )
                return {
                    "applied": True,
                    "original_journal_ids": original_journal_ids,
                    "corrected_journal_ids": corrected_journal_ids,
                    "corrected_transaction_id": corrected_transaction_id,
                    "error": "",
                    "already_applied": True  # Flag to indicate this was already applied
                }
        
        if pending_count == 0:
            status_details = ", ".join([f"{status}: {count}" for status, count in status_info.items()])
            return {
                "applied": False,
                "original_journal_ids": [],
                "corrected_journal_ids": [],
                "corrected_transaction_id": None,
                "error": f"Transaction {transaction_id} has no entries with status='pending'. Found: {status_details}. Entries may have been processed already or have a different status."
            }
        
        # Now get the pending entries
        cursor.execute("""
            SELECT journal_id, posting_key, gl_account, company_code, business_area,
                   assignment, document_type, document_date, posting_date, reference,
                   header_text, document_currency, amount, local_currency, amount_local,
                   tax_code, profit_center, cost_center, clearing_doc_no, clearing_date,
                   plant, "order", wbs_element, status, scenario_type, anomaly_type
            FROM journal_entries
            WHERE transaction_id = ? AND status = 'pending'
            ORDER BY posting_key
        """, (transaction_id,))
        
        original_entries = cursor.fetchall()
        if len(original_entries) != 2:
            return {
                "applied": False,
                "original_journal_ids": [],
                "corrected_journal_ids": [],
                "corrected_transaction_id": None,
                "error": f"Expected 2 entries (debit/credit) for transaction {transaction_id} with status='pending', found {len(original_entries)}. Status breakdown: {status_info}"
            }
        
        original_debit = dict(original_entries[0]) if original_entries[0]["posting_key"] == "40" else dict(original_entries[1])
        original_credit = dict(original_entries[1]) if original_entries[0]["posting_key"] == "40" else dict(original_entries[0])
        original_debit_journal_id = original_debit["journal_id"]
        original_credit_journal_id = original_credit["journal_id"]
        
        # 2. Mark original entries as superseded
        cursor.execute("""
            UPDATE journal_entries
            SET status = 'superseded',
                processed_at = ?
            WHERE transaction_id = ? AND status = 'pending'
        """, (current_time, transaction_id))
        
        # 3. Use the same transaction_id for corrected entries (they're part of the same transaction)
        corrected_transaction_id = transaction_id
        
        # 4. Create corrected debit entry
        corrected_debit_journal_id = str(uuid4())
        corrected_debit = corrected_entry.get("debit_entry", {})
        
        cursor.execute("""
            INSERT INTO journal_entries (
                journal_id, transaction_id, company_code, gl_account, business_area,
                assignment, document_type, document_date, posting_date, reference,
                header_text, posting_key, document_currency, amount, local_currency,
                amount_local, tax_code, profit_center, cost_center, clearing_doc_no,
                clearing_date, plant, "order", wbs_element, status, original_journal_id,
                created_at, processed_at, run_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            corrected_debit_journal_id,
            corrected_transaction_id,
            corrected_entry.get("company_code") or original_debit["company_code"],
            corrected_debit.get("gl_account") or original_debit["gl_account"],
            corrected_entry.get("business_area") or original_debit.get("business_area"),
            original_debit.get("assignment"),
            original_debit.get("document_type"),
            corrected_entry.get("document_date") or original_debit.get("document_date"),
            corrected_entry.get("posting_date") or original_debit["posting_date"],
            corrected_entry.get("reference") or original_debit.get("reference"),
            corrected_entry.get("header_text") or original_debit.get("header_text"),
            "40",  # Debit posting key
            corrected_entry.get("document_currency") or original_debit.get("document_currency", "GBP"),
            corrected_entry.get("amount") or original_debit["amount"],
            corrected_entry.get("local_currency") or original_debit.get("local_currency", "GBP"),
            corrected_entry.get("amount_local") or original_debit["amount_local"],
            corrected_debit.get("tax_code") or original_debit.get("tax_code"),
            corrected_debit.get("profit_center") or original_debit.get("profit_center"),
            corrected_debit.get("cost_center") or original_debit.get("cost_center"),
            original_debit.get("clearing_doc_no"),
            original_debit.get("clearing_date"),
            corrected_debit.get("plant") or original_debit.get("plant"),
            corrected_debit.get("order") or original_debit.get("order"),
            corrected_debit.get("wbs_element") or original_debit.get("wbs_element"),
            "processed",  # Status
            original_debit_journal_id,  # Link to original
            current_time,
            current_time,  # processed_at
            run_id
        ))
        
        # 5. Create corrected credit entry
        corrected_credit_journal_id = str(uuid4())
        corrected_credit = corrected_entry.get("credit_entry", {})
        
        cursor.execute("""
            INSERT INTO journal_entries (
                journal_id, transaction_id, company_code, gl_account, business_area,
                assignment, document_type, document_date, posting_date, reference,
                header_text, posting_key, document_currency, amount, local_currency,
                amount_local, tax_code, profit_center, cost_center, clearing_doc_no,
                clearing_date, plant, "order", wbs_element, status, original_journal_id,
                created_at, processed_at, run_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            corrected_credit_journal_id,
            corrected_transaction_id,
            corrected_entry.get("company_code") or original_credit["company_code"],
            corrected_credit.get("gl_account") or original_credit["gl_account"],  # Credit GL account typically unchanged
            corrected_entry.get("business_area") or original_credit.get("business_area"),
            original_credit.get("assignment"),
            original_credit.get("document_type"),
            corrected_entry.get("document_date") or original_credit.get("document_date"),
            corrected_entry.get("posting_date") or original_credit["posting_date"],
            corrected_entry.get("reference") or original_credit.get("reference"),
            corrected_entry.get("header_text") or original_credit.get("header_text"),
            "50",  # Credit posting key
            corrected_entry.get("document_currency") or original_credit.get("document_currency", "GBP"),
            corrected_entry.get("amount") or original_credit["amount"],
            corrected_entry.get("local_currency") or original_credit.get("local_currency", "GBP"),
            corrected_entry.get("amount_local") or original_credit["amount_local"],
            corrected_credit.get("tax_code") or original_credit.get("tax_code"),
            corrected_credit.get("profit_center") or original_credit.get("profit_center"),
            corrected_credit.get("cost_center") or original_credit.get("cost_center"),  # Often None for credit
            original_credit.get("clearing_doc_no"),
            original_credit.get("clearing_date"),
            corrected_credit.get("plant") or original_credit.get("plant"),  # Often None for credit
            corrected_credit.get("order") or original_credit.get("order"),  # Often None for credit
            corrected_credit.get("wbs_element") or original_credit.get("wbs_element"),  # Often None for credit
            "processed",  # Status
            original_credit_journal_id,  # Link to original
            current_time,
            current_time,  # processed_at
            run_id
        ))
        
        conn.commit()
        conn.close()
        
        return {
            "applied": True,
            "original_journal_ids": [original_debit_journal_id, original_credit_journal_id],
            "corrected_journal_ids": [corrected_debit_journal_id, corrected_credit_journal_id],
            "corrected_transaction_id": corrected_transaction_id,
            "error": ""
        }
    
    except Exception as e:
        _logger.error("Error applying correction: {}", e)
        if conn:
            conn.rollback()
            conn.close()
        return {
            "applied": False,
            "original_journal_ids": [],
            "corrected_journal_ids": [],
            "corrected_transaction_id": None,
            "error": str(e)
        }


@pipeline_tool(toolkit="argus", name="verify_correction")
def verify_correction(
    db_file: str,
    transaction_id: str
) -> Dict[str, Any]:
    """Verify if a correction was properly applied to a transaction.
    
    This tool validates that:
    1. Original entries were marked as 'superseded'
    2. Corrected entries were created with status 'processed'
    3. Corrected entries are linked to originals via original_journal_id
    4. GL accounts were actually corrected (if applicable)
    
    Args:
        db_file: Absolute path to the database file
        transaction_id: Transaction ID of the original entries to verify
    
    Returns:
        Dictionary with:
        - verified: boolean indicating if verification passed
        - verification_status: "verified", "partially_verified", "failed", or "not_found"
        - original_entries: list of original entry details
        - corrected_entries: list of corrected entry details
        - gl_account_corrected: dict showing GL account changes (if any)
        - issues: list of issues found during verification
        - error: error message if verification failed
    """
    conn = None
    try:
        conn = _connect(db_file)
        cursor = conn.cursor()
        
        result = {
            "verified": False,
            "verification_status": "unknown",
            "original_entries": [],
            "corrected_entries": [],
            "gl_account_corrected": {},
            "issues": [],
            "error": ""
        }
        
        # 1. Get all entries for this transaction_id (both original and corrected)
        # Original entries: transaction_id = X, original_journal_id IS NULL
        # Corrected entries: transaction_id = X, original_journal_id IS NOT NULL (linked to originals)
        cursor.execute("""
            SELECT journal_id, transaction_id, gl_account, posting_key,
                   status, original_journal_id, processed_at, created_at
            FROM journal_entries
            WHERE transaction_id = ?
            ORDER BY posting_key, created_at
        """, (transaction_id,))
        
        entries = cursor.fetchall()
        
        if not entries:
            result["verification_status"] = "not_found"
            result["error"] = f"Transaction {transaction_id} not found in database"
            conn.close()
            return result
        
        # Separate original and corrected entries
        for entry in entries:
            entry_dict = dict(entry)
            if entry_dict["original_journal_id"] is None:
                # This is an original entry
                result["original_entries"].append(entry_dict)
            else:
                # This is a corrected entry (linked via original_journal_id)
                result["corrected_entries"].append(entry_dict)
        
        # 2. Verify original entries status
        original_superseded = all(
            entry["status"] == "superseded" 
            for entry in result["original_entries"]
        )
        
        if not original_superseded:
            statuses = [e["status"] for e in result["original_entries"]]
            result["issues"].append(
                f"Original entries not marked as 'superseded'. Statuses: {statuses}"
            )
        
        # 3. Check if corrected entries exist
        if not result["corrected_entries"]:
            result["issues"].append("No corrected entries found. Correction may not have been applied.")
            result["verification_status"] = "correction_not_applied"
            conn.close()
            return result
        
        # 4. Verify corrected entries status
        corrected_processed = all(
            entry["status"] == "processed"
            for entry in result["corrected_entries"]
        )
        
        if not corrected_processed:
            statuses = [e["status"] for e in result["corrected_entries"]]
            result["issues"].append(
                f"Corrected entries not marked as 'processed'. Statuses: {statuses}"
            )
        
        # 5. Verify linking via original_journal_id
        if len(result["original_entries"]) == 2 and len(result["corrected_entries"]) == 2:
            original_ids = {e["journal_id"] for e in result["original_entries"]}
            corrected_original_ids = {e["original_journal_id"] for e in result["corrected_entries"]}
            
            if original_ids != corrected_original_ids:
                result["issues"].append(
                    f"Corrected entries not properly linked. "
                    f"Original IDs: {original_ids}, Corrected original_journal_ids: {corrected_original_ids}"
                )
        
        # 6. Check if GL accounts were actually changed
        if len(result["original_entries"]) == 2 and len(result["corrected_entries"]) == 2:
            # Find corresponding entries by posting_key
            original_debit = next((e for e in result["original_entries"] if e["posting_key"] == "40"), None)
            original_credit = next((e for e in result["original_entries"] if e["posting_key"] == "50"), None)
            corrected_debit = next((e for e in result["corrected_entries"] if e["posting_key"] == "40"), None)
            corrected_credit = next((e for e in result["corrected_entries"] if e["posting_key"] == "50"), None)
            
            if original_debit and corrected_debit:
                if original_debit["gl_account"] == corrected_debit["gl_account"]:
                    result["issues"].append(
                        f"Debit GL account not changed: {original_debit['gl_account']}"
                    )
                else:
                    result["gl_account_corrected"]["debit"] = {
                        "original": original_debit["gl_account"],
                        "corrected": corrected_debit["gl_account"]
                    }
            
            if original_credit and corrected_credit:
                if original_credit["gl_account"] != corrected_credit["gl_account"]:
                    result["gl_account_corrected"]["credit"] = {
                        "original": original_credit["gl_account"],
                        "corrected": corrected_credit["gl_account"]
                    }
        
        # Determine overall verification status
        if not result["issues"]:
            result["verified"] = True
            result["verification_status"] = "verified"
        elif original_superseded and result["corrected_entries"]:
            result["verified"] = True  # Partially verified - correction was applied but with minor issues
            result["verification_status"] = "partially_verified"
        else:
            result["verification_status"] = "failed"
        
        conn.close()
        return result
    
    except Exception as e:
        _logger.error("Error verifying correction: {}", e)
        if conn:
            conn.close()
        return {
            "verified": False,
            "verification_status": "error",
            "original_entries": [],
            "corrected_entries": [],
            "gl_account_corrected": {},
            "issues": [],
            "error": str(e)
        }


@pipeline_tool(toolkit="argus", name="save_processing_results")
def save_processing_results(
    db_file: str,
    journal_id: str,
    transaction_id: str,
    status: str,
    processing_status: str,
    final_decision: str,
    decision_rationale: str,
    straight_through_eligible: bool,
    requires_human_review: bool,
    run_id: Optional[str] = None,
    anomaly_detection_results: Optional[Dict[str, Any]] = None,
    correction_suggestions: Optional[Dict[str, Any]] = None,
    hitl_decision: Optional[str] = None,
    hitl_response_data: Optional[Dict[str, Any]] = None,
    extracted_entry: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Save journal entry processing results to database.
    
    This tool handles all database writes for journal entry processing:
    - Updates journal_entries table (status)
    - Inserts into anomaly_detection_results table
    - Inserts into correction_suggestions table
    - Inserts into validation_results table
    
    Args:
        db_file: Absolute path to the database file
        journal_id: Journal ID (from debit entry)
        transaction_id: Transaction ID
        status: Journal entry status (processed, rejected, needs_clarification)
        processing_status: Processing status (completed, in_review, etc.)
        final_decision: Final decision (approve, reject, modify_and_approve, request_clarification)
        decision_rationale: Rationale for the decision
        straight_through_eligible: Whether entry was eligible for straight-through processing
        requires_human_review: Whether entry required human review
        run_id: Processing run ID (optional)
        anomaly_detection_results: Anomaly detection results dictionary (optional)
        correction_suggestions: Correction suggestions dictionary (optional)
        hitl_decision: HITL decision (optional)
        hitl_response_data: HITL response data (optional)
        extracted_entry: Extracted entry data (optional)
    
    Returns:
        Dictionary with recorded (boolean), result_id, and error
    """
    conn = None
    try:
        # Normalize optional parameters
        if hitl_response_data == "" or (isinstance(hitl_response_data, str) and not hitl_response_data.strip()):
            hitl_response_data = None
        if extracted_entry == "" or (isinstance(extracted_entry, str) and not extracted_entry.strip()):
            extracted_entry = None
        
        conn = _connect(db_file)
        cursor = conn.cursor()
        current_time = _utc_iso()
        
        # 1. Update journal_entries table (both debit and credit entries)
        cursor.execute("""
            UPDATE journal_entries
            SET status = ?, processed_at = ?, run_id = ?
            WHERE transaction_id = ?
        """, (status, current_time, run_id, transaction_id))
        
        # 2. Insert into anomaly_detection_results
        if anomaly_detection_results:
            result_id = str(uuid4())
            cursor.execute("""
                INSERT INTO anomaly_detection_results (
                    result_id, journal_id, run_id, anomaly_detected,
                    anomaly_type, reasoning, confidence_score, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result_id,
                journal_id,
                run_id,
                bool(anomaly_detection_results.get("anomaly_detected", False)),
                anomaly_detection_results.get("anomaly_type"),
                anomaly_detection_results.get("reasoning"),
                float(anomaly_detection_results.get("confidence_score", 0.0)) if anomaly_detection_results.get("confidence_score") else None,
                current_time
            ))
        else:
            result_id = None
        
        # 3. Insert into correction_suggestions
        if correction_suggestions:
            suggestion_id = str(uuid4())
            corrected_entry_json = json.dumps(correction_suggestions.get("corrected_entry")) if correction_suggestions.get("corrected_entry") else None
            cursor.execute("""
                INSERT INTO correction_suggestions (
                    suggestion_id, journal_id, run_id, corrected_entry,
                    correction_reasoning, impact_analysis, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                suggestion_id,
                journal_id,
                run_id,
                corrected_entry_json,
                correction_suggestions.get("correction_reasoning"),
                correction_suggestions.get("impact_analysis"),
                current_time
            ))
        
        # 4. Insert into validation_results
        validation_id = str(uuid4())
        cursor.execute("""
            INSERT INTO validation_results (
                validation_id, journal_id, run_id, human_decision,
                decision_reasoning, decision_date, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            validation_id,
            journal_id,
            run_id,
            hitl_decision,
            decision_rationale,
            current_time if hitl_decision else None,
            current_time
        ))
        
        conn.commit()
        conn.close()
        
        return {
            "recorded": True,
            "result_id": result_id or validation_id,
            "error": ""
        }
    
    except Exception as e:
        _logger.error("Error saving processing results: {}", e)
        if conn:
            conn.rollback()
            conn.close()
        return {
            "recorded": False,
            "result_id": None,
            "error": str(e)
        }
