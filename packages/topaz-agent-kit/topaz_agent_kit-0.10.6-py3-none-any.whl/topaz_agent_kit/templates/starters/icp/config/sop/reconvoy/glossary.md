# ReconVoy Glossary

This glossary defines key terms used in the ReconVoy pipeline. Use `sop_get_glossary_term(term_id="<term>")` to look up definitions during processing.

---

## GBP items

**Definition**: BlackLine items where `currency = "GBP"`.

**Role**: UK-side endpoint items (bank receipts, IC accounts in GBP). These represent the final settlement or bank transactions.

**Key Rules**:
- **Never marked as `need_to_process`**: GBP items are terminal - they don't drive recursive discovery.
- **May be marked as `processing`**: When included in a case, mark as `processing` to include them in the case group.
- **Status handling**: GBP items remain `UNMATCHED` until journals are posted. They are never part of the recursive discovery loop.
- **Matching**: GBP items may have matches in foreign books, but they are not used to find related items in the other foreign book.

**Example**: A bank receipt in GBP (`BL-S3-003-001`, currency: GBP, amount_local_gbp: 101070.38) is a GBP item.

---

## USD items

**Definition**: BlackLine items where `currency = "USD"`.

**Role**: US-leg items in intercompany transactions. Can be the initial case driver or related items discovered during processing.

**Key Rules**:
- **Can be marked as `need_to_process`**: If a USD item is found as a related item (not the initial match), mark it as `need_to_process` to find its match in the other foreign book (FR).
- **Can be marked as `processing`**: After finding a match in the other foreign book, mark as `processing` to include in the case.
- **Matching**: USD items match against `us_books` (US foreign book entries).

**Example**: An invoice receivable from US (`BL-S3-001-001`, currency: USD, amount_foreign: 440655.63) is a USD item.

---

## EUR items

**Definition**: BlackLine items where `currency = "EUR"`.

**Role**: FR-leg items in intercompany transactions. Can be the initial case driver or related items discovered during processing.

**Key Rules**:
- **Can be marked as `need_to_process`**: If an EUR item is found as a related item (not the initial match), mark it as `need_to_process` to find its match in the other foreign book (US).
- **Can be marked as `processing`**: After finding a match in the other foreign book, mark as `processing` to include in the case.
- **Matching**: EUR items match against `fr_books` (FR foreign book entries).

**Example**: A logistics payable to FR (`BL-S3-002-001`, currency: EUR, amount_foreign: 5076.35) is an EUR item.

---

## processing_status

**Definition**: A field on BlackLine items that tracks whether an item is currently being processed in a case.

**Values**:
- `NULL` (or not set): Item is not being processed. These items are candidates for `get_blackline_unmatched_items`.
- `"processing"`: Item is currently part of an active case. Do not skip these items - they are part of the current case group.
- `"need_to_process"`: Item was discovered as related but needs recursive matching in the other foreign book. These items are picked up by `get_related_items_to_process`.

**Key Rules**:
- **Never skip items with `processing_status = "processing"`**: These are part of the current case.
- **Always skip items with `processing_status = "processing"` when looking for new items**: Use `get_blackline_unmatched_items` which filters out items with `processing_status IS NOT NULL`.
- **GBP items**: Should be marked as `"processing"` when included in a case, never as `"need_to_process"`.
- **USD/EUR items**: Can be marked as `"need_to_process"` during initial discovery, then `"processing"` after recursive match.

---

## need_to_process

**Definition**: A value for `processing_status` indicating an item needs recursive matching in the other foreign book.

**When to use**:
- When a USD or EUR item is discovered as a related item (not the initial match).
- The item has a match in one foreign book but needs to find its match in the other foreign book to complete a three-way case.

**When NOT to use**:
- **Never for GBP items**: GBP items should never be marked as `need_to_process`. They remain `UNMATCHED` or are marked as `processing` when included in a case.
- **Never for the initial matched item**: The initial item should be marked as `processing` immediately after finding its match.

**Transition**: Items with `need_to_process` are picked up by `get_related_items_to_process`, and after finding their match in the other foreign book, they should be marked as `processing`.

---

## case_item

**Definition**: A BlackLine item that is part of the current case being processed.

**Characteristics**:
- All case items have `processing_status = "processing"` (or are being set to this status).
- Case items are grouped together for FX variance calculation.
- Case items are included in the final journal entries.

**How items become case items**:
1. **Initial item**: The item being processed in the current loop iteration.
2. **Related items found in Step 3**: Items discovered by matching references from foreign book entries.
3. **Recursively discovered items in Step 4**: Items that were marked `need_to_process` and then matched in the other foreign book.

**Example**: A case might contain:
- `BL-S3-001-001` (USD, initial item)
- `BL-S3-002-001` (EUR, related item)
- `BL-S3-003-001` (GBP, related item)

---

## two_way_match

**Definition**: A match between a UK BlackLine item and entries in a single foreign book (either US or FR, but not both).

**Characteristics**:
- Only one foreign book is involved (either `us_books` or `fr_books`).
- Simpler scenario - direct UK-to-US or UK-to-FR transaction.
- FX variance is calculated between the UK item and the matched foreign book entries.

**Example**: UK sells to US, US pays directly. UK item matches US book entries only.

---

## three_way_match

**Definition**: A match involving UK, US, and FR entities in a triangular settlement.

**Characteristics**:
- Multiple foreign books are involved (both `us_books` and `fr_books`).
- Complex scenario - triangular trade (e.g., UK sells to US, US pays FR, FR provides services to UK).
- FX variance is calculated across all three entities.
- Requires recursive discovery to find matches in both foreign books.

**Example**: UK sells to US, US pays FR for logistics, FR provides services to UK. UK items match both US and FR book entries.

---

## foreign_book_type

**Definition**: The type of foreign book to search for matches.

**Values**:
- `"us_books"`: US foreign book (for USD items).
- `"fr_books"`: FR foreign book (for EUR items).

**Usage**:
- Determined in Step 1 based on item currency (USD → `us_books`, EUR → `fr_books`).
- Used in `find_foreign_book_match` and `get_foreign_book_entries_by_document` calls.

---

## document_number

**Definition**: A unique identifier for a document/transaction in foreign books.

**Key Rules**:
- **US and FR entries may have different document_numbers**: In triangular trades, US entries and FR entries often have different document numbers. This is why FR entries must be searched by `reference_description`, not `document_number`.
- **Used for grouping**: Entries with the same `document_number` in the same foreign book are related.
- **Used for fetching**: `get_foreign_book_entries_by_document` uses `document_number` to fetch all entries for a document.

---

## reference_description

**Definition**: A text field on BlackLine items and foreign book entries that describes the transaction.

**Role**: Used for matching and correlation between UK items and foreign book entries.

**Key Rules**:
- **Primary matching field**: `find_foreign_book_match` uses `reference_description` to find matches.
- **FR entry discovery**: FR entries must be searched by `reference_description` (not `document_number`) because they often have different document numbers than US entries in triangular trades.
- **Related item discovery**: `find_related_blackline_items` uses `reference_texts` (extracted from foreign book entries' `reference` or `header_text` fields) to find related UK items.

---

## variance_gbp

**Definition**: The absolute difference (in GBP) between the total BlackLine amount and the total matched foreign book amount.

**Calculation**: `variance_gbp = |total_blackline_gbp - total_matched_gbp|`

**Usage**:
- **Routing decision**: If `|variance_gbp| <= 100`, route to straight-through (auto-post). Otherwise, route to HITL (human review).
- **FX gain/loss**: Positive variance = FX loss, negative variance = FX gain.

---

## variance_percent

**Definition**: The percentage difference between the total BlackLine amount and the total matched foreign book amount.

**Calculation**: `variance_percent = (variance_gbp / total_blackline_gbp) * 100`

**Usage**: Provides a relative measure of variance for reporting and analysis.

---

## is_straight_through

**Definition**: A boolean flag indicating whether the case can be auto-posted without human review.

**Determination**: `is_straight_through = true` if `|variance_gbp| <= 100`, otherwise `false`.

**Impact**:
- `true`: Case routes directly to journal applier (no HITL gate).
- `false`: Case routes to HITL review gate for human approval.

---

## item_discovery_results

**Definition**: A list of dictionaries tracking the discovery and matching of case items.

**Structure**: Each dictionary contains:
- `"blackline_item_id"`: The BlackLine item ID (CRITICAL: use `blackline_item_id`, not `item_id`).
- `"foreign_book_type"`: The foreign book type (`"us_books"` or `"fr_books"`).
- `"matched_entry"`: The matched foreign book entry.
- `"document_number"`: The document number from the matched entry.
- `"related_entries"`: List of related entries found (optional).

**Usage**: Passed to `get_case_item_foreign_book_mappings` to build the mappings for FX variance calculation.

---

## related_items_discovery_results

**Definition**: A list of dictionaries tracking the discovery of related BlackLine items.

**Structure**: Each dictionary contains:
- `"related_blackline_items"`: List of related item IDs found.
- `"related_items_mappings"`: Dictionary mapping item_id to foreign book info:
  ```python
  {
    "BL-002": {"foreign_book_type": "us_books", "document_number": "123"}
  }
  ```
- `"items_marked"`: Count of items marked with status updates.

**Usage**: Passed to `get_case_item_foreign_book_mappings` to build the mappings for FX variance calculation.
