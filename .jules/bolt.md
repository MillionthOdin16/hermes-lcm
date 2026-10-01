## 2026-05-18 - Repetitive String Operations in Hot Loops
**Learning:** Repetitive string operations (like `.lower()`) and function calls inside hot loops (e.g., search/ranking loops in `dag.py`, `store.py`, `search_query.py`) create severe CPU bottlenecks.
**Action:** Pre-process invariants (lowercase candidate text and search terms) outside the loops. Avoid inlining shared utility functions like `count_term_matches` to avoid review rejections; instead, pass pre-processed inputs or carefully update the utility's implementation.
