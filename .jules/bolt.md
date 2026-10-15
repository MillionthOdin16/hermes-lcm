## 2026-03-01 - Python Performance Note
**Learning:** Repetitive string operations (like `.lower()`) inside hot loops create severe CPU bottlenecks because CPython generates a new string object every time.
**Action:** Pre-process invariants (e.g. lowercase candidate text and search terms) outside the loops. Refactor utility functions carefully or pass pre-processed inputs.
