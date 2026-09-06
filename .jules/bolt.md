## 2026-03-01 - SQLite executemany Optimization
**Learning:** `append_batch` in `store.py` currently inserts rows one by one in a python loop. It can be significantly optimized using `executemany()`. However, we must ensure each message gets a strictly unique timestamp by applying a minor offset (`time.time() + (i * 1e-6)`), and we must manually retrieve the auto-incremented IDs by doing `SELECT last_insert_rowid()` and calculating backward, because `executemany` sets `lastrowid` to `None`.
**Action:** Optimize `append_batch` using `executemany` and backward ID calculation.
