## 2026-07-19 - [SQLite Batch Insert Optimization]
**Learning:** Using `executemany` directly instead of a loop of `execute` operations for inserting large batches is vastly faster in this codebase (around 15x speedup for 1000 records).
**Action:** When working on plugins heavily dependent on SQLite like `hermes-lcm`, always opt for `executemany` over loop-based `execute` for writes. Ensure timestamp constraints specific to this app are respected (offsetting by microsecond).
