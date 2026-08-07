## 2026-08-07 - [SQLite executemany Last Row ID Backcalculation]
**Learning:** Python's `sqlite3` driver explicitly sets `cur.lastrowid` to `None` when executing `executemany()` for batch operations. Relying on it for ID tracking will fail silently or break expectations, despite standard `execute()` calls returning it accurately.
**Action:** Always fetch `SELECT last_insert_rowid()` immediately following an `executemany` insertion inside the same transaction lock, and retroactively compute the IDs sequentially using the length of the batched items.

## 2026-08-07 - [Microsecond Timestamp Regression Constraints]
**Learning:** The codebase relies heavily on chronological consistency tests for batched data (`test_append_batch_timestamps_are_unique_per_row`), asserting that each batched row has a strictly unique monotonic timestamp. Fast executions (like `executemany`) utilizing loops with `time.time()` may cause duplicate timestamps and fail these tests due to OS time resolution constraints.
**Action:** When creating batched timestamps, capture `base = time.time()` once outside the loop and apply a deterministic offset (e.g. `base + (i * 1e-6)`) during batch parameter generation to satisfy monotonic test expectations.
