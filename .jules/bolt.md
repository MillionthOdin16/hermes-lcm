## 2026-05-15 - SQLite executemany Optimization
**Learning:** Python's `sqlite3` driver sets `cur.lastrowid` to `None` after `executemany()`. Also, the codebase requires strictly unique timestamps per row in batch inserts (for test stability and time-series correctness).
**Action:** When converting inserts to `executemany()`, execute `SELECT last_insert_rowid()` immediately after to get the last ID, and calculate the preceding inserted IDs backward using `cur.rowcount`. Also, add a small offset `time.time() + (i * 1e-6)` to timestamps within the batch.
