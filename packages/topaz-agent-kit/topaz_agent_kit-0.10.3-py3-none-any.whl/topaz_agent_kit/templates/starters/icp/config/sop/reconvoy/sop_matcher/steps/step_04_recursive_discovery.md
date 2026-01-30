# Step 4: Recursive Discovery

## What You Do

Process items marked as "need_to_process" to find three-way matches in the OTHER foreign book.

## Steps

### 4.1 Get Items to Process

```
reconvoy.get_related_items_to_process(
  db_file="<database_path>",
  run_id="<run_id>"
)
```

This returns all items with `processing_status = "need_to_process"`.

### 4.2 Process Each Item

For each `need_to_process` item:

1. **Identify currency** to determine which OTHER book to check:
   - USD item → Check `fr_books` (the OTHER book)
   - EUR item → Check `us_books` (the OTHER book)
   - GBP item → Skip (shouldn't be here, but if it is, skip it)

2. **Find match in OTHER book**:
   ```
   reconvoy.find_foreign_book_match(
     db_file="<database_path>",
     currency="<item.currency>",
     reference_description="<item.reference_description>",
     amount_foreign=<item.amount_foreign>
   )
   ```

3. **If match found**:
   - **Mark as three-way match**:
     ```
     reconvoy.update_blackline_match_status(db_file, item_id, "three_way_match")
     reconvoy.update_blackline_processing_status(db_file, item_id, "processing", run_id)
     ```
   - **Get entries by Document #**:
     ```
     reconvoy.get_foreign_book_entries_by_document(
       db_file="<database_path>",
       foreign_book_type="<other_book>",
       document_number="<matched_entry.document_number>"
     )
     ```
   - **Find more related items**:
     ```
     reconvoy.find_related_blackline_items(
       db_file="<database_path>",
       reference_texts=[...]  # From entries
     )
     ```
   - **Mark new related items** as `"need_to_process"` (following Step 3.3 logic)

4. **Add to accumulated results**:
   - Add to `item_discovery_results`:
     ```python
     {
       "blackline_item_id": "<item.item_id>",  # MUST use "blackline_item_id"
       "foreign_book_type": "<other_book>",
       "matched_entry": <matched_entry>,
       "document_number": "<document_number>",
       "related_entries": [<entries>]
     }
     ```
   - Add to `related_items_discovery_results` (if new items found)

5. **Repeat** until no more `need_to_process` items

## Loop Safety

- **Max iterations**: Process at most 50 items
- **Stop when**: `get_related_items_to_process` returns empty list
- **Skip duplicates**: If same item appears twice, skip after first processing

## Data Accumulation

**Initialize at start of Step 4:**
```python
item_discovery_results = []  # Add initial result from Step 2
related_items_discovery_results = []  # Add initial result from Step 3
```

**For each item processed in recursive loop:**
- Add discovery result to `item_discovery_results`
- Add related items result to `related_items_discovery_results` (if any found)

## Important

- **MUST use "blackline_item_id"** (not "item_id")
- **MUST mark items as "processing"** after finding match
- **MUST pass lists** (not strings) to Step 5 tools

## Document in Execution Trace

For this step, record in `execution_trace`:
- **Input**: Initial `item_discovery_results` and `related_items_discovery_results` from Steps 2 & 3
- **Loop iterations**: For each iteration, document:
  - Items returned by `get_related_items_to_process` (with full response)
  - For each item processed:
    - Item details (item_id, currency, reference_description)
    - Tool calls: `find_foreign_book_match`, `update_blackline_match_status`, `update_blackline_processing_status`, `get_foreign_book_entries_by_document`, `find_related_blackline_items` with parameters and full responses
    - Match found (yes/no) and which foreign book
    - Status updates: What status was set and confirmation (`{"updated": true}`)
    - New items discovered and marked
- **Data accumulated**: After each iteration, show the updated `item_discovery_results` and `related_items_discovery_results` lists
- **Loop termination**: Why the loop stopped (empty list, max iterations, etc.)

## Next

→ Go to Step 5 (FX Analysis) with accumulated lists
