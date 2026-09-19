## 2026-03-24 - Avoid redundant lowercasing in hot loops
**Learning:** Repetitive string operations (like `.lower()`) and function calls inside hot loops create severe CPU bottlenecks. The `count_term_matches` utility function repeatedly lowercases strings inside loops over search results.
**Action:** Pre-process invariants (lowercase candidate text and search terms) outside the loops. Update `count_term_matches` or pass pre-processed strings.
