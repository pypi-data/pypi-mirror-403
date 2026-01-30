# Scenario: Three-Way Match (Triangular)

## Description

A three-way match involves UK, US, AND FR entities in a triangular settlement. This typically occurs when one entity pays on behalf of another.

## Pattern

```
        UK Entity
           │
           │ Invoice (Receivable)
           │
           ▼
      US Entity ◄──────────────── FR Entity
                  Payment on behalf
```

**Common Triangular Scenarios:**
- UK sells to US, FR pays on behalf of US
- UK sells to FR, US pays on behalf of FR
- UK buys from US, pays via FR
- UK buys from FR, pays via US

## Example: UK Sells to US, FR Pays (Triangular)

### Initial State

**BlackLine Items (UK):**

| item_id | currency | amount_foreign | amount_local_gbp | reference_description |
|---------|----------|----------------|------------------|-----------------------|
| BL-S3-001 | USD | 625,000.00 | 500,000.00 | INV US_OCT_99/US_SUB |
| BL-S3-002 | GBP | 6,400.00 | 6,400.00 | LOGISTIQUE FR 7 |
| BL-S3-003 | GBP | 493,600.00 | 493,600.00 | WIRE FR US SUB |

**US Books Entries (Document #150000881):**

| entry_id | reference | amount_document_currency | currency |
|----------|-----------|-------------------------|----------|
| US-S3-001 | INV US_OCT_99/US_SUB | 625,000.00 | USD |
| US-S3-002 | LOGISTIQUE FR 7 | 8,000.00 | USD |
| US-S3-003 | WIRE FR US SUB | 617,000.00 | USD |

**FR Books Entries (Document #150000882):**

| entry_id | reference | amount_document_currency | currency |
|----------|-----------|-------------------------|----------|
| FR-S3-001 | LOGISTIQUE FR 7 | 7,500.00 | EUR |
| FR-S3-002 | WIRE FR US SUB | 580,000.00 | EUR |

### Discovery Process

1. **Step 1-2**: Start with BL-S3-001 (USD)
   - Find match in `us_books` → US-S3-001
   - Document #: 150000881
   - Mark as `two_way_match`, `processing`

2. **Step 3**: Recursive Discovery
   - Get all entries with Document #150000881 → US-S3-001, US-S3-002, US-S3-003
   - Find related BlackLine items by reference:
     - "LOGISTIQUE FR 7" → BL-S3-002 (mark `need_to_process`)
     - "WIRE FR US SUB" → BL-S3-003 (mark `need_to_process`)
   
3. **Process BL-S3-002** (GBP, need_to_process):
   - Check OTHER foreign book (`fr_books`) for "LOGISTIQUE FR 7"
   - Find FR-S3-001 → `three_way_match`
   - Get entries by Document #150000882 → FR-S3-001, FR-S3-002
   
4. **Process BL-S3-003** (GBP, need_to_process):
   - Check OTHER foreign book for "WIRE FR US SUB"
   - Find FR-S3-002 → `three_way_match`

5. **Case Complete**: 3 BlackLine items, entries from both US and FR books

### FX Calculation

| Item | Amount | Rate Type | Rate | GBP Value |
|------|--------|-----------|------|-----------|
| BL-S3-001 | 625,000 USD | Book | 1.25 | 500,000.00 |
| BL-S3-002 | 6,400 GBP | N/A | 1.00 | 6,400.00 |
| BL-S3-003 | 493,600 GBP | N/A | 1.00 | 493,600.00 |

**Variance Calculation:**
```
Expected Total:  500,000 + 6,400 + 493,600 = £1,000,000
Actual Total:    500,000 + 6,400 + 493,600 = £1,000,000
Variance:        £0 (no FX impact on GBP items)
```

**Note**: In this case, the FX variance is already absorbed in the GBP amounts.

### Proposed Journals (4-Row Structure)

```json
{
  "proposed_journals": [
    {
      "entry_id": "UK-JE-001",
      "gl_account": "113100",
      "assignment": "Bank Rec 99",
      "reference": "WIRE FR US SUB",
      "header_text": "AI AUTO RECON",
      "amount_local_gbp": 493600.00,
      "trading_partner": "FR01",
      "profit_center": "PC_RETAIL",
      "remarks": "Debit"
    },
    {
      "entry_id": "UK-JE-002",
      "gl_account": "210100",
      "assignment": "20251215",
      "reference": "LOGISTIQUE FR 7",
      "header_text": "AI TRI NET",
      "amount_local_gbp": 6400.00,
      "trading_partner": "FR01",
      "profit_center": "PC_LOGIST",
      "remarks": "Debit"
    },
    {
      "entry_id": "UK-JE-003",
      "gl_account": "650100",
      "assignment": "FX AUTO Calc",
      "reference": "FX VAR US",
      "header_text": "AI FX ADJ",
      "amount_local_gbp": 0.00,
      "trading_partner": null,
      "profit_center": "PC_CORP",
      "cost_center": "CC_FINANCE",
      "remarks": "Debit"
    },
    {
      "entry_id": "UK-JE-004",
      "gl_account": "120200",
      "assignment": "20251001",
      "reference": "INV US OCT 99",
      "header_text": "AI AUTO CLEAR",
      "amount_local_gbp": 500000.00,
      "trading_partner": "US01",
      "profit_center": "PC_RETAIL",
      "remarks": "Credit"
    }
  ],
  "scenario_type": "uk_sells_us_fr_triangular",
  "impact_analysis": "Triangular settlement: UK receivable from US (£500,000) cleared by FR payment (£493,600) plus FR logistics charge (£6,400). No FX variance. Balance: Debit £500,000 = Credit £500,000 ✓"
}
```

### Balance Check

| Debits | Credits |
|--------|---------|
| Bank (from FR): £493,600 | |
| IC Payable FR: £6,400 | |
| FX Loss: £0 | |
| | IC Receivable US: £500,000 |
| **Total: £500,000** | **Total: £500,000** ✓ |

## Key Points

1. Three-way matches involve ALL THREE parties: UK, US, and FR
2. BOTH foreign books are involved
3. At least one item has `three_way_match` status
4. Journal has 4 rows (bank, IC netting, FX adjustment, IC clear)
5. The "AI TRI NET" header text indicates triangular netting

## Detection Criteria

A case is triangular if:
- Multiple BlackLine items are linked via Document #
- Entries exist in BOTH `us_books` AND `fr_books`
- At least one item was discovered via reverse lookup (need_to_process → processing)

## Common Patterns

| Scenario | UK Entry | US Entry | FR Entry | Flow |
|----------|----------|----------|----------|------|
| UK sells to US, FR pays | Receivable | Payable | Payment | UK ← US ← FR |
| UK sells to FR, US pays | Receivable | Payment | Payable | UK ← FR ← US |
| UK buys from US, pays via FR | Payable | Receivable | Payment | UK → US, UK → FR |
