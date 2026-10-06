## 2026-10-06 - Avoid string operations like .lower() in hot loops
**Learning:** Repetitive string operations like .lower() inside hot loops are a severe performance bottleneck because CPython creates a new string object every time. Redundantly converting the same strings (search terms, query results) degrades search ranking throughput.
**Action:** Pre-process string invariants (e.g., lowercasing terms and content) outside inner iteration loops or mapping functions to avoid redundant memory allocations and CPU overhead.
