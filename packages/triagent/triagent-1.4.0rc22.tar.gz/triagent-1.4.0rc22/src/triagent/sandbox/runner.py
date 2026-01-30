"""Core sandbox runner with session resumption.

This module is executed inside Azure Dynamic Sessions via /code/execute.
It manages Claude SDK sessions with automatic resumption across calls.

Two-Stage Initialization:
    Stage 1 - Check auth status (non-blocking):
        from triagent.sandbox.runner import run_check_auth
        asyncio.run(run_check_auth("omnia-data"))
        # Returns immediately with auth status + device code if needed

    Stage 2 - Initialize SDK (after auth confirmed):
        from triagent.sandbox.runner import run_init_sdk
        asyncio.run(run_init_sdk("omnia-data"))
        # Assumes auth is complete, initializes Claude SDK

Legacy (blocking - deprecated):
    from triagent.sandbox.runner import run_init
    asyncio.run(run_init("omnia-data"))

Events are emitted as JSON lines to stdout, which the parent process
(SessionProxy) parses to update the Chainlit UI.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import subprocess
from typing import Any

from triagent.sandbox.events import (
    emit_config_options,
    emit_config_valid,
    emit_confirm_request,
    emit_device_code,
    emit_done,
    emit_error,
    emit_progress,
    emit_text,
    emit_tool_end,
    emit_tool_start,
)
from triagent.sandbox.session_store import SessionState, SessionStore

logger = logging.getLogger(__name__)


# =============================================================================
# Two-Stage Authentication Functions (Recommended)
# =============================================================================


async def run_check_auth(team: str = "omnia-data") -> None:
    """Stage 1: Check auth status, return device code if needed.

    This function is NON-BLOCKING - it returns immediately with auth status.
    If not authenticated, it returns the device code for the user to complete
    authentication externally.

    Args:
        team: Team profile to use (omnia-data, levvia, etc.)

    Events emitted:
        - progress: Checking auth status
        - device_code: If authentication required (code + URL)
        - done: With authenticated=True/False flag
        - error: If check fails
    """
    emit_progress("checking_auth", "Checking Azure authentication...")

    # Check for force re-authentication flag
    force_auth = os.getenv("TRIAGENT_FORCE_AUTH", "false").lower() == "true"

    if force_auth:
        emit_progress("force_auth", "Force re-authentication enabled")

    is_authenticated = _is_azure_authenticated()

    if is_authenticated and not force_auth:
        emit_progress("auth_ok", "Already authenticated")
        # Get current user for display
        user = _get_azure_user()
        emit_done(authenticated=True, user=user)
        return

    # Not authenticated - get device code without blocking
    emit_progress("auth_required", "Azure authentication required")

    device_code, url = _get_device_code_nonblocking()

    if device_code:
        emit_device_code(
            code=device_code,
            url=url or "https://microsoft.com/devicelogin",
            message="Complete authentication in your browser, then click 'Done'",
        )
        emit_done(authenticated=False, requires_auth=True)
    else:
        emit_error("Failed to get device code. Please ensure Azure CLI is installed.")


async def run_init_sdk(
    team: str = "omnia-data",
    persona: str = "developer",
    model: str = "claude-opus-4-5",
) -> None:
    """Stage 2: Initialize SDK after authentication confirmed.

    This function polls for authentication completion with a 2 minute timeout.
    The daemon started in Stage 1 may still be processing the token from Azure.

    All configuration options (team, persona, model) are passed upfront from
    the frontend configuration modal.

    Args:
        team: Team profile to use (omnia-data, levvia, etc.)
        persona: Persona profile (developer, support)
        model: Claude model to use (claude-opus-4-5, claude-sonnet-4)

    Events emitted:
        - progress: Various initialization steps
        - text: Initial response from Claude
        - done: On successful initialization with session_id
        - error: If initialization fails or auth times out
    """
    import time

    emit_progress("verifying_auth", "Waiting for authentication...")

    # Poll for authentication with 2 minute timeout
    timeout = 120  # 2 minutes
    poll_interval = 5  # Check every 5 seconds
    start = time.time()
    poll_count = 0

    while time.time() - start < timeout:
        poll_count += 1

        if _is_azure_authenticated():
            break

        elapsed = int(time.time() - start)
        remaining = timeout - elapsed
        emit_progress(
            "auth_waiting",
            f"Waiting for authentication... ({remaining}s remaining)"
        )
        await asyncio.sleep(poll_interval)
    else:
        # Timeout reached - user didn't complete auth in time
        emit_error(
            "Authentication timed out after 2 minutes. "
            "Please refresh and try again."
        )
        return

    emit_progress("auth_ok", "Authentication verified")
    user = _get_azure_user()
    emit_progress("auth_user", f"Logged in as: {user}")

    # Initialize config
    emit_progress("validating", "Validating environment...")
    store = SessionStore()

    try:
        from triagent.config import ConfigManager

        config_manager = ConfigManager()
        config_manager.ensure_dirs()
    except Exception as e:
        emit_error(f"Failed to initialize config: {str(e)}")
        return

    # Initialize SDK
    emit_progress("creating_sdk", "Initializing Claude SDK...")

    try:
        from claude_agent_sdk import ClaudeSDKClient
        from rich.console import Console

        from triagent.sdk_client import create_sdk_client

        # Create a minimal console (no output)
        console = Console(force_terminal=False, no_color=True, quiet=True)

        # Build SDK options with team and persona from parameters
        client_factory = create_sdk_client(
            config_manager, console, team=team, persona=persona
        )
        options = client_factory._build_options()

        # Run a simple query to get session_id
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt="Hello, I'm ready to help.")

            async for msg in client.receive_response():
                msg_type = type(msg).__name__

                if msg_type == "AssistantMessage":
                    # Process response content
                    for block in msg.content:
                        block_type = type(block).__name__
                        if block_type == "TextBlock":
                            emit_text(block.text)

                elif msg_type == "ResultMessage":
                    # Get session_id for future resumption
                    session_id = getattr(msg, "session_id", None)
                    num_turns = getattr(msg, "num_turns", 1)

                    if session_id:
                        # Save session with all config options
                        state = SessionState(
                            session_id=session_id,
                            team=team,
                            persona=persona,
                            model=model,
                            initialized=True,
                            conversation_turns=num_turns,
                        )
                        store.save(state)

                        emit_progress(
                            "ready",
                            "Connected to Claude",
                            model=model,
                            persona=persona,
                            session_id=session_id[:8],
                        )
                        emit_done(session_id=session_id, turns=num_turns)
                        return
                    else:
                        emit_error("No session_id in result message")
                        return

    except ImportError as e:
        emit_error(f"Missing dependency: {str(e)}")
    except Exception as e:
        logger.exception("Failed to initialize SDK")
        emit_error(f"Failed to initialize: {str(e)}")


async def run_validate_config(
    team: str,
    persona: str,
    model: str,
) -> None:
    """Validate configuration options without initializing SDK.

    This function checks if the provided team, persona, and model values
    are valid options without actually initializing the SDK.

    Args:
        team: Team profile to validate
        persona: Persona to validate
        model: Model to validate

    Events emitted:
        - config_options: Available configuration options
        - config_valid: Validation result (valid=True/False, errors=[])
        - error: If validation fails unexpectedly
    """
    # Define valid options
    valid_teams = ["omnia-data", "omnia", "levvia"]
    valid_personas = ["developer", "support"]
    valid_models = ["claude-opus-4-5", "claude-sonnet-4"]

    # Emit available options
    emit_config_options(
        teams=valid_teams,
        personas=valid_personas,
        models=valid_models,
    )

    # Validate provided options
    errors: list[str] = []

    if team not in valid_teams:
        errors.append(f"Invalid team '{team}'. Valid options: {valid_teams}")

    if persona not in valid_personas:
        errors.append(f"Invalid persona '{persona}'. Valid options: {valid_personas}")

    if model not in valid_models:
        errors.append(f"Invalid model '{model}'. Valid options: {valid_models}")

    # Emit validation result
    if errors:
        emit_config_valid(valid=False, errors=errors)
    else:
        emit_config_valid(valid=True)

    emit_done()


async def run_health_check() -> None:
    """Check session health and return status.

    This function checks:
    1. Azure CLI authentication status
    2. Session file existence and initialization
    3. Stored preferences (team, persona, model)

    Used by Chainlit frontend to determine if session can be resumed
    without showing the configuration modal.

    Events emitted:
        - progress: Checking session health
        - done: With health status and stored preferences
    """
    import time

    emit_progress("health_check", "Checking session health...")

    # Check Azure CLI auth
    is_auth = _is_azure_authenticated()
    user = _get_azure_user() if is_auth else None

    # Check session file
    store = SessionStore()
    session = store.load()

    # Update last_active timestamp if session exists
    if session and is_auth:
        session.last_active = time.time()
        if user:
            session.azure_user = user
        store.save(session)

    # Trust session file - if initialized with turns > 0, consider healthy
    # Even if Azure CLI auth expired, we can still resume the SDK session
    is_healthy = (
        session is not None
        and session.initialized
        and session.session_id
        and session.conversation_turns > 0
    )

    emit_done(
        healthy=is_healthy,
        azure_auth=is_auth,
        azure_user=user,
        session_initialized=session.initialized if session else False,
        conversation_turns=session.conversation_turns if session else 0,
        team=session.team if session else None,
        persona=session.persona if session else None,
        model=session.model if session else None,
        last_active=session.last_active if session else None,
    )


def _get_device_code_nonblocking() -> tuple[str | None, str | None]:
    """Get device code by starting az login as a background daemon.

    Uses nohup to keep the process alive after /code/execute returns.
    The daemon will save credentials to ~/.azure when auth completes.

    This is critical because Azure Dynamic Sessions terminates all processes
    when /code/execute returns. The nohup daemon survives and can receive
    the authentication token when the user completes device flow in browser.

    Returns:
        Tuple of (device_code, verification_url) or (None, None) on failure
    """
    import time
    from pathlib import Path

    # Use ~/.triagent/ for log file (works with any user: root, triagent, local)
    log_dir = Path.home() / ".triagent"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = str(log_dir / "az_login_device.log")

    try:
        # Clear any previous log file
        try:
            os.remove(log_file)
        except FileNotFoundError:
            pass

        # Start az login as a daemon that survives /code/execute exit
        # Using os.system with nohup ensures the process is fully detached
        # The & at the end backgrounds the process
        os.system(f"nohup az login --use-device-code > {log_file} 2>&1 &")

        # Wait for device code to appear in log file
        timeout = 15
        start = time.time()

        while time.time() - start < timeout:
            time.sleep(0.5)

            try:
                with open(log_file) as f:
                    content = f.read()

                # Look for device code pattern in output
                if "devicelogin" in content.lower() and "code" in content.lower():
                    code_match = re.search(r"code\s+([A-Z0-9]+)", content)
                    url_match = re.search(
                        r"(https://[^\s]+devicelogin[^\s]*)", content
                    )

                    if code_match:
                        code = code_match.group(1)
                        url = (
                            url_match.group(1)
                            if url_match
                            else "https://microsoft.com/devicelogin"
                        )
                        # Daemon continues running in background
                        # It will save credentials when user completes auth
                        return (code, url)
            except FileNotFoundError:
                continue

        return (None, None)

    except Exception as e:
        logger.error(f"Device code error: {e}")
        return (None, None)


def _get_azure_user() -> str:
    """Get currently authenticated Azure user.

    Returns:
        User name/email or "unknown" if not available
    """
    try:
        result = subprocess.run(
            ["az", "account", "show", "--query", "user.name", "-o", "tsv"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        return "unknown"
    except Exception:
        return "unknown"


# =============================================================================
# Legacy Functions (Blocking - for backwards compatibility)
# =============================================================================


async def run_init(team: str = "omnia-data") -> None:
    """Initialize SDK session with device flow authentication.

    This function:
    1. Checks if Azure CLI is authenticated
    2. If not, triggers device flow and emits device_code event
    3. Waits for user to complete authentication
    4. Initializes Claude SDK with team configuration
    5. Saves session state to file

    Args:
        team: Team profile to use (omnia-data, levvia, etc.)

    Events emitted:
        - progress: Various initialization steps
        - device_code: If Azure CLI auth needed
        - done: On successful initialization
        - error: If initialization fails
    """
    emit_progress("validating", "Validating environment...")

    store = SessionStore()

    # Import here to avoid circular imports and ensure we're in container context
    try:
        from triagent.config import ConfigManager

        config_manager = ConfigManager()
        config_manager.ensure_dirs()
    except Exception as e:
        emit_error(f"Failed to initialize config: {str(e)}")
        return

    # Check Azure CLI authentication
    emit_progress("checking_auth", "Checking Azure CLI authentication...")

    # Check for force re-authentication flag
    force_auth = os.getenv("TRIAGENT_FORCE_AUTH", "false").lower() == "true"
    is_authenticated = _is_azure_authenticated()

    if force_auth:
        emit_progress("force_auth", "Force re-authentication enabled")

    if force_auth or not is_authenticated:
        emit_progress("auth_required", "Azure authentication required")

        # Start device flow
        device_code, url = await _start_device_flow()
        if device_code:
            emit_device_code(
                code=device_code,
                url=url or "https://microsoft.com/devicelogin",
                message="Complete authentication in your browser",
            )

            # Wait for authentication (polls every 5 seconds, timeout 15 min)
            emit_progress("auth_waiting", "Waiting for authentication...")
            success = await _wait_for_auth(timeout=900)

            if not success:
                emit_progress("auth_timeout", "Authentication timed out")
                emit_error("Azure authentication timed out after 15 minutes")
                return

            emit_progress("auth_ok", "Azure CLI authenticated successfully")
        else:
            emit_error("Failed to start device flow authentication")
            return
    else:
        emit_progress("auth_ok", "Azure CLI already authenticated")

    # Initialize SDK
    emit_progress("creating_sdk", "Initializing Claude SDK...")

    try:
        from claude_agent_sdk import ClaudeSDKClient
        from rich.console import Console

        from triagent.sdk_client import create_sdk_client

        # Create a minimal console (no output)
        console = Console(force_terminal=False, no_color=True, quiet=True)

        # Build SDK options (legacy: uses team only, defaults to developer persona)
        client_factory = create_sdk_client(config_manager, console, team=team)
        options = client_factory._build_options()

        # Run a simple query to get session_id
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt="Hello, I'm ready to help.")

            async for msg in client.receive_response():
                msg_type = type(msg).__name__

                if msg_type == "AssistantMessage":
                    # Process response content
                    for block in msg.content:
                        block_type = type(block).__name__
                        if block_type == "TextBlock":
                            emit_text(block.text)

                elif msg_type == "ResultMessage":
                    # Get session_id for future resumption
                    session_id = getattr(msg, "session_id", None)
                    num_turns = getattr(msg, "num_turns", 1)

                    if session_id:
                        # Save session
                        state = SessionState(
                            session_id=session_id,
                            team=team,
                            initialized=True,
                            conversation_turns=num_turns,
                        )
                        store.save(state)

                        emit_progress(
                            "ready",
                            "Connected to Claude",
                            model="claude-opus-4-5",
                            session_id=session_id[:8],
                        )
                        emit_done(session_id=session_id, turns=num_turns)
                        return
                    else:
                        emit_error("No session_id in result message")
                        return

    except ImportError as e:
        emit_error(f"Missing dependency: {str(e)}")
    except Exception as e:
        logger.exception("Failed to initialize SDK")
        emit_error(f"Failed to initialize: {str(e)}")


async def run_chat(message: str, team: str = "omnia-data") -> None:
    """Send chat message with automatic session resumption.

    This function:
    1. Loads existing session from file
    2. Builds ClaudeAgentOptions with resume parameter
    3. Sends message and streams response events
    4. Updates session state

    Args:
        message: User message to send
        team: Team profile (used if no existing session)

    Events emitted:
        - progress: Session resumption status
        - text: Claude response content
        - tool_start/tool_end: Tool execution
        - done: On completion with updated session_id
        - error: If chat fails
    """
    store = SessionStore()

    # Load existing session
    existing = store.load()

    if not existing or not existing.initialized:
        emit_error("Session not initialized. Run init first.")
        return

    emit_progress("resuming", f"Resuming session {existing.session_id[:8]}...")

    try:
        from claude_agent_sdk import ClaudeSDKClient
        from rich.console import Console

        from triagent.config import ConfigManager
        from triagent.sdk_client import create_sdk_client

        config_manager = ConfigManager()
        console = Console(force_terminal=False, no_color=True, quiet=True)

        # Build SDK options with team and persona from stored session
        client_factory = create_sdk_client(
            config_manager, console,
            team=existing.team or team,
            persona=existing.persona,
        )
        options = client_factory._build_options()

        # Resume existing session
        options.resume = existing.session_id

        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt=message)

            async for msg in client.receive_response():
                _process_sdk_message(msg)

                # Check for result message to update session
                msg_type = type(msg).__name__
                if msg_type == "ResultMessage":
                    session_id = getattr(msg, "session_id", existing.session_id)
                    num_turns = getattr(msg, "num_turns", existing.conversation_turns + 1)

                    # Update session
                    existing.session_id = session_id
                    existing.conversation_turns = num_turns
                    store.save(existing)

                    emit_done(session_id=session_id, turns=num_turns)
                    return

    except ImportError as e:
        emit_error(f"Missing dependency: {str(e)}")
    except Exception as e:
        logger.exception("Chat error")
        emit_error(str(e))


def _process_sdk_message(msg: Any) -> None:
    """Process SDK message and emit corresponding events.

    Args:
        msg: SDK message (AssistantMessage, ResultMessage, etc.)
    """
    msg_type = type(msg).__name__

    if msg_type == "AssistantMessage":
        for block in msg.content:
            block_type = type(block).__name__

            if block_type == "TextBlock":
                emit_text(block.text)

            elif block_type == "ToolUseBlock":
                tool_name = getattr(block, "name", "unknown")
                tool_input = getattr(block, "input", {})
                # Truncate input for preview
                input_preview = str(tool_input)[:200]
                if len(str(tool_input)) > 200:
                    input_preview += "..."
                emit_tool_start(tool_name, input_preview)

            elif block_type == "ToolResultBlock":
                tool_id = getattr(block, "tool_use_id", "")
                is_error = getattr(block, "is_error", False)
                emit_tool_end(tool_id, not is_error)

    elif msg_type == "SystemMessage":
        # System messages can contain confirmation requests
        subtype = getattr(msg, "subtype", "")
        data = getattr(msg, "data", {})

        if subtype == "permission_request":
            request_id = data.get("request_id", "")
            tool_name = data.get("tool_name", "")
            description = data.get("description", "")
            emit_confirm_request(request_id, tool_name, description, data)


def _is_azure_authenticated() -> bool:
    """Check if Azure CLI is authenticated.

    Returns:
        True if authenticated, False otherwise
    """
    try:
        result = subprocess.run(
            ["az", "account", "show", "--query", "user.name", "-o", "tsv"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0 and bool(result.stdout.strip())
    except Exception:
        return False


async def _start_device_flow() -> tuple[str | None, str | None]:
    """Start Azure device flow authentication.

    Runs `az login --use-device-code` and parses the device code from stderr.

    Returns:
        Tuple of (device_code, verification_url) or (None, None) on failure
    """
    try:
        # Start device flow (non-blocking)
        proc = await asyncio.create_subprocess_exec(
            "az",
            "login",
            "--use-device-code",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Read stderr to get device code
        # Output format: "To sign in, use a web browser to open the page
        # https://microsoft.com/devicelogin and enter the code XXXX to authenticate."

        while True:
            line = await proc.stderr.readline()
            if not line:
                break

            text = line.decode().strip()
            if "devicelogin" in text.lower() and "code" in text.lower():
                # Parse device code from message
                code_match = re.search(r"code\s+([A-Z0-9]+)", text)
                url_match = re.search(r"(https://[^\s]+devicelogin[^\s]*)", text)

                if code_match:
                    code = code_match.group(1)
                    url = (
                        url_match.group(1)
                        if url_match
                        else "https://microsoft.com/devicelogin"
                    )
                    return (code, url)

        return (None, None)

    except Exception as e:
        logger.error(f"Device flow error: {e}")
        return (None, None)


async def _wait_for_auth(timeout: int = 900) -> bool:
    """Wait for Azure authentication to complete.

    Polls `az account show` every 5 seconds until authenticated or timeout.

    Args:
        timeout: Maximum wait time in seconds (default 15 min)

    Returns:
        True if authenticated, False if timeout
    """
    import time

    start = time.time()

    while time.time() - start < timeout:
        if _is_azure_authenticated():
            return True
        await asyncio.sleep(5)  # Poll every 5 seconds

    return False


# Convenience function for direct execution testing
if __name__ == "__main__":
    import sys

    def print_usage():
        print("Usage:")
        print("  python -m triagent.sandbox.runner check_auth [team]")
        print("  python -m triagent.sandbox.runner init_sdk [team] [persona] [model]")
        print("  python -m triagent.sandbox.runner validate_config <team> <persona> <model>")
        print("  python -m triagent.sandbox.runner health_check  # Check session health")
        print("  python -m triagent.sandbox.runner init [team]  # Legacy")
        print("  python -m triagent.sandbox.runner chat <msg> [team]")

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "check_auth":
            # Stage 1: Non-blocking auth check
            team = sys.argv[2] if len(sys.argv) > 2 else "omnia-data"
            asyncio.run(run_check_auth(team))
        elif command == "init_sdk":
            # Stage 2: Initialize SDK after auth with all options
            team = sys.argv[2] if len(sys.argv) > 2 else "omnia-data"
            persona = sys.argv[3] if len(sys.argv) > 3 else "developer"
            model = sys.argv[4] if len(sys.argv) > 4 else "claude-opus-4-5"
            asyncio.run(run_init_sdk(team, persona, model))
        elif command == "validate_config":
            # Validate config options
            if len(sys.argv) < 5:
                print("Error: validate_config requires team, persona, model")
                print_usage()
                sys.exit(1)
            team = sys.argv[2]
            persona = sys.argv[3]
            model = sys.argv[4]
            asyncio.run(run_validate_config(team, persona, model))
        elif command == "health_check":
            # Check session health
            asyncio.run(run_health_check())
        elif command == "init":
            # Legacy: Blocking init with device flow
            team = sys.argv[2] if len(sys.argv) > 2 else "omnia-data"
            asyncio.run(run_init(team))
        elif command == "chat":
            message = sys.argv[2] if len(sys.argv) > 2 else "Hello"
            team = sys.argv[3] if len(sys.argv) > 3 else "omnia-data"
            asyncio.run(run_chat(message, team))
        else:
            print(f"Unknown command: {command}")
            print_usage()
    else:
        print_usage()
