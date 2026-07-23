## 2026-07-23 - [Python SQLite Batch Insert Last Row ID]
**Learning:** Python's `sqlite3` driver does not set `lastrowid` after `executemany()`. In batch insert procedures that return auto-increment IDs, calling `executemany` directly breaks the return contract because `lastrowid` will be `None`.
**Action:** Always fetch `SELECT last_insert_rowid()` immediately following the `executemany` batch, and backward-calculate the preceding sequential IDs using the batch size (`len(batch)`) and the final returned auto-increment ID (`last_id - len(batch) + 1`).

## 2026-07-23 - [Message Store Timestamp Uniqueness Constraint]
**Learning:** The database model has a strict constraint against duplicated message timestamps which can fail tests if batch queries execute too quickly (e.g., `test_append_batch_timestamps_are_unique_per_row`).
**Action:** When swapping sequential inserts to `executemany` for batch message inserts, pre-calculate the timestamps and manually inject a microscopic offset inside the list iteration: `ts = base_ts + (i * 1e-6)`.
