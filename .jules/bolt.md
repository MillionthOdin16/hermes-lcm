## 2026-10-24 - [executemany optimization]
**Learning:** Python`s sqlite3 driver sets cur.lastrowid to None after executemany.
**Action:** Use SELECT last_insert_rowid() and calculate backwards based on len(batch) to get IDs for batch inserts.
