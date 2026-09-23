## 2026-09-12 - SQLite Batch Insert via RETURNING
**Learning:** `sqlite3` driver in Python does not support `executemany` with `RETURNING` clauses, making it hard to efficiently retrieve auto-incremented IDs for a batch of inserts. Relying on `last_insert_rowid()` minus batch size is unsafe because it assumes contiguous ID generation.
**Action:** Dynamically construct a single `INSERT INTO ... VALUES (...), (...) RETURNING store_id` query instead of using `executemany`. Ensure parameter limits (SQLite defaults to 999) aren't exceeded by chunking the batch into smaller pieces before executing.
