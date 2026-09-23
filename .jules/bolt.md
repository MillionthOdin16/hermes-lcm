## 2026-05-18 - SQLite Batch Insert Optimizations
**Learning:** Python's `sqlite3` driver returns `None` for `lastrowid` when using `executemany()`. Calling `SELECT last_insert_rowid()` immediately after batch insert safely returns the last auto-incremented ID, even with AFTER INSERT triggers.
**Action:** When performing bulk database insertions, use `executemany` with parameter lists and fetch the last ID with `SELECT last_insert_rowid()`. Calculate preceding IDs by subtracting `len(batch)` to avoid the N+1 query problem without sacrificing correctness.
