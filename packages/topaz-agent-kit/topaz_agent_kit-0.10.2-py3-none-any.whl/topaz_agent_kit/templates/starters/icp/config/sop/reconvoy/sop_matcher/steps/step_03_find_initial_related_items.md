# Step 3: Find Initial Related Items

## What You Do

Find all BlackLine items related to the initial match by looking up references from foreign book entries.

## Steps

### 3.1 Get All Entries with Same Document #

```
reconvoy.get_foreign_book_entries_by_document(
  db_file="<database_path>",
  foreign_book_type="<us_books|fr_books>",
  document_number="<document_number_from_step_2>"
)
```

This gives you all foreign book entries with the same Document # as the initial match.

### 3.2 Find Related BlackLine Items

1. **Collect ALL reference texts** from ALL entries:
   - Extract `reference` from each entry (if not null/empty)
   - Extract `header_text` from each entry (if not null/empty)
   - Remove duplicates and null/empty values
   - Create a single list: `["ref1", "ref2", "ref3", ...]`

2. **Call tool ONCE with all reference texts** (as JSON array):
   ```
   reconvoy.find_related_blackline_items(
     db_file="<database_path>",
     reference_texts=["ref1", "ref2", "ref3"]  # JSON array, not string
   )
   ```

**CRITICAL**: Pass as JSON array, not comma-separated string.

### 3.3 Mark Related Items

For each related BlackLine item found:

1. **Check status**:
   - If `processing_status = "processing"` → Skip (already in case)
   - If `processing_status = "need_to_process"` → Skip (already queued)
   - If `processing_status IS NULL` → Mark it

2. **Mark based on currency**:
   - **GBP items**: Mark as `"processing"` (already have match, skip recursive loop)
   - **USD/EUR items**: Mark as `"need_to_process"` (will check other book in recursive loop)

3. **Update both statuses**:
   ```
   reconvoy.update_blackline_match_status(db_file, item_id, "two_way_match")
   reconvoy.update_blackline_processing_status(db_file, item_id, "processing" or "need_to_process", run_id)
   ```

## Save This for Step 4

Add to `related_items_discovery_results`:
```python
{
  "related_blackline_items": ["BL-002", "BL-003"],
  "related_items_mappings": {
    "BL-002": {
      "foreign_book_type": "us_books",
      "document_number": "<document_number>"
    },
    "BL-003": {
      "foreign_book_type": "fr_books",
      "document_number": "<document_number>"
    }
  },
  "items_marked": 2
}
```

**IMPORTANT**: 
- Use the same `document_number` and `foreign_book_type` from Step 2
- These items were found via reverse lookup, so they share the same Document #

## Document in Execution Trace

For this step, record in `execution_trace`:
- **Input**: document_number and foreign_book_type from Step 2
- **Tool calls**: 
  - `get_foreign_book_entries_by_document` with parameters and full response
  - `find_related_blackline_items` with reference_texts array and full response
  - `update_blackline_match_status` for each item with parameters and response
  - `update_blackline_processing_status` for each item with parameters and response (verify `{"updated": true}`)
- **Output**: related_entries list, related_blackline_items list, items marked count
- **Data accumulated**: Exact structure of `related_items_discovery_results` dict added
- **Decisions**: Which items were marked as "processing" vs "need_to_process" and why

## Next

→ Go to Step 4 (Recursive Discovery)
