## 2026-05-18 - [SQLite `executemany` optimization]
**Learning:** Python's `sqlite3` driver sets `cur.lastrowid` to `None` after `executemany()`. To retrieve auto-incremented IDs for batch inserts without a `RETURNING` clause, execute `SELECT last_insert_rowid()` immediately after the batch insert to get the last inserted ID, then calculate the preceding inserted IDs backward using `cur.rowcount` or `len(batch)`.
**Action:** Use this pattern to batch insert rows and retrieve IDs.
