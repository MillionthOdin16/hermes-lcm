## 2026-02-18 - [SQLite Optimization]
**Learning:** Python's `sqlite3` driver sets `cur.lastrowid` to `None` after `executemany()`. To retrieve auto-incremented IDs for batch inserts without a `RETURNING` clause, execute `SELECT last_insert_rowid()` immediately after the batch insert to get the last inserted ID, then calculate the preceding inserted IDs backward using `cur.rowcount` or `len(batch)`.
**Action:** When using `executemany` for auto-increment inserts, manually compute IDs and add a minor offset to timestamps in iterations to prevent unique constraint failures in tests.
