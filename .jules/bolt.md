## 2026-10-24 - [Store Write Performance]
**Learning:** `append_batch` in `store.py` currently executes individual `INSERT` statements in a python loop over the provided messages. Using `executemany` directly with SQLite significantly improves write batch performance by moving the loop from Python into C.
**Action:** Always favor `executemany` for batch database inserts.
