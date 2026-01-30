# Step 6: Journal Proposal

## What You Do

Create 4 journal entries to clear the open items.

## Journal Structure (Always 4 Rows)

| Row | Account | Purpose |
|-----|---------|---------|
| 1 | 113100 (Bank) | Record payment received/made |
| 2 | 210100/120100 (IC) | Intercompany settlement |
| 3 | 650100/750100 (FX) | FX gain/loss adjustment |
| 4 | 120100/210100 (IC) | Clear original intercompany |

## Steps

1. **Identify scenario** (two-way or three-way)
2. **Calculate amounts** from case items and variance
3. **Create 4 journal entries** with ALL required fields:
   - `entry_id`: "UK-JE-001", "UK-JE-002", etc.
   - `company_code`: "UK01" (always)
   - `gl_account`: See table above
   - `amount_local_gbp`: Calculated amount
   - `remarks`: "Debit" or "Credit"
   - `reference`: Extract from foreign book entries or case items (e.g., entry["reference"] or item["reference_description"])
   - `header_text`: Use standard header texts:
     - Row 1 (Bank): "AI AUTO RECON"
     - Row 2 (IC): "AI TRI NET" (for triangular) or "AI AUTO RECON" (for two-way)
     - Row 3 (FX): "AI FX ADJ"
     - Row 4 (IC Clear): "AI AUTO CLEAR"
   - `assignment`: Extract from foreign book entries (e.g., entry["assignment"]) or use date/transaction reference
   - `trading_partner`: Extract from foreign book entries (e.g., entry["company_code"] like "US01", "FR01") or null if not applicable
   - `profit_center`: Extract from foreign book entries (e.g., entry["profit_center"]) or use defaults:
     - Bank entries: "PC_RETAIL"
     - IC entries: "PC_LOGIST" (FR) or "PC_RETAIL" (US)
     - FX entries: "PC_CORP"
   - `cost_center`: Extract from foreign book entries (e.g., entry["cost_center"]) or null (FX entries may use "CC_FINANCE")

4. **Ensure balance**: Debits = Credits

## Account Selection

- Bank: 113100
- IC Payable FR: 210100
- IC Payable US: 210200
- IC Receivable FR: 120100
- IC Receivable US: 120200
- FX Loss: 650100
- FX Gain: 750100

## Example

```json
{
  "proposed_journals": [
    {
      "entry_id": "UK-JE-001",
      "company_code": "UK01",
      "gl_account": "113100",
      "amount_local_gbp": 493600.00,
      "remarks": "Debit",
      "reference": "WIRE FR US SUB",
      "header_text": "AI AUTO RECON",
      "assignment": "Bank Rec 99",
      "trading_partner": "US01",
      "profit_center": "PC_RETAIL",
      "cost_center": null
    },
    {
      "entry_id": "UK-JE-002",
      "company_code": "UK01",
      "gl_account": "210100",
      "amount_local_gbp": 6048.00,
      "remarks": "Debit",
      "reference": "LOGISTIQUE FR 7",
      "header_text": "AI TRI NET",
      "assignment": "20251215",
      "trading_partner": "FR01",
      "profit_center": "PC_LOGIST",
      "cost_center": null
    },
    {
      "entry_id": "UK-JE-003",
      "company_code": "UK01",
      "gl_account": "650100",
      "amount_local_gbp": 352.00,
      "remarks": "Debit",
      "reference": "FX VAR US",
      "header_text": "AI FX ADJ",
      "assignment": "FX AUTO Calc",
      "trading_partner": null,
      "profit_center": "PC_CORP",
      "cost_center": "CC_FINANCE"
    },
    {
      "entry_id": "UK-JE-004",
      "company_code": "UK01",
      "gl_account": "120100",
      "amount_local_gbp": 500000.00,
      "remarks": "Credit",
      "reference": "INV US OCT 99/",
      "header_text": "AI AUTO CLEAR",
      "assignment": "20251201",
      "trading_partner": "US01",
      "profit_center": "PC_RETAIL",
      "cost_center": null
    }
  ]
}
```

## Document in Execution Trace

For this step, record in `execution_trace`:
- **Input**: 
  - case_items list
  - variance_gbp, variance_percent
  - foreign_book_mappings
  - is_straight_through flag
- **Reasoning**: 
  - Scenario type identified (two-way vs three-way, which direction)
  - Amount calculations for each journal row
  - Account selection for each row
  - Debit/Credit assignment
- **Output**: 
  - Complete proposed_journals array with all 4 entries
  - Verification that Debits = Credits
  - Impact analysis summary

## Next

→ Return complete output JSON
