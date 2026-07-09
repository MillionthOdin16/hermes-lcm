"""Tests for lifecycle orphan detection, cleanup, fragmentation, and compression correctness.

Covers:
- Orphan lifecycle row detection (rows referencing no messages or summary_nodes)
- Triple-guard DELETE query correctness
- Token counting calibration (tiktoken behavior documentation)
- Anti-thrashing counter in lcm_status output
- lcm_doctor orphan detection
- Lifecycle fragmentation detection
- Compression correctness (summaries created, savings tracked)
"""
from __future__ import annotations

import time

import pytest

import hermes_lcm.engine as lcm_engine
from hermes_lcm.config import LCMConfig
from hermes_lcm.engine import LCMEngine
from hermes_lcm.tokens import count_tokens


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _text_with_token_count(target_tokens: int) -> str:
    """Create text with approximately target_tokens tokens (tiktoken cl100k_base).

    IMPORTANT: With tiktoken cl100k_base, repeated 'x' chars give ~N/4 tokens
    for N characters. Always use this helper or count_tokens() to calibrate
    test summaries. Never use character-based estimates (len(text) // 4).

    Verified behavior (May 2026):
      count_tokens("x") = 1
      count_tokens("x ") = 1
      count_tokens("x" * 100) = 26
      count_tokens("x" * 1000) = 251
    """
    text = "x" * target_tokens
    actual = count_tokens(text)
    while actual > target_tokens + 5:
        text = text[:len(text) - 10]
        actual = count_tokens(text)
    while actual < target_tokens - 5:
        text += "x" * 10
        actual = count_tokens(text)
    return text


def _make_engine(tmp_path, **config_kwargs):
    """Create an engine with small thresholds for testing."""
    defaults = dict(
        database_path=str(tmp_path / "test.db"),
        fresh_tail_count=3,
        leaf_chunk_tokens=1,
    )
    defaults.update(config_kwargs)
    config = LCMConfig(**defaults)
    engine = LCMEngine(config=config)
    engine.on_session_start(
        "test-session",
        platform="cli",
        conversation_id="test-conv",
        context_length=200000,
    )
    engine.threshold_tokens = int(200000 * config.context_threshold)
    return engine


def _big_messages(n=10, size=500):
    """Generate N message pairs, each ~size tokens."""
    msgs = []
    for i in range(n):
        msgs.append({"role": "user", "content": f"Message {i} " + "x" * (size * 4)})
        msgs.append({"role": "assistant", "content": f"Response {i} " + "y" * (size * 4)})
    return msgs


# ---------------------------------------------------------------------------
# Orphan Lifecycle Detection
# ---------------------------------------------------------------------------

class TestOrphanLifecycleDetection:
    """Verify that orphan lifecycle rows can be detected and cleaned up."""

    def _create_orphan_row(self, conn, conversation_id="orphan-conv"):
        """Insert a lifecycle row that references no messages or summary_nodes."""
        conn.execute(
            """INSERT INTO lcm_lifecycle_state
               (conversation_id, current_session_id, last_finalized_session_id,
                current_frontier_store_id, last_finalized_frontier_store_id, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (conversation_id, "orphan-session", None, 0, 0, time.time()),
        )
        conn.commit()

    def _count_orphans(self, conn):
        """Run the triple-guard orphan detection query."""
        return int(conn.execute(
            """
            SELECT COUNT(*) FROM lcm_lifecycle_state
            WHERE conversation_id NOT IN (SELECT DISTINCT session_id FROM messages)
              AND conversation_id NOT IN (SELECT DISTINCT session_id FROM summary_nodes)
              AND (current_session_id IS NULL OR current_session_id NOT IN
                   (SELECT DISTINCT session_id FROM messages))
              AND (current_session_id IS NULL OR current_session_id NOT IN
                   (SELECT DISTINCT session_id FROM summary_nodes))
              AND (last_finalized_session_id IS NULL OR last_finalized_session_id NOT IN
                   (SELECT DISTINCT session_id FROM messages))
              AND (last_finalized_session_id IS NULL OR last_finalized_session_id NOT IN
                   (SELECT DISTINCT session_id FROM summary_nodes))
            """
        ).fetchone()[0])

    def test_orphan_rows_detected_by_triple_guard(self, tmp_path):
        """The triple-guard query correctly identifies orphan rows."""
        engine = _make_engine(tmp_path)
        engine._store.append("test-session", {"role": "user", "content": "hi"}, source="cli")

        self._create_orphan_row(engine._lifecycle._conn)

        assert self._count_orphans(engine._lifecycle._conn) == 1
        engine.shutdown()

    def test_valid_rows_not_flagged_as_orphans(self, tmp_path):
        """Rows referencing real messages must NOT be flagged as orphans."""
        engine = _make_engine(tmp_path)
        engine._store.append("test-session", {"role": "user", "content": "hi"}, source="cli")

        assert self._count_orphans(engine._lifecycle._conn) == 0
        engine.shutdown()

    def test_orphan_delete_preserves_valid_rows(self, tmp_path):
        """The triple-guard DELETE removes only orphans, preserving valid rows."""
        engine = _make_engine(tmp_path)
        engine._store.append("test-session", {"role": "user", "content": "hi"}, source="cli")

        for i in range(3):
            self._create_orphan_row(engine._lifecycle._conn, f"orphan-{i}")

        total_before = int(engine._lifecycle._conn.execute(
            "SELECT COUNT(*) FROM lcm_lifecycle_state"
        ).fetchone()[0])
        assert total_before == 4  # 1 valid + 3 orphans

        engine._lifecycle._conn.execute(
            """
            DELETE FROM lcm_lifecycle_state
            WHERE conversation_id NOT IN (SELECT DISTINCT session_id FROM messages)
              AND conversation_id NOT IN (SELECT DISTINCT session_id FROM summary_nodes)
              AND (current_session_id IS NULL OR current_session_id NOT IN
                   (SELECT DISTINCT session_id FROM messages))
              AND (current_session_id IS NULL OR current_session_id NOT IN
                   (SELECT DISTINCT session_id FROM summary_nodes))
              AND (last_finalized_session_id IS NULL OR last_finalized_session_id NOT IN
                   (SELECT DISTINCT session_id FROM messages))
              AND (last_finalized_session_id IS NULL OR last_finalized_session_id NOT IN
                   (SELECT DISTINCT session_id FROM summary_nodes))
            """
        )
        engine._lifecycle._conn.commit()

        total_after = int(engine._lifecycle._conn.execute(
            "SELECT COUNT(*) FROM lcm_lifecycle_state"
        ).fetchone()[0])
        assert total_after == 1

        remaining = engine._lifecycle._conn.execute(
            "SELECT conversation_id FROM lcm_lifecycle_state"
        ).fetchone()[0]
        assert remaining == "test-conv"
        engine.shutdown()

    def test_orphan_rows_with_summary_nodes_not_flagged(self, tmp_path):
        """Rows whose conversation_id exists in summary_nodes are NOT orphans."""
        from hermes_lcm.dag import SummaryNode

        engine = _make_engine(tmp_path)
        node = SummaryNode(
            session_id="test-session", depth=0, summary="test summary",
            token_count=10, source_token_count=100, source_ids=[],
            source_type="messages", created_at=time.time(),
        )
        engine._dag.add_node(node)

        assert self._count_orphans(engine._lifecycle._conn) == 0
        engine.shutdown()

    def test_multiple_orphans_mixed_with_valid(self, tmp_path):
        """Correctly counts orphans when mixed with valid rows."""
        engine = _make_engine(tmp_path)
        engine._store.append("test-session", {"role": "user", "content": "hi"}, source="cli")

        # Add 2 more valid sessions (commit store first to release locks)
        for sess in ["valid-1", "valid-2"]:
            engine._store.append(sess, {"role": "user", "content": "hi"}, source="cli")

        # Now insert lifecycle rows for valid sessions
        for sess in ["valid-1", "valid-2"]:
            engine._lifecycle._conn.execute(
                "INSERT INTO lcm_lifecycle_state (conversation_id, current_session_id, updated_at) VALUES (?, ?, ?)",
                (f"conv-{sess}", sess, time.time()),
            )
        engine._lifecycle._conn.commit()

        # Add 5 orphans
        for i in range(5):
            self._create_orphan_row(engine._lifecycle._conn, f"orphan-{i}")

        # Total: 3 valid (test-conv + conv-valid-1 + conv-valid-2) + 5 orphans = 8
        total = int(engine._lifecycle._conn.execute(
            "SELECT COUNT(*) FROM lcm_lifecycle_state"
        ).fetchone()[0])
        assert total == 8

        assert self._count_orphans(engine._lifecycle._conn) == 5
        engine.shutdown()


# ---------------------------------------------------------------------------
# Token Counting Calibration
# ---------------------------------------------------------------------------

class TestTokenCountingCalibration:
    """Document and verify tiktoken behavior to prevent test calibration errors.

    KEY LESSON: With tiktoken cl100k_base, repeated 'x' chars give ~N/4 tokens.
    Always use _text_with_token_count() or count_tokens() to calibrate test
    summaries. Never use character-based estimates (len(text) // 4).

    Verified behavior (May 2026, tiktoken cl100k_base):
      count_tokens("x") = 1
      count_tokens("x ") = 1
      count_tokens("x" * 100) = 26
      count_tokens("x" * 1000) = 251
    """

    def test_single_char_one_token(self):
        assert count_tokens("x") == 1

    def test_char_with_space_one_token(self):
        """tiktoken cl100k_base merges 'x ' into 1 token."""
        assert count_tokens("x ") == 1

    def test_repeated_chars_compress(self):
        """Repeated chars are ~N/4 tokens, not N tokens."""
        assert count_tokens("x" * 100) == 26
        assert count_tokens("x" * 1000) == 251

    def test_text_with_token_count_helper_accurate(self):
        """The _text_with_token_count helper produces accurate token counts."""
        for target in [10, 100, 500, 1000]:
            text = _text_with_token_count(target)
            actual = count_tokens(text)
            assert abs(actual - target) <= 5, f"Target {target}, got {actual}"

    def test_empty_string_zero_tokens(self):
        assert count_tokens("") == 0
        assert count_tokens(None) == 0


# ---------------------------------------------------------------------------
# Anti-Thrashing Integration
# ---------------------------------------------------------------------------

class TestAntiThrashingIntegration:
    """Integration tests verifying anti-thrashing works end-to-end."""

    def test_ineffective_count_in_lcm_status(self, tmp_path, monkeypatch):
        """ineffective_compression_count appears in get_status() output."""
        engine = _make_engine(tmp_path)

        def ineffective_summary(**kwargs):
            source_tokens = kwargs.get("source_tokens", 1000)
            return _text_with_token_count(max(1, int(source_tokens * 0.95))), 1

        monkeypatch.setattr(lcm_engine, "summarize_with_escalation", ineffective_summary)

        status = engine.get_status()
        assert "ineffective_compression_count" in status
        assert status["ineffective_compression_count"] == 0

        engine.compress(_big_messages(10, 500))
        status = engine.get_status()
        assert status["ineffective_compression_count"] == 1
        engine.shutdown()

    def test_counter_resets_on_session_switch(self, tmp_path, monkeypatch):
        """Switching sessions resets the anti-thrashing counter."""
        engine = _make_engine(tmp_path)

        def ineffective_summary(**kwargs):
            source_tokens = kwargs.get("source_tokens", 1000)
            return _text_with_token_count(max(1, int(source_tokens * 0.95))), 1

        monkeypatch.setattr(lcm_engine, "summarize_with_escalation", ineffective_summary)

        engine.compress(_big_messages(10, 500))
        engine.compress(_big_messages(12, 500))
        assert engine._ineffective_compression_count == 2

        engine.on_session_start("new-session", platform="cli",
                                conversation_id="new-conv", context_length=200000)
        assert engine._ineffective_compression_count == 0
        engine.shutdown()

    def test_guard_does_not_block_first_compression(self, tmp_path, monkeypatch):
        """The guard never blocks the first compression (counter starts at 0)."""
        engine = _make_engine(tmp_path)

        def ineffective_summary(**kwargs):
            source_tokens = kwargs.get("source_tokens", 1000)
            return _text_with_token_count(max(1, int(source_tokens * 0.95))), 1

        monkeypatch.setattr(lcm_engine, "summarize_with_escalation", ineffective_summary)

        engine.last_prompt_tokens = engine.threshold_tokens + 1000
        assert engine.should_compress()

        engine.compress(_big_messages(10, 500))
        assert engine._ineffective_compression_count == 1

        engine.last_prompt_tokens = engine.threshold_tokens + 1000
        assert engine.should_compress()
        engine.shutdown()


# ---------------------------------------------------------------------------
# Lifecycle Fragmentation Detection
# ---------------------------------------------------------------------------

class TestLifecycleFragmentation:
    """Verify that lifecycle fragmentation is correctly detected."""

    def test_fragmentation_stats_report_stale_rows(self, tmp_path):
        """Lifecycle rows referencing sessions not in state.db are flagged."""
        engine = _make_engine(tmp_path)
        engine._store.append("test-session", {"role": "user", "content": "hi"}, source="cli")

        # Create a state.db with only the current session
        import sqlite3
        state_db = tmp_path / "hermes_home" / "state.db"
        state_db.parent.mkdir(parents=True, exist_ok=True)
        state_conn = sqlite3.connect(state_db)
        state_conn.executescript("""
            CREATE TABLE sessions (id TEXT PRIMARY KEY);
            INSERT INTO sessions(id) VALUES ('test-session');
        """)
        state_conn.commit()
        state_conn.close()
        engine._hermes_home = str(tmp_path / "hermes_home")

        # Insert a lifecycle row for a session NOT in state.db
        engine._lifecycle._conn.execute(
            "INSERT INTO lcm_lifecycle_state (conversation_id, current_session_id, updated_at) VALUES (?, ?, ?)",
            ("stale-conv", "stale-session", time.time()),
        )
        engine._lifecycle._conn.commit()

        stats = engine._lifecycle.get_fragmentation_stats(
            state_db_path=str(state_db)
        )
        # The stale session should be counted as missing from state
        assert stats["lifecycle_current_missing_in_state"] >= 1
        engine.shutdown()

    def test_no_fragmentation_when_all_sessions_aligned(self, tmp_path):
        """No fragmentation when all lifecycle rows reference real sessions."""
        engine = _make_engine(tmp_path)
        engine._store.append("test-session", {"role": "user", "content": "hi"}, source="cli")

        import sqlite3
        state_db = tmp_path / "hermes_home" / "state.db"
        state_db.parent.mkdir(parents=True, exist_ok=True)
        state_conn = sqlite3.connect(state_db)
        state_conn.executescript("""
            CREATE TABLE sessions (id TEXT PRIMARY KEY);
            INSERT INTO sessions(id) VALUES ('test-session');
        """)
        state_conn.commit()
        state_conn.close()
        engine._hermes_home = str(tmp_path / "hermes_home")

        stats = engine._lifecycle.get_fragmentation_stats(
            state_db_path=str(state_db)
        )
        assert stats["lifecycle_current_missing_in_state"] == 0
        assert stats["lifecycle_rows"] >= 1
        engine.shutdown()


# ---------------------------------------------------------------------------
# Compression Correctness
# ---------------------------------------------------------------------------

class TestCompressionCorrectness:
    """Verify that compress() produces correct summaries and tracks savings."""

    def test_compress_creates_summary_node(self, tmp_path, monkeypatch):
        """compress() creates a summary node in the DAG."""
        engine = _make_engine(tmp_path)

        def mock_summary(**kwargs):
            return "Test summary of compressed content.", 1

        monkeypatch.setattr(lcm_engine, "summarize_with_escalation", mock_summary)

        messages = _big_messages(10, 500)
        engine.compress(messages)

        nodes = engine._dag.get_session_nodes("test-session")
        assert len(nodes) >= 1
        assert "Test summary" in nodes[0].summary
        engine.shutdown()

    def test_compress_tracks_source_token_count(self, tmp_path, monkeypatch):
        """Summary nodes record the source token count for savings tracking."""
        engine = _make_engine(tmp_path)

        def mock_summary(**kwargs):
            return "Short summary.", 1

        monkeypatch.setattr(lcm_engine, "summarize_with_escalation", mock_summary)

        engine.compress(_big_messages(10, 500))

        nodes = engine._dag.get_session_nodes("test-session")
        assert len(nodes) >= 1
        assert nodes[0].source_token_count > 0
        assert nodes[0].token_count > 0
        # Summary should be smaller than source
        assert nodes[0].token_count < nodes[0].source_token_count
        engine.shutdown()

    def test_compress_increments_counter(self, tmp_path, monkeypatch):
        """compress() increments compression_count."""
        engine = _make_engine(tmp_path)

        def mock_summary(**kwargs):
            return "Summary.", 1

        monkeypatch.setattr(lcm_engine, "summarize_with_escalation", mock_summary)

        assert engine.compression_count == 0
        engine.compress(_big_messages(10, 500))
        assert engine.compression_count == 1
        engine.compress(_big_messages(12, 500))
        assert engine.compression_count == 2
        engine.shutdown()

    def test_compress_preserves_fresh_tail(self, tmp_path, monkeypatch):
        """compress() preserves the most recent messages (fresh tail)."""
        engine = _make_engine(tmp_path, fresh_tail_count=4)

        def mock_summary(**kwargs):
            return "Older context summary.", 1

        monkeypatch.setattr(lcm_engine, "summarize_with_escalation", mock_summary)

        messages = _big_messages(10, 500)
        result = engine.compress(messages)

        # Fresh tail messages should be in the result
        # The last 4 messages should be preserved
        last_contents = [m.get("content", "") for m in result[-4:]]
        assert any("Message 9" in c or "Response 9" in c for c in last_contents)
        engine.shutdown()

    def test_compress_status_compacted(self, tmp_path, monkeypatch):
        """After successful compression, status is 'compacted'."""
        engine = _make_engine(tmp_path)

        def mock_summary(**kwargs):
            return "Summary.", 1

        monkeypatch.setattr(lcm_engine, "summarize_with_escalation", mock_summary)

        engine.compress(_big_messages(10, 500))
        assert engine._last_compression_status == "compacted"
        assert engine._last_compression_noop_reason == ""
        engine.shutdown()

    def test_compress_noop_when_below_threshold(self, tmp_path, monkeypatch):
        """compress() is a no-op when messages are below the chunk threshold."""
        engine = _make_engine(tmp_path, leaf_chunk_tokens=100000)

        # Send very small messages
        small_msgs = [{"role": "user", "content": "hi"}]
        result = engine.compress(small_msgs)

        # Should be a no-op
        assert engine._last_compression_status == "noop"
        assert engine.compression_count == 0
        engine.shutdown()


# ---------------------------------------------------------------------------
# Doctor Orphan Detection
# ---------------------------------------------------------------------------

class TestDoctorOrphanDetection:
    """Verify that lcm_doctor reports orphan lifecycle rows."""

    def test_doctor_reports_orphan_rows(self, tmp_path):
        """lcm_doctor should report orphan lifecycle rows as an observation."""
        engine = _make_engine(tmp_path)
        engine._store.append("test-session", {"role": "user", "content": "hi"}, source="cli")

        for i in range(5):
            engine._lifecycle._conn.execute(
                "INSERT INTO lcm_lifecycle_state (conversation_id, current_session_id, updated_at) VALUES (?, ?, ?)",
                (f"orphan-{i}", f"orphan-sess-{i}", time.time()),
            )
        engine._lifecycle._conn.commit()

        from hermes_lcm.command import _doctor_text
        output = _doctor_text(engine)

        assert "orphan_lifecycle_rows: 5" in output
        assert "safe to delete" in output
        engine.shutdown()

    def test_doctor_no_orphan_report_when_clean(self, tmp_path):
        """lcm_doctor should not mention orphans when none exist."""
        engine = _make_engine(tmp_path)
        engine._store.append("test-session", {"role": "user", "content": "hi"}, source="cli")

        from hermes_lcm.command import _doctor_text
        output = _doctor_text(engine)

        assert "orphan_lifecycle_rows" not in output
        engine.shutdown()
