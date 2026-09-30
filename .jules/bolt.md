## 2026-05-18 - Repetitive String Lowercasing in Search Loops
**Learning:** `count_term_matches` and `compute_directness_score` are called inside loops in `dag.py` and `store.py`. They internally call `.lower()` on both the search text and search terms repeatedly. This causes a massive CPU bottleneck during searches.
**Action:** Update `count_term_matches` to optionally accept pre-lowered strings (or introduce a new parameter to bypass `lower()`) and update `dag.py` and `store.py` to lower the candidate string once per row, and lower the terms once outside the loop entirely.
