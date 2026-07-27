
## 2026-03-09 - SQLite executemany ID Retrieval and Unique Constraints
**Learning:** Python's `sqlite3` driver resets `cur.lastrowid` to `None` after `executemany()`. Also, if unique continuous timestamps are strictly required in batch inserts (for things like ordering constraints), relying on `time.time()` in a fast loop isn't sufficient since it doesn't change fast enough. Using `time.time() + (i * 1e-6)` is needed to enforce strict sequence uniqueness.
**Action:** When converting multiple `execute()` loop inserts into `executemany()`, immediately follow with `SELECT last_insert_rowid()` and subtract the batch length to reconstruct sequential IDs, and ensure timestamp uniqueness via an index-based minor offset if the data model depends on them being distinct.
