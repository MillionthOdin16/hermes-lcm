
## 2026-07-03 - SQLite Optimization Pattern: executemany and rowids
**Learning:** Python's `sqlite3` driver does not set `cur.lastrowid` after `executemany()` (it sets it to `None`). For batch inserts, `executemany` is much faster, but returning IDs requires a workaround when a `RETURNING` clause isn't supported or used. Additionally, test constraints may require slightly shifted timestamps in a fast batch processing loop.
**Action:** When migrating loops of `execute()` to `executemany()` in SQLite without `RETURNING`, execute `SELECT last_insert_rowid()` immediately afterward to get the ID of the last inserted row, then infer the rest of the IDs backward using `cur.rowcount`. Also, use `base_ts + (i * 1e-6)` for strictly unique timestamps when iterating fast.
