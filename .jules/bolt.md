## 2026-03-02 - Python conditional expressions
**Learning:** Python's conditional expression `A if condition else B` short-circuits. Therefore, `min(func(), 1) if condition else func()` will only evaluate `func()` once per execution, unlike what might be expected from other languages or simple inspection.
**Action:** Do not refactor ternary conditionals just to "prevent double evaluation" because Python already handles short-circuiting. Focus on actual repeated work like `.lower()` operations in loops.
