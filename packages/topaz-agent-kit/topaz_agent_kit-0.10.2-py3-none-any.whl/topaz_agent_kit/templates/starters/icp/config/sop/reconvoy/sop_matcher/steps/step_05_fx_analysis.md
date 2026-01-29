# Step 5: FX Analysis

## What You Do

Calculate FX variance and decide if case can auto-post.

## Steps

### 5.1 Get All Item IDs in Case

Get all items with `processing_status = "processing"` for this run_id. These are your case items.

### 5.2 Build Mappings

```
reconvoy.get_case_item_foreign_book_mappings(
  db_file="<database_path>",
  item_ids=["BL-001", "BL-002", ...],  # All case item IDs
  item_discovery_results=<item_discovery_results_list>,  # From Steps 2 & 4
  related_items_discovery_results=<related_items_discovery_results_list>  # From Steps 3 & 4
)
```

**CRITICAL - Format:**
- `item_discovery_results` must be a Python list of dicts
- Each dict must have `"blackline_item_id"` (not `"item_id"`)
- `related_items_discovery_results` must be a Python list of dicts
- Each dict must have `"related_items_mappings"` (a dict)

**Example:**
```python
item_discovery_results = [
  {
    "blackline_item_id": "BL-001",
    "foreign_book_type": "us_books",
    "matched_entry": {...},
    "document_number": "123",
    "related_entries": [...]
  },
  {
    "blackline_item_id": "BL-002",
    "foreign_book_type": "fr_books",
    "matched_entry": {...},
    "document_number": "456",
    "related_entries": [...]
  }
]

related_items_discovery_results = [
  {
    "related_blackline_items": ["BL-003"],
    "related_items_mappings": {
      "BL-003": {"foreign_book_type": "us_books", "document_number": "123"}
    },
    "items_marked": 1
  }
]
```

### 5.3 Calculate Variance

```
reconvoy.calculate_case_fx_variance(
  db_file="<database_path>",
  main_item_id="<current_blackline_item.item_id>",
  mappings=<mappings_dict_from_5.2>
)
```

**CRITICAL:**
- `main_item_id` = the original item ID (e.g., `current_blackline_item.item_id`)
- `mappings` = the `mappings` dict returned from step 5.2 (not the lists)

### 5.4 Decide Routing

- If `|variance_gbp| <= 100` → `is_straight_through = true`
- If `|variance_gbp| > 100` → `is_straight_through = false`

### 5.5 Fetch Foreign Book Entries (for display)

**CRITICAL**: Track ALL document_numbers discovered during Steps 2-4 (both US and FR) and use them to fetch entries. Document numbers are the most reliable way to fetch related entries.

**Steps:**

1. **Collect unique document numbers from mappings (BOTH US and FR)**:
   - Create sets to track document numbers:
     - `unique_us_document_numbers = set()` for US document numbers
     - `unique_fr_document_numbers = set()` for FR document numbers
   - For each `item_id, mapping_info` pair in `mappings.items()`:
     - If `mapping_info.get("foreign_book_type") == "us_books"` and `mapping_info.get("document_number")`:
       - Add `mapping_info["document_number"]` to `unique_us_document_numbers`.
     - If `mapping_info.get("foreign_book_type") == "fr_books"` and `mapping_info.get("document_number")`:
       - Add `mapping_info["document_number"]` to `unique_fr_document_numbers`.

2. **Also collect document numbers from item_discovery_results and related_items_discovery_results**:
   - **From item_discovery_results**: For each result dict:
     - If `result.get("foreign_book_type") == "us_books"` and `result.get("document_number")`:
       - Add to `unique_us_document_numbers`.
     - If `result.get("foreign_book_type") == "fr_books"` and `result.get("document_number")`:
       - Add to `unique_fr_document_numbers`.
   - **From related_items_discovery_results**: For each result dict:
     - Check `result.get("related_items_mappings", {})`:
       - For each `item_id, mapping_info` in the mappings:
         - If `mapping_info.get("foreign_book_type") == "us_books"` and `mapping_info.get("document_number")`:
           - Add to `unique_us_document_numbers`.
         - If `mapping_info.get("foreign_book_type") == "fr_books"` and `mapping_info.get("document_number")`:
           - Add to `unique_fr_document_numbers`.

3. **Fetch US entries by document_number**:
   - For each `document_number` in `unique_us_document_numbers`:
     - Call: `reconvoy.get_foreign_book_entries_by_document(db_file=database_path, foreign_book_type="us_books", document_number=document_number)`
     - If the tool returns a non-empty `entries` list:
       - For each entry in `entries`, add `entry["book"] = "US"`.
       - Store entries temporarily: `foreign_book_mappings_by_item[(document_number, "us_books")] = entries`.

4. **Fetch FR entries by document_number (PRIMARY METHOD)**:
   - For each `document_number` in `unique_fr_document_numbers`:
     - Call: `reconvoy.get_foreign_book_entries_by_document(db_file=database_path, foreign_book_type="fr_books", document_number=document_number)`
     - If the tool returns a non-empty `entries` list:
       - For each entry in `entries`, add `entry["book"] = "FR"`.
       - Store entries temporarily: `foreign_book_mappings_by_item[(document_number, "fr_books")] = entries`.

5. **FALLBACK - Fetch FR entries by reference (only if no FR document_numbers found)**:
   - **Only if `unique_fr_document_numbers` is empty**:
     - **Collect references from case items**:
       - After calling `calculate_case_fx_variance`, you have `main_item` and `matched_items`.
       - Extract all `reference_description` values from `main_item` and all items in `matched_items`.
       - **CRITICAL**: Also check `case_items` for EUR items - if any case item has `currency == "EUR"`, use its `reference_description` to search FR books:
         - For each item in `case_items`:
           - If `item.get("currency") == "EUR"` and `item.get("reference_description")`:
             - Add `item["reference_description"]` to `case_references`.
       - Create a set `case_references = set()` containing all unique reference descriptions.
     - **Search FR books for each reference**:
       - For each `reference` in `case_references`:
         - Call: `reconvoy.find_foreign_book_match(db_file=database_path, currency="EUR", reference_description=reference, amount_foreign=0.0, target_book="fr_books")`
         - If the tool returns a non-empty `related_entries` list:
           - For each entry in `related_entries`, add `entry["book"] = "FR"`.
           - **CRITICAL**: Add the `document_number` from the matched entry to `unique_fr_document_numbers` for future iterations.
           - Store entries temporarily: `foreign_book_mappings_by_item[(entry["document_number"], "fr_books")] = related_entries` (use the document_number from the matched entry).

6. **Deduplicate and group by book**:
   - Initialize `foreign_book_mappings = {"US": [], "FR": []}`.
   - Create a set `seen_entries` to track duplicates (using tuple of: `company_code, entry_id, document_number, reference, amount_document_currency, document_currency`).
   - For each `(document_number, foreign_book_type), entries` in `foreign_book_mappings_by_item.items()`:
     - For each `entry` in `entries`:
       - **CRITICAL**: Ensure `entry["book"]` is set correctly:
         - If `foreign_book_type == "us_books"`, `entry["book"]` MUST be "US"
         - If `foreign_book_type == "fr_books"`, `entry["book"]` MUST be "FR"
       - Create a deduplication key: `(entry.get("company_code"), entry.get("entry_id"), entry.get("document_number"), entry.get("reference"), entry.get("amount_document_currency"), entry.get("document_currency"))`.
       - If this key is NOT in `seen_entries`:
         - Add the key to `seen_entries`.
         - Append the entry to `foreign_book_mappings[entry["book"]]` (this will be either `foreign_book_mappings["US"]` or `foreign_book_mappings["FR"]`).
   - **VERIFICATION**: After deduplication, ensure both `foreign_book_mappings["US"]` and `foreign_book_mappings["FR"]` are lists (even if empty). If you fetched entries for both book types, both lists should contain entries.

## Outputs

- `variance_gbp` - Absolute variance amount
- `variance_percent` - Variance percentage
- `total_blackline_gbp` - Sum of BlackLine amounts
- `total_matched_gbp` - Sum of matched amounts
- `is_straight_through` - true/false
- `foreign_book_mappings` - {"US": [...], "FR": [...]}

## Document in Execution Trace

For this step, record in `execution_trace`:
- **Input**: 
  - All case item IDs (list)
  - `item_discovery_results` list (show structure and length)
  - `related_items_discovery_results` list (show structure and length)
- **Tool calls**: 
  - `get_case_item_foreign_book_mappings` with exact parameters and full response (mappings dict)
  - `calculate_case_fx_variance` with main_item_id and mappings, full response showing variance_gbp, variance_percent, total_blackline_gbp, total_matched_gbp
  - `get_foreign_book_entries_by_document` calls for US entries (by document_number) with parameters and responses
  - `get_foreign_book_entries_by_document` calls for FR entries (by document_number) with parameters and responses
  - `find_foreign_book_match` calls for FR entries (by reference_description, only if no FR document_numbers found) with parameters and responses
- **Output**: 
  - mappings dict structure
  - variance_gbp, variance_percent values
  - total_blackline_gbp, total_matched_gbp values
  - is_straight_through decision (true/false) and why
  - foreign_book_mappings structure
- **Decision**: Routing decision based on variance threshold

## Next

→ Go to Step 6 (Journal Proposal)
