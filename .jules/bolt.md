
## 2026-07-17 - Optimize batch inserts using executemany
**Learning:** Python's sqlite3 driver sets cur.lastrowid to None after executemany(). To retrieve auto-incremented IDs for batch inserts without a RETURNING clause, one must execute SELECT last_insert_rowid() immediately after the batch insert to get the last inserted ID, then calculate the preceding inserted IDs backward using len(batch).
**Action:** When migrating to executemany for SQLite batch inserts, calculate row IDs manually using last_insert_rowid() and the batch length. Also ensure timestamp uniqueness is maintained manually if row ordering matters.
