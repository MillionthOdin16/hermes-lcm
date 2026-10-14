
## 2026-10-27 - Pre-lower strings in hot loops
**Learning:** CPython creates a new string object every time `.lower()` is called, even if the string is already lowercase. Repeatedly calling `.lower()` in hot loops (like in search fallback scoring) for each term creates significant CPU overhead and memory allocations.
**Action:** Pre-process invariants outside the loops (e.g. lowercase candidate text once per row and pre-lower search terms once) and pass a flag to utility functions to bypass internal `.lower()` calls.
