## 2026-02-18 - Repeated string operations in hot loops
**Learning:** Calling `.lower()` on the same large string repeatedly inside a search term iteration loop is a significant CPU bottleneck due to CPython's string allocation behavior.
**Action:** Pre-calculate `text.lower()` and `[term.lower() for term in terms]` outside loops, and pass them down with an explicit `is_lowered` bypass flag to `count_term_matches`.
