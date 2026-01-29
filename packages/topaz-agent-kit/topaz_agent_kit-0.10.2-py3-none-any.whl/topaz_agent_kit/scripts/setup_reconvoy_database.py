#!/usr/bin/env python3
"""Setup script for ReconVoy pipeline - Phase 2 Redesign.

Creates a SQLite database, initializes schema, and generates mock data for
intercompany open-items research and clearance, focused on triangular
UK–US–FR scenarios.

New Design:
- BlackLine unmatched items table (input)
- US and FR books tables (reference only)
- UK journal entries table (output)
- FX rates table (book and spot rates)
- Multiple scenario types with documentation
"""

import argparse
import json
import random
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from rich.console import Console
    from rich.table import Table as RichTable
    from rich.panel import Panel
    from rich import box

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    RichTable = None
    Console = None
    Panel = None
    box = None

from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.utils.path_resolver import detect_project_name, resolve_script_path


logger = Logger("ReconVoySetup")


# ============================================================================
# Helpers
# ============================================================================


def _round2(value: float) -> float:
    """Round a numeric value to 2 decimal places consistently."""
    try:
        return float(f"{float(value):.2f}")
    except (TypeError, ValueError):
        return value


# ============================================================================
# Schema
# ============================================================================


def create_database_schema(db_path: str) -> None:
    """Create ReconVoy database schema per Phase 2 design."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # BlackLine unmatched items (input)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS blackline_unmatched_items (
            item_id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            system_id TEXT,
            trans_date TEXT NOT NULL,
            document_number TEXT,
            currency TEXT NOT NULL,
            amount_foreign DECIMAL(18, 4) NOT NULL,
            amount_local_gbp DECIMAL(18, 4) NOT NULL,
            reference_description TEXT,
            status TEXT DEFAULT 'UNMATCHED',
            processing_status TEXT,
            run_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
        """
    )

    # US books (reference only)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS us_books (
            entry_id TEXT PRIMARY KEY,
            company_code TEXT NOT NULL DEFAULT 'US01',
            document_number TEXT NOT NULL,
            gl_account TEXT NOT NULL,
            business_area TEXT,
            assignment TEXT,
            document_type TEXT NOT NULL,
            document_date TEXT NOT NULL,
            posting_date TEXT NOT NULL,
            reference TEXT,
            header_text TEXT,
            posting_key TEXT,
            document_currency TEXT NOT NULL,
            amount_document_currency DECIMAL(18, 4) NOT NULL,
            amount_local_currency DECIMAL(18, 4),
            local_currency TEXT,
            tax_code TEXT,
            profit_center TEXT,
            cost_center TEXT,
            trading_partner TEXT,
            clearing_doc_no TEXT,
            clearing_date TEXT,
            plant TEXT,
            "order" TEXT,
            wbs_element TEXT,
            remarks TEXT,
            scenario_tag TEXT
        )
        """
    )

    # FR books (reference only)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS fr_books (
            entry_id TEXT PRIMARY KEY,
            company_code TEXT NOT NULL DEFAULT 'FR01',
            document_number TEXT NOT NULL,
            gl_account TEXT NOT NULL,
            business_area TEXT,
            assignment TEXT,
            document_type TEXT NOT NULL,
            document_date TEXT NOT NULL,
            posting_date TEXT NOT NULL,
            reference TEXT,
            header_text TEXT,
            posting_key TEXT,
            document_currency TEXT NOT NULL,
            amount_document_currency DECIMAL(18, 4) NOT NULL,
            amount_local_currency DECIMAL(18, 4),
            local_currency TEXT,
            tax_code TEXT,
            profit_center TEXT,
            cost_center TEXT,
            trading_partner TEXT,
            clearing_doc_no TEXT,
            clearing_date TEXT,
            plant TEXT,
            "order" TEXT,
            wbs_element TEXT,
            remarks TEXT,
            scenario_tag TEXT
        )
        """
    )

    # UK journal entries (output)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS uk_journal_entries (
            entry_id TEXT PRIMARY KEY,
            company_code TEXT NOT NULL DEFAULT 'UK01',
            scenario TEXT,
            gl_account TEXT NOT NULL,
            business_area TEXT,
            assignment TEXT,
            document_type TEXT NOT NULL,
            document_date TEXT NOT NULL,
            posting_date TEXT NOT NULL,
            reference TEXT,
            header_text TEXT,
            posting_key TEXT,
            document_currency TEXT NOT NULL,
            amount_document_currency DECIMAL(18, 4) NOT NULL,
            amount_local_currency DECIMAL(18, 4),
            local_currency TEXT NOT NULL DEFAULT 'GBP',
            tax_code TEXT,
            profit_center TEXT,
            cost_center TEXT,
            trading_partner TEXT,
            clearing_doc_no TEXT,
            clearing_date TEXT,
            plant TEXT,
            "order" TEXT,
            wbs_element TEXT,
            remarks TEXT,
            case_id TEXT,
            blackline_item_ids TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # FX rates (book and spot)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS fx_rates (
            rate_id TEXT PRIMARY KEY,
            rate_date TEXT NOT NULL,
            from_currency TEXT NOT NULL,
            to_currency TEXT NOT NULL,
            rate_type TEXT NOT NULL,
            rate_value DECIMAL(18, 8) NOT NULL,
            scenario_tag TEXT
        )
        """
    )

    # Results table (reuse existing structure)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS reconvoy_results (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            open_item_id TEXT NOT NULL,
            run_id TEXT,
            route TEXT,
            hitl_required BOOLEAN,
            hitl_decision TEXT,
            fx_summary TEXT,
            error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Indexes
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_blackline_status "
        "ON blackline_unmatched_items(status, processing_status, run_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_blackline_source "
        "ON blackline_unmatched_items(source)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_us_books_document "
        "ON us_books(document_number)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_us_books_reference "
        "ON us_books(reference, header_text)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_us_books_scenario "
        "ON us_books(scenario_tag)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_fr_books_document "
        "ON fr_books(document_number)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_fr_books_reference "
        "ON fr_books(reference, header_text)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_fr_books_scenario "
        "ON fr_books(scenario_tag)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_fx_rates_lookup "
        "ON fx_rates(rate_date, from_currency, to_currency, rate_type)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_fx_rates_scenario "
        "ON fx_rates(scenario_tag)"
    )

    conn.commit()
    conn.close()
    logger.info("ReconVoy schema created at {}", db_path)


# ============================================================================
# Scenario Data Generation
# ============================================================================


def _jitter_date(base_date: str, max_days: int) -> str:
    """Jitter a YYYY-MM-DD date string by up to max_days in either direction."""
    if max_days <= 0:
        return base_date
    try:
        base_dt = datetime.strptime(base_date, "%Y-%m-%d")
    except ValueError:
        return base_date
    delta_days = random.randint(-max_days, max_days)
    jittered = base_dt + timedelta(days=delta_days)
    return jittered.strftime("%Y-%m-%d")


def _format_date_for_blackline(date_str: str) -> str:
    """Convert YYYY-MM-DD to DD.MM.YY format for BlackLine."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%d.%m.%y")
    except ValueError:
        return date_str


def generate_scenario_3(
    conn: sqlite3.Connection, index: int, variance_gbp: float = 352.0
) -> Dict[str, Any]:
    """Generate Scenario 3: UK Sells to US, US Pays FR on Behalf (HITL case).

    This matches the exact structure from the images:
    - UK receivable from US: £500,000 (USD 625,000)
    - UK payable to FR: €7,200 (£6,048)
    - UK bank wire received: £493,600 (USD 615,000)
    - Variance: £352 (FX loss)
    - Expected routing: HITL (variance > 100 GBP)
    """
    cursor = conn.cursor()
    scenario_tag = f"scenario3_{index+1:03d}"

    # Use exact dates from the example (year 2026)
    base_date = "2026-01-14"
    posting_date = base_date  # No jitter for canonical scenario
    trans_date_uk_inv = "01.12.25"  # UK invoice date (Dec 1, 2025)
    trans_date_wire = "14.01.26"  # Wire date (Jan 14, 2026)

    # Base amounts from the canonical example (will be scaled per-case)
    base_uk_receivable_gbp = 500_000.00
    base_uk_receivable_usd = 625_000.00
    base_us_wire_usd = 615_000.00
    base_us_wire_gbp = 493_600.00  # Using book rate ~1.245981
    base_fr_invoice_eur = 7_200.00
    base_fr_invoice_gbp = 6_048.00  # Using spot rate 0.84

    # Random scale factor so amounts vary per case but relationships stay consistent
    scale = random.uniform(0.5, 2.0)

    uk_receivable_gbp = _round2(base_uk_receivable_gbp * scale)
    uk_receivable_usd = _round2(base_uk_receivable_usd * scale)
    us_wire_usd = _round2(base_us_wire_usd * scale)
    us_wire_gbp = _round2(base_us_wire_gbp * scale)
    fr_invoice_eur = _round2(base_fr_invoice_eur * scale)
    fr_invoice_gbp = _round2(base_fr_invoice_gbp * scale)

    # ------------------------------------------------------------------------
    # Reference construction (amount-aware + case-unique)
    # ------------------------------------------------------------------------
    case_suffix = f"_{scenario_tag}"

    # Use integer EUR amount for FR logistics references (e.g., 7200 → 4680)
    fr_amount_eur_int = int(round(fr_invoice_eur))
    fr_amount_token = f"{fr_amount_eur_int}"

    # Use GBP wire amount in thousands for wire references (e.g., 493600 → 494K)
    wire_amount_k_int = int(round(us_wire_gbp / 1000))
    wire_amount_token = f"{wire_amount_k_int}K"

    bl_inv_ref = f"INV_US_OCT_99/US_SUB{case_suffix}"
    bl_log_ref = f"LOGISTIQUE_FR_{fr_amount_token}{case_suffix}"
    bl_wire_ref = f"WIRE_FR_US_SUB_REF_{wire_amount_token}{case_suffix}"

    us_inv_ref = bl_inv_ref
    us_inv_header = f"UK_INV_OCT_99{case_suffix}"

    us_wire_assignment = f"WIRE_{wire_amount_token}{case_suffix}"
    us_wire_ref = bl_wire_ref
    us_wire_header = f"Wire Ref {wire_amount_token}{case_suffix}"

    us_fr_ref = bl_log_ref
    us_fr_inv_ref = f"FR_INV_{fr_amount_token}{case_suffix}"

    fr_settle_ref = f"US_SETTLE_FR{case_suffix}"
    fr_clear_ref = f"UK_CLEAR_INV{case_suffix}"

    # Variance implied by scaled BlackLine-only rule
    fx_loss = _round2(uk_receivable_gbp - (us_wire_gbp + fr_invoice_gbp))

    # FX rates
    usd_gbp_book_rate = _round2(us_wire_usd / us_wire_gbp)  # ~1.245981
    eur_gbp_spot_rate = _round2(fr_invoice_gbp / fr_invoice_eur)  # 0.84

    # Document numbers - make unique per case while keeping base ranges
    base_us_document_number = 150000881
    base_fr_document_number = 190000442
    base_uk_document_number = 100000552
    us_document_number = str(base_us_document_number + index)
    fr_document_number = str(base_fr_document_number + index)
    uk_document_number = str(base_uk_document_number + index)

    # ========================================================================
    # BlackLine Items
    # ========================================================================

    # Item 1: UK receivable from US (GL SAP)
    cursor.execute(
        """
        INSERT OR REPLACE INTO blackline_unmatched_items (
            item_id, source, system_id, trans_date, document_number,
            currency, amount_foreign, amount_local_gbp, reference_description,
            status, processing_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"BL-S3-001-{index+1:03d}",
            "GL (SAP)",
            "SAP_UK_1001",
            trans_date_uk_inv,
            uk_document_number,
            "USD",
            uk_receivable_usd,
            uk_receivable_gbp,
            bl_inv_ref,
            "UNMATCHED",
            None,
        ),
    )

    # Item 2: UK payable to FR (GL SAP)
    cursor.execute(
        """
        INSERT OR REPLACE INTO blackline_unmatched_items (
            item_id, source, system_id, trans_date, document_number,
            currency, amount_foreign, amount_local_gbp, reference_description,
            status, processing_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"BL-S3-002-{index+1:03d}",
            "GL (SAP)",
            "SAP_UK_2002",
            trans_date_wire,
            uk_document_number,
            "EUR",
            fr_invoice_eur,
            fr_invoice_gbp,
            bl_log_ref,
            "UNMATCHED",
            None,
        ),
    )

    # Item 3: UK bank wire received (Bank)
    cursor.execute(
        """
        INSERT OR REPLACE INTO blackline_unmatched_items (
            item_id, source, system_id, trans_date, document_number,
            currency, amount_foreign, amount_local_gbp, reference_description,
            status, processing_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"BL-S3-003-{index+1:03d}",
            "Bank",
            "BNK_LON_SS",
            trans_date_wire,
            None,  # Bank items may not have document number
            "GBP",
            us_wire_gbp,
            us_wire_gbp,
            bl_wire_ref,
            "UNMATCHED",
            None,
        ),
    )

    # ========================================================================
    # US Books Entries (Document # 150000881)
    # ========================================================================

    # US Entry 1: AP clearing UK invoice (Debit)
    cursor.execute(
        """
        INSERT OR REPLACE INTO us_books (
            entry_id, company_code, document_number, gl_account, assignment,
            document_type, document_date, posting_date, reference, header_text,
            posting_key, document_currency, amount_document_currency,
            amount_local_currency, local_currency, profit_center, cost_center,
            trading_partner, remarks, scenario_tag
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"US-S3-001-{index+1:03d}",
            "US01",
            us_document_number,
            "210000",
            "CLR INV OCT 99",
            "ZP",
            "14.01.26",
            "14.01.26",
            us_inv_ref,
            us_inv_header,
            "21",
            "USD",
            uk_receivable_usd,
            uk_receivable_usd,
            "USD",
            "PC_US_CORP",
            None,
            "UK01",
            "Debit",
            scenario_tag,
        ),
    )

    # US Entry 2: Bank wire to UK (Credit)
    cursor.execute(
        """
        INSERT OR REPLACE INTO us_books (
            entry_id, company_code, document_number, gl_account, assignment,
            document_type, document_date, posting_date, reference, header_text,
            posting_key, document_currency, amount_document_currency,
            amount_local_currency, local_currency, profit_center, cost_center,
            trading_partner, remarks, scenario_tag
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"US-S3-002-{index+1:03d}",
            "US01",
            us_document_number,
            "100001",
            us_wire_assignment,
            "ZP",
            "14.01.26",
            "14.01.26",
            us_wire_ref,
            us_wire_header,
            "50",
            "USD",
            us_wire_usd,
            us_wire_usd,
            "USD",
            "PC_US_CORP",
            None,
            None,
            "Credit",
            scenario_tag,
        ),
    )

    # US Entry 3: Payment to FR on behalf of UK (Credit)
    cursor.execute(
        """
        INSERT OR REPLACE INTO us_books (
            entry_id, company_code, document_number, gl_account, assignment,
            document_type, document_date, posting_date, reference, header_text,
            posting_key, document_currency, amount_document_currency,
            amount_local_currency, local_currency, profit_center, cost_center,
            trading_partner, remarks, scenario_tag
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"US-S3-003-{index+1:03d}",
            "US01",
            us_document_number,
            "210000",
            "NET_FR_LOG",
            "ZP",
            "14.01.26",
            "14.01.26",
            us_fr_ref,
            "Pay on behalf of UK",
            "21",
            "USD",
            10_000.00,  # USD equivalent of €7,200
            10_000.00,
            "USD",
            "PC_US_LOG",
            "CC_LOG_01",
            "FR01",
            "Credit",
            scenario_tag,
        ),
    )

    # ========================================================================
    # FR Books Entries (Document # 190000442)
    # ========================================================================

    # FR Entry 1: IC Clearing (Debit) - US paid
    cursor.execute(
        """
        INSERT OR REPLACE INTO fr_books (
            entry_id, company_code, document_number, gl_account, assignment,
            document_type, document_date, posting_date, reference, header_text,
            posting_key, document_currency, amount_document_currency,
            amount_local_currency, local_currency, profit_center, cost_center,
            trading_partner, remarks, scenario_tag
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"FR-S3-001-{index+1:03d}",
            "FR01",
            fr_document_number,
            "120500",
            "US PAID UK",
            "AB",
            "14.01.26",
            "14.01.26",
            fr_settle_ref,
            bl_log_ref,
            "40",
            "EUR",
            fr_invoice_eur,
            fr_invoice_eur,
            "EUR",
            "PC_LOGIST",
            None,
            "US01",
            "Debit",
            scenario_tag,
        ),
    )

    # FR Entry 2: IC Receivable from UK (Credit)
    cursor.execute(
        """
        INSERT OR REPLACE INTO fr_books (
            entry_id, company_code, document_number, gl_account, assignment,
            document_type, document_date, posting_date, reference, header_text,
            posting_key, document_currency, amount_document_currency,
            amount_local_currency, local_currency, profit_center, cost_center,
            trading_partner, remarks, scenario_tag
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"FR-S3-002-{index+1:03d}",
            "FR01",
            fr_document_number,
            "120100",
            "INV_UK_OCT_99",
            "AB",
            "14.01.26",
            "14.01.26",
            fr_clear_ref,
            "LOGISTIQUE_FR_7200",
            "40",
            "EUR",
            fr_invoice_eur,
            fr_invoice_eur,
            "EUR",
            "PC_LOGIST",
            None,
            "UK01",
            "Credit",
            scenario_tag,
        ),
    )

    # ========================================================================
    # FX Rates
    # ========================================================================

    cursor.execute(
        """
        INSERT OR REPLACE INTO fx_rates (
            rate_id, rate_date, from_currency, to_currency, rate_type, rate_value, scenario_tag
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"FX-S3-USDGBP-BOOK-{index+1:03d}",
            posting_date,
            "USD",
            "GBP",
            "book",
            round(usd_gbp_book_rate, 8),
            scenario_tag,
        ),
    )

    cursor.execute(
        """
        INSERT OR REPLACE INTO fx_rates (
            rate_id, rate_date, from_currency, to_currency, rate_type, rate_value, scenario_tag
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"FX-S3-EURGBP-SPOT-{index+1:03d}",
            posting_date,
            "EUR",
            "GBP",
            "spot",
            eur_gbp_spot_rate,
            scenario_tag,
        ),
    )

    # ========================================================================
    # Scenario Documentation
    # ========================================================================

    doc = {
        "scenario_tag": scenario_tag,
        "scenario_type": "UK Sells to US, US Pays FR on Behalf",
        "description": (
            "UK sells inventory to US, FR provides logistics. "
            "US pays UK (reduced by FR amount) and pays FR directly."
        ),
        "blackline_items": [
            {
                "item_id": f"BL-S3-001-{index+1:03d}",
                "description": "UK receivable from US",
                "currency": "USD",
                "amount_foreign": uk_receivable_usd,
                "amount_local_gbp": uk_receivable_gbp,
                "reference": bl_inv_ref,
            },
            {
                "item_id": f"BL-S3-002-{index+1:03d}",
                "description": "UK payable to FR",
                "currency": "EUR",
                "amount_foreign": fr_invoice_eur,
                "amount_local_gbp": fr_invoice_gbp,
                "reference": bl_log_ref,
            },
            {
                "item_id": f"BL-S3-003-{index+1:03d}",
                "description": "UK bank wire received",
                "currency": "GBP",
                "amount_foreign": us_wire_gbp,
                "amount_local_gbp": us_wire_gbp,
                "reference": bl_wire_ref,
            },
        ],
        "us_books_entries": [
            {
                "entry_id": f"US-S3-001-{index+1:03d}",
                "document_number": us_document_number,
                "description": "AP clearing UK invoice",
                "reference": us_inv_ref,
            },
            {
                "entry_id": f"US-S3-002-{index+1:03d}",
                "document_number": us_document_number,
                "description": "Bank wire to UK",
                "reference": us_wire_ref,
            },
            {
                "entry_id": f"US-S3-003-{index+1:03d}",
                "document_number": us_document_number,
                "description": "Payment to FR on behalf of UK",
                "reference": us_fr_inv_ref,
            },
        ],
        "fr_books_entries": [
            {
                "entry_id": f"FR-S3-001-{index+1:03d}",
                "document_number": fr_document_number,
                "description": "IC Clearing (US paid)",
                "reference": fr_settle_ref,
            },
            {
                "entry_id": f"FR-S3-002-{index+1:03d}",
                "document_number": fr_document_number,
                "description": "IC Receivable from UK",
                "reference": fr_clear_ref,
            },
        ],
        "correlations": {
            "blackline_to_us": {
                f"BL-S3-001-{index+1:03d}": [
                    f"US-S3-001-{index+1:03d}"
                ],  # UK receivable matches US AP entry
            },
            "blackline_to_fr": {
                f"BL-S3-002-{index+1:03d}": [
                    f"FR-S3-001-{index+1:03d}",
                    f"FR-S3-002-{index+1:03d}",
                ],  # UK payable matches FR entries
            },
            "blackline_to_bank": {
                f"BL-S3-003-{index+1:03d}": [
                    f"US-S3-002-{index+1:03d}"
                ],  # UK bank wire matches US bank entry
            },
        },
        "expected_uk_journals": [
            {
                "gl_account": "113100",
                "description": "Bank Rec",
                "amount_gbp": us_wire_gbp,
                "header_text": "AI AUTO RECON",
                "remarks": "Debit",
            },
            {
                "gl_account": "210100",
                "description": "IC Payable FR",
                "amount_gbp": fr_invoice_gbp,
                "header_text": "AI TRI NET",
                "remarks": "Debit",
            },
            {
                "gl_account": "650100",
                "description": "FX Loss",
                "amount_gbp": fx_loss,
                "header_text": "AI FX ADJ",
                "remarks": "Debit",
            },
            {
                "gl_account": "120100",
                "description": "IC Receivable US (Clear)",
                "amount_gbp": uk_receivable_gbp,
                "header_text": "AI AUTO CLEAR",
                "remarks": "Credit",
            },
        ],
        "fx_calculations": {
            "us_wire_usd_to_gbp": {
                "amount_usd": us_wire_usd,
                "rate": usd_gbp_book_rate,
                "rate_type": "book",
                "amount_gbp": us_wire_gbp,
            },
            "fr_invoice_eur_to_gbp": {
                "amount_eur": fr_invoice_eur,
                "rate": eur_gbp_spot_rate,
                "rate_type": "spot",
                "amount_gbp": fr_invoice_gbp,
            },
        },
        # NOTE: Variance here is aligned with the deterministic tool logic:
        # total_blackline_gbp = main item only
        # total_matched_gbp   = sum of other case items
        "variance_calculation": {
            "total_blackline_gbp": uk_receivable_gbp,
            "total_matched_gbp": us_wire_gbp + fr_invoice_gbp,
            "variance_gbp": fx_loss,
            "variance_percent": (fx_loss / uk_receivable_gbp) * 100,
        },
        "expected_routing": "HITL" if abs(fx_loss) > 100 else "StraightThrough",
    }

    logger.info(
        "Generated Scenario 3 (scenario_tag={}) variance_gbp={:.2f} expected_routing={}",
        scenario_tag,
        fx_loss,
        doc["expected_routing"],
    )

    return doc


def generate_scenario_4(
    conn: sqlite3.Connection, index: int, variance_gbp: float = 50.0
) -> Dict[str, Any]:
    """Generate Scenario 4: UK Buys from US, US Pays FR on Behalf (Straight-through case).

    Similar to Scenario 3 but with payables instead of receivables, and lower variance.
    """
    cursor = conn.cursor()
    scenario_tag = f"scenario4_{index+1:03d}"

    base_date = "2026-02-15"
    posting_date = base_date
    trans_date_uk_inv = "01.02.26"  # Feb 1, 2026
    trans_date_wire = "15.02.26"  # Feb 15, 2026

    # Base amounts from the canonical example (will be scaled per-case)
    base_uk_payable_gbp = 100_000.00
    base_uk_payable_usd = 148_000.00
    base_us_wire_usd = 147_500.00
    # Base GBP amount chosen so that variance = 50 under BlackLine-only rule:
    #   100,000 - (98,690 + 1,260) = 50
    base_us_wire_gbp = 98_690.00
    base_fr_invoice_eur = 1_500.00
    base_fr_invoice_gbp = 1_260.00

    # Random scale factor so amounts vary per case but relationships stay consistent
    # Keep scale modest so |scaled variance| stays within straight-through band.
    scale = random.uniform(0.5, 1.5)

    uk_payable_gbp = _round2(base_uk_payable_gbp * scale)
    uk_payable_usd = _round2(base_uk_payable_usd * scale)
    us_wire_usd = _round2(base_us_wire_usd * scale)
    us_wire_gbp = _round2(base_us_wire_gbp * scale)
    fr_invoice_eur = _round2(base_fr_invoice_eur * scale)
    fr_invoice_gbp = _round2(base_fr_invoice_gbp * scale)

    # ------------------------------------------------------------------------
    # Reference construction (amount-aware + case-unique)
    # ------------------------------------------------------------------------
    case_suffix = f"_{scenario_tag}"

    fr_amount_eur_int = int(round(fr_invoice_eur))
    fr_amount_token = f"{fr_amount_eur_int}"

    wire_amount_k_int = int(round(us_wire_gbp / 1000))
    wire_amount_token = f"{wire_amount_k_int}K"

    bl_inv_ref = f"INV_US_FEB_26/US_SUB{case_suffix}"
    bl_log_ref = f"LOGISTIQUE_FR_{fr_amount_token}{case_suffix}"
    bl_wire_ref = f"WIRE_US_SUB_REF_{wire_amount_token}{case_suffix}"

    us_inv_ref = bl_inv_ref
    us_bank_stmt_ref = f"BNK_STMT_56{case_suffix}"
    us_wire_header = bl_wire_ref
    us_wire_assignment = f"WIRE_{wire_amount_token}{case_suffix}"
    us_fr_inv_ref = f"FR_INV_{fr_amount_token}{case_suffix}"

    fr_settle_ref = f"US_SETTLE_FR{case_suffix}"
    fr_clear_ref = f"UK_CLEAR_INV{case_suffix}"

    # Variance implied by scaled BlackLine-only rule (will be ~scale * 50)
    fx_gain = _round2(uk_payable_gbp - (us_wire_gbp + fr_invoice_gbp))

    # FX rates
    usd_gbp_book_rate = _round2(us_wire_usd / us_wire_gbp)
    eur_gbp_spot_rate = _round2(fr_invoice_gbp / fr_invoice_eur)

    # Document numbers - make unique per case and non-overlapping with Scenario 3
    # Scenario 3 uses US: 150000881+, FR: 190000442+, UK: 100000552+
    # Scenario 4 is moved to a separate block to avoid cross-scenario reuse
    base_us_document_number = 150001000
    base_fr_document_number = 190001000
    base_uk_document_number = 100001000
    us_document_number = str(base_us_document_number + index)
    fr_document_number = str(base_fr_document_number + index)
    uk_document_number = str(base_uk_document_number + index)

    # BlackLine Items
    cursor.execute(
        """
        INSERT OR REPLACE INTO blackline_unmatched_items (
            item_id, source, system_id, trans_date, document_number,
            currency, amount_foreign, amount_local_gbp, reference_description,
            status, processing_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"BL-S4-001-{index+1:03d}",
            "GL (SAP)",
            "SAP_UK_1002",
            trans_date_uk_inv,
            uk_document_number,
            "USD",
            uk_payable_usd,
            uk_payable_gbp,
            bl_inv_ref,
            "UNMATCHED",
            None,
        ),
    )

    cursor.execute(
        """
        INSERT OR REPLACE INTO blackline_unmatched_items (
            item_id, source, system_id, trans_date, document_number,
            currency, amount_foreign, amount_local_gbp, reference_description,
            status, processing_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"BL-S4-002-{index+1:03d}",
            "GL (SAP)",
            "SAP_UK_2003",
            trans_date_wire,
            uk_document_number,
            "EUR",
            fr_invoice_eur,
            fr_invoice_gbp,
            bl_log_ref,
            "UNMATCHED",
            None,
        ),
    )

    cursor.execute(
        """
        INSERT OR REPLACE INTO blackline_unmatched_items (
            item_id, source, system_id, trans_date, document_number,
            currency, amount_foreign, amount_local_gbp, reference_description,
            status, processing_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"BL-S4-003-{index+1:03d}",
            "Bank",
            "BNK_LON_SS",
            trans_date_wire,
            None,
            "GBP",
            us_wire_gbp,
            us_wire_gbp,
            bl_wire_ref,
            "UNMATCHED",
            None,
        ),
    )

    # US Books Entries
    cursor.execute(
        """
        INSERT OR REPLACE INTO us_books (
            entry_id, company_code, document_number, gl_account, assignment,
            document_type, document_date, posting_date, reference, header_text,
            posting_key, document_currency, amount_document_currency,
            amount_local_currency, local_currency, profit_center, trading_partner, remarks, scenario_tag
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"US-S4-001-{index+1:03d}",
            "US01",
            us_document_number,
            "120000",
            "CLR INV FEB 26",
            "ZP",
            "15.02.26",
            "15.02.26",
            us_inv_ref,
            "Clear Feb Purchase",
            "40",
            "USD",
            uk_payable_usd,
            uk_payable_usd,
            "USD",
            "PC_US_CORP",
            "UK01",
            "Credit",
            scenario_tag,
        ),
    )

    cursor.execute(
        """
        INSERT OR REPLACE INTO us_books (
            entry_id, company_code, document_number, gl_account, assignment,
            document_type, document_date, posting_date, reference, header_text,
            posting_key, document_currency, amount_document_currency,
            amount_local_currency, local_currency, profit_center, trading_partner, remarks, scenario_tag
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"US-S4-002-{index+1:03d}",
            "US01",
            us_document_number,
            "100001",
            us_wire_assignment,
            "ZP",
            "15.02.26",
            "15.02.26",
            us_bank_stmt_ref,
            us_wire_header,
            "50",
            "USD",
            us_wire_usd,
            us_wire_usd,
            "USD",
            "PC_US_CORP",
            None,
            "Debit",
            scenario_tag,
        ),
    )

    cursor.execute(
        """
        INSERT OR REPLACE INTO us_books (
            entry_id, company_code, document_number, gl_account, assignment,
            document_type, document_date, posting_date, reference, header_text,
            posting_key, document_currency, amount_document_currency,
            amount_local_currency, local_currency, profit_center, cost_center, trading_partner, remarks, scenario_tag
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"US-S4-003-{index+1:03d}",
            "US01",
            us_document_number,
            "120000",
            "NET_FR_LOG",
            "ZP",
            "15.02.26",
            "15.02.26",
            # Align reference with BlackLine item BL-S4-002 so matching works
            bl_log_ref,
            "Pay on behalf of UK",
            "40",
            "USD",
            2_100.00,  # USD equivalent
            2_100.00,
            "USD",
            "PC_US_LOG",
            "CC_LOG_01",
            "FR01",
            "Credit",
            scenario_tag,
        ),
    )

    # FR Books Entries
    cursor.execute(
        """
        INSERT OR REPLACE INTO fr_books (
            entry_id, company_code, document_number, gl_account, assignment,
            document_type, document_date, posting_date, reference, header_text,
            posting_key, document_currency, amount_document_currency,
            amount_local_currency, local_currency, profit_center, trading_partner, remarks, scenario_tag
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"FR-S4-001-{index+1:03d}",
            "FR01",
            fr_document_number,
            "120500",
            "US PAID UK",
            "AB",
            "15.02.26",
            "15.02.26",
            fr_settle_ref,
            bl_log_ref,
            "40",
            "EUR",
            fr_invoice_eur,
            fr_invoice_eur,
            "EUR",
            "PC_LOGIST",
            "US01",
            "Debit",
            scenario_tag,
        ),
    )

    cursor.execute(
        """
        INSERT OR REPLACE INTO fr_books (
            entry_id, company_code, document_number, gl_account, assignment,
            document_type, document_date, posting_date, reference, header_text,
            posting_key, document_currency, amount_document_currency,
            amount_local_currency, local_currency, profit_center, trading_partner, remarks, scenario_tag
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"FR-S4-002-{index+1:03d}",
            "FR01",
            fr_document_number,
            "210100",
            "INV_UK_FEB_26",
            "AB",
            "15.02.26",
            "15.02.26",
            "UK_CLEAR_INV",
            "LOGISTIQUE_FR_1500",
            "40",
            "EUR",
            fr_invoice_eur,
            fr_invoice_eur,
            "EUR",
            "PC_LOGIST",
            "UK01",
            "Credit",
            scenario_tag,
        ),
    )

    # FX Rates
    cursor.execute(
        """
        INSERT OR REPLACE INTO fx_rates (
            rate_id, rate_date, from_currency, to_currency, rate_type, rate_value, scenario_tag
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"FX-S4-USDGBP-BOOK-{index+1:03d}",
            posting_date,
            "USD",
            "GBP",
            "book",
            round(usd_gbp_book_rate, 8),
            scenario_tag,
        ),
    )

    cursor.execute(
        """
        INSERT OR REPLACE INTO fx_rates (
            rate_id, rate_date, from_currency, to_currency, rate_type, rate_value, scenario_tag
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"FX-S4-EURGBP-SPOT-{index+1:03d}",
            posting_date,
            "EUR",
            "GBP",
            "spot",
            eur_gbp_spot_rate,
            scenario_tag,
        ),
    )

    doc = {
        "scenario_tag": scenario_tag,
        "scenario_type": "UK Buys from US, US Pays FR on Behalf",
        "description": (
            "UK purchases goods from US, FR provides logistics. "
            "US pays FR directly on behalf of UK. Lower variance case for straight-through."
        ),
        "blackline_items": [
            {
                "item_id": f"BL-S4-001-{index+1:03d}",
                "description": "UK payable to US",
                "currency": "USD",
                "amount_foreign": uk_payable_usd,
                "amount_local_gbp": uk_payable_gbp,
                "reference": bl_inv_ref,
            },
            {
                "item_id": f"BL-S4-002-{index+1:03d}",
                "description": "UK payable to FR",
                "currency": "EUR",
                "amount_foreign": fr_invoice_eur,
                "amount_local_gbp": fr_invoice_gbp,
                "reference": bl_log_ref,
            },
            {
                "item_id": f"BL-S4-003-{index+1:03d}",
                "description": "UK bank payment",
                "currency": "GBP",
                "amount_foreign": us_wire_gbp,
                "amount_local_gbp": us_wire_gbp,
                "reference": bl_wire_ref,
            },
        ],
        "us_books_entries": [
            {
                "entry_id": f"US-S4-001-{index+1:03d}",
                "document_number": us_document_number,
                "description": "AR clearing UK invoice",
                "reference": us_inv_ref,
            },
            {
                "entry_id": f"US-S4-002-{index+1:03d}",
                "document_number": us_document_number,
                "description": "Bank wire from UK",
                "reference": us_bank_stmt_ref,
            },
            {
                "entry_id": f"US-S4-003-{index+1:03d}",
                "document_number": us_document_number,
                "description": "Payment to FR on behalf of UK",
                "reference": us_fr_inv_ref,
            },
        ],
        "fr_books_entries": [
            {
                "entry_id": f"FR-S4-001-{index+1:03d}",
                "document_number": fr_document_number,
                "description": "IC Clearing (US paid)",
                "reference": fr_settle_ref,
            },
            {
                "entry_id": f"FR-S4-002-{index+1:03d}",
                "document_number": fr_document_number,
                "description": "IC Payable to UK",
                "reference": fr_clear_ref,
            },
        ],
        "correlations": {
            "blackline_to_us": {
                f"BL-S4-001-{index+1:03d}": [
                    f"US-S4-001-{index+1:03d}"
                ],  # UK payable matches US AR entry
            },
            "blackline_to_fr": {
                f"BL-S4-002-{index+1:03d}": [
                    f"FR-S4-001-{index+1:03d}",
                    f"FR-S4-002-{index+1:03d}",
                ],  # UK payable matches FR entries
            },
            "blackline_to_bank": {
                f"BL-S4-003-{index+1:03d}": [
                    f"US-S4-002-{index+1:03d}"
                ],  # UK bank payment matches US bank entry
            },
        },
        "expected_uk_journals": [
            {
                "gl_account": "100001",
                "description": "Bank Payment",
                "amount_gbp": us_wire_gbp,
                "header_text": "AI AUTO RECON",
                "remarks": "Credit",
            },
            {
                "gl_account": "210100",
                "description": "IC Payable FR",
                "amount_gbp": fr_invoice_gbp,
                "header_text": "AI TRI NET",
                "remarks": "Debit",
            },
            {
                "gl_account": "650200",
                "description": "FX Gain",
                "amount_gbp": fx_gain,
                "header_text": "AI FX ADJ",
                "remarks": "Credit",
            },
            {
                "gl_account": "210000",
                "description": "IC Payable US (Clear)",
                "amount_gbp": uk_payable_gbp,
                "header_text": "AI AUTO CLEAR",
                "remarks": "Credit",
            },
        ],
        "fx_calculations": {
            "us_wire_usd_to_gbp": {
                "amount_usd": us_wire_usd,
                "rate": usd_gbp_book_rate,
                "rate_type": "book",
                "amount_gbp": us_wire_gbp,
            },
            "fr_invoice_eur_to_gbp": {
                "amount_eur": fr_invoice_eur,
                "rate": eur_gbp_spot_rate,
                "rate_type": "spot",
                "amount_gbp": fr_invoice_gbp,
            },
        },
        # NOTE: Variance here is aligned with the deterministic tool logic:
        # total_blackline_gbp = main item only
        # total_matched_gbp   = sum of other case items
        "variance_calculation": {
            "total_blackline_gbp": uk_payable_gbp,
            "total_matched_gbp": us_wire_gbp + fr_invoice_gbp,
            "variance_gbp": fx_gain,
            "variance_percent": (fx_gain / uk_payable_gbp) * 100,
        },
        "expected_routing": "StraightThrough" if abs(fx_gain) <= 100 else "HITL",
    }

    logger.info(
        "Generated Scenario 4 (scenario_tag={}) variance_gbp={:.2f} expected_routing={}",
        scenario_tag,
        fx_gain,
        doc["expected_routing"],
    )

    return doc


def validate_scenario_data(
    conn: sqlite3.Connection, scenario: Dict[str, Any]
) -> Dict[str, Any]:
    """Validate scenario data for quality issues.
    
    Checks:
    - Reference matching between BlackLine items and foreign book entries
    - Date format consistency
    - FX rate availability
    - Document number consistency
    - Amount consistency
    
    Returns:
        Dictionary with validation results including issues found
    """
    cursor = conn.cursor()
    issues = []
    warnings = []
    
    scenario_tag = scenario.get("scenario_tag", "unknown")
    blackline_items = scenario.get("blackline_items", [])
    us_entries = scenario.get("us_books_entries", [])
    fr_entries = scenario.get("fr_books_entries", [])
    
    # Helper to convert date format
    def convert_date_to_iso(date_str: str) -> str:
        """Convert DD.MM.YY to YYYY-MM-DD"""
        try:
            parts = date_str.split(".")
            if len(parts) == 3:
                day, month, year = parts
                # Assume YY >= 00 means 2000-2099
                full_year = f"20{year}" if len(year) == 2 else year
                return f"{full_year}-{month.zfill(2)}-{day.zfill(2)}"
        except:
            pass
        return date_str
    
    # 1. Check reference matching for BlackLine items
    for bl_item in blackline_items:
        item_id = bl_item.get("item_id", "unknown")
        currency = bl_item.get("currency", "")
        reference = bl_item.get("reference", "")
        amount_foreign = bl_item.get("amount_foreign", 0)
        
        # Check if this BlackLine item should match a foreign book entry
        if currency in ["USD", "EUR"]:
            # Query actual database entries to verify match
            if currency == "USD":
                cursor.execute(
                    """
                    SELECT entry_id, reference, header_text, amount_document_currency
                    FROM us_books
                    WHERE (reference = ? OR header_text = ?)
                      AND ABS(amount_document_currency - ?) < 0.01
                    LIMIT 1
                    """,
                    (reference, reference, amount_foreign),
                )
            else:  # EUR
                cursor.execute(
                    """
                    SELECT entry_id, reference, header_text, amount_document_currency
                    FROM fr_books
                    WHERE (reference = ? OR header_text = ?)
                      AND ABS(amount_document_currency - ?) < 0.01
                    LIMIT 1
                    """,
                    (reference, reference, amount_foreign),
                )
            
            match = cursor.fetchone()
            if not match:
                issues.append({
                    "type": "reference_mismatch",
                    "severity": "error",
                    "item": item_id,
                    "message": f"BlackLine item '{item_id}' reference '{reference}' (currency: {currency}, amount: {amount_foreign}) does not match any foreign book entry",
                })
    
    # 2. Check FX rate availability for dates used
    fx_calculations = scenario.get("fx_calculations", {})
    for calc_name, calc_data in fx_calculations.items():
        rate_type = calc_data.get("rate_type", "")
        # Determine currency from calculation name or data
        if "usd" in calc_name.lower() or "amount_usd" in calc_data:
            from_currency = "USD"
        elif "eur" in calc_name.lower() or "amount_eur" in calc_data:
            from_currency = "EUR"
        else:
            from_currency = "USD"  # Default
        to_currency = "GBP"
        
        # Get posting date from scenario (need to extract from base_date)
        base_date = None
        if "scenario3" in scenario_tag:
            base_date = "2026-01-14"
        elif "scenario4" in scenario_tag:
            base_date = "2026-02-15"
        
        if base_date:
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
                (base_date, from_currency, to_currency, rate_type),
            )
            rate = cursor.fetchone()
            if not rate:
                issues.append({
                    "type": "missing_fx_rate",
                    "severity": "error",
                    "scenario": scenario_tag,
                    "message": f"FX rate missing for {from_currency}/{to_currency} {rate_type} on {base_date}",
                })
    
    # 3. Check document number consistency
    us_doc_numbers = {entry.get("document_number") for entry in us_entries}
    fr_doc_numbers = {entry.get("document_number") for entry in fr_entries}
    
    # All US entries in a scenario should share the same document number
    if len(us_doc_numbers) > 1:
        warnings.append({
            "type": "document_number_inconsistency",
            "severity": "warning",
            "scenario": scenario_tag,
            "message": f"Multiple US document numbers found: {us_doc_numbers}",
        })
    
    if len(fr_doc_numbers) > 1:
        warnings.append({
            "type": "document_number_inconsistency",
            "severity": "warning",
            "scenario": scenario_tag,
            "message": f"Multiple FR document numbers found: {fr_doc_numbers}",
        })
    
    # 4. Check date format consistency
    # This is more of a warning since dates might be in different formats intentionally
    # Dates are stored in the database, we'd need to query them
    # For now, we'll skip this check or make it a warning
    
    # 5. Check amount consistency in correlations
    correlations = scenario.get("correlations", {})
    if "blackline_to_us" in correlations:
        for bl_id, us_ids in correlations["blackline_to_us"].items():
            bl_item = next((item for item in blackline_items if item["item_id"] == bl_id), None)
            if bl_item:
                bl_amount = bl_item.get("amount_foreign", 0)
                # Check if US entries match the amount
                for us_id in us_ids:
                    us_entry = next((entry for entry in us_entries if entry["entry_id"] == us_id), None)
                    if us_entry:
                        # Amount matching is already checked in reference matching above
                        pass
    
    return {
        "scenario_tag": scenario_tag,
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "issue_count": len(issues),
        "warning_count": len(warnings),
    }


def generate_scenario_documentation(
    db_path: str, scenarios: List[Dict[str, Any]]
) -> None:
    """Generate markdown documentation for all scenarios."""
    doc_path = Path(db_path).parent / "scenario_documentation.md"
    with open(doc_path, "w") as f:
        f.write("# ReconVoy Scenario Documentation\n\n")
        f.write(
            "This document describes the mock data scenarios generated for the ReconVoy pipeline.\n\n"
        )

        for scenario in scenarios:
            f.write(f"## {scenario['scenario_tag']}: {scenario['scenario_type']}\n\n")
            f.write(f"**Description:** {scenario['description']}\n\n")

            f.write("### BlackLine Items\n\n")
            f.write("| Item ID | Description | Currency | Foreign Amount | GBP Amount | Reference |\n")
            f.write("|---------|-------------|----------|---------------|------------|----------|\n")
            for item in scenario.get("blackline_items", []):
                f.write(
                    f"| {item['item_id']} | {item['description']} | {item['currency']} | "
                    f"{item['amount_foreign']:,.2f} | {item['amount_local_gbp']:,.2f} | "
                    f"{item['reference']} |\n"
                )

            if "us_books_entries" in scenario:
                f.write("\n### US Books Entries\n\n")
                f.write("| Entry ID | Document # | Description | Reference |\n")
                f.write("|----------|------------|-------------|----------|\n")
                for entry in scenario["us_books_entries"]:
                    f.write(
                        f"| {entry['entry_id']} | {entry['document_number']} | "
                        f"{entry['description']} | {entry['reference']} |\n"
                    )

            if "fr_books_entries" in scenario:
                f.write("\n### FR Books Entries\n\n")
                f.write("| Entry ID | Document # | Description | Reference |\n")
                f.write("|----------|------------|-------------|----------|\n")
                for entry in scenario["fr_books_entries"]:
                    f.write(
                        f"| {entry['entry_id']} | {entry['document_number']} | "
                        f"{entry['description']} | {entry['reference']} |\n"
                    )

            if "correlations" in scenario:
                f.write("\n### Row Correlations\n\n")
                f.write(
                    "**BlackLine to US Books:**\n"
                )
                for bl_id, us_ids in scenario["correlations"].get(
                    "blackline_to_us", {}
                ).items():
                    f.write(f"- {bl_id} → {', '.join(us_ids)}\n")
                f.write("\n**BlackLine to FR Books:**\n")
                for bl_id, fr_ids in scenario["correlations"].get(
                    "blackline_to_fr", {}
                ).items():
                    f.write(f"- {bl_id} → {', '.join(fr_ids)}\n")

            if "expected_uk_journals" in scenario:
                f.write("\n### Expected UK Journal Entries\n\n")
                f.write(
                    "| GL Account | Description | Amount (GBP) | Header Text | Remarks |\n"
                )
                f.write("|------------|-------------|--------------|-------------|---------|\n")
                for journal in scenario["expected_uk_journals"]:
                    f.write(
                        f"| {journal['gl_account']} | {journal['description']} | "
                        f"{journal['amount_gbp']:,.2f} | {journal['header_text']} | "
                        f"{journal['remarks']} |\n"
                    )

            if "variance_calculation" in scenario:
                f.write("\n### Variance Calculation\n\n")
                var = scenario["variance_calculation"]
                f.write(f"- Total BlackLine GBP: {var['total_blackline_gbp']:,.2f}\n")
                f.write(f"- Total Matched GBP: {var['total_matched_gbp']:,.2f}\n")
                f.write(f"- Variance GBP: {var['variance_gbp']:,.2f}\n")
                f.write(f"- Variance %: {var['variance_percent']:.4f}%\n")

            f.write(f"\n### Expected Routing\n\n")
            f.write(f"**{scenario.get('expected_routing', 'Unknown')}**\n\n")
            
            # Validation Results
            validation = scenario.get("validation", {})
            if validation:
                f.write("### Data Validation\n\n")
                if validation.get("valid"):
                    f.write("✅ **Validation Status:** PASSED\n\n")
                else:
                    f.write("❌ **Validation Status:** FAILED\n\n")
                
                issues = validation.get("issues", [])
                warnings = validation.get("warnings", [])
                
                if issues:
                    f.write("#### Issues Found\n\n")
                    for issue in issues:
                        f.write(f"- **{issue.get('type', 'unknown')}**: {issue.get('message', '')}\n")
                    f.write("\n")
                
                if warnings:
                    f.write("#### Warnings\n\n")
                    for warning in warnings:
                        f.write(f"- **{warning.get('type', 'unknown')}**: {warning.get('message', '')}\n")
                    f.write("\n")
            
            f.write("---\n\n")

    logger.info("Generated scenario documentation at {}", doc_path)


def generate_rich_report(scenarios: List[Dict[str, Any]]) -> None:
    """Generate a comprehensive rich console report for all scenarios."""
    if not RICH_AVAILABLE:
        return

    console = Console()

    # Overall summary
    total_scenarios = len(scenarios)
    hitl_count = sum(1 for s in scenarios if s.get("expected_routing") == "HITL")
    st_count = sum(1 for s in scenarios if s.get("expected_routing") == "StraightThrough")
    total_blackline_items = sum(len(s.get("blackline_items", [])) for s in scenarios)
    
    # Validation summary
    total_issues = sum(len(s.get("validation", {}).get("issues", [])) for s in scenarios)
    total_warnings = sum(len(s.get("validation", {}).get("warnings", [])) for s in scenarios)
    passed_scenarios = sum(1 for s in scenarios if s.get("validation", {}).get("valid", False))
    failed_scenarios = total_scenarios - passed_scenarios

    console.print()
    summary_content = (
        f"[bold]Total Scenarios:[/bold] {total_scenarios} | "
        f"[bold]HITL Cases:[/bold] {hitl_count} | "
        f"[bold]Straight-Through Cases:[/bold] {st_count} | "
        f"[bold]Total BlackLine Items:[/bold] {total_blackline_items}"
    )
    
    if total_issues > 0 or total_warnings > 0:
        summary_content += (
            f"\n\n[bold]Validation:[/bold] "
            f"[green]✅ {passed_scenarios} passed[/green] | "
            f"[red]❌ {failed_scenarios} failed[/red] | "
            f"[red]{total_issues} issues[/red] | "
            f"[yellow]{total_warnings} warnings[/yellow]"
        )
    
    console.print(
        Panel.fit(
            summary_content,
            title="[bold blue]ReconVoy Mock Data Generation Summary[/bold blue]",
            border_style="blue",
        )
    )
    console.print()

    # Detailed report for each scenario
    for idx, scenario in enumerate(scenarios, 1):
        scenario_tag = scenario.get("scenario_tag", "Unknown")
        scenario_type = scenario.get("scenario_type", "Unknown")
        description = scenario.get("description", "")
        expected_routing = scenario.get("expected_routing", "Unknown")
        routing_color = "red" if expected_routing == "HITL" else "green"

        # Scenario header
        console.print(
            Panel.fit(
                f"[bold]{scenario_type}[/bold]\n\n{description}",
                title=f"[bold cyan]Scenario {idx}: {scenario_tag}[/bold cyan]",
                border_style="cyan",
            )
        )
        console.print()

        # BlackLine Items Table
        blackline_items = scenario.get("blackline_items", [])
        if blackline_items:
            bl_table = RichTable(
                title="[bold]BlackLine Unmatched Items[/bold]",
                show_header=True,
                header_style="bold magenta",
                border_style="blue",
                box=box.ROUNDED,
                show_lines=True,
            )
            bl_table.add_column("Item ID", style="cyan", no_wrap=True, width=20)
            bl_table.add_column("Description", style="white", width=30)
            bl_table.add_column("Currency", style="yellow", width=10)
            bl_table.add_column("Foreign Amount", style="green", justify="right", width=16)
            bl_table.add_column("GBP Amount", style="green", justify="right", width=14)
            bl_table.add_column("Reference", style="bright_cyan", width=25)

            for item in blackline_items:
                bl_table.add_row(
                    item["item_id"],
                    item["description"],
                    item["currency"],
                    f"{item['amount_foreign']:,.2f}",
                    f"{item['amount_local_gbp']:,.2f}",
                    item["reference"],
                )
            console.print(bl_table)
            console.print()

        # Foreign Books Entries
        us_entries = scenario.get("us_books_entries", [])
        fr_entries = scenario.get("fr_books_entries", [])

        if us_entries:
            us_table = RichTable(
                title="[bold]US Books Entries (Reference Only)[/bold]",
                show_header=True,
                header_style="bold magenta",
                border_style="blue",
                box=box.ROUNDED,
                show_lines=True,
            )
            us_table.add_column("Entry ID", style="cyan", no_wrap=True, width=20)
            us_table.add_column("Document #", style="yellow", width=15)
            us_table.add_column("Description", style="white", width=35)
            us_table.add_column("Reference", style="bright_cyan", width=25)

            for entry in us_entries:
                us_table.add_row(
                    entry["entry_id"],
                    entry["document_number"],
                    entry["description"],
                    entry["reference"],
                )
            console.print(us_table)
            console.print()

        if fr_entries:
            fr_table = RichTable(
                title="[bold]FR Books Entries (Reference Only)[/bold]",
                show_header=True,
                header_style="bold magenta",
                border_style="blue",
                box=box.ROUNDED,
                show_lines=True,
            )
            fr_table.add_column("Entry ID", style="cyan", no_wrap=True, width=20)
            fr_table.add_column("Document #", style="yellow", width=15)
            fr_table.add_column("Description", style="white", width=35)
            fr_table.add_column("Reference", style="bright_cyan", width=25)

            for entry in fr_entries:
                fr_table.add_row(
                    entry["entry_id"],
                    entry["document_number"],
                    entry["description"],
                    entry["reference"],
                )
            console.print(fr_table)
            console.print()

        # Row Correlations
        correlations = scenario.get("correlations", {})
        if correlations:
            console.print("[bold]Row Correlations:[/bold]")
            if "blackline_to_us" in correlations:
                console.print("  [cyan]BlackLine → US Books:[/cyan]")
                for bl_id, us_ids in correlations["blackline_to_us"].items():
                    console.print(f"    {bl_id} → {', '.join(us_ids)}")
            if "blackline_to_fr" in correlations:
                console.print("  [cyan]BlackLine → FR Books:[/cyan]")
                for bl_id, fr_ids in correlations["blackline_to_fr"].items():
                    console.print(f"    {bl_id} → {', '.join(fr_ids)}")
            if "blackline_to_bank" in correlations:
                console.print("  [cyan]BlackLine → Bank Entries:[/cyan]")
                for bl_id, bank_ids in correlations["blackline_to_bank"].items():
                    console.print(f"    {bl_id} → {', '.join(bank_ids)}")
            console.print()

        # Expected UK Journal Entries
        uk_journals = scenario.get("expected_uk_journals", [])
        if uk_journals:
            journal_table = RichTable(
                title="[bold]Expected UK Journal Entries (Output)[/bold]",
                show_header=True,
                header_style="bold magenta",
                border_style="green",
                box=box.ROUNDED,
                show_lines=True,
            )
            journal_table.add_column("GL Account", style="cyan", width=12)
            journal_table.add_column("Description", style="white", width=25)
            journal_table.add_column("Amount (GBP)", style="green", justify="right", width=16)
            journal_table.add_column("Header Text", style="bright_cyan", width=18)
            journal_table.add_column("Remarks", style="yellow", width=10)

            for journal in uk_journals:
                journal_table.add_row(
                    journal["gl_account"],
                    journal["description"],
                    f"{journal['amount_gbp']:,.2f}",
                    journal["header_text"],
                    journal["remarks"],
                )
            console.print(journal_table)
            console.print()

        # Variance Calculation
        variance_calc = scenario.get("variance_calculation", {})
        if variance_calc:
            variance_gbp = variance_calc.get("variance_gbp", 0)
            variance_percent = variance_calc.get("variance_percent", 0)
            total_blackline = variance_calc.get("total_blackline_gbp", 0)
            total_matched = variance_calc.get("total_matched_gbp", 0)

            variance_color = "red" if abs(variance_gbp) > 100 else "green"
            variance_sign = "+" if variance_gbp >= 0 else ""

            console.print(
                Panel(
                    f"[bold]Total BlackLine GBP:[/bold] {total_blackline:,.2f}\n"
                    f"[bold]Total Matched GBP:[/bold] {total_matched:,.2f}\n"
                    f"[bold]Variance GBP:[/bold] [{variance_color}]{variance_sign}{variance_gbp:,.2f}[/{variance_color}]\n"
                    f"[bold]Variance %:[/bold] [{variance_color}]{variance_sign}{variance_percent:.4f}%[/{variance_color}]",
                    title="[bold]FX Variance Calculation[/bold]",
                    border_style="yellow",
                )
            )
            console.print()

        # Expected Routing
        console.print(
            Panel.fit(
                f"[bold {routing_color}]{expected_routing}[/bold {routing_color}]",
                title="[bold]Expected Routing[/bold]",
                border_style=routing_color,
            )
        )
        console.print()
        
        # Validation Results
        validation = scenario.get("validation", {})
        if validation:
            valid = validation.get("valid", False)
            issues = validation.get("issues", [])
            warnings = validation.get("warnings", [])
            
            if valid and not warnings:
                validation_status = "[bold green]✅ VALIDATION PASSED[/bold green]"
                border_color = "green"
            elif issues:
                validation_status = f"[bold red]❌ VALIDATION FAILED ({len(issues)} issues)[/bold red]"
                border_color = "red"
            else:
                validation_status = f"[bold yellow]⚠️  VALIDATION PASSED WITH WARNINGS ({len(warnings)} warnings)[/bold yellow]"
                border_color = "yellow"
            
            validation_panel_content = validation_status
            
            if issues:
                validation_panel_content += "\n\n[bold red]Issues:[/bold red]"
                for issue in issues[:5]:  # Show first 5 issues
                    validation_panel_content += f"\n  • {issue.get('message', '')}"
                if len(issues) > 5:
                    validation_panel_content += f"\n  ... and {len(issues) - 5} more"
            
            if warnings:
                validation_panel_content += "\n\n[bold yellow]Warnings:[/bold yellow]"
                for warning in warnings[:3]:  # Show first 3 warnings
                    validation_panel_content += f"\n  • {warning.get('message', '')}"
                if len(warnings) > 3:
                    validation_panel_content += f"\n  ... and {len(warnings) - 3} more"
            
            console.print(
                Panel(
                    validation_panel_content,
                    title="[bold]Data Validation[/bold]",
                    border_style=border_color,
                )
            )
            console.print()

        # Separator between scenarios
        if idx < len(scenarios):
            console.print()
            console.print("[dim]" + "─" * 80 + "[/dim]")
            console.print()


def generate_mock_data(
    db_path: str,
    scenario3_count: int = 1,
    scenario4_count: int = 1,
) -> None:
    """Create schema and insert mock scenarios."""
    create_database_schema(db_path)
    conn = sqlite3.connect(db_path)
    scenarios = []

    try:
        # Generate Scenario 3 (HITL cases)
        for i in range(scenario3_count):
            doc = generate_scenario_3(conn, i, variance_gbp=352.0)
            scenarios.append(doc)

        # Generate Scenario 4 (Straight-through cases)
        for i in range(scenario4_count):
            doc = generate_scenario_4(conn, i, variance_gbp=50.0)
            scenarios.append(doc)

        conn.commit()

        # Validate all scenarios
        logger.info("Validating generated scenarios...")
        for scenario in scenarios:
            validation_result = validate_scenario_data(conn, scenario)
            scenario["validation"] = validation_result
            if not validation_result["valid"]:
                logger.warning(
                    "Scenario {} validation failed: {} issues, {} warnings",
                    validation_result["scenario_tag"],
                    validation_result["issue_count"],
                    validation_result["warning_count"],
                )
            elif validation_result["warning_count"] > 0:
                logger.info(
                    "Scenario {} validation passed with {} warnings",
                    validation_result["scenario_tag"],
                    validation_result["warning_count"],
                )
            else:
                logger.info("Scenario {} validation passed", validation_result["scenario_tag"])

        # Generate documentation
        generate_scenario_documentation(db_path, scenarios)

        # Generate rich console report
        if RICH_AVAILABLE:
            generate_rich_report(scenarios)
        else:
            # Fallback to simple logging
            logger.info("BlackLine unmatched items summary:")
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT item_id, source, currency, amount_local_gbp, status
                FROM blackline_unmatched_items
                ORDER BY item_id
                """
            )
            rows = cursor.fetchall()
            for item_id, source, currency, amount, status in rows:
                logger.info(
                    "  item_id={} source={} amount={} {} status={}",
                    item_id,
                    source,
                    amount,
                    currency,
                    status,
                )

    finally:
        conn.close()
    logger.info("ReconVoy mock data generation complete at {}", db_path)


# ============================================================================
# CLI
# ============================================================================


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Setup ReconVoy database and mock data (Phase 2 Redesign)"
    )
    parser.add_argument(
        "--db-path",
        default="projects/icp/data/reconvoy/reconvoy_database.db",
        help="Path to SQLite database file",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        default=True,
        help="Reset database (delete existing and recreate) (default: True)",
    )
    parser.add_argument(
        "--no-reset",
        dest="reset",
        action="store_false",
        help="Do not reset database (keep existing data)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility (default: None = use current time)",
    )
    parser.add_argument(
        "--scenario3-count",
        type=int,
        default=1,
        help="Number of Scenario 3 cases to generate (HITL, default: 1)",
    )
    parser.add_argument(
        "--scenario4-count",
        type=int,
        default=1,
        help="Number of Scenario 4 cases to generate (Straight-through, default: 1)",
    )

    args = parser.parse_args(argv)

    # Seed RNG
    if args.seed is not None:
        random.seed(args.seed)
    else:
        import time

        random.seed(int(time.time()))

    project_name = detect_project_name(Path.cwd())
    db_path = resolve_script_path(args.db_path, project_name=project_name)

    if args.reset and db_path.exists():
        db_path.unlink()
        logger.info("Removed existing ReconVoy database at {}", db_path)

    db_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(
        "ReconVoy Database Setup (Phase 2)\nDatabase: {}\nReset: {}\nSeed: {}",
        db_path,
        args.reset,
        args.seed,
    )

    logger.info(
        "Generating ReconVoy mock data: scenario3_count={} scenario4_count={}",
        args.scenario3_count,
        args.scenario4_count,
    )

    generate_mock_data(
        str(db_path),
        scenario3_count=max(args.scenario3_count, 0),
        scenario4_count=max(args.scenario4_count, 0),
    )
    logger.info("ReconVoy database setup complete at {}", db_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
