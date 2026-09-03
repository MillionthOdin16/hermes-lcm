## 2026-09-03 - [SQLite executemany optimization]
**Learning:** Python's sqlite3 driver sets cur.lastrowid to None after executemany(). To get the IDs of the inserted rows, we must execute SELECT last_insert_rowid() immediately after and calculate backwards. Also, time.time() might be identical for batch inserted rows, breaking regression constraints; adding a microsecond offset is needed.
**Action:** Used executemany for batch inserts and calculated row IDs backwards. Applied an i * 1e-6 offset to timestamps.
