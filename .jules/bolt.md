## 2026-05-18 - Replacing `encode` with `encode_ordinary` in `tiktoken`
**Learning:** `tiktoken.encode_ordinary()` ignores special tokens, which makes it faster than `.encode()` for simple token counting, especially for shorter strings, without sacrificing any actual count correctness for non-special text. We avoid throwing exceptions on special tokens as `encode()` does, which we don't care about when estimating text tokens.
**Action:** When only the token count is needed and not the exact tokens or special token parsing, prefer `encode_ordinary` over `encode`.
