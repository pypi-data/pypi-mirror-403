# ReconVoy SOP Matcher - Overview

## Your Job

Process one BlackLine item by:
1. Finding its match in US or FR books
2. Finding all related items
3. Calculating FX variance
4. Proposing journal entries

## Simple Workflow

```
Step 1: Identify Foreign Book (USD→US, EUR→FR, GBP→both)
   ↓
Step 2: Find Match (use reference_description)
   ↓
Step 3: Find Initial Related Items (same Document #)
   ↓
Step 4: Recursive Discovery (process need_to_process items)
   ↓
Step 5: Calculate FX Variance
   ↓
Step 6: Propose Journals
```

## Key Rules

- **Always read SOP section before doing the step** - Use `sop_get_section(section_id="step_XX")`
- **Mark items as "processing"** after finding matches - Prevents duplicates
- **Use exact field names** - `blackline_item_id` not `item_id` in accumulated data
- **Pass lists, not strings** - Tools expect Python lists, not JSON strings

## Tools You Have

**SOP Tools** (read instructions):
- `sop_initialize` - Load SOP
- `sop_get_section` - Read a step
- `sop_get_example` - See examples
- `sop_get_troubleshooting` - Get help

**Business Tools** (do work):
- `reconvoy.find_foreign_book_match` - Find match
- `reconvoy.get_foreign_book_entries_by_document` - Get entries by Document #
- `reconvoy.find_related_blackline_items` - Find related items
- `reconvoy.update_blackline_match_status` - Update match status
- `reconvoy.update_blackline_processing_status` - Update processing status
- `reconvoy.get_case_item_foreign_book_mappings` - Build mappings
- `reconvoy.calculate_case_fx_variance` - Calculate variance

## Output Format

Return JSON with these fields:
- `item_id` - The item you processed
- `case_items` - All items in the case
- `variance_gbp` - FX variance amount
- `is_straight_through` - true if |variance| ≤ 100
- `proposed_journals` - 4 journal entries
- `execution_trace` - What you did (markdown)

See the prompt for full output schema.
