"""Hermes LCM Plugin — Lossless Context Management.

Replaces the built-in ContextCompressor with a DAG-based context engine
that persists every message and provides structured retrieval tools.

Based on the LCM paper by Ehrlich & Blackman (Voltropy PBC, Feb 2026).
"""

import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _env_flag_enabled(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _make_wrapped_handler(tool_name: str, engine):
    """Route a registered lcm_* tool through the engine dispatch path."""
    def _wrapped(args: dict, **kwargs) -> str:
        return engine.handle_tool_call(tool_name, args, **kwargs)
    return _wrapped


def _host_forwards_registered_tool_messages(ctx) -> bool:
    """Return whether ctx.register_tool handlers receive active messages.

    Hermes Agent's current registry dispatch passes task_id/user_task to
    plugin tools, but not the active conversation messages list. Registering
    duplicate lcm_* tool names on that host makes the model call the registry
    handler instead of the native context-engine dispatch branch, so LCM loses
    current-turn ingest before lcm_grep/lcm_expand style recovery.

    Keep plugin-side tool registration opt-in until a host explicitly
    advertises that registered context-engine handlers receive messages.
    """
    capability = getattr(ctx, "context_engine_tool_handlers_receive_messages", False)
    if callable(capability):
        try:
            capability = capability()
        except Exception:
            return False
    return bool(capability)


def register(ctx):
    """Plugin entry point — register the LCM context engine and tools."""
    from .config import LCMConfig
    from .engine import LCMEngine
    from .schemas import (
        LCM_GREP,
        LCM_LOAD_SESSION,
        LCM_DESCRIBE,
        LCM_EXPAND,
        LCM_EXPAND_QUERY,
        LCM_STATUS,
        LCM_DOCTOR,
    )

    config = LCMConfig.from_env()

    # Resolve hermes_home for profile-scoped storage
    hermes_home = ""
    try:
        from hermes_cli.config import get_hermes_home
        hermes_home = str(get_hermes_home())
    except Exception:
        import os
        hermes_home = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))

    engine = LCMEngine(config=config, hermes_home=hermes_home)

    # Register as the context engine (replaces ContextCompressor)
    ctx.register_context_engine(engine)

    # Register tools via the plugin registry only on hosts that preserve the
    # active messages=... contract for registered context-engine tools. Current
    # Hermes Agent handles lcm_* correctly through the native context-engine
    # schema/dispatch path; registering duplicate names there would shadow that
    # path and lose current-turn ingest.
    _TOOLS = [
        ("lcm_grep", LCM_GREP, "🔍"),
        ("lcm_load_session", LCM_LOAD_SESSION, "📋"),
        ("lcm_describe", LCM_DESCRIBE, "📊"),
        ("lcm_expand", LCM_EXPAND, "🔎"),
        ("lcm_expand_query", LCM_EXPAND_QUERY, "❓"),
        ("lcm_status", LCM_STATUS, "💚"),
        ("lcm_doctor", LCM_DOCTOR, "🏥"),
    ]
    register_tool = getattr(ctx, "register_tool", None)
    if callable(register_tool) and _host_forwards_registered_tool_messages(ctx):
        for name, schema, emoji in _TOOLS:
            try:
                register_tool(
                    name=name,
                    toolset="context_engine",
                    schema=schema,
                    handler=_make_wrapped_handler(name, engine),
                    description=schema.get("description", ""),
                    emoji=emoji,
                )
            except Exception as exc:
                logger.warning(
                    "LCM tool registration failed for %s; "
                    "continuing with context-engine schemas: %s",
                    name,
                    exc,
                )
    elif callable(register_tool):
        logger.info(
            "LCM plugin tool registration skipped because this Hermes host "
            "does not advertise messages forwarding for registered "
            "context-engine tools; continuing with context-engine schemas"
        )
    else:
        logger.info(
            "LCM tool registration unavailable on this Hermes host; "
            "continuing with context-engine schemas"
        )

    register_command = getattr(ctx, "register_command", None)
    slash_enabled = _env_flag_enabled("LCM_ENABLE_SLASH_COMMAND", default=False)
    if callable(register_command) and slash_enabled:
        from .command import handle_lcm_command

        register_command(
            "lcm",
            lambda raw_args: handle_lcm_command(raw_args, engine),
            description="LCM context management commands",
        )
    elif callable(register_command):
        logger.info("LCM slash command registration disabled (set LCM_ENABLE_SLASH_COMMAND=1 to enable /lcm)")
    else:
        logger.info("LCM slash command registration unavailable on this Hermes host; continuing without /lcm")

    logger.info("LCM plugin loaded — lossless context management active")


def health_check() -> dict:
    """
    Returns hermes-lcm operational status.
    Checks engine binding, storage availability, and DB path.
    Note: status "error" is expected when not running inside active Hermes runtime.
    """
    status = "ok"
    issues = []
    storage_path = ""
    sessions_active = 0

    try:
        from .engine import LCMEngine
        from .config import LCMConfig

        default_cfg = LCMConfig.from_env()
        hermes_home = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))
        engine = LCMEngine(config=default_cfg, hermes_home=hermes_home)
        storage_path = str(engine.db_path) if hasattr(engine, "db_path") else "unknown"

        if not engine.db_path:
            issues.append("storage_not_initialized")
            status = "degraded"
        elif not engine.db_path.exists():
            issues.append("storage_path_not_found")
            status = "degraded"

        if callable(getattr(engine, "get_session_count", None)):
            try:
                sessions_active = engine.get_session_count()
            except Exception:
                pass

        # Watchdog: check maintenance debt load
        try:
            lifecycle_conn = getattr(getattr(engine, "_lifecycle", None), "_conn", None)
            if lifecycle_conn is not None:
                debt_rows = lifecycle_conn.execute(
                    """
                    SELECT COUNT(*) AS debt_count,
                           SUM(debt_size_estimate) AS total_debt
                      FROM lcm_lifecycle_state
                     WHERE debt_kind IS NOT NULL AND debt_size_estimate > 0
                    """
                ).fetchone()
                if debt_rows and debt_rows["debt_count"]:
                    debt_count = debt_rows["debt_count"]
                    total_debt = debt_rows["total_debt"] or 0
                    if total_debt > 500_000:
                        status = "degraded"
                        issues.append(f"high_maintenance_debt: {debt_count} convos, {total_debt} tokens")
                    # else: healthy, no issue flag needed
        except Exception:
            pass  # non-critical diagnostic

    except Exception as e:
        err_str = str(e)
        issues.append(err_str)
        # agent module missing = Hermes runtime not active = "unknown" (expected,
        # not an error). The plugin is unavailable but not broken.
        if "agent" in err_str:
            status = "unknown"
        elif "ContextEngine" in err_str:
            status = "degraded"
        else:
            status = "error"

    return {
        "plugin": "hermes-lcm",
        "status": status,
        "storage_path": storage_path,
        "sessions_active": sessions_active,
        "issues": issues,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
