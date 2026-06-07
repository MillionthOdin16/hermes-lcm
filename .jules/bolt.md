## 2024-05-30 - [Regex Pre-compilation in Context Parsing]
**Learning:** Python's internal regex cache (`re._MAXCACHE`) typically handles repeated raw string compilation quickly, but bypassing the cache dictionary lookup by storing the compiled `re.Pattern` object at the module level yields ~30-40% faster execution in tight loops. In context management systems like Hermes-LCM, checking hundreds of messages per compression cycle adds up.
**Action:** Always pre-compile regular expressions at the module scope if they are evaluated inside critical loops or message-filtering functions.
