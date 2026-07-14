## 2026-07-14 - Python SQLite executemany Behavior
**Learning:** Python's `sqlite3` driver sets `cur.lastrowid` to `None` after `executemany()`. The codebase requires batch insert mechanisms to return the IDs of inserted records.
**Action:** To retrieve auto-incremented IDs for batch inserts without a `RETURNING` clause (older SQLite or simple driver), execute `SELECT last_insert_rowid()` immediately after the batch insert to get the last inserted ID, then calculate the preceding inserted IDs backward using `cur.rowcount` or `len(batch)`.
