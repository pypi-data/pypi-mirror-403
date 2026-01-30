# Troubleshooting Guide

## Common Issues and Solutions

### No Match Found

**Symptom**: `find_foreign_book_match` returns `matched_entry: null`

**Possible Causes:**

1. **Reference Mismatch**
   - Check for typos in `reference_description`
   - Compare exact characters (spaces, case, special chars)
   - Foreign book may use `header_text` instead of `reference`

2. **Wrong Foreign Book**
   - GBP items should check BOTH books
   - USD → `us_books`, EUR → `fr_books`
   - Verify currency is correct on BlackLine item

3. **Item Already Processed**
   - Check if matching entry was already consumed by another case
   - Look for entries with same Document # that were processed

**Action**: Do NOT mark as rejected. Leave unchanged for future investigation.

---

### Item Already Being Processed

**Symptom**: Item has `processing_status = 'processing'`

**Cause**: This item is already part of another case being processed in the same run.

**Action**: Skip this item (return early with `matched_entry: null`, `error: ""`). This is expected behavior, not an error.

---

### Infinite Loop in Recursive Discovery

**Symptom**: Discovery keeps finding new items indefinitely

**Possible Causes:**

1. **Items not being marked as `processing`**
   - Ensure `update_blackline_processing_status` is called after each match
   - Check that run_id is passed correctly

2. **Circular references**
   - Document # correlation creates a loop
   - Same items keep appearing in `need_to_process`

**Prevention**:
- Always mark items as `processing` immediately after finding their match
- Check `processing_status` before processing any item
- Set max_iterations safety limit (50 recommended)

---

### FX Variance Calculation Wrong

**Symptom**: Variance doesn't match expected value

**Check:**

1. **Rate Type Selection**
   - Incoming transactions → Book Rate
   - Outgoing transactions → Spot Rate
   - Are you using the correct rate for each item?

2. **Currency Conversion Direction**
   - USD/GBP: Divide USD amount by rate
   - EUR/GBP: Divide EUR amount by rate
   - GBP/GBP: No conversion needed (rate = 1.0)

3. **Rounding**
   - All GBP amounts should be rounded to 2 decimal places
   - Rounding differences can accumulate

4. **Missing Items**
   - Are all case items included in the calculation?
   - Check `case_items` list is complete

---

### Journals Don't Balance

**Symptom**: Sum of debits ≠ sum of credits

**Check:**

1. **FX Variance Entry**
   - Is the FX gain/loss correctly calculated?
   - Sign: Loss = Debit, Gain = Credit

2. **All Items Included**
   - Bank entry for each payment received
   - IC clear entry for each receivable/payable
   - Netting entries for triangular scenarios

3. **Amount Precision**
   - Use 2 decimal places consistently
   - Don't mix rounded and unrounded values

**Fix**: Recalculate from source amounts. If small discrepancy (< £0.01), adjust FX entry.

---

### GBP Currency Items Not Matching

**Symptom**: GBP items return no match from either book

**Explanation**: GBP items are typically:
- Bank wire receipts/payments
- Already-converted amounts
- They match via reverse lookup (other items find them)

**Action**:
1. Don't expect direct matches for GBP items
2. They will be discovered when USD/EUR items find related entries
3. Mark as `processing` when found via `find_related_blackline_items`

---

### Three-Way Match Not Detected

**Symptom**: Triangular scenario treated as two-way

**Check:**

1. **Recursive Discovery**
   - Did you process all `need_to_process` items?
   - Did you check the OTHER foreign book for each?

2. **Match Status Update**
   - Items found via reverse lookup should be `three_way_match`
   - Initial item stays as `two_way_match`

3. **Document # Correlation**
   - Entries must share Document # within each book
   - Cross-book correlation is via reference/header_text

---

### Tool Call Timeout

**Symptom**: Tool returns timeout error

**Cause**: Database query taking too long

**Action**:
1. Check database connection
2. Verify db_file path is correct
3. Retry the operation
4. If persistent, report as infrastructure issue

---

### SOP Section Not Found

**Symptom**: `sop_get_section` returns "Section not found"

**Check:**

1. **Section ID Spelling**
   - Use exact ID from manifest (e.g., `step_02_find_match`)
   - IDs are case-sensitive

2. **SOP Initialized**
   - Must call `sop_initialize` before `sop_get_section`
   - Check that initialization succeeded

3. **Use sop_list_sections**
   - Get list of available sections
   - Verify the section exists

---

## Error Response Format

When encountering an error, return:

```json
{
  "item_id": "<item_id>",
  "matched_items": [],
  "related_items_mappings": {},
  "foreign_book_mappings": {"US": [], "FR": []},
  "case_items": [],
  "case_items_markdown": null,
  "foreign_book_mappings_markdown": null,
  "total_blackline_gbp": 0,
  "total_matched_gbp": 0,
  "variance_gbp": 0,
  "variance_percent": 0,
  "is_straight_through": false,
  "proposed_journals": [],
  "proposed_journals_markdown": null,
  "match_summary": "",
  "tools_used": {"<tool>": <count>},
  "error": "<descriptive error message>"
}
```

## When to Escalate

Escalate to human review if:
- Repeated tool failures
- Data inconsistency (amounts don't add up)
- Unusual scenario not covered by SOP
- Variance calculation seems wrong

Do NOT:
- Mark items as rejected without human approval
- Skip items silently (always return a result)
- Make assumptions about missing data
