## 2026-06-25 - Prevented CPU Bottleneck in Hot Search Loops
**Learning:** Repetitive string operations (like `.lower()`) and function calls inside hot loops (e.g., search/ranking loops in `dag.py`, `store.py`, `search_query.py`) create severe CPU bottlenecks in Python since `.lower()` always allocates a new string.
**Action:** Pre-process invariants (like lowercasing candidate text and search terms) outside the loops. We passed `is_lowered=True` to `count_term_matches` to reuse the pre-lowered states and save allocations.
