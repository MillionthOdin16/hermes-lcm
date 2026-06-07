
## 2026-05-18 - Avoid repeated string formatting in O(N*M) ID mapping
**Learning:** In `LCMEngine._get_store_ids_for_messages`, raw messages are mapped back to their DB `store_id` using a nested loop (`messages` over `candidates`), resulting in an O(N*M) check. The check involved repeatedly calling `_message_replay_identity` on the *same* candidate rows across different outer loop iterations. This identity function does complex JSON normalization, regex lookups, and dictionary traversal which scales very poorly when done redundantly.
**Action:** When performing nested loops against a candidate list, always precalculate complex structural identities or fingerprints beforehand into a linear array or map before diving into the nested `while` or `for` loops.
