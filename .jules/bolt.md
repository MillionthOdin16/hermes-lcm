# Bolt's Journal
## 2026-05-15 - Eliminating redundant `.lower()` in search inner loops
**Learning:** Python's overhead for repetitive string operations (`.lower()`) and function calls inside hot ranking loops (like the `LIKE` fallback loop processing hundreds/thousands of candidates against multiple terms) can become a significant CPU bottleneck. The abstract helper `count_term_matches` was inadvertently enforcing repetitive `.lower()` calls and object creations on every iteration.
**Action:** Always pre-process loop invariants (like lowercasing the search terms or the candidate row text) and inline or tailor the hot-path counting logic directly (e.g., using `text.count(term)`) rather than relying on generalized abstraction helpers when looping over dataset rows.
