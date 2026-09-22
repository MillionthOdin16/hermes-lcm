"""Tests for the anti-thrashing guard in should_compress().

Anti-thrashing blocks compression after 2 consecutive ineffective compressions
(less than 10% token savings). Resets after 1 effective compression. Overflow
recovery bypasses the guard entirely.
"""
from __future__ import annotations

import pytest

import hermes_lcm.engine as lcm_engine
from hermes_lcm.config import LCMConfig
from hermes_lcm.engine import LCMEngine
from hermes_lcm.tokens import count_tokens


def _text_with_token_count(target_tokens: int) -> str:
    """Create text that has approximately target_tokens tokens (tiktoken)."""
    # "x" is 1 token in cl100k_base, so repeat target_tokens times
    # Add some padding to account for overhead
    text = "x" * target_tokens
    actual = count_tokens(text)
    # If we overshot, trim; if undershot, add more
    while actual > target_tokens + 5:
        text = text[:len(text) - 10]
        actual = count_tokens(text)
    while actual < target_tokens - 5:
        text += "x" * 10
        actual = count_tokens(text)
    return text


def _make_engine(tmp_path, leaf_chunk_tokens=1, fresh_tail_count=3, context_length=200000):
    """Create an engine with small thresholds for testing."""
    config = LCMConfig(
        database_path=str(tmp_path / "anti_thrash.db"),
        fresh_tail_count=fresh_tail_count,
        leaf_chunk_tokens=leaf_chunk_tokens,
    )
    engine = LCMEngine(config=config)
    engine.on_session_start(
        "anti-thrash-session",
        platform="cli",
        conversation_id="anti-thrash-conv",
        context_length=context_length,
    )
    engine.threshold_tokens = int(context_length * config.context_threshold)
    return engine


def _big_messages(n=10, size=500):
    """Generate N messages, each ~size tokens (size*4 chars)."""
    msgs = []
    for i in range(n):
        msgs.append({"role": "user", "content": f"Message {i} " + "x" * (size * 4)})
        msgs.append({"role": "assistant", "content": f"Response {i} " + "y" * (size * 4)})
    return msgs


class TestAntiThrashingGuard:
    """Anti-thrashing blocks after 2 consecutive ineffective compressions."""

    def test_ineffective_compression_increments_counter(self, tmp_path, monkeypatch):
        """Compressions with <10% savings should increment the counter."""
        engine = _make_engine(tmp_path)

        def ineffective_summary(**kwargs):
            source_tokens = kwargs.get("source_tokens", 1000)
            # Return summary that's 95% of source -> 5% savings (< 10%)
            target = max(1, int(source_tokens * 0.95))
            return _text_with_token_count(target), 1

        monkeypatch.setattr(lcm_engine, "summarize_with_escalation", ineffective_summary)

        messages = _big_messages(10, 500)

        # First compression - should work, counter goes to 1
        engine.compress(messages)
        assert engine._ineffective_compression_count == 1

        # Second compression - should work, counter goes to 2
        messages2 = _big_messages(12, 500)
        engine.compress(messages2)
        assert engine._ineffective_compression_count == 2

        engine.shutdown()

    def test_guard_blocks_after_two_ineffective(self, tmp_path, monkeypatch):
        """should_compress returns False after 2 consecutive ineffective compressions."""
        engine = _make_engine(tmp_path)

        def ineffective_summary(**kwargs):
            source_tokens = kwargs.get("source_tokens", 1000)
            target = max(1, int(source_tokens * 0.95))
            return _text_with_token_count(target), 1

        monkeypatch.setattr(lcm_engine, "summarize_with_escalation", ineffective_summary)

        # Two ineffective compressions
        engine.compress(_big_messages(10, 500))
        engine.compress(_big_messages(12, 500))
        assert engine._ineffective_compression_count == 2

        # Now should_compress should return False even though tokens exceed threshold
        engine.last_prompt_tokens = engine.threshold_tokens + 1000
        assert not engine.should_compress(), "Guard should block after 2 ineffective compressions"

        engine.shutdown()

    def test_effective_compression_resets_counter(self, tmp_path, monkeypatch):
        """An effective compression (>=10% savings) resets the counter to 0."""
        engine = _make_engine(tmp_path)

        call_count = [0]

        def alternating_summary(**kwargs):
            source_tokens = kwargs.get("source_tokens", 1000)
            call_count[0] += 1
            if call_count[0] <= 2:
                # First two: ineffective (5% savings)
                target = max(1, int(source_tokens * 0.95))
            else:
                # Third: effective (50% savings)
                target = max(1, int(source_tokens * 0.50))
            return _text_with_token_count(target), 1

        monkeypatch.setattr(lcm_engine, "summarize_with_escalation", alternating_summary)

        # Two ineffective
        engine.compress(_big_messages(10, 500))
        assert engine._ineffective_compression_count == 1
        engine.compress(_big_messages(12, 500))
        assert engine._ineffective_compression_count == 2

        # Guard is active
        engine.last_prompt_tokens = engine.threshold_tokens + 1000
        assert not engine.should_compress()

        # One effective compression (compress() doesn't call should_compress())
        engine.compress(_big_messages(12, 500))
        assert engine._ineffective_compression_count == 0, "Counter should reset after effective compression"

        # Guard is now lifted
        engine.last_prompt_tokens = engine.threshold_tokens + 1000
        assert engine.should_compress(), "Guard should be lifted after effective compression"

        engine.shutdown()

    def test_guard_resets_on_session_reset(self, tmp_path, monkeypatch):
        """Session reset clears the anti-thrashing counter."""
        engine = _make_engine(tmp_path)

        def ineffective_summary(**kwargs):
            source_tokens = kwargs.get("source_tokens", 1000)
            target = max(1, int(source_tokens * 0.95))
            return _text_with_token_count(target), 1

        monkeypatch.setattr(lcm_engine, "summarize_with_escalation", ineffective_summary)

        # Build up counter
        engine.compress(_big_messages(10, 500))
        engine.compress(_big_messages(12, 500))
        assert engine._ineffective_compression_count == 2

        # Session reset
        engine.on_session_start(
            "new-session",
            platform="cli",
            conversation_id="new-conv",
            context_length=200000,
        )
        assert engine._ineffective_compression_count == 0

        engine.shutdown()

    def test_overflow_recovery_bypasses_guard(self, tmp_path, monkeypatch):
        """Overflow recovery should bypass the anti-thrashing guard."""
        config = LCMConfig(
            database_path=str(tmp_path / "overflow.db"),
            fresh_tail_count=3,
            leaf_chunk_tokens=1,
            max_assembly_tokens=3000,  # explicit cap triggers overflow recovery
        )
        engine = LCMEngine(config=config)
        engine.on_session_start(
            "overflow-session",
            platform="cli",
            conversation_id="overflow-conv",
            context_length=200000,
        )
        engine.threshold_tokens = int(200000 * config.context_threshold)

        def ineffective_summary(**kwargs):
            source_tokens = kwargs.get("source_tokens", 1000)
            target = max(1, int(source_tokens * 0.95))
            return _text_with_token_count(target), 1

        monkeypatch.setattr(lcm_engine, "summarize_with_escalation", ineffective_summary)

        # Build up counter to 2
        engine.compress(_big_messages(5, 200))
        engine.compress(_big_messages(6, 200))
        assert engine._ineffective_compression_count == 2

        # Now trigger overflow: observed_tokens >= max_assembly_tokens (3000)
        engine.last_prompt_tokens = 5000
        assert engine.should_compress(), "Overflow recovery must bypass anti-thrashing guard"

        engine.shutdown()

    def test_should_compress_preflight_respects_guard(self, tmp_path, monkeypatch):
        """should_compress_preflight also checks the anti-thrashing guard."""
        engine = _make_engine(tmp_path)

        def ineffective_summary(**kwargs):
            source_tokens = kwargs.get("source_tokens", 1000)
            target = max(1, int(source_tokens * 0.95))
            return _text_with_token_count(target), 1

        monkeypatch.setattr(lcm_engine, "summarize_with_escalation", ineffective_summary)

        # Build up counter
        engine.compress(_big_messages(10, 500))
        engine.compress(_big_messages(12, 500))
        assert engine._ineffective_compression_count == 2

        # Preflight should also block
        big_msgs = _big_messages(10, 500)
        assert not engine.should_compress_preflight(big_msgs), "Preflight should also respect anti-thrashing guard"

        engine.shutdown()

    def test_guard_visible_in_status(self, tmp_path, monkeypatch):
        """The ineffective_compression_count should appear in get_status()."""
        engine = _make_engine(tmp_path)

        def ineffective_summary(**kwargs):
            source_tokens = kwargs.get("source_tokens", 1000)
            target = max(1, int(source_tokens * 0.95))
            return _text_with_token_count(target), 1

        monkeypatch.setattr(lcm_engine, "summarize_with_escalation", ineffective_summary)

        # Initially 0
        status = engine.get_status()
        assert status["ineffective_compression_count"] == 0

        # After one ineffective compression
        engine.compress(_big_messages(10, 500))
        status = engine.get_status()
        assert status["ineffective_compression_count"] == 1

        engine.shutdown()


class TestAntiThrashingEdgeCases:
    """Edge cases for the anti-thrashing guard."""

    def test_zero_source_tokens_skips_tracking(self, tmp_path, monkeypatch):
        """If source_tokens is 0, don't divide by zero."""
        engine = _make_engine(tmp_path)

        def zero_source_summary(**kwargs):
            return "tiny", 1

        monkeypatch.setattr(lcm_engine, "summarize_with_escalation", zero_source_summary)

        # The counter shouldn't change if source_tokens is 0
        engine.compress(_big_messages(10, 500))
        assert engine._ineffective_compression_count == 0

        engine.shutdown()

    def test_exact_10_percent_boundary(self, tmp_path, monkeypatch):
        """Exactly 10% savings should reset the counter (not trigger anti-thrashing)."""
        engine = _make_engine(tmp_path)

        # First: ineffective (5% savings)
        def ineffective_summary(**kwargs):
            source_tokens = kwargs.get("source_tokens", 1000)
            target = max(1, int(source_tokens * 0.95))
            return _text_with_token_count(target), 1

        monkeypatch.setattr(lcm_engine, "summarize_with_escalation", ineffective_summary)
        engine.compress(_big_messages(10, 500))
        assert engine._ineffective_compression_count == 1

        # Second: effective (50% savings - well above 10% boundary)
        def effective_summary(**kwargs):
            source_tokens = kwargs.get("source_tokens", 1000)
            target = max(1, int(source_tokens * 0.50))
            return _text_with_token_count(target), 1

        monkeypatch.setattr(lcm_engine, "summarize_with_escalation", effective_summary)
        engine.compress(_big_messages(12, 500))
        # savings_pct > 10%, so counter should reset to 0
        assert engine._ineffective_compression_count == 0, (
            f"Expected counter reset at 10% boundary, got {engine._ineffective_compression_count}"
        )

        engine.shutdown()
