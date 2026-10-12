## 2026-10-12 - Repetitive String Lowering in Hot Loops
**Learning:** Calling `.lower()` redundantly inside search and ranking loops causes significant CPU bottlenecks due to new string allocations for every call.
**Action:** Pre-process text to lowercase before iterating and update shared utility functions (like `count_term_matches`) with a `pre_lowered` flag to avoid breaking the default contract while enabling optimization.
