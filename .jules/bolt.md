## 2026-10-25 - Prevent Inefficient Lowercasing in Search Hot Loops
**Learning:** Calling `.lower()` inside nested loops for string matching (e.g. `haystack.lower().count(needle.lower())` in `count_term_matches`) is a severe CPU bottleneck during large dataset processing.
**Action:** Always pre-process invariants (lowercase candidate text and search terms) outside the loops. Update shared utility functions to accept pre-processed text or change implementations safely to minimize repeated allocations.
