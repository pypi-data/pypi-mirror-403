"""Sandbox execution module for Azure Dynamic Sessions.

This module provides session-aware code execution that:
1. Stores Claude session IDs in local files
2. Resumes conversations across /code/execute calls
3. Emits JSON events to stdout for parent process parsing

Two-Stage Authentication (Recommended):

    # Stage 1: Check auth status (non-blocking)
    from triagent.sandbox.runner import run_check_auth
    import asyncio
    asyncio.run(run_check_auth("omnia-data"))
    # Returns device code if auth needed, user completes auth externally

    # Stage 2: Initialize SDK (after auth confirmed)
    from triagent.sandbox.runner import run_init_sdk
    import asyncio
    asyncio.run(run_init_sdk("omnia-data"))

    # Chat (automatically resumes session)
    from triagent.sandbox.runner import run_chat
    import asyncio
    asyncio.run(run_chat("What is 2+2?"))

Events are emitted as JSON lines to stdout:
    {"type": "progress", "step": "validating", "message": "..."}
    {"type": "device_code", "code": "ABC123", "url": "https://..."}
    {"type": "text", "content": "I'll help you..."}
    {"type": "done", "session_id": "...", "turns": 1}
"""

from triagent.sandbox.events import EventType, emit_event
from triagent.sandbox.session_store import SessionState, SessionStore

# Import runner functions - these are the main entry points
# Note: Lazy import to avoid circular dependencies at module load time


def run_check_auth(team: str = "omnia-data"):
    """Stage 1: Check auth status, return device code if needed.

    Non-blocking - returns immediately with auth status.
    See triagent.sandbox.runner.run_check_auth for full documentation.
    """
    import asyncio

    from triagent.sandbox.runner import run_check_auth as _run_check_auth
    return asyncio.run(_run_check_auth(team))


def run_init_sdk(team: str = "omnia-data"):
    """Stage 2: Initialize SDK after authentication confirmed.

    See triagent.sandbox.runner.run_init_sdk for full documentation.
    """
    import asyncio

    from triagent.sandbox.runner import run_init_sdk as _run_init_sdk
    return asyncio.run(_run_init_sdk(team))


def run_init(team: str = "omnia-data"):
    """Initialize SDK session with device flow authentication (legacy).

    This is the blocking version - use run_check_auth + run_init_sdk instead.
    See triagent.sandbox.runner.run_init for full documentation.
    """
    import asyncio

    from triagent.sandbox.runner import run_init as _run_init
    return asyncio.run(_run_init(team))


def run_chat(message: str, team: str = "omnia-data"):
    """Send chat message with automatic session resumption.

    See triagent.sandbox.runner.run_chat for full documentation.
    """
    import asyncio

    from triagent.sandbox.runner import run_chat as _run_chat
    return asyncio.run(_run_chat(message, team))


__all__ = [
    # Two-stage auth (recommended)
    "run_check_auth",
    "run_init_sdk",
    # Legacy entry points
    "run_init",
    "run_chat",
    # Events
    "emit_event",
    "EventType",
    # Session storage
    "SessionStore",
    "SessionState",
]
