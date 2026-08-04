## 2026-08-04 - SQLite Batch Insert Optimization
**Learning:** Python's `sqlite3` driver resets `cur.lastrowid` to `None` for `executemany` operations. Batch inserts using a loop of `execute` are slower but provide `lastrowid`.
**Action:** Use `executemany` with `SELECT last_insert_rowid()` executed immediately afterward to get the last ID, and then calculate the preceding row IDs backward using `cur.rowcount` or `len(batch)`. Also, enforce strictly unique timestamps in batch rows by applying minor offsets (e.g., `time.time() + (i * 1e-6)`) when appending messages.
