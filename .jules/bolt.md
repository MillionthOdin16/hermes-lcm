## 2026-05-20 - [SQLite Batch Insert Optimization]
**Learning:** In Python's `sqlite3` driver, when using `cur.executemany()` for batch inserts, `cur.lastrowid` is set to `None`. To retrieve auto-incremented IDs without a `RETURNING` clause, you must execute `SELECT last_insert_rowid()` immediately after the batch insert to get the last inserted ID, then calculate the preceding inserted IDs backward using `cur.rowcount` or `len(batch)`.
**Action:** When converting iterative `execute()` inserts to `executemany()` for performance, ensure the `last_insert_rowid()` workaround is implemented to maintain correct return values for generated IDs.

## 2026-05-20 - [Unique Timestamps in Batch Inserts]
**Learning:** In this codebase's architecture (specifically `store.py`), there is a strict regression constraint where each message row must receive a strictly unique timestamp. Batch inserts that reuse the same `time.time()` will fail tests like `test_append_batch_timestamps_are_unique_per_row`.
**Action:** When implementing `executemany()` for message batch insertions, always apply a minor microsecond offset (e.g., `time.time() + (i * 1e-6)`) when generating batch parameters to ensure strict timestamp monotonicity per row.
