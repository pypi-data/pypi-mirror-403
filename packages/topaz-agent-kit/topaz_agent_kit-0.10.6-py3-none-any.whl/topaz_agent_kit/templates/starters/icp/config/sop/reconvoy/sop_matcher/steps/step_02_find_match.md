# Step 2: Find Match

## What You Do

Find the matching entry in the foreign book using the reference description.

## Steps

1. Call the match tool:
   ```
   reconvoy.find_foreign_book_match(
     db_file="<database_path>",
     currency="<item.currency>",
     reference_description="<item.reference_description>",
     amount_foreign=<item.amount_foreign>
   )
   ```

2. **If match found:**
   - Extract `document_number` from the matched entry
   - Extract `foreign_book_type` ("us_books" or "fr_books")
   - **MUST DO**: Mark item as "processing":
     ```
     reconvoy.update_blackline_match_status(db_file, item_id, "two_way_match")
     reconvoy.update_blackline_processing_status(db_file, item_id, "processing", run_id)
     ```
   - Continue to Step 3

3. **If no match:**
   - Return early with `matched_entry: null`
   - Do NOT mark as rejected

## Why Mark as "processing"?

If you don't mark it, the loop will process it again. The `get_blackline_unmatched_items` tool only returns items where `processing_status IS NULL`.

## Save This for Step 3

You'll need to add this to `item_discovery_results` in Step 3:
```python
{
  "blackline_item_id": "<item.item_id>",  # MUST use "blackline_item_id"
  "foreign_book_type": "<us_books|fr_books>",
  "matched_entry": <matched_entry_object>,
  "document_number": "<document_number>",
  "related_entries": []  # Will fill in Step 3
}
```

## Document in Execution Trace

For this step, record in `execution_trace`:
- **Input**: Item details (currency, reference_description, amount_foreign), foreign_book_type from Step 1
- **Tool calls**: 
  - `find_foreign_book_match` with exact parameters
  - `update_blackline_match_status` with parameters and response
  - `update_blackline_processing_status` with parameters and response (verify `{"updated": true}`)
- **Output**: matched_entry (or null), document_number, match_status
- **Decision**: Whether match was found and what to do next

## Next

→ If match found: Go to Step 3
→ If no match: Return early
