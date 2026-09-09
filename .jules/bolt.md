
## 2026-05-18 - Batch Insert Auto-Increment Resolution in SQLite
**Learning:** When using `sqlite3.Connection.executemany()` for batch inserts to optimize away Python loops, `lastrowid` is nullified by the driver. For tables utilizing auto-increment primary keys, executing `SELECT last_insert_rowid()` immediately after the transaction accurately yields the final inserted ID even when `AFTER INSERT` triggers exist on the table (as in `messages` to `messages_fts`).
**Action:** When replacing loops with `executemany()` for `INSERT`, always calculate the returned IDs backwards from the `last_insert_rowid()` result using `last_id - len(batch) + 1`, and explicitly guard the function with `if not batch: return []` to prevent arbitrary IDs from being fetched on empty arrays.
