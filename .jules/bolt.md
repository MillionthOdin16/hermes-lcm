## 2026-02-18 - Avoid repeated .lower() in Python hot loops
**Learning:** Calling `.lower()` on strings inside hot loops (e.g. over database rows and search terms) creates severe CPU bottlenecks and memory allocation overhead in Python.
**Action:** When implementing filtering or search logic over arrays/rows, pre-process string variants (like lowering search text or terms) outside the loop to avoid redundant allocations.
