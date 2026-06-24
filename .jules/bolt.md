## 2026-10-24 - SQLite executemany with AUTOINCREMENT
**Learning:** Python's `sqlite3` driver does not support `RETURNING` clauses in `executemany()` for batch inserts.
**Action:** When using `executemany()` to insert rows and we need their auto-incremented primary keys, query `SELECT MAX(id)` within the write lock and calculate the inserted IDs backwards using `cur.rowcount` to avoid concurrency race conditions while still gaining the batch insert speed boost.
## 2026-06-24 - SQLite executemany with cur.lastrowid
**Learning:** The Python `sqlite3` driver does support returning the maximum inserted auto-incremented primary key via `cur.lastrowid` after an `executemany()` operation. Querying `SELECT MAX(id)` can be incorrect if the column name is hallucinated or if it's not the actual primary key/rowid.
**Action:** Use `cur.lastrowid` alongside `cur.rowcount` to calculate the inserted IDs backwards instead of guessing the column name and querying it manually.
