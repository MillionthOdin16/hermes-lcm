## 2026-10-27 - SQLite Optimization Pattern
**Learning:** Python's `sqlite3` driver sets `cur.lastrowid` to `None` after `executemany()`. The most efficient pattern for batch inserts returning IDs is `executemany` followed by `SELECT last_insert_rowid()`. Tests may require distinct timestamps for uniqueness which must be offset per row.
**Action:** Use `SELECT last_insert_rowid()` after `executemany` when replacing iterative `execute` loops for batch operations in SQLite. Also ensure to compute distinct timestamps per item in the batch.
