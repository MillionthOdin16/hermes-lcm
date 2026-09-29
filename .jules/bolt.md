
## 2026-09-29 - Repetitive string operations in SQLite row processing loops
**Learning:** In paths where a large number of rows are processed in memory (e.g., `_search_like` pagination fetching rows and computing text scores), repeatedly calling `.lower()` on strings inside the row-iteration loop (`nodes` or `rows` loop multiplied by `terms` loop) creates a substantial CPU bottleneck.
**Action:** When working on row inspection/scoring logic for SQLite searches, extract string normalization (like `t.lower() for t in terms`) outside the iteration loop. For string methods like `count_term_matches`, pass an explicit bypass flag to prevent repeated conversion when dealing with pre-normalized haystack/needle parameters.
