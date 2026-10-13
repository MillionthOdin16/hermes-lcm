## 2026-10-27 - [Optimize .lower() allocations in ranking hot loops]
**Learning:** Repetitive string operations like `.lower()` on the same candidate text inside ranking hot loops (e.g. `compute_directness_score` and `search_like`) causes severe CPU bottlenecks because CPython generates a new string object each time.
**Action:** Pre-process invariants (like lowercasing the candidate text and search terms) outside the loops. Update shared utility functions like `count_term_matches` to accept an optional `pre_lowered` boolean flag to bypass redundant `.lower()` operations.
