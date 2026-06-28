## 2026-06-27 - SQLite executemany Pattern

**Learning:** Python's `sqlite3` driver resets `cur.lastrowid` to `None` after `executemany()` making batch inserts with auto-increment keys difficult without a `RETURNING` clause (which may not be available across all SQLite versions in the target environment).
**Action:** When performing batch inserts with `executemany()` that require auto-incremented IDs to be returned, you can run `SELECT last_insert_rowid()` immediately after the insert, then calculate the full range of inserted IDs backwards using `cur.rowcount`: `list(range(last_id - rowcount + 1, last_id + 1))`. This provides the performance benefit of `executemany` while preserving the ID list return values.
