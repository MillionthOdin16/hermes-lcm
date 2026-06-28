## 2026-10-18 - [SQLite executemany Last Row ID]
**Learning:** Python's `sqlite3` driver resets `cur.lastrowid` to `None` when executing `executemany()`. Also, there are explicit regression constraints enforcing that timestamps in a batch must remain unique on a microsecond level.
**Action:** Always fetch the sequential ID via `SELECT last_insert_rowid()` manually within the batch insert transaction block and extrapolate range IDs using `cur.rowcount` backwards. Ensure to add explicit microsecond increments across loop batching arrays.
