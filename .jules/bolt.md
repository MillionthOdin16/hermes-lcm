## 2026-04-20 - [SQLite Batch Insert Timestamps]
**Learning:** `test_append_batch_timestamps_are_unique_per_row` enforces strictly unique and non-decreasing timestamps for batch insertion. When optimizing with `executemany`, the rapid parameter generation in a loop may evaluate `time.time()` to the same exact value multiple times, causing tests to fail.
**Action:** Apply a micro-offset `time.time() + (i * 1e-6)` inside the parameter generation loop before `executemany` to preserve deterministic and monotonically increasing timestamps.

## 2026-04-20 - [Python Tuple Unpacking Performance]
**Learning:** For frequently-called hydration methods like `_row_to_dict`, dynamic dictionary generation (`dict(zip(cols, row))`) is ~2.25x slower than a static dictionary literal utilizing index-based tuple unpacking `{"store_id": row[0], "session_id": row[1]...}`.
**Action:** Unroll dynamic `zip` mappings into static dictionary literals for hot-path object hydration when the schema structure is rigid and known.
