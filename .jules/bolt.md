
## 2026-10-27 - Inefficient Filtering of Large In-Memory Lists
**Learning:** `get_session_messages` fetched the *entire* session message history and deserialized every row. When searching for candidates strictly after `_last_compacted_store_id`, a list comprehension (`[stored for stored in get_session_messages(...) if stored["store_id"] > _last_compacted_store_id]`) forced Python to load and discard huge amounts of already-compacted historical data.
**Action:** Use SQLite's capabilities by replacing `get_session_messages(...)` with `get_range(..., start_id=_last_compacted_store_id + 1)` to push the filter to the database and stream only necessary uncompacted candidates, dropping overhead.
