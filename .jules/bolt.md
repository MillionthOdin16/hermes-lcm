
## 2026-09-16 - Prevent repeatedly calling .lower() inside search scoring loops
**Learning:** Repetitive string operations (like `.lower()`) inside hot loops for search algorithms/scoring mechanisms in Python create significant CPU overhead. Using `count_term_matches(content, term)` which does `content.lower().count(term.lower())` inside a loop over terms and fetched rows leads to exponential redundant work.
**Action:** When calculating search rank or score, always pre-process invariants outside the loops. Lowercase search terms beforehand and lowercase string content once per row, then use native Python functions like `.count()` on the already formatted strings.
