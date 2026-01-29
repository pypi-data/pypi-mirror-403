#!/usr/bin/env python3
"""Setup script for Argus pipeline.

Creates SQLite database, initializes schema, and generates mock data:
- Journal entries (pending and historical)
- Account classifications (chart of accounts)
- Historical journal patterns (for anomaly detection)
- Suppliers and lease agreements
- Anomaly detection results tables

Usage:
    python scripts/setup_argus_database.py [--db-path <path>] [--reset] [--entry-count <n>] [--historical-count <n>]
    uv run -m scripts.setup_argus_database --db-path projects/icp/data/argus/argus_database.db --reset
"""

import sqlite3
import os
import sys
import argparse
import random
import uuid
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

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

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from topaz_agent_kit.utils.path_resolver import resolve_script_path, detect_project_name

# Initialize console for rich output
console = Console() if RICH_AVAILABLE else None


# ============================================================================
# Database Schema Creation
# ============================================================================

def create_database_schema(db_path: str) -> None:
    """Create all database tables."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # ============================================================================
    # Core Tables
    # ============================================================================
    
    # Journal entries table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS journal_entries (
            journal_id TEXT PRIMARY KEY,
            transaction_id TEXT NOT NULL,
            company_code TEXT NOT NULL,
            gl_account TEXT NOT NULL,
            business_area TEXT,
            assignment TEXT,
            document_type TEXT,
            document_date TEXT,
            posting_date TEXT NOT NULL,
            reference TEXT,
            header_text TEXT,
            posting_key TEXT,
            document_currency TEXT DEFAULT 'GBP',
            amount DECIMAL(15, 2) NOT NULL,
            local_currency TEXT DEFAULT 'GBP',
            amount_local DECIMAL(15, 2) NOT NULL,
            tax_code TEXT,
            profit_center TEXT,
            cost_center TEXT,
            clearing_doc_no TEXT,
            clearing_date TEXT,
            plant TEXT,
            "order" TEXT,
            wbs_element TEXT,
            status TEXT DEFAULT 'pending',
            scenario_type TEXT,
            anomaly_type TEXT,
            original_journal_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP,
            run_id TEXT,
            FOREIGN KEY (original_journal_id) REFERENCES journal_entries(journal_id)
        )
    """)
    
    # Account classifications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS account_classifications (
            gl_account TEXT NOT NULL,
            account_name TEXT NOT NULL,
            account_type TEXT NOT NULL,
            company_code TEXT NOT NULL,
            business_area TEXT,
            posting_rules TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (gl_account, company_code)
        )
    """)
    
    # Historical journal patterns table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historical_journal_patterns (
            pattern_id TEXT PRIMARY KEY,
            company_code TEXT NOT NULL,
            gl_account TEXT NOT NULL,
            business_area TEXT,
            description_keywords TEXT,
            avg_amount DECIMAL(15, 2),
            frequency_per_month REAL,
            last_posting_date TEXT,
            sample_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Suppliers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id TEXT PRIMARY KEY,
            supplier_name TEXT NOT NULL,
            company_code TEXT NOT NULL,
            tax_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Lease agreements table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lease_agreements (
            lease_id TEXT PRIMARY KEY,
            company_code TEXT NOT NULL,
            asset_description TEXT NOT NULL,
            lessor_name TEXT NOT NULL,
            lease_start_date TEXT NOT NULL,
            lease_end_date TEXT NOT NULL,
            expected_usage_hours INTEGER,
            rou_account TEXT,
            repairs_account TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # ============================================================================
    # Results Tables
    # ============================================================================
    
    # Anomaly detection results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anomaly_detection_results (
            result_id TEXT PRIMARY KEY,
            journal_id TEXT NOT NULL,
            run_id TEXT,
            anomaly_detected BOOLEAN NOT NULL,
            anomaly_type TEXT,
            reasoning TEXT,
            confidence_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (journal_id) REFERENCES journal_entries(journal_id)
        )
    """)
    
    # Correction suggestions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS correction_suggestions (
            suggestion_id TEXT PRIMARY KEY,
            journal_id TEXT NOT NULL,
            run_id TEXT,
            corrected_entry TEXT,
            correction_reasoning TEXT,
            impact_analysis TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (journal_id) REFERENCES journal_entries(journal_id)
        )
    """)
    
    # Validation results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS validation_results (
            validation_id TEXT PRIMARY KEY,
            journal_id TEXT NOT NULL,
            run_id TEXT,
            human_decision TEXT,
            decision_reasoning TEXT,
            decision_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (journal_id) REFERENCES journal_entries(journal_id)
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_journal_status ON journal_entries(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_journal_company ON journal_entries(company_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_journal_account ON journal_entries(gl_account)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_journal_transaction ON journal_entries(transaction_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_journal_original ON journal_entries(original_journal_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_account_classification ON account_classifications(gl_account, company_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pattern_lookup ON historical_journal_patterns(company_code, gl_account)")
    
    conn.commit()
    conn.close()
    
    if console:
        console.print("[green]✓[/green] Database schema created")


# ============================================================================
# Account Classifications Generation
# ============================================================================

def generate_account_classifications(cursor, company_codes: List[str]) -> Dict[str, Dict[str, Any]]:
    """Generate chart of accounts with 50-100 accounts."""
    account_types = {
        "CAPITAL": ["Fixed Assets", "Asset Clearing", "Capital Expenditure"],
        "REVENUE": ["Repairs & Maintenance", "Operating Expenses", "Consumables", "Utilities"],
        "ROU_ASSET": ["Right of Use Assets", "ROU Asset Clearing"],
        "ASSET": ["Current Assets", "Inventory", "Accounts Receivable"],
        "LIABILITY": ["Accounts Payable", "Accrued Expenses", "Lease Liabilities"],
        "EQUITY": ["Retained Earnings", "Share Capital"]
    }
    
    accounts = {}
    account_counter = 1
    
    # Generate accounts for each company
    for company_code in company_codes:
        # Capital accounts (Fixed Assets)
        for i in range(5):
            gl_account = f"160{100 + i:03d}"
            accounts[gl_account] = {
                "gl_account": gl_account,
                "account_name": f"Fixed Asset Clearing Account {i+1}",
                "account_type": "CAPITAL",
                "company_code": company_code,
                "posting_rules": json.dumps({"exclude_keywords": ["repairs", "maintenance", "consumables", "running"]})
            }
        
        # Revenue accounts (Repairs & Maintenance)
        for i in range(10):
            gl_account = f"700{200 + i:03d}"
            accounts[gl_account] = {
                "gl_account": gl_account,
                "account_name": f"Repairs & Maintenance {i+1}",
                "account_type": "REVENUE",
                "company_code": company_code,
                "posting_rules": json.dumps({"typical_amount_range": [5000, 15000]})
            }
        
        # ROU Asset accounts
        for i in range(3):
            gl_account = f"151{500 + i:03d}"
            accounts[gl_account] = {
                "gl_account": gl_account,
                "account_name": f"ROU Asset {i+1}",
                "account_type": "ROU_ASSET",
                "company_code": company_code,
                "posting_rules": json.dumps({"exclude_keywords": ["repairs", "damages", "excess usage"]})
            }
        
        # Repairs/Damages Expense accounts
        for i in range(5):
            gl_account = f"620{550 + i:03d}"
            accounts[gl_account] = {
                "gl_account": gl_account,
                "account_name": f"Lease Repairs & Damages {i+1}",
                "account_type": "REVENUE",
                "company_code": company_code,
                "posting_rules": json.dumps({"typical_amount_range": [50000, 200000]})
            }
        
        # Other standard accounts
        other_accounts = [
            ("100100", "Cash", "ASSET"),
            ("120100", "Accounts Receivable", "ASSET"),
            ("200100", "Accounts Payable", "LIABILITY"),
            ("300100", "Share Capital", "EQUITY"),
            ("400100", "Retained Earnings", "EQUITY"),
        ]
        
        for gl_account, name, acc_type in other_accounts:
            accounts[gl_account] = {
                "gl_account": gl_account,
                "account_name": name,
                "account_type": acc_type,
                "company_code": company_code,
                "posting_rules": json.dumps({})
            }
    
    # Insert into database
    for account in accounts.values():
        cursor.execute("""
            INSERT OR REPLACE INTO account_classifications 
            (gl_account, account_name, account_type, company_code, posting_rules)
            VALUES (?, ?, ?, ?, ?)
        """, (
            account["gl_account"],
            account["account_name"],
            account["account_type"],
            account["company_code"],
            account["posting_rules"]
        ))
    
    if console:
        console.print(f"[green]✓[/green] Generated {len(accounts)} account classifications")
    
    return accounts


# ============================================================================
# Historical Pattern Generation (Derived from Historical Entries)
# ============================================================================

def generate_historical_patterns_from_entries(cursor) -> None:
    """Derive historical journal patterns from historical entries in journal_entries table.
    
    This function aggregates historical entries to create pattern summaries for quick
    anomaly detection without scanning all historical entries.
    
    Patterns include:
    - Average amount per company/account combination
    - Frequency per month
    - Common description keywords
    - Last posting date
    - Sample count
    """
    # Query historical entries (status = 'processed')
    cursor.execute("""
        SELECT 
            company_code,
            gl_account,
            business_area,
            header_text,
            amount,
            posting_date,
            COUNT(*) as entry_count
        FROM journal_entries
        WHERE status = 'processed' AND scenario_type = 'historical'
        GROUP BY company_code, gl_account, business_area
    """)
    
    historical_data = cursor.fetchall()
    
    if not historical_data:
        if console:
            console.print("[yellow]⚠[/yellow] No historical entries found to generate patterns from")
        return
    
    patterns = []
    
    for row in historical_data:
        company_code, gl_account, business_area, header_text, amount, posting_date, entry_count = row
        
        # Get all entries for this company/account/business_area combination
        cursor.execute("""
            SELECT amount, posting_date, header_text
            FROM journal_entries
            WHERE status = 'processed' 
              AND scenario_type = 'historical'
              AND company_code = ?
              AND gl_account = ?
              AND business_area = ?
        """, (company_code, gl_account, business_area))
        
        entries = cursor.fetchall()
        
        if not entries:
            continue
        
        # Calculate statistics
        amounts = [float(e[0]) for e in entries]
        avg_amount = sum(amounts) / len(amounts) if amounts else 0
        
        # Extract keywords from header texts (simple approach - use common words)
        all_texts = " ".join([e[2] or "" for e in entries]).lower()
        keywords = []
        common_words = ["repairs", "maintenance", "machinery", "equipment", "capital", 
                       "asset", "acquisition", "installation", "lease", "damages"]
        for word in common_words:
            if word in all_texts:
                keywords.append(word)
        description_keywords = ",".join(keywords[:5]) if keywords else "general"
        
        # Calculate frequency per month (approximate)
        dates = [datetime.strptime(e[1], "%Y-%m-%d") for e in entries if e[1]]
        if dates:
            date_range = (max(dates) - min(dates)).days
            frequency_per_month = (len(entries) / max(date_range / 30.0, 1)) if date_range > 0 else len(entries)
            last_posting_date = max(dates).strftime("%Y-%m-%d")
        else:
            frequency_per_month = 0
            last_posting_date = posting_date or datetime.now().strftime("%Y-%m-%d")
        
        pattern_id = str(uuid.uuid4())
        patterns.append({
            "pattern_id": pattern_id,
            "company_code": company_code,
            "gl_account": gl_account,
            "business_area": business_area,
            "description_keywords": description_keywords,
            "avg_amount": avg_amount,
            "frequency_per_month": round(frequency_per_month, 2),
            "last_posting_date": last_posting_date,
            "sample_count": len(entries)
        })
    
    # Insert patterns
    for pattern in patterns:
        cursor.execute("""
            INSERT OR REPLACE INTO historical_journal_patterns
            (pattern_id, company_code, gl_account, business_area, description_keywords,
             avg_amount, frequency_per_month, last_posting_date, sample_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pattern["pattern_id"],
            pattern["company_code"],
            pattern["gl_account"],
            pattern["business_area"],
            pattern["description_keywords"],
            pattern["avg_amount"],
            pattern["frequency_per_month"],
            pattern["last_posting_date"],
            pattern["sample_count"]
        ))
    
    if console:
        console.print(f"[green]✓[/green] Generated {len(patterns)} historical patterns from {sum(p['sample_count'] for p in patterns)} historical entries")


# ============================================================================
# Supporting Data Generation
# ============================================================================

def generate_supporting_data(cursor, company_count: int = 12) -> tuple[List[str], List[Dict[str, Any]], List[Dict[str, Any]], List[str], Dict[str, List[str]]]:
    """Generate company codes, suppliers, lease agreements, business areas, and master data."""
    # Generate company codes
    company_codes = [f"UK{i:02d}" for i in range(1, company_count + 1)]
    
    # Generate business areas (common in SAP systems for segment reporting)
    # Business areas represent operational divisions/units within a company
    business_areas = [
        "BA01", "BA02", "BA03", "BA04", "BA05",
        "BA06", "BA07", "BA08", "BA09", "BA10"
    ]
    
    # Generate master data codes for journal entries
    # Tax codes (VAT codes in UK: V0=Zero rate, V1=Standard rate 20%, V2=Reduced rate 5%)
    tax_codes = ["V0", "V1", "V2", "V3", "V4"]  # V0=Zero, V1=Standard, V2=Reduced, V3/V4=Exempt
    
    # Profit centers (for profitability analysis)
    profit_centers = [f"PC{i:03d}" for i in range(1, 21)]  # PC001-PC020
    
    # Cost centers (for cost allocation)
    cost_centers = [f"CC{i:03d}" for i in range(1, 31)]  # CC001-CC030
    
    # Plants (locations/facilities)
    plants = [f"PLANT{i:02d}" for i in range(1, 11)]  # PLANT01-PLANT10
    
    # Internal orders (for project/cost tracking)
    internal_orders = [f"ORD-{i:05d}" for i in range(10001, 10051)]  # ORD-10001 to ORD-10050
    
    # WBS elements (Work Breakdown Structure for project accounting)
    wbs_elements = [f"WBS-{i:04d}" for i in range(1, 51)]  # WBS-0001 to WBS-0050
    
    master_data = {
        "tax_codes": tax_codes,
        "profit_centers": profit_centers,
        "cost_centers": cost_centers,
        "plants": plants,
        "internal_orders": internal_orders,
        "wbs_elements": wbs_elements
    }
    
    # Generate suppliers
    supplier_names = [
        "North Sea Equipment Ltd", "Maritime Services UK", "Offshore Solutions Ltd",
        "Industrial Supplies Co", "Engineering Partners Ltd", "Marine Equipment Corp",
        "Technical Services Group", "Asset Management UK", "Maintenance Experts Ltd",
        "Equipment Leasing Co", "Industrial Maintenance Ltd", "Maritime Equipment Ltd",
        "Offshore Maintenance Co", "Engineering Services Ltd", "Asset Solutions UK",
        "Technical Equipment Co", "Marine Services Ltd", "Industrial Partners Ltd",
        "Equipment Services Group", "Maintenance Solutions Ltd", "Offshore Equipment Co",
        "Maritime Solutions Ltd", "Engineering Equipment Co", "Asset Services Ltd",
        "Technical Maintenance Co", "Marine Partners Ltd", "Industrial Equipment Ltd",
        "Equipment Solutions UK", "Maintenance Services Ltd", "Offshore Partners Co"
    ]
    
    suppliers = []
    for i, company_code in enumerate(company_codes):
        for j in range(2):  # 2 suppliers per company
            supplier_id = str(uuid.uuid4())
            supplier_name = random.choice(supplier_names)
            suppliers.append({
                "supplier_id": supplier_id,
                "supplier_name": supplier_name,
                "company_code": company_code,
                "tax_id": f"GB{random.randint(100000000, 999999999)}"
            })
    
    # Generate lease agreements
    asset_descriptions = [
        "Gas Turbine Generator", "Diesel Engine", "Compressor Unit",
        "Pump System", "Control Panel", "HVAC System", "Power Distribution Unit",
        "Water Treatment System", "Fire Suppression System", "Communication Equipment"
    ]
    
    lessor_names = [
        "Global Equipment Leasing", "Industrial Lease Partners", "Asset Finance Solutions",
        "Equipment Rental Corp", "Lease Management Ltd", "Capital Equipment Leasing"
    ]
    
    lease_agreements = []
    for i, company_code in enumerate(company_codes):
        for j in range(random.randint(1, 2)):  # 1-2 leases per company
            lease_id = str(uuid.uuid4())
            start_date = datetime.now() - timedelta(days=random.randint(365, 1095))
            end_date = start_date + timedelta(days=random.randint(1095, 1825))
            
            lease_agreements.append({
                "lease_id": lease_id,
                "company_code": company_code,
                "asset_description": random.choice(asset_descriptions),
                "lessor_name": random.choice(lessor_names),
                "lease_start_date": start_date.strftime("%Y-%m-%d"),
                "lease_end_date": end_date.strftime("%Y-%m-%d"),
                "expected_usage_hours": random.randint(5000, 15000),
                "rou_account": f"151{500 + random.randint(0, 2):03d}",
                "repairs_account": f"620{550 + random.randint(0, 4):03d}"
            })
    
    # Insert suppliers
    for supplier in suppliers:
        cursor.execute("""
            INSERT OR REPLACE INTO suppliers (supplier_id, supplier_name, company_code, tax_id)
            VALUES (?, ?, ?, ?)
        """, (supplier["supplier_id"], supplier["supplier_name"], 
              supplier["company_code"], supplier["tax_id"]))
    
    # Insert lease agreements
    for lease in lease_agreements:
        cursor.execute("""
            INSERT OR REPLACE INTO lease_agreements
            (lease_id, company_code, asset_description, lessor_name, lease_start_date,
             lease_end_date, expected_usage_hours, rou_account, repairs_account)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lease["lease_id"], lease["company_code"], lease["asset_description"],
            lease["lessor_name"], lease["lease_start_date"], lease["lease_end_date"],
            lease["expected_usage_hours"], lease["rou_account"], lease["repairs_account"]
        ))
    
    if console:
        console.print(f"[green]✓[/green] Generated {len(company_codes)} company codes")
        console.print(f"[green]✓[/green] Generated {len(suppliers)} suppliers")
        console.print(f"[green]✓[/green] Generated {len(lease_agreements)} lease agreements")
        console.print(f"[green]✓[/green] Generated {len(business_areas)} business areas")
        console.print(f"[green]✓[/green] Generated master data: {len(tax_codes)} tax codes, {len(profit_centers)} profit centers, {len(cost_centers)} cost centers")
    
    return company_codes, suppliers, lease_agreements, business_areas, master_data


# ============================================================================
# Journal Entry Generation
# ============================================================================

def generate_journal_entries(
    cursor,
    company_codes: List[str],
    accounts: Dict[str, Dict[str, Any]],
    suppliers: List[Dict[str, Any]],
    lease_agreements: List[Dict[str, Any]],
    business_areas: List[str],
    master_data: Dict[str, List[str]],
    entry_count: int = 6,
    historical_count: int = 25,
    correct_pct: float = 33.33,
    scenario1_pct: float = 33.33,
    scenario2_pct: float = 33.34
) -> None:
    """Generate journal entries with anomalies.
    
    Args:
        entry_count: Number of pending journal transactions (pairs) to generate
        historical_count: Number of historical entries per company/account combination
        correct_pct: Percentage of correct entries (default: 33.33)
        scenario1_pct: Percentage of Scenario 1 entries (Capital/Revenue misclassification) (default: 33.33)
        scenario2_pct: Percentage of Scenario 2 entries (Lease/ROU misclassification) (default: 33.34)
    """
    entries = []
    # run_id should be NULL for new pending entries so they can be picked up by the pipeline
    # The pipeline will set run_id when it processes the entries
    run_id = None
    
    # Validate distribution percentages sum to 100
    total_pct = correct_pct + scenario1_pct + scenario2_pct
    if abs(total_pct - 100.0) > 0.01:  # Allow small floating point differences
        raise ValueError(f"Distribution percentages must sum to 100.0, got {total_pct}")
    
    # Scenario 1: Capital vs Revenue entries
    scenario1_descriptions = [
        "Running R&M to machinery",
        "Fan Belts, Engine Oil",
        "Repairs to compressor unit",
        "Maintenance - Pump system",
        "Consumables for equipment",
        "Running repairs to generator",
        "Lubricants and filters",
        "Maintenance services",
        "Equipment consumables",
        "Running maintenance"
    ]
    
    # Scenario 2: Lease/ROU entries
    scenario2_descriptions = [
        "Repairs - Lease Equipment (Gas Turbine, used beyond hours)",
        "Lease Damages",
        "Excess usage charges - Lease equipment",
        "Repairs to leased asset",
        "Lease equipment damages",
        "Excess hours - Lease equipment",
        "Lease asset repairs",
        "Damages to leased equipment"
    ]
    
    # Calculate counts based on percentages
    correct_count = int(round(entry_count * correct_pct / 100.0))
    scenario1_count = int(round(entry_count * scenario1_pct / 100.0))
    scenario2_count = entry_count - correct_count - scenario1_count  # Ensure total matches entry_count
    
    # Generate correct entries
    revenue_accounts = [acc for acc in accounts.values() 
                       if acc["account_type"] == "REVENUE" and "Repairs" in acc["account_name"]]
    
    # Pre-filter companies that have required accounts and AP accounts
    valid_companies_correct = []
    for company_code in company_codes:
        company_revenue_accounts = [acc for acc in revenue_accounts if acc["company_code"] == company_code]
        ap_accounts = [acc for acc in accounts.values() 
                      if acc["account_type"] == "LIABILITY" and "Payable" in acc["account_name"] 
                      and acc["company_code"] == company_code]
        if not ap_accounts:
            ap_accounts = [acc for acc in accounts.values() 
                          if acc["account_type"] == "LIABILITY" and acc["company_code"] == company_code]
        if company_revenue_accounts and ap_accounts:
            valid_companies_correct.append(company_code)
    
    if not valid_companies_correct:
        if console:
            console.print("[red]✗[/red] Error: No companies have both revenue accounts and AP accounts for correct entries")
        else:
            print("Error: No companies have both revenue accounts and AP accounts for correct entries")
        return
    
    correct_generated = 0
    max_attempts = max(correct_count * 100, 1000)  # Much higher limit to ensure we can generate all entries
    attempts = 0
    
    while correct_generated < correct_count and attempts < max_attempts:
        attempts += 1
        company_code = random.choice(valid_companies_correct)
        company_revenue_accounts = [acc for acc in revenue_accounts if acc["company_code"] == company_code]
        
        account = random.choice(company_revenue_accounts)
        
        # Generate transaction ID shared by both debit and credit entries
        transaction_id = str(uuid.uuid4())
        # Generate document reference shared by both debit and credit
        doc_reference = f"REF-{random.randint(10000, 99999)}"
        doc_date = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
        posting_date = datetime.now().strftime("%Y-%m-%d")
        header_text = random.choice(scenario1_descriptions)
        amount = round(random.uniform(5000, 15000), 2)
        business_area = random.choice(business_areas)  # Use predefined business areas
        assignment = random.choice(suppliers)["supplier_name"] if suppliers else "Supplier"
        
        # Generate additional SAP fields
        tax_code = random.choice(master_data["tax_codes"])
        profit_center = random.choice(master_data["profit_centers"])
        cost_center = random.choice(master_data["cost_centers"])
        plant = random.choice(master_data["plants"])
        internal_order = random.choice(master_data["internal_orders"])
        wbs_element = random.choice(master_data["wbs_elements"])
        
        # Get Accounts Payable account for credit side
        ap_accounts = [acc for acc in accounts.values() 
                      if acc["account_type"] == "LIABILITY" and "Payable" in acc["account_name"] 
                      and acc["company_code"] == company_code]
        if not ap_accounts:
            # Fallback to any liability account
            ap_accounts = [acc for acc in accounts.values() 
                          if acc["account_type"] == "LIABILITY" and acc["company_code"] == company_code]
        if not ap_accounts:
            continue  # Skip if no AP account available
        
        ap_account = random.choice(ap_accounts)
        
        # Debit entry (expense account)
        debit_entry = {
            "journal_id": str(uuid.uuid4()),
            "transaction_id": transaction_id,
            "company_code": company_code,
            "gl_account": account["gl_account"],
            "business_area": business_area,
            "assignment": assignment,
            "document_type": "KR",
            "document_date": doc_date,
            "posting_date": posting_date,
            "reference": doc_reference,
            "header_text": header_text,
            "posting_key": "40",  # Debit
            "amount": amount,
            "amount_local": amount,
            "tax_code": tax_code,
            "profit_center": profit_center,
            "cost_center": cost_center,
            "plant": plant,
            "order": internal_order,
            "wbs_element": wbs_element,
            "status": "pending",
            "scenario_type": "correct",
            "anomaly_type": None,
            "run_id": run_id
        }
        
        # Credit entry (Accounts Payable) - typically has fewer segment fields
        credit_entry = {
            "journal_id": str(uuid.uuid4()),
            "transaction_id": transaction_id,
            "company_code": company_code,
            "gl_account": ap_account["gl_account"],
            "business_area": business_area,
            "assignment": assignment,
            "document_type": "KR",
            "document_date": doc_date,
            "posting_date": posting_date,
            "reference": doc_reference,
            "header_text": header_text,
            "posting_key": "50",  # Credit
            "amount": amount,
            "amount_local": amount,
            "tax_code": tax_code,  # Same tax code for both entries
            "profit_center": profit_center,  # Same profit center
            "cost_center": None,  # AP accounts typically don't have cost center
            "plant": None,  # AP accounts typically don't have plant
            "order": None,  # AP accounts typically don't have internal order
            "wbs_element": None,  # AP accounts typically don't have WBS
            "status": "pending",
            "scenario_type": "correct",
            "anomaly_type": None,
            "run_id": run_id
        }
        
        entries.append(debit_entry)
        entries.append(credit_entry)
        correct_generated += 1
    
    # Warn if we didn't generate all required entries
    if correct_generated < correct_count:
        if console:
            console.print(f"[yellow]⚠[/yellow] Warning: Only generated {correct_generated} correct transactions (target: {correct_count})")
        else:
            print(f"Warning: Only generated {correct_generated} correct transactions (target: {correct_count})")
    
    # Generate Scenario 1 anomalies (Capital/Revenue misclassification)
    capital_accounts = [acc for acc in accounts.values() 
                       if acc["account_type"] == "CAPITAL"]
    
    # Pre-filter companies that have both capital and revenue accounts
    valid_companies_scenario1 = []
    for company_code in company_codes:
        company_capital_accounts = [acc for acc in capital_accounts if acc["company_code"] == company_code]
        company_revenue_accounts = [acc for acc in revenue_accounts if acc["company_code"] == company_code]
        ap_accounts = [acc for acc in accounts.values() 
                      if acc["account_type"] == "LIABILITY" and "Payable" in acc["account_name"] 
                      and acc["company_code"] == company_code]
        if not ap_accounts:
            ap_accounts = [acc for acc in accounts.values() 
                          if acc["account_type"] == "LIABILITY" and acc["company_code"] == company_code]
        if company_capital_accounts and company_revenue_accounts and ap_accounts:
            valid_companies_scenario1.append(company_code)
    
    if not valid_companies_scenario1:
        if console:
            console.print("[red]✗[/red] Error: No companies have capital, revenue, and AP accounts for Scenario 1 entries")
        else:
            print("Error: No companies have capital, revenue, and AP accounts for Scenario 1 entries")
        return
    
    scenario1_generated = 0
    max_attempts = max(scenario1_count * 100, 1000)  # Much higher limit to ensure we can generate all entries
    attempts = 0
    
    while scenario1_generated < scenario1_count and attempts < max_attempts:
        attempts += 1
        company_code = random.choice(valid_companies_scenario1)
        company_capital_accounts = [acc for acc in capital_accounts if acc["company_code"] == company_code]
        account = random.choice(company_capital_accounts)
        
        # Find correct revenue account for this company
        company_revenue_accounts = [acc for acc in revenue_accounts 
                                   if acc["company_code"] == company_code]
        
        correct_account = random.choice(company_revenue_accounts)
        
        # Generate transaction ID shared by both debit and credit entries
        transaction_id = str(uuid.uuid4())
        # Generate document reference shared by both debit and credit
        doc_reference = f"REF-{random.randint(10000, 99999)}"
        doc_date = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
        posting_date = datetime.now().strftime("%Y-%m-%d")
        header_text = random.choice(scenario1_descriptions)
        amount = round(random.uniform(5000, 20000), 2)  # Revenue amounts posted to capital
        business_area = random.choice(business_areas)  # Use predefined business areas
        assignment = random.choice(suppliers)["supplier_name"] if suppliers else "Supplier"
        
        # Generate additional SAP fields
        tax_code = random.choice(master_data["tax_codes"])
        profit_center = random.choice(master_data["profit_centers"])
        cost_center = random.choice(master_data["cost_centers"])
        plant = random.choice(master_data["plants"])
        internal_order = random.choice(master_data["internal_orders"])
        wbs_element = random.choice(master_data["wbs_elements"])
        
        # Get Accounts Payable account for credit side
        ap_accounts = [acc for acc in accounts.values() 
                      if acc["account_type"] == "LIABILITY" and "Payable" in acc["account_name"] 
                      and acc["company_code"] == company_code]
        if not ap_accounts:
            ap_accounts = [acc for acc in accounts.values() 
                          if acc["account_type"] == "LIABILITY" and acc["company_code"] == company_code]
        if not ap_accounts:
            continue
        
        ap_account = random.choice(ap_accounts)
        
        # Debit entry (wrong account - capital instead of revenue)
        debit_entry = {
            "journal_id": str(uuid.uuid4()),
            "transaction_id": transaction_id,
            "company_code": company_code,
            "gl_account": account["gl_account"],  # Wrong account (capital)
            "business_area": business_area,
            "assignment": assignment,
            "document_type": "KR",
            "document_date": doc_date,
            "posting_date": posting_date,
            "reference": doc_reference,
            "header_text": header_text,
            "posting_key": "40",  # Debit
            "amount": amount,
            "amount_local": amount,
            "tax_code": tax_code,
            "profit_center": profit_center,
            "cost_center": cost_center,
            "plant": plant,
            "order": internal_order,
            "wbs_element": wbs_element,
            "status": "pending",
            "scenario_type": "scenario1",
            "anomaly_type": "CAPITAL_REVENUE_MISCLASSIFICATION",
            "run_id": run_id,
            "_correct_account": correct_account["gl_account"]  # Store for validation
        }
        
        # Credit entry (Accounts Payable)
        credit_entry = {
            "journal_id": str(uuid.uuid4()),
            "transaction_id": transaction_id,
            "company_code": company_code,
            "gl_account": ap_account["gl_account"],
            "business_area": business_area,
            "assignment": assignment,
            "document_type": "KR",
            "document_date": doc_date,
            "posting_date": posting_date,
            "reference": doc_reference,
            "header_text": header_text,
            "posting_key": "50",  # Credit
            "amount": amount,
            "amount_local": amount,
            "tax_code": tax_code,
            "profit_center": profit_center,
            "cost_center": None,
            "plant": None,
            "order": None,
            "wbs_element": None,
            "status": "pending",
            "scenario_type": "scenario1",
            "anomaly_type": "CAPITAL_REVENUE_MISCLASSIFICATION",
            "run_id": run_id,
            "_correct_account": correct_account["gl_account"]  # Store for validation
        }
        
        entries.append(debit_entry)
        entries.append(credit_entry)
        scenario1_generated += 1
    
    # Warn if we didn't generate all required entries
    if scenario1_generated < scenario1_count:
        if console:
            console.print(f"[yellow]⚠[/yellow] Warning: Only generated {scenario1_generated} Scenario 1 transactions (target: {scenario1_count})")
        else:
            print(f"Warning: Only generated {scenario1_generated} Scenario 1 transactions (target: {scenario1_count})")
    
    # Generate Scenario 2 anomalies (Lease/ROU misclassification)
    rou_accounts = [acc for acc in accounts.values() 
                   if acc["account_type"] == "ROU_ASSET"]
    
    # Pre-filter companies that have ROU accounts, lease agreements, and AP accounts
    valid_companies_scenario2 = []
    for company_code in company_codes:
        company_leases = [lease for lease in lease_agreements if lease["company_code"] == company_code]
        company_rou_accounts = [acc for acc in rou_accounts if acc["company_code"] == company_code]
        ap_accounts = [acc for acc in accounts.values() 
                      if acc["account_type"] == "LIABILITY" and "Payable" in acc["account_name"] 
                      and acc["company_code"] == company_code]
        if not ap_accounts:
            ap_accounts = [acc for acc in accounts.values() 
                          if acc["account_type"] == "LIABILITY" and acc["company_code"] == company_code]
        if company_leases and company_rou_accounts and ap_accounts:
            valid_companies_scenario2.append(company_code)
    
    if not valid_companies_scenario2:
        if console:
            console.print("[red]✗[/red] Error: No companies have ROU accounts, lease agreements, and AP accounts for Scenario 2 entries")
        else:
            print("Error: No companies have ROU accounts, lease agreements, and AP accounts for Scenario 2 entries")
        return
    
    scenario2_generated = 0
    max_attempts = max(scenario2_count * 100, 1000)  # Much higher limit to ensure we can generate all entries
    attempts = 0
    
    while scenario2_generated < scenario2_count and attempts < max_attempts:
        attempts += 1
        company_code = random.choice(valid_companies_scenario2)
        
        # Find lease agreement for this company
        company_leases = [lease for lease in lease_agreements if lease["company_code"] == company_code]
        # Find ROU accounts for this company
        company_rou_accounts = [acc for acc in rou_accounts if acc["company_code"] == company_code]
        
        lease = random.choice(company_leases)
        account = random.choice(company_rou_accounts)
        
        # Generate transaction ID shared by both debit and credit entries
        transaction_id = str(uuid.uuid4())
        # Generate document reference shared by both debit and credit
        doc_reference = f"REF-{random.randint(10000, 99999)}"
        doc_date = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
        posting_date = datetime.now().strftime("%Y-%m-%d")
        header_text = random.choice(scenario2_descriptions)
        amount = round(random.uniform(50000, 200000), 2)  # Large amounts for lease damages
        business_area = random.choice(business_areas)  # Use predefined business areas
        assignment = lease["lessor_name"]
        
        # Generate additional SAP fields
        tax_code = random.choice(master_data["tax_codes"])
        profit_center = random.choice(master_data["profit_centers"])
        cost_center = random.choice(master_data["cost_centers"])
        plant = random.choice(master_data["plants"])
        internal_order = random.choice(master_data["internal_orders"])
        wbs_element = random.choice(master_data["wbs_elements"])
        
        # Get Accounts Payable account for credit side
        ap_accounts = [acc for acc in accounts.values() 
                      if acc["account_type"] == "LIABILITY" and "Payable" in acc["account_name"] 
                      and acc["company_code"] == company_code]
        if not ap_accounts:
            ap_accounts = [acc for acc in accounts.values() 
                          if acc["account_type"] == "LIABILITY" and acc["company_code"] == company_code]
        if not ap_accounts:
            continue
        
        ap_account = random.choice(ap_accounts)
        
        # Debit entry (wrong account - ROU instead of repairs expense)
        debit_entry = {
            "journal_id": str(uuid.uuid4()),
            "transaction_id": transaction_id,
            "company_code": company_code,
            "gl_account": account["gl_account"],  # Wrong account (ROU)
            "business_area": business_area,
            "assignment": assignment,
            "document_type": "KR",
            "document_date": doc_date,
            "posting_date": posting_date,
            "reference": doc_reference,
            "header_text": header_text,
            "posting_key": "40",  # Debit
            "amount": amount,
            "amount_local": amount,
            "tax_code": tax_code,
            "profit_center": profit_center,
            "cost_center": cost_center,
            "plant": plant,
            "order": internal_order,
            "wbs_element": wbs_element,
            "status": "pending",
            "scenario_type": "scenario2",
            "anomaly_type": "LEASE_ROU_MISCLASSIFICATION",
            "run_id": run_id,
            "_correct_account": lease["repairs_account"],  # Store for validation
            "_lease_id": lease["lease_id"]
        }
        
        # Credit entry (Accounts Payable)
        credit_entry = {
            "journal_id": str(uuid.uuid4()),
            "transaction_id": transaction_id,
            "company_code": company_code,
            "gl_account": ap_account["gl_account"],
            "business_area": business_area,
            "assignment": assignment,
            "document_type": "KR",
            "document_date": doc_date,
            "posting_date": posting_date,
            "reference": doc_reference,
            "header_text": header_text,
            "posting_key": "50",  # Credit
            "amount": amount,
            "amount_local": amount,
            "tax_code": tax_code,
            "profit_center": profit_center,
            "cost_center": None,
            "plant": None,
            "order": None,
            "wbs_element": None,
            "status": "pending",
            "scenario_type": "scenario2",
            "anomaly_type": "LEASE_ROU_MISCLASSIFICATION",
            "run_id": run_id,
            "_correct_account": lease["repairs_account"],  # Store for validation
            "_lease_id": lease["lease_id"]
        }
        
        entries.append(debit_entry)
        entries.append(credit_entry)
        scenario2_generated += 1
    
    # Warn if we didn't generate all required entries
    if scenario2_generated < scenario2_count:
        if console:
            console.print(f"[yellow]⚠[/yellow] Warning: Only generated {scenario2_generated} Scenario 2 transactions (target: {scenario2_count})")
        else:
            print(f"Warning: Only generated {scenario2_generated} Scenario 2 transactions (target: {scenario2_count})")
    
    # Insert entries
    for entry in entries:
        cursor.execute("""
            INSERT OR REPLACE INTO journal_entries
            (journal_id, transaction_id, company_code, gl_account, business_area, assignment, document_type,
             document_date, posting_date, reference, header_text, posting_key, amount, amount_local,
             tax_code, profit_center, cost_center, plant, "order", wbs_element,
             status, scenario_type, anomaly_type, run_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry["journal_id"], entry["transaction_id"], entry["company_code"], entry["gl_account"],
            entry["business_area"], entry["assignment"], entry["document_type"],
            entry["document_date"], entry["posting_date"], entry["reference"],
            entry["header_text"], entry["posting_key"], entry["amount"],
            entry["amount_local"], entry.get("tax_code"), entry.get("profit_center"),
            entry.get("cost_center"), entry.get("plant"), entry.get("order"),
            entry.get("wbs_element"), entry["status"], entry["scenario_type"],
            entry["anomaly_type"], entry["run_id"]
        ))
    
    # Generate historical entries for pattern matching
    historical_entries = []
    for company_code in company_codes:
        # Get AP account for this company for credit side
        company_ap_accounts = [acc for acc in accounts.values() 
                              if acc["account_type"] == "LIABILITY" and "Payable" in acc["account_name"] 
                              and acc["company_code"] == company_code]
        if not company_ap_accounts:
            company_ap_accounts = [acc for acc in accounts.values() 
                                  if acc["account_type"] == "LIABILITY" and acc["company_code"] == company_code]
        if not company_ap_accounts:
            continue  # Skip if no AP account
        
        ap_account = company_ap_accounts[0]  # Use same AP account for all historical entries
        
        for account in accounts.values():
            if account["company_code"] != company_code:
                continue
            
            # Skip AP accounts for debit side (they're used for credit)
            if account["account_type"] == "LIABILITY" and "Payable" in account["account_name"]:
                continue
            
            # Generate 20-30 historical entries per company/account combination
            for i in range(historical_count):
                # Generate transaction ID shared by both debit and credit entries
                transaction_id = str(uuid.uuid4())
                doc_reference = f"REF-HIST-{random.randint(10000, 99999)}"
                doc_date = (datetime.now() - timedelta(days=random.randint(1, 180))).strftime("%Y-%m-%d")
                posting_date = (datetime.now() - timedelta(days=random.randint(1, 180))).strftime("%Y-%m-%d")
                header_text = f"Historical entry {i+1}"
                amount = round(random.uniform(1000, 50000), 2)
                business_area = random.choice(business_areas)  # Use predefined business areas
                assignment = random.choice(suppliers)["supplier_name"] if suppliers else "Supplier"
                
                # Generate additional SAP fields for historical entries
                tax_code = random.choice(master_data["tax_codes"])
                profit_center = random.choice(master_data["profit_centers"])
                cost_center = random.choice(master_data["cost_centers"])
                plant = random.choice(master_data["plants"])
                internal_order = random.choice(master_data["internal_orders"])
                wbs_element = random.choice(master_data["wbs_elements"])
                
                # Debit entry
                debit_entry = {
                    "journal_id": str(uuid.uuid4()),
                    "transaction_id": transaction_id,
                    "company_code": company_code,
                    "gl_account": account["gl_account"],
                    "business_area": business_area,
                    "assignment": assignment,
                    "document_type": "KR",
                    "document_date": doc_date,
                    "posting_date": posting_date,
                    "reference": doc_reference,
                    "header_text": header_text,
                    "posting_key": "40",  # Debit
                    "amount": amount,
                    "amount_local": amount,
                    "tax_code": tax_code,
                    "profit_center": profit_center,
                    "cost_center": cost_center,
                    "plant": plant,
                    "order": internal_order,
                    "wbs_element": wbs_element,
                    "status": "processed",
                    "scenario_type": "historical",
                    "anomaly_type": None,
                    "run_id": None
                }
                
                # Credit entry
                credit_entry = {
                    "journal_id": str(uuid.uuid4()),
                    "transaction_id": transaction_id,
                    "company_code": company_code,
                    "gl_account": ap_account["gl_account"],
                    "business_area": business_area,
                    "assignment": assignment,
                    "document_type": "KR",
                    "document_date": doc_date,
                    "posting_date": posting_date,
                    "reference": doc_reference,
                    "header_text": header_text,
                    "posting_key": "50",  # Credit
                    "amount": amount,
                    "amount_local": amount,
                    "tax_code": tax_code,
                    "profit_center": profit_center,
                    "cost_center": None,
                    "plant": None,
                    "order": None,
                    "wbs_element": None,
                    "status": "processed",
                    "scenario_type": "historical",
                    "anomaly_type": None,
                    "run_id": None
                }
                
                historical_entries.append(debit_entry)
                historical_entries.append(credit_entry)
    
    # Insert historical entries
    for entry in historical_entries:
        cursor.execute("""
            INSERT OR REPLACE INTO journal_entries
            (journal_id, transaction_id, company_code, gl_account, business_area, assignment, document_type,
             document_date, posting_date, reference, header_text, posting_key, amount, amount_local,
             tax_code, profit_center, cost_center, plant, "order", wbs_element,
             status, scenario_type, anomaly_type, run_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry["journal_id"], entry["transaction_id"], entry["company_code"], entry["gl_account"],
            entry["business_area"], entry["assignment"], entry["document_type"],
            entry["document_date"], entry["posting_date"], entry["reference"],
            entry["header_text"], entry["posting_key"], entry["amount"],
            entry["amount_local"], entry.get("tax_code"), entry.get("profit_center"),
            entry.get("cost_center"), entry.get("plant"), entry.get("order"),
            entry.get("wbs_element"), entry["status"], entry["scenario_type"],
            entry["anomaly_type"], entry["run_id"]
        ))
    
    if console:
        # Count transactions (each transaction has 2 entries: debit + credit)
        correct_transactions = len([e for e in entries if e.get("scenario_type") == "correct" and e.get("posting_key") == "40"])
        scenario1_transactions = len([e for e in entries if e.get("scenario_type") == "scenario1" and e.get("posting_key") == "40"])
        scenario2_transactions = len([e for e in entries if e.get("scenario_type") == "scenario2" and e.get("posting_key") == "40"])
        historical_transactions = len([e for e in historical_entries if e.get("posting_key") == "40"])
        
        console.print(f"[green]✓[/green] Generated {len(entries)} pending journal entry lines ({len(entries)//2} transactions)")
        console.print(f"[green]✓[/green] Generated {len(historical_entries)} historical journal entry lines ({historical_transactions} transactions)")
        console.print(f"  - Correct transactions: {correct_transactions} (target: {correct_count}) - {correct_transactions * 2} entry lines")
        console.print(f"  - Scenario 1 anomalies: {scenario1_transactions} (target: {scenario1_count}) - {scenario1_transactions * 2} entry lines")
        console.print(f"  - Scenario 2 anomalies: {scenario2_transactions} (target: {scenario2_count}) - {scenario2_transactions * 2} entry lines")
        console.print(f"  Note: Each transaction has 2 entries (debit + credit)")


# ============================================================================
# Read Existing Data from Database
# ============================================================================

def read_existing_data(cursor) -> tuple[List[str], Dict[str, Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[str], Dict[str, List[str]]]:
    """Read existing data from database to use for generating new pending entries.
    
    Returns:
        Tuple of (company_codes, accounts, suppliers, lease_agreements, business_areas, master_data)
    """
    # Read company codes from account_classifications
    cursor.execute("SELECT DISTINCT company_code FROM account_classifications ORDER BY company_code")
    company_codes = [row[0] for row in cursor.fetchall()]
    
    if not company_codes:
        raise ValueError("No company codes found in database. Please run with --reset first to initialize the database.")
    
    # Read account classifications
    cursor.execute("""
        SELECT gl_account, account_name, account_type, company_code, posting_rules
        FROM account_classifications
    """)
    accounts = {}
    for row in cursor.fetchall():
        gl_account, account_name, account_type, company_code, posting_rules = row
        key = f"{gl_account}_{company_code}"
        accounts[key] = {
            "gl_account": gl_account,
            "account_name": account_name,
            "account_type": account_type,
            "company_code": company_code,
            "posting_rules": posting_rules
        }
    
    # Read suppliers
    cursor.execute("SELECT supplier_id, supplier_name, company_code, tax_id FROM suppliers")
    suppliers = []
    for row in cursor.fetchall():
        suppliers.append({
            "supplier_id": row[0],
            "supplier_name": row[1],
            "company_code": row[2],
            "tax_id": row[3]
        })
    
    # Read lease agreements
    cursor.execute("""
        SELECT lease_id, company_code, asset_description, lessor_name, lease_start_date,
               lease_end_date, expected_usage_hours, rou_account, repairs_account
        FROM lease_agreements
    """)
    lease_agreements = []
    for row in cursor.fetchall():
        lease_agreements.append({
            "lease_id": row[0],
            "company_code": row[1],
            "asset_description": row[2],
            "lessor_name": row[3],
            "lease_start_date": row[4],
            "lease_end_date": row[5],
            "expected_usage_hours": row[6],
            "rou_account": row[7],
            "repairs_account": row[8]
        })
    
    # Extract business areas from existing journal entries
    cursor.execute("SELECT DISTINCT business_area FROM journal_entries WHERE business_area IS NOT NULL")
    business_areas = [row[0] for row in cursor.fetchall()]
    
    # If no business areas found, use defaults
    if not business_areas:
        business_areas = [
            "BA01", "BA02", "BA03", "BA04", "BA05",
            "BA06", "BA07", "BA08", "BA09", "BA10"
        ]
    
    # Extract master data from existing journal entries
    cursor.execute("SELECT DISTINCT tax_code FROM journal_entries WHERE tax_code IS NOT NULL")
    tax_codes = [row[0] for row in cursor.fetchall()] or ["V0", "V1", "V2", "V3", "V4"]
    
    cursor.execute("SELECT DISTINCT profit_center FROM journal_entries WHERE profit_center IS NOT NULL")
    profit_centers = [row[0] for row in cursor.fetchall()] or [f"PC{i:03d}" for i in range(1, 21)]
    
    cursor.execute("SELECT DISTINCT cost_center FROM journal_entries WHERE cost_center IS NOT NULL")
    cost_centers = [row[0] for row in cursor.fetchall()] or [f"CC{i:03d}" for i in range(1, 31)]
    
    cursor.execute("SELECT DISTINCT plant FROM journal_entries WHERE plant IS NOT NULL")
    plants = [row[0] for row in cursor.fetchall()] or [f"PLANT{i:02d}" for i in range(1, 11)]
    
    cursor.execute("SELECT DISTINCT \"order\" FROM journal_entries WHERE \"order\" IS NOT NULL")
    internal_orders = [row[0] for row in cursor.fetchall()] or [f"ORD-{i:05d}" for i in range(10001, 10051)]
    
    cursor.execute("SELECT DISTINCT wbs_element FROM journal_entries WHERE wbs_element IS NOT NULL")
    wbs_elements = [row[0] for row in cursor.fetchall()] or [f"WBS-{i:04d}" for i in range(1, 51)]
    
    master_data = {
        "tax_codes": tax_codes,
        "profit_centers": profit_centers,
        "cost_centers": cost_centers,
        "plants": plants,
        "internal_orders": internal_orders,
        "wbs_elements": wbs_elements
    }
    
    # Convert accounts dict to format expected by generate_journal_entries
    # The function expects a dict keyed by gl_account (same as generate_account_classifications)
    # If multiple companies have the same gl_account, the last one wins (same behavior as original)
    # This is fine because generate_journal_entries filters by company_code when using accounts
    accounts_dict = {}
    for key, account in accounts.items():
        # Use gl_account as key (matches structure from generate_account_classifications)
        accounts_dict[account["gl_account"]] = account
    
    if console:
        console.print(f"[green]✓[/green] Read {len(company_codes)} company codes from database")
        console.print(f"[green]✓[/green] Read {len(accounts_dict)} account classifications from database")
        console.print(f"[green]✓[/green] Read {len(suppliers)} suppliers from database")
        console.print(f"[green]✓[/green] Read {len(lease_agreements)} lease agreements from database")
    
    return company_codes, accounts_dict, suppliers, lease_agreements, business_areas, master_data


def generate_pending_entries_only(
    cursor,
    company_codes: List[str],
    accounts: Dict[str, Dict[str, Any]],
    suppliers: List[Dict[str, Any]],
    lease_agreements: List[Dict[str, Any]],
    business_areas: List[str],
    master_data: Dict[str, List[str]],
    entry_count: int = 6,
    correct_pct: float = 33.33,
    scenario1_pct: float = 33.33,
    scenario2_pct: float = 33.34
) -> None:
    """Generate only pending journal entries (no historical entries).
    
    This is a simplified version of generate_journal_entries that only creates
    pending entries without historical entries.
    """
    # This is essentially the same as generate_journal_entries but with historical_count=0
    generate_journal_entries(
        cursor, company_codes, accounts, suppliers, lease_agreements,
        business_areas, master_data, entry_count, historical_count=0,
        correct_pct=correct_pct, scenario1_pct=scenario1_pct, scenario2_pct=scenario2_pct
    )


# ============================================================================
# Main Function
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Setup Argus database and mock data")
    parser.add_argument(
        "--db-path",
        default="projects/icp/data/argus/argus_database.db",
        help="Path to SQLite database file"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        default=True,
        help="Reset database (delete existing and recreate) (default: True)"
    )
    parser.add_argument(
        "--no-reset",
        dest="reset",
        action="store_false",
        help="Do not reset database (keep existing data)"
    )
    parser.add_argument(
        "--entry-count",
        type=int,
        default=6,
        help="Number of pending journal transactions (pairs) to generate (default: 6)"
    )
    parser.add_argument(
        "--historical-count",
        type=int,
        default=25,
        help="Number of historical entries per company/account combination (default: 25)"
    )
    parser.add_argument(
        "--company-count",
        type=int,
        default=12,
        help="Number of company codes to generate (default: 12)"
    )
    parser.add_argument(
        "--correct-pct",
        type=float,
        default=33.33,
        help="Percentage of correct entries (default: 33.33)"
    )
    parser.add_argument(
        "--scenario1-pct",
        type=float,
        default=33.33,
        help="Percentage of Scenario 1 entries (Capital/Revenue misclassification) (default: 33.33)"
    )
    parser.add_argument(
        "--scenario2-pct",
        type=float,
        default=33.34,
        help="Percentage of Scenario 2 entries (Lease/ROU misclassification) (default: 33.34)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility (default: None = use current time)"
    )
    parser.add_argument(
        "--pending-only",
        action="store_true",
        help="Only generate new pending entries, keep all existing data (suppliers, accounts, historical entries, etc.). Automatically sets --no-reset."
    )
    
    args = parser.parse_args()
    
    # If --pending-only is set, automatically disable reset
    if args.pending_only:
        args.reset = False
    
    # Set random seed
    if args.seed is not None:
        random.seed(args.seed)
    else:
        import time
        random.seed(int(time.time()))
    
    # Detect project name for path resolution
    project_name = detect_project_name(Path.cwd())
    
    # Resolve paths intelligently
    db_path = resolve_script_path(args.db_path, project_name=project_name)
    
    # Reset database if requested
    if args.reset:
        if db_path.exists():
            db_path.unlink()
            if console:
                console.print(f"[green]✓[/green] Removed existing database: {db_path}")
            else:
                print(f"✓ Removed existing database: {db_path}")
    
    # Create directories
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    if console:
        console.print("\n" + "=" * 70)
        console.print("Argus Database Setup")
        console.print("=" * 70)
        console.print(f"\nDatabase: {db_path}")
        console.print(f"Reset mode: {args.reset}")
        console.print(f"Pending-only mode: {args.pending_only}")
        console.print(f"Entry count: {args.entry_count}")
        if not args.pending_only:
            console.print(f"Historical count: {args.historical_count}")
            console.print(f"Company count: {args.company_count}")
        console.print(f"Distribution: Correct={args.correct_pct}%, Scenario1={args.scenario1_pct}%, Scenario2={args.scenario2_pct}%")
        console.print(f"Random seed: {args.seed}")
        console.print()
    else:
        print("\n" + "=" * 70)
        print("Argus Database Setup")
        print("=" * 70)
        print(f"\nDatabase: {db_path}")
        print(f"Reset mode: {args.reset}")
        print(f"Pending-only mode: {args.pending_only}")
        print(f"Entry count: {args.entry_count}")
        if not args.pending_only:
            print(f"Historical count: {args.historical_count}")
            print(f"Company count: {args.company_count}")
        print(f"Distribution: Correct={args.correct_pct}%, Scenario1={args.scenario1_pct}%, Scenario2={args.scenario2_pct}%")
        print(f"Random seed: {args.seed}")
        print()
    
    # Create database and schema
    if console:
        console.print("1. Creating database schema...")
    else:
        print("1. Creating database schema...")
    create_database_schema(str(db_path))
    
    # Connect to database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    if args.pending_only:
        # Pending-only mode: read existing data and only generate new pending entries
        if console:
            console.print("\n2. Reading existing data from database...")
        else:
            print("\n2. Reading existing data from database...")
        try:
            company_codes, accounts, suppliers, lease_agreements, business_areas, master_data = read_existing_data(cursor)
        except ValueError as e:
            if console:
                console.print(f"[red]✗[/red] Error: {e}")
            else:
                print(f"Error: {e}")
            conn.close()
            return 1
        
        # Generate only pending entries (no historical entries, no data regeneration)
        if console:
            console.print("\n3. Generating new pending journal entries only...")
        else:
            print("\n3. Generating new pending journal entries only...")
        generate_pending_entries_only(
            cursor, company_codes, accounts, suppliers, lease_agreements,
            business_areas, master_data, args.entry_count,
            args.correct_pct, args.scenario1_pct, args.scenario2_pct
        )
    else:
        # Full mode: generate everything
        # Generate supporting data
        if console:
            console.print("\n2. Generating supporting data...")
        else:
            print("\n2. Generating supporting data...")
        company_codes, suppliers, lease_agreements, business_areas, master_data = generate_supporting_data(cursor, args.company_count)
        
        # Generate account classifications
        if console:
            console.print("\n3. Generating account classifications...")
        else:
            print("\n3. Generating account classifications...")
        accounts = generate_account_classifications(cursor, company_codes)
        
        # Generate journal entries (including historical entries)
        if console:
            console.print("\n4. Generating journal entries...")
        else:
            print("\n4. Generating journal entries...")
        generate_journal_entries(cursor, company_codes, accounts, suppliers, lease_agreements, 
                                business_areas, master_data, args.entry_count, args.historical_count,
                                args.correct_pct, args.scenario1_pct, args.scenario2_pct)
        
        # Generate historical patterns FROM historical entries (derived data)
        if console:
            console.print("\n5. Generating historical patterns from historical entries...")
        else:
            print("\n5. Generating historical patterns from historical entries...")
        generate_historical_patterns_from_entries(cursor)
    
    # Commit and close
    conn.commit()
    conn.close()
    
    if console:
        console.print("\n[green]✓[/green] Database setup complete!")
        console.print(f"\nDatabase location: {db_path}")
    else:
        print("\n✓ Database setup complete!")
        print(f"\nDatabase location: {db_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
