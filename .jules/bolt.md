## 2026-07-22 - SQLite executemany lastrowid behavior
**Learning:** Python's sqlite3 driver clears `cur.lastrowid` when using `executemany()`. The codebase also enforces unique timestamp constraints across bulk row inserts.
**Action:** Calculate the auto-increment IDs manually starting from `SELECT last_insert_rowid()` minus the parameter length and use a microsecond offset iterator `base_ts + (i * 1e-6)` during batch insert payload creation.
