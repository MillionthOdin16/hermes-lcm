## 2026-09-17 - Hoisting string operations outside hot loops
**Learning:** Repetitive string allocations/operations like `.lower()` inside a hot scoring loop (such as iterating over search terms in `compute_directness_score`) creates severe CPU bottlenecks and memory allocation overhead in Python.
**Action:** Always pre-process loop-invariant operations (like lowercasing the candidate document) before entering the loop to ensure O(1) string allocations instead of O(N).
