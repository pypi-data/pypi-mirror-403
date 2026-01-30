# Scenario: Two-Way Match

## Description

A two-way match is the simplest reconciliation scenario where a UK BlackLine item matches directly to a single foreign book entry.

## Pattern

```
UK Entity ←────────────────→ Foreign Entity (US or FR)
   │                              │
   │  Invoice / Payment           │
   │  (one-to-one match)          │
   └──────────────────────────────┘
```

## Example: UK Sells to US (Direct Payment)

### Initial State

**BlackLine Item (UK):**
| Field | Value |
|-------|-------|
| item_id | BL-001 |
| source | GL (SAP) |
| currency | USD |
| amount_foreign | 625,000.00 |
| amount_local_gbp | 500,000.00 |
| reference_description | INV US_OCT_99/US_SUB |
| status | UNMATCHED |

**US Books Entry:**
| Field | Value |
|-------|-------|
| entry_id | US-001 |
| document_number | 150000881 |
| reference | INV US_OCT_99/US_SUB |
| amount_document_currency | 625,000.00 |
| currency | USD |

### Matching Process

1. **Step 1**: Currency is USD → Target `us_books`
2. **Step 2**: `find_foreign_book_match` by reference → Match found (US-001)
3. **Step 3**: No related items (single document)
4. **Step 4**: Calculate FX variance
   - Book rate: 1.25 USD/GBP
   - Spot rate: 1.266 USD/GBP
   - Expected GBP: 500,000
   - Actual GBP: 493,680 (625,000 ÷ 1.266)
   - Variance: £6,320 (FX Loss)
5. **Step 5**: Generate journals

### FX Calculation

```
Expected (Book):  625,000 USD ÷ 1.25  = £500,000.00
Actual (Spot):    625,000 USD ÷ 1.266 = £493,680.00
────────────────────────────────────────────────────
Variance:                               £6,320.00 (Loss)
```

### Proposed Journals

```json
{
  "proposed_journals": [
    {
      "entry_id": "UK-JE-001",
      "gl_account": "113100",
      "assignment": "Bank Rec 99",
      "reference": "WIRE US SUB",
      "header_text": "AI AUTO RECON",
      "amount_local_gbp": 493680.00,
      "trading_partner": "US01",
      "profit_center": "PC_RETAIL",
      "remarks": "Debit"
    },
    {
      "entry_id": "UK-JE-002",
      "gl_account": "650100",
      "assignment": "FX AUTO Calc",
      "reference": "FX VAR US OCT",
      "header_text": "AI FX ADJ",
      "amount_local_gbp": 6320.00,
      "trading_partner": null,
      "profit_center": "PC_CORP",
      "cost_center": "CC_FINANCE",
      "remarks": "Debit"
    },
    {
      "entry_id": "UK-JE-003",
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
  "scenario_type": "uk_sells_us_direct",
  "impact_analysis": "Clears UK receivable from US (£500,000) by recording bank receipt (£493,680) and FX loss (£6,320). Balance: Debit £500,000 = Credit £500,000 ✓"
}
```

### Balance Check

| Debits | Credits |
|--------|---------|
| Bank: £493,680 | |
| FX Loss: £6,320 | |
| | IC Receivable: £500,000 |
| **Total: £500,000** | **Total: £500,000** ✓ |

## Example: UK Buys from FR (Direct Payment)

### Initial State

**BlackLine Item (UK):**
| Field | Value |
|-------|-------|
| item_id | BL-002 |
| currency | EUR |
| amount_foreign | 100,000.00 |
| amount_local_gbp | 85,000.00 |
| reference_description | LOGISTIQUE FR 7 |
| status | UNMATCHED |

**FR Books Entry:**
| Field | Value |
|-------|-------|
| entry_id | FR-001 |
| reference | LOGISTIQUE FR 7 |
| amount_document_currency | 100,000.00 |
| currency | EUR |

### Routing Decision

- Variance: £1,200 (> £100)
- `is_straight_through`: `false`
- Route to HITL for review

## Key Points

1. Two-way matches involve exactly TWO parties: UK and one foreign entity
2. Only ONE foreign book is involved (either US or FR, not both)
3. Match status is `two_way_match`
4. Journal has 3 rows (bank, FX adjustment, IC clear)
