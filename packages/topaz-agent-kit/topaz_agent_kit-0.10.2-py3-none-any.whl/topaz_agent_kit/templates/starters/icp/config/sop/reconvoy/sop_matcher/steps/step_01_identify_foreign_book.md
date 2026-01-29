# Step 1: Identify Foreign Book

## What You Do

Look at the item's currency and decide which foreign book to check.

## Simple Rules

| Currency | Check This Book |
|----------|----------------|
| USD | us_books |
| EUR | fr_books |
| GBP | Try both (tool does this automatically) |

## Steps

1. Get the item (if you only have item_id):
   ```
   reconvoy.get_blackline_item_by_id(db_file, item_id)
   ```

2. Check the `currency` field

3. Set `foreign_book_type`:
   - USD → "us_books"
   - EUR → "fr_books"
   - GBP → "both" (tool handles it)

## Skip If

- `processing_status = "processing"` → Skip (already being processed)
- `processing_status = "need_to_process"` → Do NOT skip (process it)

## Document in Execution Trace

For this step, record in `execution_trace`:
- **Input**: Item details (item_id, currency, processing_status)
- **Tool calls**: `get_blackline_item_by_id` (if needed) with parameters
- **Output**: foreign_book_type decision
- **Decision**: Why you chose this foreign book

## Next

→ Go to Step 2
