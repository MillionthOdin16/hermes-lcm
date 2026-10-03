## 2026-05-18 - Repetitive String Lowercasing in Search Loops

**Learning:** `search_query.py`'s `count_term_matches` function takes `text` and `term`, and repeatedly converts them to lowercase using `.lower()`. When this function is called inside hot loops (e.g., scoring candidates retrieved from SQLite in `dag.py` and `store.py`), the repetitive string `.lower()` conversion becomes a significant performance bottleneck. Memory states also highlighted this exact anti-pattern.

**Action:** Pre-process invariant text (lowercased candidate strings and lowercased search terms) before invoking the matching logic. Update `count_term_matches` (and related hot-loop usages) to assume or require pre-lowercased inputs, or create an optimized fast-path matching function that takes pre-lowercased strings, thereby hoisting `.lower()` operations out of loops.
