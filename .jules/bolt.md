## 2024-05-15 - Redundant `.lower()` ops inside loops are a performance anti-pattern
**Learning:** Repetitive string operations (like `.lower()`) inside hot loops (e.g., search/ranking loops in `dag.py`, `store.py`, `search_query.py`) and inside shared utility functions like `count_term_matches` create severe CPU bottlenecks because CPython allocates a new string object every time.
**Action:** Pre-process text to lowercase before iterating and update utility functions to optionally accept pre-lowered text or pre-lower invariants outside loops.
