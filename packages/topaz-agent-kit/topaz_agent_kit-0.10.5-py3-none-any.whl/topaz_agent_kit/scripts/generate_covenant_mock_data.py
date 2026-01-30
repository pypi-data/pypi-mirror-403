#!/usr/bin/env python3
"""Generate mock data for Covenant Contract Lifecycle Intelligence pipeline.

Creates realistic contract lifecycle data:
- Pre-contract artifacts (emails, meeting notes, informal documents)
- Draft contracts with intentional deviations
- Signed contracts (clean, final versions)
- Historical WBS documents (reference data)

Usage:
    # Interactive mode (recommended - can run from anywhere)
    python scripts/generate_covenant_mock_data.py --interactive
    uv run -m scripts.generate_covenant_mock_data --interactive
    
    # Command-line mode (can run from anywhere)
    python scripts/generate_covenant_mock_data.py --option 1
    python scripts/generate_covenant_mock_data.py --option 2 --project-dir projects/pa
    uv run -m scripts.generate_covenant_mock_data --option 3

Note: The script automatically detects the project directory, so you can run it from
the repository root or from within the project directory.
"""

import argparse
import json
import random
import shutil
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from topaz_agent_kit.utils.path_resolver import resolve_script_path, detect_project_name

try:
    from docx import Document  # type: ignore[reportMissingModuleSource]
    from docx.shared import Pt, RGBColor  # type: ignore[reportMissingModuleSource]
    from docx.enum.text import WD_ALIGN_PARAGRAPH  # type: ignore[reportMissingModuleSource]
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("Warning: python-docx not available. DOCX generation will be skipped.")
    print("Install with: pip install python-docx")

try:
    from reportlab.lib.pagesizes import letter  # type: ignore[reportMissingModuleSource]
    from reportlab.lib import colors  # type: ignore[reportMissingModuleSource]
    from reportlab.lib.units import inch  # type: ignore[reportMissingModuleSource]
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak  # type: ignore[reportMissingModuleSource]
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # type: ignore[reportMissingModuleSource]
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY  # type: ignore[reportMissingModuleSource]
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: reportlab not available. PDF generation will be skipped.")
    print("Install with: pip install reportlab")


# ============================================================================
# Constants
# ============================================================================

# SOW ID prefix uses current year
SOW_ID_PREFIX = f"SOW-{datetime.now().year}"
BASE_DIR = "data/covenant"

# Pre-contract sections (based on real-world analysis)
PRE_CONTRACT_SECTIONS = [
    "Project Intent & Scope",
    "Commercial Assumptions",
    "Acceptance Criteria & KPIs",
    "Milestones & Billing Triggers",
    "Invoice & Billing Expectations",
    "Accounting Positions (Owner's Books)",
    "Compliance & Controls",
    "Governance & Reporting",
    "WBS & Asset Mapping"
]

# Real-world deviations (from analysis)
DEVIATIONS = {
    "indexation": {"pre_contract": "UK CPI/WPI ±2.5% annually", "draft": "UK CPI/WPI ±3% p.a.", "risk": "High"},
    "delay_lds": {"pre_contract": "£45k/week, cap 10% of contract price", "draft": "£50k/week capped at 10% of Contract Price", "risk": "High"},
    "performance_lds": {"pre_contract": "£20k per % shortfall, cap 5%", "draft": "£25k per percentage point shortfall capped at 5%", "risk": "High"},
    "earnback": {"pre_contract": "Service credits reversible if KPI ≥110% sustained for 3 months", "draft": "Earnbacks permitted on sustained ≥105% KPI for three consecutive months", "risk": "Medium"},
    "change_order": {"pre_contract": "≤£2m PM; £2–£4m Steering Committee; >£4m CFO", "draft": "up to £2m (Project Manager), £2–£5m (Steering Committee), >£5m CFO", "risk": "Medium"},
    "payment_terms": {"pre_contract": "Net 30 days", "draft": "Net 45 days", "risk": "Medium"},
    "retention_wording": {"pre_contract": "10% withheld until Final Acceptance; release conditions defined", "draft": "10% until Final Acceptance; release conditions defined", "risk": "Low"},
    "invoice_format": {"pre_contract": "Must include contract reference, WBS/asset IDs, PO number, milestone achieved, AFIU status, retention amount, tax details", "draft": "Invoices: monthly WBS/asset IDs, GRN/MRS, time sheets, progress certificates", "risk": "Low"},
    "terminology": {"pre_contract": "Service credits reversible", "draft": "Earnbacks permitted", "risk": "Low"},
}

# ============================================================================
# Scenario Configurations
# ============================================================================

# Contract Type Scenarios
CONTRACT_TYPE_SCENARIOS = {
    "large_capital": {
        "name": "Large Capital Project - Refinery & Upstream",
        "value_range": (1000_000_000, 1500_000_000),
        "currency": "£",
        "components": ["upstream", "refinery", "downstream"],
        "component_names": {
            "upstream": "12 horizontal development wells with completion, flowlines, and SCADA integration",
            "refinery": "Crude Distillation Unit (CDU) upgrade and Hydrodesulfurization (HDS) unit (nameplate ≥95%)",
            "downstream": "50 km, 24-inch pipeline with terminal tanks (2 × 50,000 m³) and metering station"
        },
        "complexity": "high",
        "sections": 9,
        "industry": "oil_gas",
        "industry_name": "Oil & Gas / Energy",
        "commercial_detail": "comprehensive",
        "accounting_standards": ["IAS 16", "IAS 23", "IAS 37", "IAS 36", "IFRS 16"],
        "compliance_regimes": ["HSWA 1974", "COMAH 2015", "CDM 2015", "PUWER 1998", "Pipeline Safety Regs 1996"],
    },
    "medium_infrastructure": {
        "name": "Medium Infrastructure Project - Refinery Operations",
        "value_range": (200_000_000, 500_000_000),
        "currency": "£",
        "components": ["refinery_upgrade", "material_handling", "labor_services"],
        "component_names": {
            "refinery_upgrade": "Catalytic cracking unit (FCC) revamp and heat exchanger network optimization",
            "material_handling": "Crude oil storage tanks (4 × 25,000 m³) and material logistics systems",
            "labor_services": "Specialized refinery operations, maintenance, and HSSE services"
        },
        "complexity": "medium",
        "sections": 7,
        "industry": "oil_gas",
        "industry_name": "Oil & Gas / Refinery Operations",
        "commercial_detail": "standard",
        "accounting_standards": ["IAS 16", "IAS 23"],
        "compliance_regimes": ["COMAH 2015", "HSWA 1974", "PUWER 1998"],
    },
    "small_service": {
        "name": "Small Service Agreement - Downstream Operations",
        "value_range": (10_000_000, 50_000_000),
        "currency": "£",
        "components": ["downstream_maintenance", "material_supply"],
        "component_names": {
            "downstream_maintenance": "Pipeline integrity management, terminal operations, and metering services",
            "material_supply": "Specialty chemicals, catalysts, and consumables supply chain management"
        },
        "complexity": "low",
        "sections": 5,
        "industry": "oil_gas",
        "industry_name": "Oil & Gas / Downstream Services",
        "commercial_detail": "basic",
        "accounting_standards": ["IAS 16"],
        "compliance_regimes": ["Pipeline Safety Regs 1996", "COMAH 2015"],
    },
}

# Deviation Pattern Scenarios
DEVIATION_PATTERNS = {
    "high_risk": {
        "name": "High-Risk Deviations",
        "deviations": ["indexation", "delay_lds", "performance_lds"],
        "description": "Critical commercial term deviations"
    },
    "medium_risk": {
        "name": "Medium-Risk Deviations",
        "deviations": ["earnback", "change_order", "payment_terms"],
        "description": "Moderate commercial term deviations"
    },
    "low_risk": {
        "name": "Low-Risk Deviations",
        "deviations": ["retention_wording", "invoice_format", "terminology"],
        "description": "Minor wording and format differences"
    },
    "none": {
        "name": "No Deviations",
        "deviations": [],
        "description": "Perfect match - all terms align"
    },
}

# Document Completeness Scenarios
COMPLETENESS_LEVELS = {
    "complete": {
        "name": "Complete & Detailed",
        "sections": 9,
        "sections_list": PRE_CONTRACT_SECTIONS,
        "commercial_detail": "comprehensive",
        "accounting_detail": "full",
        "compliance_detail": "comprehensive",
    },
    "moderate": {
        "name": "Moderate Detail",
        "sections": 7,
        "sections_list": [
            "Project Intent & Scope",
            "Commercial Assumptions",
            "Acceptance Criteria & KPIs",
            "Milestones & Billing Triggers",
            "Invoice & Billing Expectations",
            "Accounting Positions (Owner's Books)",
            "Compliance & Controls",
        ],
        "commercial_detail": "standard",
        "accounting_detail": "basic",
        "compliance_detail": "essential",
    },
    "minimal": {
        "name": "Minimal / Incomplete",
        "sections": 5,
        "sections_list": [
            "Project Intent & Scope",
            "Commercial Assumptions",
            "Acceptance Criteria & KPIs",
            "Milestones & Billing Triggers",
            "Invoice & Billing Expectations",
        ],
        "commercial_detail": "basic",
        "accounting_detail": "minimal",
        "compliance_detail": "minimal",
    },
}

# Communication Style Scenarios
COMMUNICATION_STYLES = {
    "formal": {
        "name": "Formal & Detailed",
        "tone": "professional",
        "detail_level": "comprehensive",
        "structure": "structured",
        "greeting": "Dear Team,",
        "closing": "Best regards,",
    },
    "informal": {
        "name": "Informal & Brief",
        "tone": "casual",
        "detail_level": "brief",
        "structure": "loose",
        "greeting": "Hi Team,",
        "closing": "Thanks,",
    },
    "mixed": {
        "name": "Mixed / Inconsistent",
        "tone": "varied",
        "detail_level": "varied",
        "structure": "inconsistent",
        "greeting": ["Hi Team,", "Dear Team,", "Hello,"],
        "closing": ["Best regards,", "Thanks,", "Regards,"],
    },
}


# ============================================================================
# Helper Functions
# ============================================================================

def initialize_random(seed: Optional[int] = None) -> None:
    """Initialize random number generator with seed for reproducibility."""
    if seed is not None:
        random.seed(seed)


def generate_sow_number(seed: Optional[int] = None) -> str:
    """Generate a unique SOW number."""
    if seed is not None:
        # Use seed to generate consistent SOW number
        rng = random.Random(seed)
        sow_num = rng.randint(2000, 2999)  # SOW-2025-2000 to SOW-2025-2999
    else:
        sow_num = random.randint(2000, 2999)
    return f"{SOW_ID_PREFIX}-{sow_num:04d}"


def select_contract_type_scenario(seed: Optional[int] = None) -> str:
    """Randomly select a contract type scenario."""
    if seed is not None:
        rng = random.Random(seed)
        return rng.choice(list(CONTRACT_TYPE_SCENARIOS.keys()))
    return random.choice(list(CONTRACT_TYPE_SCENARIOS.keys()))


def select_deviation_pattern(seed: Optional[int] = None) -> str:
    """Randomly select a deviation pattern scenario."""
    if seed is not None:
        rng = random.Random(seed + 1000 if seed else None)  # Offset seed for different selection
        return rng.choice(list(DEVIATION_PATTERNS.keys()))
    return random.choice(list(DEVIATION_PATTERNS.keys()))


def select_completeness_level(seed: Optional[int] = None) -> str:
    """Randomly select a completeness level scenario."""
    if seed is not None:
        rng = random.Random(seed + 2000 if seed else None)  # Offset seed for different selection
        return rng.choice(list(COMPLETENESS_LEVELS.keys()))
    return random.choice(list(COMPLETENESS_LEVELS.keys()))


def select_communication_style(seed: Optional[int] = None) -> str:
    """Randomly select a communication style scenario."""
    if seed is not None:
        rng = random.Random(seed + 3000 if seed else None)  # Offset seed for different selection
        return rng.choice(list(COMMUNICATION_STYLES.keys()))
    return random.choice(list(COMMUNICATION_STYLES.keys()))


def get_contract_value(contract_type: str, seed: Optional[int] = None) -> int:
    """Get contract value based on type scenario."""
    scenario = CONTRACT_TYPE_SCENARIOS[contract_type]
    min_val, max_val = scenario["value_range"]
    if seed is not None:
        rng = random.Random(seed + 4000 if seed else None)
        return rng.randint(min_val, max_val)
    return random.randint(min_val, max_val)


def get_project_scope_content(contract_type: str, contract_value: int) -> Dict[str, str]:
    """Get project scope content based on contract type."""
    scenario = CONTRACT_TYPE_SCENARIOS[contract_type]
    
    # Format contract value
    if contract_value >= 1_000_000_000:
        value_str = f"£{contract_value / 1_000_000_000:.2f} billion"
    elif contract_value >= 1_000_000:
        value_str = f"£{contract_value / 1_000_000:.0f} million"
    else:
        value_str = f"£{contract_value:,}"
    
    if contract_type == "large_capital":
        return {
            "objectives": "Comprehensive capital project including 12 horizontal development wells with completion and flowlines, refinery CDU upgrade and HDS unit construction, and 50km pipeline with terminal tanks and metering station",
            "inclusions": "Engineering, procurement, construction, commissioning, performance tests, documentation, training, materials (casing, tubing, valves, pumps, compressors), labor (drilling crews, refinery operators, pipeline technicians)",
            "exclusions": "Ongoing O&M post-handover, non-project operating spares, feedstock supply",
            "value": value_str,
            "breakdown": "Upstream (wells, completion, flowlines): £400m; Refinery (CDU upgrade, HDS unit): £650m; Downstream (pipeline, terminal, metering): £250m"
        }
    elif contract_type == "medium_infrastructure":
        return {
            "objectives": "Medium-scale refinery infrastructure project including FCC unit revamp, crude storage tanks, and specialized operations services",
            "inclusions": "Refinery unit revamp, material handling systems, specialized labor services, materials (catalysts, heat exchangers, piping), commissioning, documentation",
            "exclusions": "Feedstock supply, ongoing catalyst replacement, routine maintenance post-commissioning",
            "value": value_str,
            "breakdown": "Refinery Upgrade: 55%; Material Handling: 30%; Labor Services: 15%"
        }
    else:  # small_service
        return {
            "objectives": "Downstream operations service agreement for pipeline integrity, terminal operations, and material supply chain management",
            "inclusions": "Pipeline integrity management, terminal operations, metering services, specialty chemicals and catalyst supply, maintenance support",
            "exclusions": "Crude oil supply, major capital equipment, travel expenses",
            "value": value_str,
            "breakdown": "Downstream Maintenance: 65%; Material Supply: 35%"
        }


def get_commercial_terms_content(contract_type: str, completeness: str) -> Dict[str, str]:
    """Get commercial terms content based on contract type and completeness."""
    if contract_type == "large_capital":
        base_terms = {
            "delivery_model": "Hybrid – Unit Rate (wells) + Lump Sum EPC (HDS & pipeline)",
            "retention": "10% until Final Acceptance",
            "payment_terms": "Net 30 days",
            "indexation": "UK CPI/WPI ±2.5% annually (needs confirmation)",
            "delay_lds": "£45k/week, cap 10% of contract price",
            "performance_lds": "£20k per % shortfall, cap 5%",
            "earnback": "Service credits reversible if KPI ≥110% sustained for 3 months",
            "change_order": "≤£2m PM; £2–£4m Steering Committee; >£4m CFO"
        }
    elif contract_type == "medium_infrastructure":
        base_terms = {
            "delivery_model": "Fixed-price model with milestone payments",
            "retention": "5% until completion",
            "payment_terms": "Net 30 days",
            "indexation": "UK CPI/WPI ±2% annually",
            "delay_lds": "£25k/week, cap 8% of contract price",
            "performance_lds": "£15k per % shortfall, cap 4%",
            "earnback": "Service credits if KPI ≥105% sustained for 3 months",
            "change_order": "≤£1m PM; £1–£3m Steering Committee; >£3m CFO"
        }
    else:  # small_service
        base_terms = {
            "delivery_model": "Time-and-materials model with monthly invoicing",
            "retention": "No retention",
            "payment_terms": "Net 30 days",
            "indexation": "UK CPI/WPI ±1.5% annually",
            "delay_lds": "Not applicable",
            "performance_lds": "Service credits for SLA breaches",
            "earnback": "Not applicable",
            "change_order": "≤£500k PM; >£500k CFO"
        }
    
    # Adjust based on completeness
    if completeness == "minimal":
        # Remove some details
        base_terms.pop("indexation", None)
        base_terms.pop("earnback", None)
    
    return base_terms


def get_kpis_content(contract_type: str) -> Dict[str, str]:
    """Get KPIs content based on contract type."""
    if contract_type == "large_capital":
        return {
            "upstream": "IP ≥800 bopd per well; stabilized ≤14 days; WHP ≥1,500 psi; SCADA uptime ≥99%; drilling efficiency ≥85%; completion success rate ≥98%",
            "refinery": "CDU throughput ≥95% nameplate; HDS unit ≥95% nameplate; sulfur ≤10 ppm; EII improvement ≥3%; emissions within statutory limits; catalyst life ≥24 months",
            "downstream": "Pipeline throughput ≥2,000 m³/h; LDS sensitivity ≥1%; response ≤5 min; availability ≥98%; metering accuracy ≤0.25%; terminal tank utilization ≥90%"
        }
    elif contract_type == "medium_infrastructure":
        return {
            "refinery_upgrade": "FCC unit conversion ≥92%; heat exchanger efficiency ≥88%; unit availability ≥96%; emissions compliance 100%",
            "material_handling": "Tank capacity utilization ≥85%; material logistics efficiency ≥90%; HSSE incidents = 0",
            "labor_services": "Labor productivity ≥95%; HSSE compliance 100%; specialized operator certification ≥98%; maintenance schedule adherence ≥95%"
        }
    else:  # small_service
        return {
            "downstream_maintenance": "Pipeline integrity compliance 100%; terminal operations uptime ≥98%; metering accuracy ≤0.25%; response time ≤4 hours",
            "material_supply": "On-time delivery ≥95%; material quality compliance 100%; supply chain visibility ≥90%; inventory optimization ≥85%"
        }


def get_accounting_content(contract_type: str, completeness: str) -> Dict[str, Any]:
    """Get accounting positions content based on contract type and completeness."""
    if contract_type == "large_capital":
        base = {
            "capitalization": "Directly attributable costs only; exclude abnormal wastage, training, admin",
            "afiu_trigger": "AUC→PPE transfer and depreciation start at AFIU",
            "borrowing_costs": "Capitalize until AFIU; suspend during inactivity",
            "aro": "PV recognized in asset cost; unwind to finance cost",
            "aro_estimates": "wells £50k, pipeline £6m, tanks £3m",
            "componentization": "Wellbore, completion, flowline, metering; CDU columns, HDS reactors, furnaces, compressors, heat exchangers; pipeline segments, stations, tanks, metering station",
            "useful_lives": "Reactors/Columns 25y; Furnaces/Compressors 20y; Piping 25y; E&I 12y; SCADA/DCS 7y; Wells UoP"
        }
    elif contract_type == "medium_infrastructure":
        base = {
            "capitalization": "Directly attributable costs only; exclude abnormal wastage, training, admin",
            "afiu_trigger": "AUC→PPE transfer at completion",
            "borrowing_costs": "Capitalize until completion",
            "aro": "Not applicable",
            "componentization": "FCC unit, heat exchangers, compressors, piping; storage tanks, material handling systems; refinery operations equipment",
            "useful_lives": "FCC unit 25y; Heat exchangers 20y; Tanks 30y; Piping 25y; E&I 12y"
        }
    else:  # small_service
        base = {
            "capitalization": "Operating expenses",
            "afiu_trigger": "Not applicable",
            "borrowing_costs": "Not applicable",
            "aro": "Not applicable",
            "componentization": "Not applicable",
            "useful_lives": "Not applicable"
        }
    
    # Adjust based on completeness
    if completeness == "minimal":
        base.pop("aro_estimates", None)
        base.pop("componentization", None)
        base.pop("useful_lives", None)
    elif completeness == "moderate":
        base.pop("aro_estimates", None)
    
    return base


def clear_covenant_data(base_dir: Path, keep_existing: bool = False) -> None:
    """Clear covenant data directory (except historical_wbs if keep_existing)."""
    if not keep_existing:
        if base_dir.exists():
            # Remove all except historical_wbs
            for item in base_dir.iterdir():
                if item.name != "historical_wbs":
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
            print(f"  ✓ Cleared: {base_dir} (preserved historical_wbs/)")
    else:
        print(f"  ✓ Keeping existing data in: {base_dir}")


def delete_all_subfolders(base_dir: Path) -> None:
    """Delete all subfolders from the covenant data directory."""
    if not base_dir.exists():
        print(f"  ⚠️  Directory does not exist: {base_dir}")
        return
    
    # Find all subdirectories
    subfolders = [item for item in base_dir.iterdir() if item.is_dir()]
    
    if not subfolders:
        print(f"  ℹ️  No subfolders found in: {base_dir}")
        return
    
    print(f"\n  Found {len(subfolders)} subfolder(s):")
    for subfolder in subfolders:
        print(f"    • {subfolder.name}/")
    
    # Confirm deletion
    confirm = input(f"\n  ⚠️  WARNING: This will DELETE ALL {len(subfolders)} subfolder(s) from {base_dir}\n  Type 'DELETE' to confirm: ").strip()
    
    if confirm != "DELETE":
        print("  ❌ Deletion cancelled.")
        return
    
    # Delete all subfolders
    deleted_count = 0
    for subfolder in subfolders:
        try:
            shutil.rmtree(subfolder)
            print(f"  ✓ Deleted: {subfolder.name}/")
            deleted_count += 1
        except Exception as e:
            print(f"  ❌ Error deleting {subfolder.name}/: {e}")
    
    print(f"\n  ✅ Successfully deleted {deleted_count} out of {len(subfolders)} subfolder(s)")


def find_existing_sow_numbers(base_dir: Path) -> List[str]:
    """Find all existing SOW numbers from pre_contract directory."""
    pre_contract_base = base_dir / "pre_contract"
    if not pre_contract_base.exists():
        return []
    
    sow_numbers = []
    for item in pre_contract_base.iterdir():
        if item.is_dir() and any(item.iterdir()):
            sow_numbers.append(item.name)
    
    return sorted(sow_numbers)


def find_existing_change_orders(base_dir: Path, sow_number: str) -> List[Path]:
    """Find all existing change orders for a SOW."""
    change_orders_dir = base_dir / "change_orders"
    if not change_orders_dir.exists():
        return []
    
    change_orders = []
    for file in change_orders_dir.glob(f"{sow_number}_change_order_*.pdf"):
        change_orders.append(file)
    
    return sorted(change_orders)


def get_next_change_order_version(base_dir: Path, sow_number: str) -> str:
    """Get the next change order version number."""
    existing = find_existing_change_orders(base_dir, sow_number)
    if not existing:
        return "v1"
    
    # Extract version numbers and find the highest
    versions = []
    for file in existing:
        # Extract version from filename like SOW-2025-2019_change_order_v1.pdf
        name = file.stem  # Gets filename without extension
        if "_change_order_v" in name:
            version_part = name.split("_change_order_v")[-1]
            try:
                version_num = int(version_part)
                versions.append(version_num)
            except ValueError:
                pass
    
    if versions:
        next_version = max(versions) + 1
    else:
        next_version = 1
    
    return f"v{next_version}"


def check_existing_data(base_dir: Path, sow_number: str) -> Dict[str, bool]:
    """Check what files already exist for a SOW."""
    pre_contract_dir = base_dir / "pre_contract" / sow_number
    draft_dir = base_dir / "draft_contracts"
    signed_dir = base_dir / "signed_contracts"
    change_orders_dir = base_dir / "change_orders"
    artifacts_dir = base_dir / "artifacts" / sow_number
    reports_dir = base_dir / "reports"
    
    # Find existing change orders
    existing_change_orders = []
    if change_orders_dir.exists():
        for file in change_orders_dir.glob(f"{sow_number}_change_order_*.pdf"):
            existing_change_orders.append(file)
    
    return {
        "pre_contract_exists": pre_contract_dir.exists() and any(pre_contract_dir.iterdir()),
        "pre_contract_summary_exists": (artifacts_dir / "pre_contract_summary_v1.json").exists(),
        "pre_contract_report_exists": (reports_dir / f"{sow_number}_pre_contract_synthesis_report.md").exists(),
        "draft_contract_exists": (draft_dir / f"{sow_number}_draft_v1.pdf").exists(),
        "draft_validation_report_exists": (artifacts_dir / "draft_contract_validation_report.json").exists(),
        "signed_contract_exists": (signed_dir / f"{sow_number}_signed.pdf").exists(),
        "signed_contract_summary_exists": (artifacts_dir / "signed_contract_structured_summary.json").exists(),
        "wbs_exists": (artifacts_dir / "proposed_wbs_v1.json").exists(),
        "change_orders_exist": len(existing_change_orders) > 0,
        "change_order_files": existing_change_orders,
    }


def check_historical_wbs(base_dir: Path) -> bool:
    """Check if historical WBS exists."""
    historical_wbs_dir = base_dir / "historical_wbs"
    if not historical_wbs_dir.exists():
        return False
    wbs_files = list(historical_wbs_dir.glob("*.md"))
    return len(wbs_files) >= 3


def write_sow_terms_to_global_memory(
    sow_number: str,
    sow_terms: Dict[str, Any],
    project_dir: Path
) -> None:
    """Write SOW terms to global memory for Aegis to read.
    
    Writes to: data/agentos/global_shared/contracts/sow_terms.jsonl
    Uses sow_number as key - overwrites if exists (for change order updates)
    
    Args:
        sow_number: SOW number (e.g., "SOW-2025-2019")
        sow_terms: Dictionary containing SOW terms:
            - retention_percentage: float
            - ld_applicable: bool
            - ld_rate_per_day: float or None
            - milestones: list of milestone dicts
            - effective_date: str (ISO format)
        project_dir: Project root directory
    """
    global_memory_dir = project_dir / "data" / "agentos" / "global_shared" / "contracts"
    global_memory_dir.mkdir(parents=True, exist_ok=True)
    
    sow_data = {
        "sow_number": sow_number,
        "retention_percentage": sow_terms.get("retention_percentage"),
        "ld_applicable": sow_terms.get("ld_applicable"),
        "ld_rate_per_day": sow_terms.get("ld_rate_per_day"),
        "milestones": sow_terms.get("milestones", []),
        "effective_date": sow_terms.get("effective_date"),
        "status": "active"
    }
    
    terms_file = global_memory_dir / "sow_terms.jsonl"
    
    # Read existing terms, update this SOW, write back
    existing_terms = {}
    if terms_file.exists():
        with open(terms_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        existing_terms[data["sow_number"]] = data
                    except (json.JSONDecodeError, KeyError):
                        # Skip invalid lines
                        continue
    
    # Update/overwrite this SOW's terms
    existing_terms[sow_number] = sow_data
    
    # Write all terms back
    with open(terms_file, "w", encoding="utf-8") as f:
        for sow_num, data in existing_terms.items():
            f.write(json.dumps(data) + "\n")


def write_rate_cards_to_global_memory(
    sow_number: str,
    vendor_name: str,
    rate_cards: List[Dict[str, Any]],
    project_dir: Path,
    effective_date: str
) -> None:
    """Write rate cards to global memory for Aegis to read.
    
    Writes to: data/agentos/global_shared/contracts/rate_cards.jsonl
    """
    global_memory_dir = project_dir / "data" / "agentos" / "global_shared" / "contracts"
    global_memory_dir.mkdir(parents=True, exist_ok=True)
    
    rate_card_data = {
        "sow_number": sow_number,
        "vendor_name": vendor_name,
        "rate_cards": rate_cards,
        "effective_date": effective_date,
        "status": "active"
    }
    
    rate_cards_file = global_memory_dir / "rate_cards.jsonl"
    
    # Read-filter-write pattern
    existing_entries = {}
    if rate_cards_file.exists():
        with open(rate_cards_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        existing_entries[data["sow_number"]] = data
                    except (json.JSONDecodeError, KeyError):
                        continue
    
    existing_entries[sow_number] = rate_card_data
    
    with open(rate_cards_file, "w", encoding="utf-8") as f:
        for sow_num, data in existing_entries.items():
            f.write(json.dumps(data) + "\n")


def write_evidence_requirements_to_global_memory(
    sow_number: str,
    work_type: str,
    required_evidence_types: List[str],
    coverage_requirements: Dict[str, Any],
    project_dir: Path,
    effective_date: str
) -> None:
    """Write evidence requirements to global memory for Aegis to read.
    
    Writes to: data/agentos/global_shared/contracts/evidence_requirements.jsonl
    """
    global_memory_dir = project_dir / "data" / "agentos" / "global_shared" / "contracts"
    global_memory_dir.mkdir(parents=True, exist_ok=True)
    
    evidence_data = {
        "sow_number": sow_number,
        "work_type": work_type,
        "required_evidence_types": required_evidence_types,
        "coverage_requirements": coverage_requirements,
        "effective_date": effective_date,
        "status": "active"
    }
    
    evidence_file = global_memory_dir / "evidence_requirements.jsonl"
    
    # Read-filter-write pattern
    existing_entries = {}
    if evidence_file.exists():
        with open(evidence_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        existing_entries[data["sow_number"]] = data
                    except (json.JSONDecodeError, KeyError):
                        continue
    
    existing_entries[sow_number] = evidence_data
    
    with open(evidence_file, "w", encoding="utf-8") as f:
        for sow_num, data in existing_entries.items():
            f.write(json.dumps(data) + "\n")


def write_sow_metadata_to_global_memory(
    sow_number: str,
    invoice_type: str,
    vendor_name: str,
    project_id: Optional[str] = None,
    project_name: Optional[str] = None,
    pricing_model: str = "time_and_materials",
    project_dir: Path = None,
    effective_date: str = None
) -> None:
    """Write SOW metadata to global memory for invoice type classification.
    
    Writes to: data/agentos/global_shared/contracts/sow_metadata.jsonl
    """
    if project_dir is None:
        return
    
    global_memory_dir = project_dir / "data" / "agentos" / "global_shared" / "contracts"
    global_memory_dir.mkdir(parents=True, exist_ok=True)
    
    metadata = {
        "sow_number": sow_number,
        "invoice_type": invoice_type,
        "vendor_name": vendor_name,
        "project_id": project_id,
        "project_name": project_name,
        "pricing_model": pricing_model,
        "effective_date": effective_date or datetime.now().strftime("%Y-%m-%d"),
        "status": "active"
    }
    
    metadata_file = global_memory_dir / "sow_metadata.jsonl"
    
    # Read-filter-write pattern
    existing_entries = {}
    if metadata_file.exists():
        with open(metadata_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        existing_entries[data["sow_number"]] = data
                    except (json.JSONDecodeError, KeyError):
                        continue
    
    existing_entries[sow_number] = metadata
    
    with open(metadata_file, "w", encoding="utf-8") as f:
        for sow_num, data in existing_entries.items():
            f.write(json.dumps(data) + "\n")


# ============================================================================
# Pre-Contract Data Generation
# ============================================================================

def generate_email_thread(
    sow_number: str,
    thread_num: int,
    contract_type: str = "large_capital",
    communication_style: str = "formal",
    contract_value: Optional[int] = None,
    seed: Optional[int] = None
) -> str:
    """Generate email thread content with scenario-based variations."""
    scenario = CONTRACT_TYPE_SCENARIOS[contract_type]
    style = COMMUNICATION_STYLES[communication_style]
    
    # Generate contract value if not provided
    if contract_value is None:
        contract_value = get_contract_value(contract_type, seed)
    
    # Format contract value
    if contract_value >= 1_000_000_000:
        value_str = f"£{contract_value / 1_000_000_000:.2f} billion"
    elif contract_value >= 1_000_000:
        value_str = f"£{contract_value / 1_000_000:.0f} million"
    else:
        value_str = f"£{contract_value:,}"
    
    subjects = [
        f"Initial Discussion - {sow_number} Project Scope",
        f"Commercial Terms Discussion - {sow_number}",
        f"Follow-up: {sow_number} Requirements",
    ]
    
    senders = [
        "john.smith@company.com",
        "sarah.johnson@company.com",
        "michael.chen@company.com",
        "emily.davis@company.com",
    ]
    
    subject = subjects[thread_num % len(subjects)]
    if seed is not None:
        rng = random.Random(seed + thread_num * 100)
        sender = rng.choice(senders)
        days_ago = rng.randint(30, 60)
    else:
        sender = random.choice(senders)
        days_ago = random.randint(30, 60)
    
    date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M")
    
    # Select greeting and closing based on style
    if communication_style == "mixed":
        if seed is not None:
            rng = random.Random(seed + thread_num * 200)
            greeting = rng.choice(style["greeting"])
            closing = rng.choice(style["closing"])
        else:
            greeting = random.choice(style["greeting"])
            closing = random.choice(style["closing"])
    else:
        greeting = style["greeting"]
        closing = style["closing"]
    
    # Generate content based on contract type and style
    if contract_type == "large_capital":
        scope_text = f"We're looking at a comprehensive oil & gas capital project that includes upstream drilling (12 horizontal wells), refinery operations (CDU upgrade and HDS unit), and downstream infrastructure (pipeline and terminal). The target contract price is around {value_str}, split between upstream, refinery, and downstream components."
        commercial_text = "We discussed a hybrid delivery model - Unit Rate for wells and Lump Sum EPC for refinery and pipeline. Payment terms should be Net 30 days, with 10% retention until Final Acceptance. Materials (casing, tubing, valves, pumps, compressors) and labor (drilling crews, refinery operators, pipeline technicians) are included."
        milestones_text = "NTP by 01-Feb-2026, rig mobilization by 15-Feb-2026, first oil by Apr-2026, refinery mechanical completion by 15-Oct-2026, pipeline hydrotest by 10-Nov-2026, with final acceptance by 20-Dec-2026."
        kpis_text = "We need to ensure upstream wells achieve IP ≥800 bopd per well, refinery CDU/HDS units ≥95% nameplate, and pipeline throughput ≥2,000 m³/h with metering accuracy ≤0.25%."
        accounting_text = "We'll need to track this under IAS 16 for capitalization, with AFIU triggers for depreciation. ARO estimates are around £50k for wells, £6m for pipeline, and £3m for terminal tanks."
    elif contract_type == "medium_infrastructure":
        scope_text = f"We're planning a medium-scale refinery infrastructure project. The target contract price is around {value_str}, covering FCC unit revamp, crude storage tanks, and specialized operations services including materials (catalysts, heat exchangers) and labor (refinery operators, maintenance crews)."
        commercial_text = "We discussed a fixed-price model with milestone payments. Payment terms should be Net 30 days, with 5% retention until completion. Materials and specialized labor are included in the scope."
        milestones_text = "Project kickoff by 01-Mar-2026, FCC revamp completion by 30-Sep-2026, tank commissioning by 15-Nov-2026, with final handover by 31-Dec-2026."
        kpis_text = "We need to ensure FCC unit conversion ≥92%, heat exchanger efficiency ≥88%, tank utilization ≥85%, and labor productivity ≥95% with zero HSSE incidents."
        accounting_text = "We'll track this under IAS 16 for capitalization, with standard depreciation schedules for refinery assets."
    else:  # small_service
        scope_text = f"We're planning a downstream operations service agreement. The target contract value is around {value_str}, covering pipeline integrity management, terminal operations, metering services, and specialty chemicals/catalyst supply chain."
        commercial_text = "We discussed a time-and-materials model with monthly invoicing. Payment terms should be Net 30 days, with no retention. Materials (specialty chemicals, catalysts) and labor (pipeline technicians, terminal operators) are included."
        milestones_text = "Service start by 01-Apr-2026, with quarterly reviews and annual renewal options."
        kpis_text = "We need to ensure pipeline integrity compliance 100%, terminal uptime ≥98%, metering accuracy ≤0.25%, and on-time material delivery ≥95%."
        accounting_text = "We'll track this as operating expenses, with standard accrual accounting for materials and labor."
    
    # Adjust detail level based on communication style
    if style["detail_level"] == "brief":
        content = f"""From: {sender}
To: procurement@company.com
Subject: {subject}
Date: {date}

{greeting}

Quick update on {sow_number}:

- Scope: {scope_text.split('.')[0]}.
- Value: {value_str}
- Payment: Net 30 days
- Timeline: {milestones_text.split(',')[0]}

Let me know if you have questions.

{closing}
{sender.split('@')[0].replace('.', ' ').title()}
"""
    elif style["detail_level"] == "comprehensive":
        content = f"""From: {sender}
To: procurement@company.com
Subject: {subject}
Date: {date}

{greeting}

I wanted to follow up on our discussion about the {sow_number} project. Based on our meeting last week, here are the key points we discussed:

1. Project Scope: {scope_text}

2. Commercial Terms: {commercial_text}

3. Key Milestones: {milestones_text}

4. KPIs: {kpis_text}

5. Accounting: {accounting_text}

There are still some open questions around:
- Indexation formula (we discussed UK CPI/WPI ±2.5% annually, but need to confirm)
- Liquidated damages structure (need to finalize)
- Change order approval thresholds (need to align with governance)

Let me know if you need any clarification.

{closing}
{sender.split('@')[0].replace('.', ' ').title()}

---
Reply from procurement@company.com:
Date: {date}

Thanks for the summary. I'll review and get back to you with any questions.

One thing to note - we discussed earnbacks if KPI ≥110% sustained for 3 months, but I want to double-check the exact threshold.

Regards,
Procurement Team
"""
    else:  # varied
        # Mix of brief and detailed sections
        content = f"""From: {sender}
To: procurement@company.com
Subject: {subject}
Date: {date}

{greeting}

Update on {sow_number}:

1. Scope: {scope_text}
2. Commercial: {commercial_text}
3. Milestones: {milestones_text}
4. KPIs: {kpis_text}
5. Accounting: {accounting_text}

Open questions: indexation, LDs, change orders.

{closing}
{sender.split('@')[0].replace('.', ' ').title()}
"""
    
    return content


def generate_meeting_notes(
    sow_number: str,
    contract_type: str = "large_capital",
    completeness_level: str = "complete",
    communication_style: str = "formal",
    contract_value: Optional[int] = None,
    seed: Optional[int] = None
) -> str:
    """Generate meeting notes in Markdown format with scenario-based variations."""
    scenario = CONTRACT_TYPE_SCENARIOS[contract_type]
    completeness = COMPLETENESS_LEVELS[completeness_level]
    style = COMMUNICATION_STYLES[communication_style]
    
    # Generate contract value if not provided
    if contract_value is None:
        contract_value = get_contract_value(contract_type, seed)
    
    # Format contract value
    if contract_value >= 1_000_000_000:
        value_str = f"£{contract_value / 1_000_000_000:.2f} billion"
    elif contract_value >= 1_000_000:
        value_str = f"£{contract_value / 1_000_000:.0f} million"
    else:
        value_str = f"£{contract_value:,}"
    
    if seed is not None:
        rng = random.Random(seed + 5000)
        days_ago = rng.randint(20, 40)
    else:
        days_ago = random.randint(20, 40)
    date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    
    # Get scenario-based content
    scope_content = get_project_scope_content(contract_type, contract_value)
    commercial_terms = get_commercial_terms_content(contract_type, completeness_level)
    kpis_content = get_kpis_content(contract_type)
    accounting_content = get_accounting_content(contract_type, completeness_level)
    
    # Build content sections based on completeness level
    sections = []
    
    # Section 1: Project Scope (always included)
    sections.append(f"""### 1. Project Scope
- **Objectives:** {scope_content['objectives']}
- **Inclusions:** {scope_content['inclusions']}
- **Exclusions:** {scope_content['exclusions']}""")
    
    # Section 2: Commercial Assumptions (always included)
    commercial_section = f"""### 2. Commercial Assumptions
- **Delivery Model:** {commercial_terms['delivery_model']}
- **Target Contract Price:** {scope_content['value']}
  - {scope_content['breakdown']}
- **Retention:** {commercial_terms['retention']}
- **Payment Terms:** {commercial_terms['payment_terms']}"""
    
    if "indexation" in commercial_terms:
        commercial_section += f"\n- **Indexation:** {commercial_terms['indexation']}"
    if "delay_lds" in commercial_terms and commercial_terms['delay_lds'] != "Not applicable":
        commercial_section += f"\n- **Liquidated Damages:**\n  - Delay LDs: {commercial_terms['delay_lds']}\n  - Performance LDs: {commercial_terms['performance_lds']}"
    if "earnback" in commercial_terms and commercial_terms['earnback'] != "Not applicable":
        commercial_section += f"\n- **Earnbacks:** {commercial_terms['earnback']}"
    if "change_order" in commercial_terms:
        commercial_section += f"\n- **Change Orders:** Approval thresholds – {commercial_terms['change_order']}"
    
    sections.append(commercial_section)
    
    # Section 3: Acceptance Criteria & KPIs (always included)
    kpis_section = "### 3. Acceptance Criteria & KPIs"
    for key, value in kpis_content.items():
        kpis_section += f"\n- **{key.replace('_', ' ').title()}:** {value}"
    sections.append(kpis_section)
    
    # Section 4: Milestones (always included)
    if contract_type == "large_capital":
        milestones_section = """### 4. Milestones & Billing Triggers
- **NTP:** 01-Feb-2026
- **Rig Mobilization:** 15-Feb-2026
- **First Spud:** 20-Feb-2026
- **First Oil:** Apr-2026
- **CDU Upgrade Mechanical Completion:** 15-Sep-2026
- **HDS Unit Mechanical Completion:** 15-Oct-2026
- **Pipeline Hydrotest:** 10-Nov-2026
- **Terminal Commissioning:** 15-Nov-2026
- **AFIU:** Wells Apr–Jun 2026; Refinery Nov 2026; Pipeline Nov 2026
- **Final Acceptance:** 20-Dec-2026"""
    elif contract_type == "medium_infrastructure":
        milestones_section = """### 4. Milestones & Billing Triggers
- **Project Kickoff:** 01-Mar-2026
- **FCC Revamp Start:** 15-Mar-2026
- **Heat Exchanger Installation:** Jun–Aug 2026
- **Tank Construction:** Jul–Sep 2026
- **FCC Mechanical Completion:** 30-Sep-2026
- **Tank Commissioning:** 15-Nov-2026
- **Final Handover:** 31-Dec-2026"""
    else:  # small_service
        milestones_section = """### 4. Milestones & Billing Triggers
- **Service Start:** 01-Apr-2026
- **Quarterly Reviews:** Jul, Oct 2026; Jan 2027
- **Annual Renewal:** 31-Mar-2027"""
    sections.append(milestones_section)
    
    # Section 5: Invoice & Billing (always included)
    sections.append(f"""### 5. Invoice & Billing Expectations
- **Invoice Format:** Must include contract reference, WBS/asset IDs, PO number, milestone achieved, retention amount, tax details
- **Supporting Documents:** Evidence pack mandatory for milestone invoices
- **Retention Handling:** {commercial_terms['retention']}; release conditions defined
- **Tax Compliance:** UK VAT; customs duties; sanctions screening""")
    
    # Section 6: Accounting Positions (if completeness >= moderate)
    if completeness_level in ["complete", "moderate"]:
        accounting_section = "### 6. Accounting Positions"
        if "capitalization" in accounting_content:
            accounting_section += f"\n- **Capitalization (IAS 16):** {accounting_content['capitalization']}"
        if "afiu_trigger" in accounting_content and accounting_content['afiu_trigger'] != "Not applicable":
            accounting_section += f"\n- **AFIU Trigger:** {accounting_content['afiu_trigger']}"
        if "borrowing_costs" in accounting_content and accounting_content['borrowing_costs'] != "Not applicable":
            accounting_section += f"\n- **Borrowing Costs (IAS 23):** {accounting_content['borrowing_costs']}"
        if "aro" in accounting_content and accounting_content['aro'] != "Not applicable":
            accounting_section += f"\n- **ARO (IAS 37/IFRIC 1):** {accounting_content['aro']}"
        if "aro_estimates" in accounting_content:
            accounting_section += f"\n  - Baseline estimates: {accounting_content['aro_estimates']}"
        if "componentization" in accounting_content and accounting_content['componentization'] != "Not applicable":
            accounting_section += f"\n- **Componentization:** {accounting_content['componentization']}"
        if "componentization" in accounting_content and accounting_content['componentization'] != "Not applicable":
            accounting_section += f"\n- **Componentization:** {accounting_content['componentization']}"
        if "useful_lives" in accounting_content and accounting_content['useful_lives'] != "Not applicable":
            accounting_section += f"\n- **Useful Lives:** {accounting_content['useful_lives']}"
        sections.append(accounting_section)
    
    # Section 7: Compliance & Controls (if completeness >= moderate)
    if completeness_level in ["complete", "moderate"]:
        compliance_section = "### 7. Compliance & Controls"
        compliance_regimes = scenario.get("compliance_regimes", [])
        if compliance_regimes:
            compliance_section += f"\n- **HSSE/Regulatory:** {', '.join(compliance_regimes)}"
        compliance_section += "\n- **Data Protection:** UK GDPR/DPA 2018 for evidence packs"
        if completeness_level == "complete":
            compliance_section += "\n- **Sanctions & ABC:** OFSI screening; Bribery Act 2010 compliance"
            compliance_section += "\n- **Approvals:** Maker-checker; SoD thresholds enforced"
            compliance_section += "\n- **Audit Trail:** Evidence retention for 7 years; linkage to WBS/asset IDs"
        sections.append(compliance_section)
    
    # Section 8: Open Questions (if completeness >= moderate)
    if completeness_level in ["complete", "moderate"]:
        sections.append("""### 8. Open Questions
1. Exact indexation formula confirmation (need final approval)
2. LD structure details (need legal review)
3. Earnback threshold confirmation (need to verify)
4. Change order threshold alignment (need CFO approval)""")
    
    # Section 9: Next Steps (always included)
    sections.append("""### 9. Next Steps
1. Legal team to review commercial terms
2. Finance to confirm accounting positions
3. Procurement to draft contract based on these discussions
4. Schedule follow-up meeting in 2 weeks""")
    
    # Build final content
    content = f"""# Meeting Notes - {sow_number} Project Discussion
**Date:** {date}
**Attendees:** John Smith, Sarah Johnson, Michael Chen, Emily Davis
**Location:** Conference Room A / Virtual

## Agenda
1. Project scope and objectives
2. Commercial terms discussion
3. Timeline and milestones
4. Open questions and next steps

## Discussion Points

{chr(10).join(sections)}

## Action Items
- [ ] John: Confirm indexation formula with Finance
- [ ] Sarah: Review LD structure with Legal
- [ ] Michael: Prepare draft contract based on discussions
- [ ] Emily: Schedule follow-up meeting

---
**Note:** These are informal meeting notes. Formal pre-contract summary will be generated by the pipeline.
"""
    return content


def generate_informal_scope_doc(
    sow_number: str,
    contract_type: str = "large_capital",
    contract_value: Optional[int] = None,
    seed: Optional[int] = None
) -> str:
    """Generate informal scope document in PDF format with scenario-based variations."""
    if not REPORTLAB_AVAILABLE:
        # Fallback to text format
        scenario = CONTRACT_TYPE_SCENARIOS[contract_type]
        if contract_value is None:
            contract_value = get_contract_value(contract_type, seed)
        if contract_value >= 1_000_000_000:
            value_str = f"£{contract_value / 1_000_000_000:.2f} billion"
        elif contract_value >= 1_000_000:
            value_str = f"£{contract_value / 1_000_000:.0f} million"
        else:
            value_str = f"£{contract_value:,}"
        scope_content = get_project_scope_content(contract_type, contract_value)
        return f"""Informal Scope Document - {sow_number}

This is an informal document capturing initial scope discussions.

Project: {sow_number}
Scope: {scope_content['objectives']}
Target Price: {value_str}
Timeline: {scenario['industry_name']} project

Note: This is a preliminary document. Formal scope will be defined in the contract.
"""
    
    scenario = CONTRACT_TYPE_SCENARIOS[contract_type]
    
    # Generate contract value if not provided
    if contract_value is None:
        contract_value = get_contract_value(contract_type, seed)
    
    # Format contract value
    if contract_value >= 1_000_000_000:
        value_str = f"£{contract_value / 1_000_000_000:.2f} billion"
    elif contract_value >= 1_000_000:
        value_str = f"£{contract_value / 1_000_000:.0f} million"
    else:
        value_str = f"£{contract_value:,}"
    
    scope_content = get_project_scope_content(contract_type, contract_value)
    commercial_terms = get_commercial_terms_content(contract_type, "moderate")
    
    # Save to temporary location first
    temp_path = Path(tempfile.gettempdir()) / f"{sow_number}_informal_scope_temp.pdf"
    
    doc = SimpleDocTemplate(str(temp_path), pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=18,
        textColor=colors.HexColor('#003366'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Heading style
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#003366'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Title
    story.append(Paragraph(f'Informal Scope Document - {sow_number}', title_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # Introduction
    story.append(Paragraph(
        "This document captures initial scope discussions for the project. "
        "It is informal and subject to change based on further discussions and contract negotiations.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.2 * inch))
    
    # Project Overview
    story.append(Paragraph('Project Overview', heading_style))
    story.append(Paragraph(f"Project ID: {sow_number}", styles['Normal']))
    story.append(Paragraph(f"Project Type: {scenario['name']}", styles['Normal']))
    story.append(Paragraph(f"Industry: {scenario['industry_name']}", styles['Normal']))
    story.append(Paragraph(f"Target Contract Price: {value_str}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    
    # Scope Components
    story.append(Paragraph('Scope Components', heading_style))
    component_names = scenario["component_names"]
    for component_key, component_name in component_names.items():
        story.append(Paragraph(
            f"• {component_key.replace('_', ' ').title()}: {component_name}",
            styles['Normal']
        ))
    story.append(Spacer(1, 0.2 * inch))
    
    # Key Assumptions
    story.append(Paragraph('Key Assumptions', heading_style))
    assumptions = [
        f"Delivery model: {commercial_terms['delivery_model']}",
        f"Payment terms: {commercial_terms['payment_terms']}",
        f"Retention: {commercial_terms['retention']}",
    ]
    if "indexation" in commercial_terms:
        assumptions.append(f"Indexation: {commercial_terms['indexation']}")
    
    for assumption in assumptions:
        story.append(Paragraph(f"• {assumption}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    
    # Timeline
    story.append(Paragraph('Timeline', heading_style))
    if contract_type == "large_capital":
        story.append(Paragraph("NTP: 01-Feb-2026", styles['Normal']))
        story.append(Paragraph("Final Acceptance: 20-Dec-2026", styles['Normal']))
    elif contract_type == "medium_infrastructure":
        story.append(Paragraph("Project Kickoff: 01-Mar-2026", styles['Normal']))
        story.append(Paragraph("Final Handover: 31-Dec-2026", styles['Normal']))
    else:  # small_service
        story.append(Paragraph("Service Start: 01-Apr-2026", styles['Normal']))
        story.append(Paragraph("Annual Renewal: 31-Mar-2027", styles['Normal']))
    
    doc.build(story)
    
    return str(temp_path)


def generate_pre_contract_data(
    base_dir: Path,
    sow_number: str,
    contract_type: str = "large_capital",
    completeness_level: str = "complete",
    communication_style: str = "formal",
    contract_value: Optional[int] = None,
    seed: Optional[int] = None
) -> List[Path]:
    """Generate all pre-contract artifacts with scenario-based variations."""
    pre_contract_dir = base_dir / "pre_contract" / sow_number
    pre_contract_dir.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    
    # Generate contract value if not provided
    if contract_value is None:
        contract_value = get_contract_value(contract_type, seed)
    
    # Email thread 1
    email1_path = pre_contract_dir / "email_thread_1.txt"
    email1_path.write_text(generate_email_thread(
        sow_number, 0, contract_type, communication_style, contract_value, seed
    ), encoding="utf-8")
    generated_files.append(email1_path)
    
    # Email thread 2
    email2_path = pre_contract_dir / "email_thread_2.txt"
    email2_path.write_text(generate_email_thread(
        sow_number, 1, contract_type, communication_style, contract_value, seed
    ), encoding="utf-8")
    generated_files.append(email2_path)
    
    # Meeting notes
    meeting_notes_path = pre_contract_dir / "meeting_notes_2025-01-10.md"
    meeting_notes_path.write_text(generate_meeting_notes(
        sow_number, contract_type, completeness_level, communication_style, contract_value, seed
    ), encoding="utf-8")
    generated_files.append(meeting_notes_path)
    
    # Informal scope document
    if REPORTLAB_AVAILABLE:
        scope_doc_temp = generate_informal_scope_doc(sow_number, contract_type, contract_value, seed)
        scope_doc_path = pre_contract_dir / "informal_scope_doc.pdf"
        shutil.copy(scope_doc_temp, scope_doc_path)
        Path(scope_doc_temp).unlink()  # Clean up temp file
        generated_files.append(scope_doc_path)
    else:
        # Fallback to text
        scope_doc_path = pre_contract_dir / "informal_scope_doc.txt"
        scope_doc_path.write_text(generate_informal_scope_doc(sow_number, contract_type, contract_value, seed), encoding="utf-8")
        generated_files.append(scope_doc_path)
    
    return generated_files


def generate_pre_contract_summary(
    sow_number: str,
    contract_type: str = "large_capital",
    completeness_level: str = "complete",
    contract_value: Optional[int] = None,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """Generate pre-contract summary JSON (simulated pipeline output) with scenario-based variations."""
    scenario = CONTRACT_TYPE_SCENARIOS[contract_type]
    completeness = COMPLETENESS_LEVELS[completeness_level]
    
    # Generate contract value if not provided
    if contract_value is None:
        contract_value = get_contract_value(contract_type, seed)
    
    # Format contract value
    if contract_value >= 1_000_000_000:
        value_str = f"£{contract_value / 1_000_000_000:.2f} billion"
    elif contract_value >= 1_000_000:
        value_str = f"£{contract_value / 1_000_000:.0f} million"
    else:
        value_str = f"£{contract_value:,}"
    
    # Get scenario-based content
    scope_content = get_project_scope_content(contract_type, contract_value)
    commercial_terms = get_commercial_terms_content(contract_type, completeness_level)
    kpis_content = get_kpis_content(contract_type)
    accounting_content = get_accounting_content(contract_type, completeness_level)
    
    # Build sections based on completeness
    sections = {
        "project_intent_scope": {
            "project_name": sow_number,
            "objectives": [scope_content["objectives"]],
            "inclusions": scope_content["inclusions"].split("; ") if ";" in scope_content["inclusions"] else [scope_content["inclusions"]],
            "exclusions": scope_content["exclusions"].split("; ") if ";" in scope_content["exclusions"] else [scope_content["exclusions"]]
        },
        "commercial_assumptions": {
            "delivery_model": commercial_terms["delivery_model"],
            "target_contract_price": value_str,
            "price_breakdown": scope_content["breakdown"],
            "retention": commercial_terms["retention"],
            "payment_terms": commercial_terms["payment_terms"],
        }
    }
    
    # Add optional commercial terms based on completeness
    if "indexation" in commercial_terms:
        sections["commercial_assumptions"]["indexation"] = commercial_terms["indexation"]
    if "delay_lds" in commercial_terms and commercial_terms["delay_lds"] != "Not applicable":
        sections["commercial_assumptions"]["liquidated_damages"] = {
            "delay_lds": commercial_terms["delay_lds"],
            "performance_lds": commercial_terms["performance_lds"]
        }
    if "earnback" in commercial_terms and commercial_terms["earnback"] != "Not applicable":
        sections["commercial_assumptions"]["earnbacks"] = commercial_terms["earnback"]
    if "change_order" in commercial_terms:
        # Parse change order thresholds
        co_parts = commercial_terms["change_order"].split("; ")
        co_dict = {}
        for part in co_parts:
            if "PM" in part or "Project Manager" in part:
                co_dict["pm"] = part.split(":")[0].strip()
            elif "Steering Committee" in part:
                co_dict["steering_committee"] = part.split(":")[1].strip() if ":" in part else part.strip()
            elif "CFO" in part:
                co_dict["cfo"] = part.split(":")[1].strip() if ":" in part else part.strip()
        if co_dict:
            sections["commercial_assumptions"]["change_order_thresholds"] = co_dict
    
    # Add KPIs
    sections["acceptance_criteria_kpis"] = kpis_content
    
    # Add milestones (simplified for now - can be enhanced)
    if contract_type == "large_capital":
        sections["milestones_billing_triggers"] = {
            "ntp": "01-Feb-2026",
            "rig_mobilization": "15-Feb-2026",
            "first_spud": "20-Feb-2026",
            "first_oil": "Apr-2026",
            "cdu_upgrade_mechanical_completion": "15-Sep-2026",
            "hds_unit_mechanical_completion": "15-Oct-2026",
            "pipeline_hydrotest": "10-Nov-2026",
            "terminal_commissioning": "15-Nov-2026",
            "afiu": {"wells": "Apr–Jun 2026", "refinery": "Nov 2026", "pipeline": "Nov 2026"},
            "final_acceptance": "20-Dec-2026"
        }
    elif contract_type == "medium_infrastructure":
        sections["milestones_billing_triggers"] = {
            "project_kickoff": "01-Mar-2026",
            "fcc_revamp_start": "15-Mar-2026",
            "heat_exchanger_installation": "Jun–Aug 2026",
            "tank_construction": "Jul–Sep 2026",
            "fcc_mechanical_completion": "30-Sep-2026",
            "tank_commissioning": "15-Nov-2026",
            "final_handover": "31-Dec-2026"
        }
    else:  # small_service
        sections["milestones_billing_triggers"] = {
            "service_start": "01-Apr-2026",
            "quarterly_reviews": "Jul, Oct 2026; Jan 2027",
            "annual_renewal": "31-Mar-2027"
        }
    
    # Add invoice/billing
    sections["invoice_billing_expectations"] = {
        "invoice_format": "Must include contract reference, WBS/asset IDs, PO number, milestone achieved, retention amount, tax details",
        "supporting_documents": "Evidence pack mandatory for milestone invoices",
        "retention_handling": f"{commercial_terms['retention']}; release conditions defined",
        "tax_compliance": "UK VAT; customs duties; sanctions screening"
    }
    
    # Add accounting positions if completeness >= moderate
    if completeness_level in ["complete", "moderate"]:
        sections["accounting_positions"] = {}
        if "capitalization" in accounting_content:
            sections["accounting_positions"]["capitalization_ias16"] = accounting_content["capitalization"]
        if "afiu_trigger" in accounting_content and accounting_content["afiu_trigger"] != "Not applicable":
            sections["accounting_positions"]["afiu_trigger"] = accounting_content["afiu_trigger"]
        if "borrowing_costs" in accounting_content and accounting_content["borrowing_costs"] != "Not applicable":
            sections["accounting_positions"]["borrowing_costs_ias23"] = accounting_content["borrowing_costs"]
        if "aro" in accounting_content and accounting_content["aro"] != "Not applicable":
            sections["accounting_positions"]["aro_ias37_ifric1"] = {"baseline_estimates": accounting_content.get("aro_estimates", {})}
        if "componentization" in accounting_content and accounting_content["componentization"] != "Not applicable":
            sections["accounting_positions"]["componentization"] = accounting_content["componentization"].split("; ")
        if "useful_lives" in accounting_content and accounting_content["useful_lives"] != "Not applicable":
            # Parse useful lives
            useful_lives_dict = {}
            for item in accounting_content["useful_lives"].split("; "):
                if ":" in item:
                    key, value = item.split(":")
                    useful_lives_dict[key.strip().lower().replace(" ", "_")] = value.strip()
            if useful_lives_dict:
                sections["accounting_positions"]["useful_lives"] = useful_lives_dict
    
    # Add compliance if completeness >= moderate
    if completeness_level in ["complete", "moderate"]:
        sections["compliance_controls"] = {
            "hsse": scenario.get("compliance_regimes", []),
            "data_protection": "UK GDPR/DPA 2018 for evidence packs"
        }
        if completeness_level == "complete":
            sections["compliance_controls"]["sanctions_abc"] = ["OFSI screening", "Bribery Act 2010 compliance"]
            sections["compliance_controls"]["approvals"] = ["Maker-checker", "SoD thresholds enforced"]
            sections["compliance_controls"]["audit_trail"] = "Evidence retention for 7 years; linkage to WBS/asset IDs"
    
    # Add governance if completeness == complete
    if completeness_level == "complete":
        sections["governance_reporting"] = {
            "monthly_project_cost_reports": "Capex/Opex split; AUC roll-forward; EAC; commitments; accruals",
            "period_end_close": "GR/IR accruals; T&M accruals; reversal on invoice"
        }
        sections["wbs_asset_mapping"] = {
            "programme_wbs": sow_number,
            "components": list(scenario["component_names"].keys())
        }
    
    # Build summary
    summary = {
        "sow_number": sow_number,
        "version": "v1",
        "generated_at": datetime.now().isoformat(),
        "contract_type": contract_type,
        "completeness_level": completeness_level,
        "sections": sections,
        "open_questions": [
            "Exact indexation formula confirmation (need final approval)",
            "LD structure details (need legal review)",
            "Earnback threshold confirmation (need to verify)",
            "Change order threshold alignment (need CFO approval)"
        ] if completeness_level in ["complete", "moderate"] else [],
        "verbal_agreements": [
            f"Discussed {commercial_terms['retention']}, but release conditions need formalization",
            f"Agreed on {commercial_terms['payment_terms']}, but need to confirm exact terms"
        ]
    }
    
    return summary


# ============================================================================
# Draft Contract Generation
# ============================================================================

def generate_draft_contract_pdf(
    sow_number: str,
    base_dir: Path,
    deviation_pattern: str = "high_risk",
    contract_type: str = "large_capital",
    contract_value: Optional[int] = None,
    seed: Optional[int] = None
) -> Path:
    """Generate draft contract PDF with scenario-based deviations."""
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab is required for PDF generation")
    
    draft_dir = base_dir / "draft_contracts"
    draft_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = draft_dir / f"{sow_number}_draft_v1.pdf"
    
    # Get deviation pattern
    pattern = DEVIATION_PATTERNS[deviation_pattern]
    deviations_to_apply = pattern["deviations"]
    
    doc = SimpleDocTemplate(str(filepath), pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=18,
        textColor=colors.HexColor('#003366'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#003366'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    story.append(Paragraph("DRAFT CONTRACT", title_style))
    story.append(Paragraph(f"Project: {sow_number}", title_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # Parties
    story.append(Paragraph("Parties", heading_style))
    story.append(Paragraph(
        "This Agreement is between Company (the 'Company') and Service Provider (the 'Service Provider').",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.2 * inch))
    
    # Purpose & Scope
    story.append(Paragraph("1. PURPOSE & SCOPE", heading_style))
    story.append(Paragraph(
        "Company outsources execution of internal capital projects comprising: (i) twelve horizontal development wells with completion and flowlines; "
        "(ii) Crude Distillation Unit (CDU) upgrade and Hydrodesulfurization (HDS) unit at the coastal refinery; and (iii) a 50 km, 24-inch pipeline with terminal tankage and metering station. "
        "Scope includes materials (casing, tubing, valves, pumps, compressors, catalysts, heat exchangers) and labor (drilling crews, refinery operators, pipeline technicians).",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.2 * inch))
    
    # Pricing
    story.append(Paragraph("6. PRICING, FUNDING & PAYMENT", heading_style))
    story.append(Paragraph(
        "Contract Price: £1,250,000,000 (Upstream £400m; Refinery £650m; Downstream £200m).",
        styles['Normal']
    ))
    story.append(Paragraph("Retention: 10% until Final Acceptance.", styles['Normal']))
    # Payment Terms (with deviation if in pattern)
    if "payment_terms" in deviations_to_apply:
        story.append(Paragraph("Payment Terms: Net 45 days.", styles['Normal']))  # Deviation: pre-contract says Net 30
    else:
        story.append(Paragraph("Payment Terms: Net 30 days.", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    
    # Indexation (with deviation if in pattern)
    if "indexation" in deviations_to_apply:
        indexation_text = DEVIATIONS["indexation"]["draft"]
    else:
        indexation_text = DEVIATIONS["indexation"]["pre_contract"]
    story.append(Paragraph(f"Indexation: {indexation_text}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    
    # Liquidated Damages (with deviations if in pattern)
    story.append(Paragraph("17. LIQUIDATED DAMAGES & SERVICE CREDITS", heading_style))
    if "delay_lds" in deviations_to_apply or "performance_lds" in deviations_to_apply:
        delay_text = DEVIATIONS["delay_lds"]["draft"] if "delay_lds" in deviations_to_apply else DEVIATIONS["delay_lds"]["pre_contract"]
        perf_text = DEVIATIONS["performance_lds"]["draft"] if "performance_lds" in deviations_to_apply else DEVIATIONS["performance_lds"]["pre_contract"]
        story.append(Paragraph(
            f"Delay LDs {delay_text}; performance LDs {perf_text}.",
            styles['Normal']
        ))
    else:
        story.append(Paragraph(
            f"Delay LDs {DEVIATIONS['delay_lds']['pre_contract']}; "
            f"performance LDs {DEVIATIONS['performance_lds']['pre_contract']}.",
            styles['Normal']
        ))
    
    # Earnbacks (with deviation if in pattern)
    if "earnback" in deviations_to_apply:
        earnback_text = DEVIATIONS["earnback"]["draft"]
    else:
        earnback_text = DEVIATIONS["earnback"]["pre_contract"]
    story.append(Paragraph(earnback_text, styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    
    # Change Orders (with deviation if in pattern)
    story.append(Paragraph("Change Order Approval Thresholds", heading_style))
    if "change_order" in deviations_to_apply:
        story.append(Paragraph(
            DEVIATIONS["change_order"]["draft"],
            styles['Normal']
        ))
    else:
        story.append(Paragraph(
            DEVIATIONS["change_order"]["pre_contract"],
            styles['Normal']
        ))
    story.append(Spacer(1, 0.2 * inch))
    
    # Invoice Format (with deviation if in pattern)
    story.append(Paragraph("Invoice Format", heading_style))
    if "invoice_format" in deviations_to_apply:
        story.append(Paragraph(
            DEVIATIONS["invoice_format"]["draft"],
            styles['Normal']
        ))
    else:
        story.append(Paragraph(
            DEVIATIONS["invoice_format"]["pre_contract"],
            styles['Normal']
        ))
    
    doc.build(story)
    return filepath


# ============================================================================
# Signed Contract Generation
# ============================================================================

def generate_signed_contract_pdf(
    sow_number: str,
    base_dir: Path,
    contract_type: str = "large_capital",
    contract_value: Optional[int] = None,
    seed: Optional[int] = None
) -> Path:
    """Generate signed contract PDF (clean, final version with all deviations resolved)."""
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab is required for PDF generation")
    
    signed_dir = base_dir / "signed_contracts"
    signed_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = signed_dir / f"{sow_number}_signed.pdf"
    
    doc = SimpleDocTemplate(str(filepath), pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=18,
        textColor=colors.HexColor('#003366'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#003366'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    story.append(Paragraph("PROJECT OUTSOURCING AGREEMENT", title_style))
    story.append(Paragraph(f"Project: {sow_number}", title_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # Parties
    story.append(Paragraph("Parties", heading_style))
    story.append(Paragraph(
        "This Agreement is between Company (the 'Company') and Service Provider (the 'Service Provider').",
        styles['Normal']
    ))
    story.append(Paragraph("Effective Date: 15-Jan-2026", styles['Normal']))
    story.append(Paragraph("Governing Law: England & Wales", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    
    # Purpose & Scope
    story.append(Paragraph("1. PURPOSE & SCOPE", heading_style))
    story.append(Paragraph(
        "Company outsources execution of internal capital projects comprising: (i) twelve horizontal development wells with completion and flowlines; "
        "(ii) Crude Distillation Unit (CDU) upgrade and Hydrodesulfurization (HDS) unit at the coastal refinery; and (iii) a 50 km, 24-inch pipeline with terminal tankage and metering station. "
        "Scope includes materials (casing, tubing, valves, pumps, compressors, catalysts, heat exchangers) and labor (drilling crews, refinery operators, pipeline technicians).",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.2 * inch))
    
    # Pricing (all terms from pre-contract, deviations resolved)
    story.append(Paragraph("6. PRICING, FUNDING & PAYMENT", heading_style))
    story.append(Paragraph(
        "Contract Price: £1,250,000,000 (Upstream £400m; Refinery £650m; Downstream £200m).",
        styles['Normal']
    ))
    story.append(Paragraph("Retention: 10% until Final Acceptance; release conditions defined.", styles['Normal']))
    story.append(Paragraph("Payment Terms: Net 30 days.", styles['Normal']))  # Resolved: matches pre-contract
    story.append(Paragraph("Indexation: UK CPI/WPI ±3% p.a.", styles['Normal']))  # Resolved: contract standard (matches draft)
    story.append(Spacer(1, 0.2 * inch))
    
    # Liquidated Damages (resolved to contract standards)
    story.append(Paragraph("17. LIQUIDATED DAMAGES & SERVICE CREDITS", heading_style))
    story.append(Paragraph(
        "Delay LDs £50k/week capped at 10% of Contract Price; "
        "performance LDs £25k per percentage point shortfall capped at 5%.",
        styles['Normal']
    ))  # Resolved: contract standards (matches draft)
    story.append(Paragraph(
        "Earnbacks permitted on sustained ≥105% KPI for three consecutive months.",
        styles['Normal']
    ))  # Resolved: contract standard (matches draft)
    story.append(Spacer(1, 0.2 * inch))
    
    # Change Orders (resolved)
    story.append(Paragraph("Change Order Approval Thresholds", heading_style))
    story.append(Paragraph(
        "up to £2m (Project Manager), £2–£5m (Steering Committee), >£5m CFO.",
        styles['Normal']
    ))  # Resolved: contract standard (matches draft)
    story.append(Spacer(1, 0.2 * inch))
    
    # Invoice Format (resolved: includes all required fields from pre-contract)
    story.append(Paragraph("Invoice Format", heading_style))
    story.append(Paragraph(
        "Must include contract reference, WBS/asset IDs, PO number, milestone achieved, AFIU status, retention amount, tax details.",
        styles['Normal']
    ))  # Resolved: includes all pre-contract requirements
    
    # Signatures
    story.append(PageBreak())
    story.append(Paragraph("SIGNATURES", heading_style))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Company:", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("_________________________", styles['Normal']))
    story.append(Paragraph("Authorized Signatory", styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Service Provider:", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("_________________________", styles['Normal']))
    story.append(Paragraph("Authorized Signatory", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Date: 15-Jan-2026", styles['Normal']))
    
    doc.build(story)
    return filepath


# ============================================================================
# Change Order Generation
# ============================================================================

def generate_change_order_pdf(
    sow_number: str,
    base_dir: Path,
    version: str,
    contract_type: str = "large_capital",
    contract_value: Optional[int] = None,
    previous_change_orders: Optional[List[Path]] = None,
    seed: Optional[int] = None
) -> Path:
    """Generate change order PDF that modifies terms from signed SOW and previous change orders."""
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab is required for PDF generation")
    
    change_orders_dir = base_dir / "change_orders"
    change_orders_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = change_orders_dir / f"{sow_number}_change_order_{version}.pdf"
    
    doc = SimpleDocTemplate(str(filepath), pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=18,
        textColor=colors.HexColor('#cc6600'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#cc6600'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    story.append(Paragraph("CHANGE ORDER", title_style))
    story.append(Paragraph(f"Project: {sow_number}", title_style))
    story.append(Paragraph(f"Change Order {version}", title_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # Change Order Metadata
    story.append(Paragraph("Change Order Information", heading_style))
    story.append(Paragraph(f"Change Order Number: {version}", styles['Normal']))
    story.append(Paragraph(f"Date: {(datetime.now() + timedelta(days=90)).strftime('%d-%b-%Y')}", styles['Normal']))
    story.append(Paragraph("Reason: Scope expansion and timeline adjustment", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    
    # Modified Terms
    story.append(Paragraph("1. MODIFIED TERMS", heading_style))
    
    # Example modifications - these would be based on signed SOW + previous change orders
    story.append(Paragraph("1.1 Payment Terms", styles['Heading3']))
    story.append(Paragraph(
        "Original: Net 30 days from invoice date",
        styles['Normal']
    ))
    story.append(Paragraph(
        "Modified: Net 45 days from invoice date",
        styles['Normal']
    ))
    story.append(Paragraph(
        "Rationale: Extended payment terms to align with project cash flow requirements.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.15 * inch))
    
    story.append(Paragraph("1.2 Scope Modification", styles['Heading3']))
    if contract_type == "large_capital":
        story.append(Paragraph(
            "Original: 50 km, 24-inch pipeline with terminal tanks",
            styles['Normal']
        ))
        story.append(Paragraph(
            "Modified: 60 km, 24-inch pipeline with terminal tanks (10 km extension added)",
            styles['Normal']
        ))
        story.append(Paragraph(
            "Rationale: Client requested additional 10 km pipeline segment to connect to new facility.",
            styles['Normal']
        ))
    elif contract_type == "medium_infrastructure":
        story.append(Paragraph(
            "Original: FCC unit revamp and heat exchanger network optimization",
            styles['Normal']
        ))
        story.append(Paragraph(
            "Modified: FCC unit revamp, heat exchanger network optimization, and additional catalyst storage (2 × 500 m³ tanks)",
            styles['Normal']
        ))
        story.append(Paragraph(
            "Rationale: Additional catalyst storage required for extended operations.",
            styles['Normal']
        ))
    else:  # small_service
        story.append(Paragraph(
            "Original: Pipeline integrity management and terminal operations",
            styles['Normal']
        ))
        story.append(Paragraph(
            "Modified: Pipeline integrity management, terminal operations, and additional metering station",
            styles['Normal']
        ))
        story.append(Paragraph(
            "Rationale: Additional metering station required for new pipeline segment.",
            styles['Normal']
        ))
    story.append(Spacer(1, 0.15 * inch))
    
    story.append(Paragraph("1.3 Milestone Adjustment", styles['Heading3']))
    story.append(Paragraph(
        "Original: Pipeline completion milestone - Due: 2025-12-31",
        styles['Normal']
    ))
    story.append(Paragraph(
        "Modified: Pipeline completion milestone - Due: 2026-03-31 (extended by 3 months)",
        styles['Normal']
    ))
    story.append(Paragraph(
        "Rationale: Timeline extension required to accommodate scope expansion.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.15 * inch))
    
    story.append(Paragraph("1.4 Deliverables", styles['Heading3']))
    story.append(Paragraph(
        "Original: Pipeline, Terminal tanks, Metering station",
        styles['Normal']
    ))
    story.append(Paragraph(
        "Modified: Pipeline (60 km), Terminal tanks, Metering station, Additional 10 km pipeline segment",
        styles['Normal']
    ))
    story.append(Paragraph(
        "Rationale: New deliverable added to support scope expansion.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.2 * inch))
    
    # Financial Impact
    story.append(Paragraph("2. FINANCIAL IMPACT", heading_style))
    if contract_value:
        additional_value = int(contract_value * 0.04)  # ~4% increase
        story.append(Paragraph(
            f"Original Contract Value: £{contract_value:,}",
            styles['Normal']
        ))
        story.append(Paragraph(
            f"Additional Value: £{additional_value:,}",
            styles['Normal']
        ))
        story.append(Paragraph(
            f"Revised Contract Value: £{contract_value + additional_value:,}",
            styles['Normal']
        ))
    story.append(Spacer(1, 0.2 * inch))
    
    # Approval
    story.append(PageBreak())
    story.append(Paragraph("APPROVAL", heading_style))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Company:", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("_________________________", styles['Normal']))
    story.append(Paragraph("Authorized Signatory", styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Service Provider:", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("_________________________", styles['Normal']))
    story.append(Paragraph("Authorized Signatory", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(f"Date: {(datetime.now() + timedelta(days=90)).strftime('%d-%b-%Y')}", styles['Normal']))
    
    doc.build(story)
    return filepath


# ============================================================================
# Historical WBS Generation
# ============================================================================

def generate_historical_wbs(base_dir: Path) -> List[Path]:
    """Generate historical WBS documents (reference data)."""
    historical_wbs_dir = base_dir / "historical_wbs"
    historical_wbs_dir.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    
    # Simple WBS (3-5 deliverables)
    simple_wbs = f"""# Work Breakdown Structure
## CONTRACT-2024-050

### 1.0 Project Initiation
1.1. Kickoff Meeting
1.2. Requirements Gathering
1.3. Project Plan Approval

### 2.0 Development
2.1. System Design
2.2. Implementation
2.3. Testing

### 3.0 Deployment
3.1. Deployment Planning
3.2. Go-Live
3.3. Post-Deployment Support

### Timeline
- Start: Q1 2024
- Completion: Q2 2024
- Duration: 12 weeks
"""
    simple_path = historical_wbs_dir / "CONTRACT-2024-050_wbs_v1.md"
    simple_path.write_text(simple_wbs, encoding="utf-8")
    generated_files.append(simple_path)
    
    # Medium WBS (6-10 deliverables)
    medium_wbs = f"""# Work Breakdown Structure
## CONTRACT-2024-051

### 1.0 Project Initiation
1.1. Stakeholder Alignment
1.2. Requirements Analysis
1.3. Technical Architecture Design
1.4. Project Plan & Approval

### 2.0 Development Phase
2.1. Core System Development
2.2. Integration Development
2.3. UI/UX Development
2.4. Unit Testing

### 3.0 Testing Phase
3.1. System Integration Testing
3.2. User Acceptance Testing
3.3. Performance Testing

### 4.0 Deployment
4.1. Deployment Planning
4.2. Production Deployment
4.3. Post-Deployment Support

### Timeline
- Start: Q2 2024
- Completion: Q4 2024
- Duration: 24 weeks
"""
    medium_path = historical_wbs_dir / "CONTRACT-2024-051_wbs_v1.md"
    medium_path.write_text(medium_wbs, encoding="utf-8")
    generated_files.append(medium_path)
    
    # Complex WBS (11-15 deliverables)
    complex_wbs = f"""# Work Breakdown Structure
## CONTRACT-2024-052

### 1.0 Project Initiation
1.1. Stakeholder Kickoff
1.2. Requirements Gathering
1.3. Business Process Analysis
1.4. Technical Architecture Design
1.5. Security & Compliance Review
1.6. Project Plan & Approval

### 2.0 Development Phase
2.1. Core System Development
    2.1.1. Backend Services
    2.1.2. API Development
    2.1.3. Database Design
2.2. Integration Development
    2.2.1. Third-party Integrations
    2.2.2. Legacy System Integration
2.3. UI/UX Development
2.4. Mobile App Development
2.5. Unit Testing

### 3.0 Testing Phase
3.1. System Integration Testing
3.2. Security Testing
3.3. Performance Testing
3.4. User Acceptance Testing

### 4.0 Deployment
4.1. Deployment Planning
4.2. Staging Environment Setup
4.3. Production Deployment
4.4. Post-Deployment Support

### Timeline
- Start: Q1 2024
- Completion: Q3 2024
- Duration: 36 weeks
"""
    complex_path = historical_wbs_dir / "CONTRACT-2024-052_wbs_v1.md"
    complex_path.write_text(complex_wbs, encoding="utf-8")
    generated_files.append(complex_path)
    
    return generated_files


# ============================================================================
# Main Functions
# ============================================================================

def option_1_pre_contract(
    base_dir: Path,
    sow_number: str,
    keep_existing: bool,
    contract_type: str = "large_capital",
    completeness_level: str = "complete",
    communication_style: str = "formal",
    seed: Optional[int] = None
) -> None:
    """Option 1: Generate pre-contract artifacts with scenario-based variations."""
    print(f"\n{'='*70}")
    print("Generating Mock Data: Pre-Contract Notes Synthesis")
    print(f"{'='*70}\n")
    
    scenario = CONTRACT_TYPE_SCENARIOS[contract_type]
    completeness = COMPLETENESS_LEVELS[completeness_level]
    style = COMMUNICATION_STYLES[communication_style]
    
    print(f"SOW Number: {sow_number} (auto-generated)")
    print(f"Contract Type: {scenario['name']} ({scenario['industry_name']})")
    print(f"Completeness: {completeness['name']} ({completeness['sections']} sections)")
    print(f"Communication Style: {style['name']}")
    if seed is not None:
        print(f"Seed: {seed} (reproducible)")
    print()
    
    if not keep_existing:
        print("Clearing existing mock data...")
        clear_covenant_data(base_dir, keep_existing=False)
        print()
    
    print("Generating pre-contract artifacts...")
    contract_value = get_contract_value(contract_type, seed)
    files = generate_pre_contract_data(
        base_dir, sow_number, contract_type, completeness_level, communication_style, contract_value, seed
    )
    
    for file in files:
        print(f"  ✓ Generated: {file.relative_to(base_dir)}")
    
    print(f"\n✅ Mock data ready for Pre-Contract Notes Synthesis pipeline")
    print(f"\nFiles generated: {len(files)} files")
    for file in files:
        print(f"  • {file.relative_to(base_dir)}")


def option_2_draft_validation(
    base_dir: Path,
    sow_number: str,
    keep_existing: bool,
    contract_type: str = "large_capital",
    deviation_pattern: str = "high_risk",
    completeness_level: str = "complete",
    communication_style: str = "formal",
    seed: Optional[int] = None
) -> None:
    """Option 2: Generate draft contract validation data with scenario-based variations."""
    print(f"\n{'='*70}")
    print("Generating Mock Data: Draft Contract Validation")
    print(f"{'='*70}\n")
    
    # If keep_existing is True, try to find existing contract IDs first
    if keep_existing:
        existing_sow_numbers = find_existing_sow_numbers(base_dir)
        if existing_sow_numbers:
            # Use the most recent existing SOW number
            sow_number = existing_sow_numbers[-1]
            print(f"SOW Number: {sow_number} (using existing)")
        else:
            print(f"SOW Number: {sow_number} (auto-generated - no existing SOWs found)")
    else:
        print(f"SOW Number: {sow_number} (auto-generated)")
    
    scenario = CONTRACT_TYPE_SCENARIOS[contract_type]
    pattern = DEVIATION_PATTERNS[deviation_pattern]
    completeness = COMPLETENESS_LEVELS[completeness_level]
    
    print(f"Contract Type: {scenario['name']} ({scenario['industry_name']})")
    print(f"Deviation Pattern: {pattern['name']} ({pattern['description']})")
    print(f"  Deviations: {', '.join(pattern['deviations']) if pattern['deviations'] else 'None (perfect match)'}")
    print(f"Completeness: {completeness['name']} ({completeness['sections']} sections)")
    if seed is not None:
        print(f"Seed: {seed} (reproducible)")
    print()
    
    existing = check_existing_data(base_dir, sow_number)
    
    if keep_existing and existing["pre_contract_exists"]:
        print("Checking existing data...")
        print("  ✓ Found: Pre-contract artifacts (will use existing)")
        if existing["pre_contract_summary_exists"]:
            print("  ✓ Found: Pre-contract summary (will use existing)")
        else:
            print("  ⚠️  Pre-contract summary not found. Generating summary...")
            # Try to infer contract_type and completeness from existing summary or use defaults
            artifacts_dir = base_dir / "artifacts" / sow_number
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            summary_path = artifacts_dir / "pre_contract_summary_v1.json"
            # Try to read existing summary to get contract_type and completeness
            contract_value = get_contract_value(contract_type, seed)
            summary_path.write_text(json.dumps(
                generate_pre_contract_summary(sow_number, contract_type, completeness_level, contract_value, seed),
                indent=2
            ), encoding="utf-8")
            print(f"  ✓ Generated: {summary_path.relative_to(base_dir)}")
        print("\nGenerating draft contract only...")
        files_to_generate = []
        contract_value = None  # Will be inferred from existing data
    else:
        print("Checking existing data...")
        print("  ⚠️  No previous data found. Generating pre-contract artifacts + summary + draft...")
        if not keep_existing:
            print("\nClearing existing mock data...")
            clear_covenant_data(base_dir, keep_existing=False)
            print()
        print("Generating pre-contract artifacts...")
        contract_value = get_contract_value(contract_type, seed)
        files_to_generate = generate_pre_contract_data(
            base_dir, sow_number, contract_type, completeness_level, communication_style, contract_value, seed
        )
        
        # Generate pre-contract summary (simulated pipeline output)
        artifacts_dir = base_dir / "artifacts" / sow_number
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        summary_path = artifacts_dir / "pre_contract_summary_v1.json"
        summary_path.write_text(json.dumps(
            generate_pre_contract_summary(sow_number, contract_type, completeness_level, contract_value, seed),
            indent=2
        ), encoding="utf-8")
        files_to_generate.append(summary_path)
        print(f"  ✓ Generated: {summary_path.relative_to(base_dir)}")
    
    # Generate draft contract with deviation pattern
    print("\nGenerating draft contract...")
    draft_path = generate_draft_contract_pdf(
        sow_number, base_dir, deviation_pattern, contract_type, contract_value, seed
    )
    files_to_generate.append(draft_path)
    print(f"  ✓ Generated: {draft_path.relative_to(base_dir)}")
    
    print(f"\n✅ Mock data ready for Draft Contract Validation pipeline")
    print(f"\nFiles generated: {len(files_to_generate)} file(s)")
    for file in files_to_generate:
        print(f"  • {file.relative_to(base_dir)}")


def option_3_signed_contract(
    base_dir: Path,
    sow_number: str,
    keep_existing: bool,
    contract_type: str = "large_capital",
    completeness_level: str = "complete",
    seed: Optional[int] = None
) -> None:
    """Option 3: Generate signed contract intelligence data with scenario-based variations."""
    print(f"\n{'='*70}")
    print("Generating Mock Data: Signed Contract Intelligence")
    print(f"{'='*70}\n")
    
    # If keep_existing is True, try to find existing SOW numbers first
    if keep_existing:
        existing_sow_numbers = find_existing_sow_numbers(base_dir)
        if existing_sow_numbers:
            # Use the most recent existing SOW number
            sow_number = existing_sow_numbers[-1]
            print(f"SOW Number: {sow_number} (using existing)")
        else:
            print(f"SOW Number: {sow_number} (auto-generated - no existing SOWs found)")
    else:
        print(f"SOW Number: {sow_number} (auto-generated)")
    
    scenario = CONTRACT_TYPE_SCENARIOS[contract_type]
    completeness = COMPLETENESS_LEVELS[completeness_level]
    
    print(f"Contract Type: {scenario['name']} ({scenario['industry_name']})")
    print(f"Completeness: {completeness['name']} ({completeness['sections']} sections)")
    if seed is not None:
        print(f"Seed: {seed} (reproducible)")
    print()
    
    existing = check_existing_data(base_dir, sow_number)
    
    if not keep_existing:
        print("Clearing existing mock data...")
        clear_covenant_data(base_dir, keep_existing=False)
        print()
    else:
        # Check what exists from previous options
        print("Checking existing data from previous pipeline stages...")
        found_items = []
        if existing["pre_contract_exists"]:
            found_items.append("Pre-contract artifacts (Option 1)")
        if existing["pre_contract_summary_exists"]:
            found_items.append("Pre-contract summary (Option 1 agent output)")
        if existing["pre_contract_report_exists"]:
            found_items.append("Pre-contract synthesis report (Option 1 agent output)")
        if existing["draft_contract_exists"]:
            found_items.append("Draft contract (Option 2)")
        if existing["draft_validation_report_exists"]:
            found_items.append("Draft validation report (Option 2 agent output)")
        if existing["signed_contract_exists"]:
            found_items.append("Signed contract (already exists)")
        if existing["signed_contract_summary_exists"]:
            found_items.append("Signed contract summary (already exists)")
        if existing["wbs_exists"]:
            found_items.append("WBS (already exists)")
        
        if found_items:
            print("  ✓ Found existing data:")
            for item in found_items:
                print(f"    • {item}")
        else:
            print("  ⚠️  No previous data found. Will generate signed contract only.")
        print()
    
    # Check and generate historical WBS if missing
    print("Checking historical WBS (reference data)...")
    if not check_historical_wbs(base_dir):
        print("  ⚠️  Historical WBS not found. Generating reference data...")
        print("\nGenerating historical WBS documents...")
        wbs_files = generate_historical_wbs(base_dir)
        for wbs_file in wbs_files:
            print(f"  ✓ Generated: {wbs_file.relative_to(base_dir)}")
    else:
        print("  ✓ Found: 3 historical WBS documents (already exist)")
    
    # Generate signed contract (only if it doesn't exist or keep_existing is False)
    if existing["signed_contract_exists"] and keep_existing:
        print("\nSigned contract already exists. Skipping generation.")
        print(f"  ✓ Using existing: signed_contracts/{sow_number}_signed.pdf")
        signed_path = base_dir / "signed_contracts" / f"{sow_number}_signed.pdf"
    else:
        print("\nGenerating signed contract...")
        contract_value = get_contract_value(contract_type, seed)
        signed_path = generate_signed_contract_pdf(sow_number, base_dir, contract_type, contract_value, seed)
        print(f"  ✓ Generated: {signed_path.relative_to(base_dir)}")
    
    # Extract SOW terms from signed contract and write to global memory
    # Note: In a real scenario, these would be extracted by the Covenant agent
    # For now, we'll generate sample terms based on contract type
    print("\nWriting contract data to global memory for Aegis...")
    project_dir = base_dir.parent.parent  # Go up from data/covenant to project root
    effective_date = datetime.now().strftime("%Y-%m-%d")
    
    # Determine invoice type based on contract type
    # large_capital -> PROFORMA (comprehensive, both labor and materials)
    # medium_infrastructure -> MATERIAL (material handling focus)
    # small_service -> LABOR (service/labor focus)
    invoice_type_map = {
        "large_capital": "PROFORMA",
        "medium_infrastructure": "MATERIAL",
        "small_service": "LABOR"
    }
    invoice_type = invoice_type_map.get(contract_type, "PROFORMA")
    
    # Generate vendor name (simplified - in real scenario would come from contract)
    vendor_name = "Service Provider Corporation"
    
    # 1. Write SOW terms
    sow_terms = {
        "retention_percentage": 10.0 if contract_type == "large_capital" else 5.0,
        "ld_applicable": True,
        "ld_rate_per_day": 500.0 if contract_type == "large_capital" else 300.0,
        "milestones": [],
        "effective_date": effective_date
    }
    write_sow_terms_to_global_memory(sow_number, sow_terms, project_dir)
    print(f"  ✓ Wrote SOW terms: {sow_number}")
    
    # 2. Write rate cards (only for LABOR and PROFORMA invoice types)
    if invoice_type in ["LABOR", "PROFORMA"]:
        rate_cards = []
        if invoice_type == "LABOR":
            # Generate labor rate cards
            rate_cards = [
                {
                    "item_code": "LAB-ENG-SR",
                    "description": "Senior Engineer - Labor",
                    "unit_price": 150.0,
                    "effective_date": effective_date,
                    "expiry_date": None
                },
                {
                    "item_code": "LAB-ENG-JR",
                    "description": "Junior Engineer - Labor",
                    "unit_price": 100.0,
                    "effective_date": effective_date,
                    "expiry_date": None
                },
                {
                    "item_code": "LAB-TECH",
                    "description": "Technician - Labor",
                    "unit_price": 75.0,
                    "effective_date": effective_date,
                    "expiry_date": None
                }
            ]
        elif invoice_type == "PROFORMA":
            # Generate comprehensive rate cards (labor + material)
            rate_cards = [
                {
                    "item_code": "LAB-ENG-SR",
                    "description": "Senior Engineer - Labor",
                    "unit_price": 150.0,
                    "effective_date": effective_date,
                    "expiry_date": None
                },
                {
                    "item_code": "LAB-ENG-JR",
                    "description": "Junior Engineer - Labor",
                    "unit_price": 100.0,
                    "effective_date": effective_date,
                    "expiry_date": None
                },
                {
                    "item_code": "MAT-EQUIP-001",
                    "description": "Equipment Component - Material",
                    "unit_price": 5000.0,
                    "effective_date": effective_date,
                    "expiry_date": None
                },
                {
                    "item_code": "MAT-SUPPLY-001",
                    "description": "Supply Material - Material",
                    "unit_price": 250.0,
                    "effective_date": effective_date,
                    "expiry_date": None
                }
            ]
        
        write_rate_cards_to_global_memory(sow_number, vendor_name, rate_cards, project_dir, effective_date)
        print(f"  ✓ Wrote rate cards: {len(rate_cards)} rate card(s)")
    
    # 3. Write evidence requirements
    work_type_map = {
        "LABOR": "labor",
        "MATERIAL": "material",
        "PROFORMA": "mixed"
    }
    work_type = work_type_map.get(invoice_type, "mixed")
    
    # Evidence requirements based on invoice type
    if invoice_type == "LABOR":
        required_evidence_types = ["Timesheet"]
        coverage_requirements = {
            "Timesheet": {
                "required": True,
                "frequency": "weekly",
                "fields": ["employee_name", "hours", "date", "role"]
            }
        }
    elif invoice_type == "MATERIAL":
        required_evidence_types = ["GRN"]
        coverage_requirements = {
            "GRN": {
                "required": True,
                "frequency": "per_delivery",
                "fields": ["grn_number", "delivery_date", "quantity", "item_code"]
            }
        }
    else:  # PROFORMA
        required_evidence_types = ["Timesheet", "Completion-Cert", "GRN"]
        coverage_requirements = {
            "Timesheet": {
                "required": True,
                "frequency": "weekly",
                "fields": ["employee_name", "hours", "date", "role"]
            },
            "Completion-Cert": {
                "required": True,
                "frequency": "per_milestone",
                "fields": ["certificate_number", "completion_date", "signatory"]
            },
            "GRN": {
                "required": True,
                "frequency": "per_delivery",
                "fields": ["grn_number", "delivery_date", "quantity", "item_code"]
            }
        }
    
    write_evidence_requirements_to_global_memory(
        sow_number, work_type, required_evidence_types, coverage_requirements, project_dir, effective_date
    )
    print(f"  ✓ Wrote evidence requirements: {len(required_evidence_types)} evidence type(s)")
    
    # 4. Write SOW metadata
    pricing_model_map = {
        "large_capital": "milestone_based",
        "medium_infrastructure": "fixed_price",
        "small_service": "time_and_materials"
    }
    pricing_model = pricing_model_map.get(contract_type, "time_and_materials")
    
    write_sow_metadata_to_global_memory(
        sow_number, invoice_type, vendor_name, None, scenario.get("name"), pricing_model, project_dir, effective_date
    )
    print(f"  ✓ Wrote SOW metadata: invoice_type={invoice_type}, pricing_model={pricing_model}")
    
    print(f"\n✅ Mock data ready for Signed Contract Intelligence pipeline")
    
    # Show what will be used by the pipeline
    files_summary = []
    if existing["pre_contract_exists"] or not keep_existing:
        files_summary.append(f"  • pre_contract/{sow_number}/ (from Option 1)")
    if existing["pre_contract_summary_exists"] or not keep_existing:
        files_summary.append(f"  • artifacts/{sow_number}/pre_contract_summary_v1.json (from Option 1)")
    if existing["draft_contract_exists"] or not keep_existing:
        files_summary.append(f"  • draft_contracts/{sow_number}_draft_v1.pdf (from Option 2)")
    if existing["draft_validation_report_exists"]:
        files_summary.append(f"  • artifacts/{sow_number}/draft_contract_validation_report.json (from Option 2)")
    files_summary.append(f"  • {signed_path.relative_to(base_dir)} (new)")
    files_summary.append(f"  • historical_wbs/ (3 files, reference data)")
    
    print(f"\nFiles available for pipeline:")
    for item in files_summary:
        print(item)


def option_4_change_order(
    base_dir: Path,
    sow_number: str,
    keep_existing: bool,
    contract_type: str = "large_capital",
    seed: Optional[int] = None
) -> None:
    """Option 4: Generate change order data with versioning support."""
    print(f"\n{'='*70}")
    print("Generating Mock Data: Change Order Review")
    print(f"{'='*70}\n")
    
    # If keep_existing is True, try to find existing contract IDs first
    if keep_existing:
        existing_sow_numbers = find_existing_sow_numbers(base_dir)
        if existing_sow_numbers:
            # Use the most recent existing SOW number
            sow_number = existing_sow_numbers[-1]
            print(f"SOW Number: {sow_number} (using existing)")
        else:
            print(f"SOW Number: {sow_number} (auto-generated - no existing SOWs found)")
    else:
        print(f"SOW Number: {sow_number} (auto-generated)")
    
    scenario = CONTRACT_TYPE_SCENARIOS[contract_type]
    print(f"Contract Type: {scenario['name']} ({scenario['industry_name']})")
    if seed is not None:
        print(f"Seed: {seed} (reproducible)")
    print()
    
    existing = check_existing_data(base_dir, sow_number)
    
    # Check if signed contract exists (required for change orders)
    if not existing["signed_contract_exists"]:
        print("⚠️  Error: Signed contract (SOW) not found.")
        print(f"   Change orders require a signed contract from Option 3.")
        print(f"   Expected file: signed_contracts/{sow_number}_signed.pdf")
        print(f"   Please run Option 3 first to generate signed contract.")
        return
    
    print("Checking existing data...")
    print(f"  ✓ Found: Signed contract (required for change orders)")
    
    # Check for existing change orders
    existing_change_orders = find_existing_change_orders(base_dir, sow_number)
    if existing_change_orders:
        print(f"  ✓ Found: {len(existing_change_orders)} existing change order(s)")
        for co in existing_change_orders:
            print(f"    • {co.name}")
    else:
        print("  ✓ No existing change orders found (will generate v1)")
    print()
    
    # Get next version number
    version = get_next_change_order_version(base_dir, sow_number)
    print(f"Generating change order {version}...")
    
    # Get contract value for change order generation
    contract_value = get_contract_value(contract_type, seed)
    
    # Generate change order PDF
    change_order_path = generate_change_order_pdf(
        sow_number=sow_number,
        base_dir=base_dir,
        version=version,
        contract_type=contract_type,
        contract_value=contract_value,
        previous_change_orders=existing_change_orders if existing_change_orders else None,
        seed=seed
    )
    print(f"  ✓ Generated: {change_order_path.relative_to(base_dir)}")
    
    print(f"\n✅ Mock data ready for Change Order Review pipeline")
    
    # Show what will be used by the pipeline
    files_summary = []
    files_summary.append(f"  • signed_contracts/{sow_number}_signed.pdf (required)")
    if existing["signed_contract_summary_exists"]:
        files_summary.append(f"  • artifacts/{sow_number}/signed_contract_structured_summary.json (if available)")
    files_summary.append(f"  • {change_order_path.relative_to(base_dir)} (new)")
    if existing_change_orders:
        files_summary.append(f"  • Previous change orders: {len(existing_change_orders)} file(s)")
    
    print(f"\nFiles available for pipeline:")
    for item in files_summary:
        print(item)


def run_interactive_mode(base_dir: Path, seed: Optional[int] = None):
    """Run interactive menu mode with scenario-based generation."""
    # Initialize random seed if provided
    initialize_random(seed)
    
    while True:
        print("\n" + "╔" + "═"*68 + "╗")
        print("║" + " " * 20 + "Covenant Mock Data Generator" + " " * 20 + "║")
        print("╚" + "═"*68 + "╝")
        print("\nSelect pipeline to generate mock data for:")
        print("  1. Pre-Contract Notes Synthesis")
        print("     → Generates: 4 pre-contract artifact files (emails, meeting notes, scope doc)")
        print("     → Pipeline output: pre_contract_summary_v1.json + synthesis report")
        print()
        print("  2. Draft Contract Validation")
        print("     → Generates: Draft contract PDF (with deviations)")
        print("     → Requires: Pre-contract data from Option 1 (if keeping existing)")
        print("     → Pipeline output: draft_contract_validation_report.json")
        print()
        print("  3. Signed Contract Intelligence")
        print("     → Generates: Signed contract PDF (clean, final version)")
        print("     → Requires: Pre-contract data from Option 1 + draft from Option 2 (if keeping existing)")
        print("     → Pipeline output: signed_contract_structured_summary.json + proposed_wbs_v1.json")
        print()
        print("  4. Change Order Review")
        print("     → Generates: Change order PDF (modifies signed SOW)")
        print("     → Requires: Signed contract from Option 3 (SOW)")
        print("     → Supports versioning: Checks for existing change orders and asks user")
        print("     → Pipeline output: change_order_*_comparison_report.json + risk assessment")
        print()
        print("  5. Delete All Subfolders")
        print("     → Deletes: All subfolders from data/covenant/ directory")
        print("     → Warning: This action cannot be undone!")
        print()
        print("  0. Exit")
        if seed is not None:
            print(f"\n📌 Using seed: {seed} (reproducible scenarios)")
        
        try:
            choice = input("\nEnter choice [0-5]: ").strip()
            
            if choice == "0":
                print("\nExiting...")
                break
            elif choice == "5":
                print("\n" + "-"*70)
                print("OPTION 5: Delete All Subfolders")
                print("-"*70)
                delete_all_subfolders(base_dir)
                print("\n" + "="*70)
                print("Operation Complete!")
                print("="*70)
                
                # Ask if user wants to continue
                continue_input = input("\nPress Enter to return to menu (or 'q' to quit): ").strip().lower()
                if continue_input in ["q", "quit", "exit"]:
                    break
            elif choice == "4":
                # Option 4: Change Order Review
                existing_sow_numbers = find_existing_sow_numbers(base_dir)
                if existing_sow_numbers:
                    print(f"\n✓ Found {len(existing_sow_numbers)} existing SOW(s): {', '.join(existing_sow_numbers)}")
                    sow_number = existing_sow_numbers[-1]
                    print(f"Using SOW: {sow_number}")
                else:
                    print("\n⚠️  No existing contracts found.")
                    print("Change orders require a signed contract (SOW) from Option 3.")
                    print("Please run Option 3 first to generate signed contract.")
                    continue_input = input("\nPress Enter to return to menu (or 'q' to quit): ").strip().lower()
                    if continue_input in ["q", "quit", "exit"]:
                        break
                    continue
                
                # Select contract type (randomly or based on seed)
                contract_type = select_contract_type_scenario(seed)
                
                option_4_change_order(base_dir, sow_number, keep_existing=True, contract_type=contract_type, seed=seed)
                
                print("\n" + "="*70)
                print("Setup Complete!")
                print("="*70)
                
                # Ask if user wants to continue
                continue_input = input("\nPress Enter to return to menu (or 'q' to quit): ").strip().lower()
                if continue_input in ["q", "quit", "exit"]:
                    break
            elif choice in ["1", "2", "3"]:
                option = int(choice)
                
                # Select scenarios (randomly or based on seed)
                contract_type = select_contract_type_scenario(seed)
                deviation_pattern = select_deviation_pattern(seed)
                completeness_level = select_completeness_level(seed)
                communication_style = select_communication_style(seed)
                
                sow_number = generate_sow_number(seed)
                
                # Show what will happen and ask about keep-existing with clearer prompt
                print("\n" + "-"*70)
                if option == 1:
                    print("OPTION 1: Pre-Contract Notes Synthesis")
                    print("-"*70)
                    print("\nWhat will be generated:")
                    print(f"  • pre_contract/{sow_number}/email_thread_1.txt")
                    print(f"  • pre_contract/{sow_number}/email_thread_2.txt")
                    print(f"  • pre_contract/{sow_number}/meeting_notes_2025-01-10.md")
                    print(f"  • pre_contract/{sow_number}/informal_scope_doc.pdf")
                    print("\n⚠️  WARNING: If you choose 'N' (clear existing), ALL existing mock data")
                    print("   will be deleted (except historical_wbs/).")
                    print("\n   Choose 'Y' (keep existing) to add new contract data without clearing.")
                    keep_existing_input = input("\nKeep existing data and add new contract? (Y/n): ").strip().lower()
                    keep_existing = keep_existing_input not in ["n", "no"]
                elif option == 2:
                    print("OPTION 2: Draft Contract Validation")
                    print("-"*70)
                    existing_sow_numbers = find_existing_sow_numbers(base_dir)
                    if existing_sow_numbers:
                        print(f"\n✓ Found {len(existing_sow_numbers)} existing SOW(s): {', '.join(existing_sow_numbers)}")
                        print("\nWhat will happen:")
                        print("  • If you choose 'Y' (keep existing):")
                        print(f"    - Will use existing SOW: {existing_sow_numbers[-1]}")
                        print("    - Will reuse pre-contract artifacts from Option 1")
                        print(f"    - Will generate: draft_contracts/{sow_number}_draft_v1.pdf")
                        print("  • If you choose 'N' (clear existing):")
                        print("    - Will clear ALL existing data (except historical_wbs/)")
                        print("    - Will generate new pre-contract artifacts + summary + draft contract")
                    else:
                        print("\n⚠️  No existing SOWs found.")
                        print("\nWhat will be generated:")
                        print(f"  • pre_contract/{sow_number}/ (4 files)")
                        print(f"  • artifacts/{sow_number}/pre_contract_summary_v1.json")
                        print(f"  • draft_contracts/{sow_number}_draft_v1.pdf")
                        print("\n⚠️  WARNING: If you choose 'N' (clear existing), ALL existing mock data")
                        print("   will be deleted (except historical_wbs/).")
                    keep_existing_input = input("\nKeep existing data? (Y/n): ").strip().lower()
                    keep_existing = keep_existing_input not in ["n", "no"]
                elif option == 3:
                    print("OPTION 3: Signed Contract Intelligence")
                    print("-"*70)
                    existing_sow_numbers = find_existing_sow_numbers(base_dir)
                    if existing_sow_numbers:
                        print(f"\n✓ Found {len(existing_sow_numbers)} existing SOW(s): {', '.join(existing_sow_numbers)}")
                        print("\nWhat will happen:")
                        print("  • If you choose 'Y' (keep existing):")
                        print(f"    - Will use existing SOW: {existing_sow_numbers[-1]}")
                        print("    - Will reuse pre-contract data from Option 1")
                        print("    - Will reuse draft contract from Option 2 (if exists)")
                        print(f"    - Will generate: signed_contracts/{sow_number}_signed.pdf")
                        print("  • If you choose 'N' (clear existing):")
                        print("    - Will clear ALL existing data (except historical_wbs/)")
                        print("    - Will generate new signed contract only")
                    else:
                        print("\n⚠️  No existing SOWs found.")
                        print("\nWhat will be generated:")
                        print(f"  • signed_contracts/{sow_number}_signed.pdf")
                        print("  • historical_wbs/ (3 reference files, if missing)")
                        print("\n⚠️  WARNING: If you choose 'N' (clear existing), ALL existing mock data")
                        print("   will be deleted (except historical_wbs/).")
                    keep_existing_input = input("\nKeep existing data? (Y/n): ").strip().lower()
                    keep_existing = keep_existing_input not in ["n", "no"]
                
                print()
                
                # Execute selected option with scenarios
                if option == 1:
                    option_1_pre_contract(base_dir, sow_number, keep_existing, contract_type, completeness_level, communication_style, seed)
                elif option == 2:
                    option_2_draft_validation(base_dir, sow_number, keep_existing, contract_type, deviation_pattern, completeness_level, communication_style, seed)
                elif option == 3:
                    option_3_signed_contract(base_dir, sow_number, keep_existing, contract_type, completeness_level, seed)
                
                print("\n" + "="*70)
                print("Setup Complete!")
                print("="*70)
                
                # Ask if user wants to continue
                continue_input = input("\nPress Enter to return to menu (or 'q' to quit): ").strip().lower()
                if continue_input in ["q", "quit", "exit"]:
                    break
            else:
                print("\n⚠️  Invalid choice. Please enter 0, 1, 2, 3, 4, or 5.")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\n⚠️  Error: {e}")
            continue_input = input("\nPress Enter to return to menu (or 'q' to quit): ").strip().lower()
            if continue_input in ["q", "quit", "exit"]:
                break


def main():
    parser = argparse.ArgumentParser(
        description="Generate mock data for Covenant Contract Lifecycle Intelligence pipeline"
    )
    parser.add_argument(
        "--option",
        type=int,
        choices=[1, 2, 3, 4],
        help="Option to generate: 1=Pre-Contract, 2=Draft Validation, 3=Signed Contract, 4=Change Order (required if not using --interactive)"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive menu mode"
    )
    parser.add_argument(
        "--project-dir",
        type=str,
        default="projects/pa",
        help="Project directory path (default: projects/pa). Used if --output-dir is not specified."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Base directory for generated files (default: {project_dir}/data/covenant)"
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Keep existing data (only generate new files for selected option)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible scenario generation"
    )
    
    args = parser.parse_args()
    
    # Initialize random seed if provided
    initialize_random(args.seed)
    
    # Detect project name and resolve paths
    project_name = detect_project_name(Path.cwd())
    
    # Determine output directory
    if args.output_dir:
        # Use explicitly provided output directory
        base_dir = resolve_script_path(args.output_dir, project_name=project_name)
    else:
        # Use project_dir + BASE_DIR
        project_dir = resolve_script_path(args.project_dir, project_name=project_name)
        base_dir = project_dir / BASE_DIR
    
    # Interactive mode
    if args.interactive:
        run_interactive_mode(base_dir, seed=args.seed)
        return
    
    # Non-interactive mode requires --option
    if args.option is None:
        parser.error("--option is required when not using --interactive mode")
    
    # Select scenarios (randomly or based on seed)
    contract_type = select_contract_type_scenario(args.seed)
    deviation_pattern = select_deviation_pattern(args.seed)
    completeness_level = select_completeness_level(args.seed)
    communication_style = select_communication_style(args.seed)
    
    sow_number = generate_sow_number(args.seed)
    
    # Execute selected option with scenarios
    if args.option == 1:
        option_1_pre_contract(base_dir, sow_number, args.keep_existing, contract_type, completeness_level, communication_style, args.seed)
    elif args.option == 2:
        option_2_draft_validation(base_dir, sow_number, args.keep_existing, contract_type, deviation_pattern, completeness_level, communication_style, args.seed)
    elif args.option == 3:
        option_3_signed_contract(base_dir, sow_number, args.keep_existing, contract_type, completeness_level, args.seed)
    elif args.option == 4:
        # For option 4, try to find existing SOW number
        existing_sow_numbers = find_existing_sow_numbers(base_dir)
        if existing_sow_numbers:
            sow_number = existing_sow_numbers[-1]
        option_4_change_order(base_dir, sow_number, args.keep_existing, contract_type, args.seed)
    
    print("\n" + "="*70)
    print("Setup Complete!")
    print("="*70)


if __name__ == "__main__":
    main()
