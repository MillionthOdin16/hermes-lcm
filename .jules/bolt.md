## 2026-07-25 - Python SQLite optimization for bulk inserts
**Learning:** Python's sqlite3 executemany does not reliably return lastrowid.
**Action:** When using executemany for bulk inserts where returned autoincrement IDs are needed, query SELECT last_insert_rowid() after the batch insert and calculate the assigned IDs backward based on the length of the batch.
