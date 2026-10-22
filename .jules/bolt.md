## 2026-10-27 - [Lowercasing in loops bottleneck]
**Learning:** Calling `.lower()` on strings inside hot loops (like in `dag.py` and `store.py` during fallback searches and ranking) creates severe CPU bottlenecks because CPython generates a new string object every time.
**Action:** Pre-process text to lowercase before iterating (e.g. `lower_summary = node.summary.lower()`) and pass `pre_lowered=True` to functions like `count_term_matches` if they support it, or modify them to support it.
