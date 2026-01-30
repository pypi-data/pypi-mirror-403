"""Chainlit chat interface for Triagent with Dynamic Sessions sandbox pattern.

This module provides the Chainlit-based web UI for Triagent, using the
/code/execute pattern for Azure Dynamic Sessions.

For local testing, set TRIAGENT_LOCAL_MODE=true to use a local Docker
container instead of Azure Dynamic Sessions.
"""

import logging
import os
import time
import uuid

import chainlit as cl

from triagent.web.container.session_manager import ChainlitSessionManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _log_user_request(
    action: str,
    user_id: str,
    session_id: str,
    correlation_id: str,
    duration_ms: int | None = None,
    **extra: str | int | bool,
) -> None:
    """Log user request with consistent key=value format for grep-friendly filtering.

    Format: user={user_id} session={session_id} correlation_id={id} action={action} [duration={ms}ms] [extra]

    Args:
        action: The action name (e.g., "user_message", "request_complete").
        user_id: User identifier.
        session_id: Session identifier.
        correlation_id: Correlation ID for request tracing.
        duration_ms: Optional operation duration in milliseconds.
        **extra: Additional key-value pairs to log.
    """
    parts = [
        f"user={user_id}",
        f"session={session_id}",
        f"correlation_id={correlation_id}",
        f"action={action}",
    ]
    if duration_ms is not None:
        parts.append(f"duration={duration_ms}ms")
    for k, v in extra.items():
        # Quote string values that contain spaces
        if isinstance(v, str) and " " in v:
            parts.append(f'{k}="{v}"')
        else:
            parts.append(f"{k}={v}")
    logger.info(" ".join(parts))


@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: dict[str, str],
    default_user: cl.User,
) -> cl.User | None:
    """Handle Azure AD OAuth callback.

    Args:
        provider_id: OAuth provider ("azure-ad")
        token: Access token
        raw_user_data: User info from Azure AD
        default_user: Default user object from Chainlit

    Returns:
        cl.User with Azure AD identity, or None to reject
    """
    if provider_id == "azure-ad":
        # Extract user info from Azure AD claims
        return cl.User(
            identifier=raw_user_data.get("preferred_username", default_user.identifier),
            metadata={
                "provider": "azure-ad",
                "name": raw_user_data.get("name", ""),
                "email": raw_user_data.get("preferred_username", ""),
            },
        )
    return None


# Configuration options
TEAMS = {
    "Omnia Data": "omnia-data",
    "Omnia": "omnia",
    "Levvia": "levvia",
}

PERSONAS = {
    "Developer": "developer",
    "Support": "support",
}

MODELS = {
    "Claude Opus 4.5": "claude-opus-4-5",
    "Claude Sonnet 4": "claude-sonnet-4",
}


@cl.set_chat_profiles
async def set_chat_profiles(current_user: cl.User | None) -> list[cl.ChatProfile]:
    """Define available team profiles for session selection."""
    return [
        cl.ChatProfile(
            name="Omnia Data",
            markdown_description="Default team for Audit Cortex 2 project",
            default=True,
        ),
        cl.ChatProfile(
            name="Omnia",
            markdown_description="Omnia team",
        ),
        cl.ChatProfile(
            name="Levvia",
            markdown_description="Levvia team",
        ),
    ]


def _get_display_label(value: str, mapping: dict[str, str]) -> str:
    """Get display label from value by reversing the mapping."""
    for label, val in mapping.items():
        if val == value:
            return label
    return list(mapping.keys())[0]  # Return first key as default


async def show_configuration_modal(
    initial_team: str = "omnia-data",
    initial_persona: str = "developer",
) -> dict[str, str] | None:
    """Show configuration dialog with blocking wait for user input.

    Uses AskActionMessage which properly blocks until user responds,
    unlike ChatSettings which returns immediately.

    Note: Model selection is controlled via TRIAGENT_MODEL environment variable.

    Args:
        initial_team: Pre-fill team value (internal format like "omnia-data")
        initial_persona: Pre-fill persona value (internal format like "developer")

    Returns:
        Dict with team, persona, model keys if user confirms, None if cancelled.
    """
    # Step 1: Select Team
    team_response = await cl.AskActionMessage(
        content=(
            "**Select Your Team**\n\n"
            "Choose the team profile for this session:"
        ),
        actions=[
            cl.Action(
                name="omnia-data",
                label="Omnia Data (Default)",
                payload={"team": "omnia-data"},
            ),
            cl.Action(
                name="omnia",
                label="Omnia",
                payload={"team": "omnia"},
            ),
            cl.Action(
                name="levvia",
                label="Levvia",
                payload={"team": "levvia"},
            ),
        ],
        timeout=300,  # 5 minutes
    ).send()

    if not team_response:
        return None

    team = team_response.get("payload", {}).get("team", initial_team)

    # Step 2: Select Persona
    persona_response = await cl.AskActionMessage(
        content=(
            "**Select Your Persona**\n\n"
            "Choose your work persona:"
        ),
        actions=[
            cl.Action(
                name="developer",
                label="Developer (Default)",
                payload={"persona": "developer"},
            ),
            cl.Action(
                name="support",
                label="Support",
                payload={"persona": "support"},
            ),
            cl.Action(
                name="product_owner",
                label="Product Owner",
                payload={"persona": "product_owner"},
            ),
            cl.Action(
                name="business_analyst",
                label="Business Analyst",
                payload={"persona": "business_analyst"},
            ),
        ],
        timeout=300,
    ).send()

    if not persona_response:
        return None

    persona = persona_response.get("payload", {}).get("persona", initial_persona)

    # Model is controlled via TRIAGENT_MODEL environment variable
    # No UI selection - use environment variable directly
    model = os.environ.get("TRIAGENT_MODEL", "claude-opus-4-5")

    return {"team": team, "persona": persona, "model": model}


@cl.on_settings_update
async def on_settings_update(settings: dict) -> None:
    """Handle settings updates during session.

    Note: Settings cannot be changed after SDK initialization.
    This handler is mainly for initial configuration.
    """
    logger.info(f"Settings updated: {settings}")


@cl.on_chat_start
async def on_chat_start() -> None:
    """Initialize Dynamic Session for user with health check for session persistence.

    Flow:
    1. Generate deterministic session_id from username
    2. Run health check to detect if session can be resumed
    3. If healthy → skip config modal, use stored preferences
    4. If unhealthy → show config modal (pre-filled if preferences exist)
    5. Check auth status (non-blocking)
    6. Initialize SDK (after user confirms auth complete)
    """
    # Get user info (for local mode, use default)
    user = cl.user_session.get("user")
    if not user:
        # Local mode - create anonymous user
        user = cl.User(identifier="local-user", metadata={})
        cl.user_session.set("user", user)

    # Generate session ID from username
    session_id = ChainlitSessionManager.generate_session_id(user.identifier)
    cl.user_session.set("session_id", session_id)
    logger.info(f"Generated session ID: {session_id} for user: {user.identifier}")

    # Initialize session manager
    manager = ChainlitSessionManager()
    cl.user_session.set("session_manager", manager)

    # =========================================================================
    # Health Check: Determine if session can be resumed
    # =========================================================================
    checking_msg = await cl.Message(content="*Checking session...*").send()

    health_status = {
        "healthy": False,
        "azure_auth": False,
        "session_initialized": False,
        "conversation_turns": 0,
        "team": None,
        "persona": None,
        "model": None,
        "azure_user": None,
    }

    try:
        async for event in manager.health_check(session_id):
            event_type = event.get("type", "")

            if event_type == "done":
                # Extract health status from done event
                health_status["healthy"] = event.get("healthy", False)
                health_status["azure_auth"] = event.get("azure_auth", False)
                health_status["azure_user"] = event.get("azure_user")
                health_status["session_initialized"] = event.get("session_initialized", False)
                health_status["conversation_turns"] = event.get("conversation_turns", 0)
                health_status["team"] = event.get("team")
                health_status["persona"] = event.get("persona")
                health_status["model"] = event.get("model")

            elif event_type == "error":
                logger.warning(f"Health check error: {event.get('error')}")
                # Continue with full flow on error

    except Exception as e:
        logger.warning(f"Health check failed: {e}")
        # Continue with full flow on exception

    # =========================================================================
    # Session Resumption: Skip config modal if healthy
    # =========================================================================
    if health_status["healthy"]:
        # Session is healthy - restore preferences and skip modal
        team = health_status["team"] or "omnia-data"
        persona = health_status["persona"] or "developer"
        model = health_status["model"] or "claude-opus-4-5"
        turns = health_status["conversation_turns"]
        azure_user = health_status["azure_user"] or "user"

        # Store configuration in session
        cl.user_session.set("team", team)
        cl.user_session.set("persona", persona)
        cl.user_session.set("model", model)

        checking_msg.content = (
            f"**Session Resumed**\n\n"
            f"Logged in as: *{azure_user}*\n"
            f"Previous turns: {turns}\n\n"
            f"How can I help you with Azure DevOps?"
        )
        await checking_msg.update()
        logger.info(
            f"Session resumed for {azure_user} with {turns} turns "
            f"(team={team}, persona={persona}, model={model})"
        )
        return

    # =========================================================================
    # Show Configuration Modal (with pre-filled preferences if available)
    # =========================================================================
    # Get team from chat profile as initial value
    chat_profile = cl.user_session.get("chat_profile")

    # Use stored preferences if available, otherwise use defaults
    initial_team = health_status["team"] or TEAMS.get(chat_profile, "omnia-data") or "omnia-data"
    initial_persona = health_status["persona"] or "developer"

    # Update message based on health status
    if health_status["session_initialized"] and not health_status["azure_auth"]:
        checking_msg.content = "*Session expired, reconnecting...*"
    else:
        checking_msg.content = "*Creating new session...*"
    await checking_msg.update()

    # Show configuration modal with pre-filled values
    # Note: Model is controlled via TRIAGENT_MODEL environment variable
    config = await show_configuration_modal(
        initial_team=initial_team,
        initial_persona=initial_persona,
    )

    if config:
        team = config["team"]
        persona = config["persona"]
        model = config["model"]
    else:
        # Use initial values if modal cancelled
        team = initial_team
        persona = initial_persona
        # Model from environment variable (fallback to default)
        model = os.environ.get("TRIAGENT_MODEL", "claude-opus-4-5")

    # Store configuration in session
    cl.user_session.set("team", team)
    cl.user_session.set("persona", persona)
    cl.user_session.set("model", model)

    # =========================================================================
    # Stage 1: Check Authentication Status (Non-Blocking)
    # =========================================================================
    await cl.Message(content="**Checking authentication...**").send()

    progress_msg = await cl.Message(content="").send()
    auth_complete = False
    device_code = None
    device_url = None

    try:
        async for event in manager.check_auth_status(session_id, team):
            event_type = event.get("type", "")
            step = event.get("step", "")
            message = event.get("message", "")

            if event_type == "error":
                error_msg = event.get("error", "Unknown error")
                progress_msg.content = f"**Error**: {error_msg}"
                await progress_msg.update()
                return

            # Device code - need user authentication
            if event_type == "device_code":
                device_code = event.get("code", "")
                device_url = event.get("url", "https://microsoft.com/devicelogin")

            # Done event - check if authenticated
            if event_type == "done":
                auth_complete = event.get("authenticated", False)
                if auth_complete:
                    auth_user = event.get("user", "")
                    progress_msg.content = f"*Authenticated as: {auth_user}*"
                    await progress_msg.update()

            if message:
                progress_msg.content = f"*{message}*"
                await progress_msg.update()

    except Exception as e:
        logger.exception(f"Failed to check auth: {e}")
        await cl.Message(content=f"**Auth check failed**: {e}").send()
        return

    # =========================================================================
    # Handle Device Code Authentication
    # =========================================================================
    if device_code and not auth_complete:
        # Show device code with confirmation button
        response = await cl.AskActionMessage(
            content=(
                f"**Azure Authentication Required**\n\n"
                f"1. Open: [{device_url}]({device_url})\n"
                f"2. Enter code: **`{device_code}`**\n\n"
                f"After completing authentication in your browser, click **Done**."
            ),
            actions=[
                cl.Action(
                    name="auth_done",
                    label="Done",
                    payload={"completed": True},
                ),
                cl.Action(
                    name="auth_cancel",
                    label="Cancel",
                    payload={"completed": False},
                ),
            ],
            timeout=900,  # 15 minutes
        ).send()

        if not response or response.get("name") != "auth_done":
            await cl.Message(content="Authentication cancelled.").send()
            return

        progress_msg.content = "*Verifying authentication...*"
        await progress_msg.update()

    # =========================================================================
    # Stage 2: Initialize SDK with configuration options
    # =========================================================================
    progress_msg.content = "*Initializing Claude SDK...*"
    await progress_msg.update()

    try:
        async for event in manager.init_sdk_session(
            session_id, team, persona, model
        ):
            event_type = event.get("type", "")
            step = event.get("step", "")
            message = event.get("message", "")

            if event_type == "error":
                error_msg = event.get("error", "Unknown error")
                progress_msg.content = f"**Error**: {error_msg}"
                await progress_msg.update()
                return

            # Update progress
            if step == "ready":
                model_name = event.get("model", "Claude")
                progress_msg.content = f"**Connected to {model_name}!**"
                await progress_msg.update()
                await cl.Message(
                    content="How can I help you with Azure DevOps today?"
                ).send()
                return

            if message:
                progress_msg.content = f"*{message}*"
                await progress_msg.update()

        # If we get here without a "ready" event
        if event_type == "done":
            await cl.Message(
                content="How can I help you with Azure DevOps today?"
            ).send()

    except Exception as e:
        logger.exception(f"Failed to initialize session: {e}")
        await cl.Message(content=f"**Failed to connect**: {e}").send()


@cl.on_chat_end
async def on_chat_end() -> None:
    """Cleanup session manager on session end."""
    manager = cl.user_session.get("session_manager")
    if manager:
        await manager.close()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    """Handle user message and stream response from Dynamic Session."""
    start_time = time.time()

    # Extract context for logging
    user = cl.user_session.get("user")
    user_id = user.identifier if user else "anonymous"
    session_id: str | None = cl.user_session.get("session_id")
    team: str = cl.user_session.get("team", "omnia-data")
    correlation_id = str(uuid.uuid4())[:8]

    manager: ChainlitSessionManager | None = cl.user_session.get("session_manager")

    if not manager or not session_id:
        await cl.Message(
            content="Session not ready. Please refresh and try again."
        ).send()
        return

    # Log incoming user message
    question_preview = message.content[:100].replace("\n", " ")
    _log_user_request(
        "user_message",
        user_id,
        session_id,
        correlation_id,
        question=question_preview,
    )

    # Status message that updates in place
    status_msg = cl.Message(content="*Thinking...*")
    await status_msg.send()

    # Accumulate text for final response
    text_buffer: list[str] = []

    try:
        async for event in manager.send_sdk_message(
            session_id, message.content, team,
            user_id=user_id, correlation_id=correlation_id
        ):
            event_type = event.get("type", "")

            if event_type == "text":
                content = event.get("content", "")
                text_buffer.append(content)

            elif event_type == "tool_start":
                tool_name = event.get("name", "tool")
                display_name = _format_tool_name(tool_name)
                status_msg.content = f"*{display_name}...*"
                await status_msg.update()

            elif event_type == "tool_end":
                status_msg.content = "*Thinking...*"
                await status_msg.update()

            elif event_type == "confirm_request":
                # Handle write confirmation
                _request_id = event.get("request_id", "")  # noqa: F841 (for future use)
                tool_name = event.get("tool_name", "")
                description = event.get("description", "Operation")

                status_msg.content = "*Waiting for confirmation...*"
                await status_msg.update()

                approved = await _show_confirmation(tool_name, description)

                await cl.Message(
                    content="Approved" if approved else "Denied"
                ).send()

                # TODO: Submit confirmation back to session
                status_msg.content = "*Continuing...*"
                await status_msg.update()

            elif event_type == "done":
                usage = event.get("usage", {})
                if usage:
                    logger.info(
                        f"Done. Tokens: in={usage.get('input_tokens', 0)}, "
                        f"out={usage.get('output_tokens', 0)}"
                    )

            elif event_type == "error":
                error_msg = event.get("error", "Unknown error")
                text_buffer.append(f"\n\n**Error**: {error_msg}")

            elif event_type == "progress":
                # Show progress message during auto-retry on 504 timeout
                progress_message = event.get("message", "Processing...")
                status_msg.content = f"*⏳ {progress_message}*"
                await status_msg.update()

        # Final response
        status_msg.content = "*Complete*"
        await status_msg.update()

        final_text = "".join(text_buffer)
        if final_text.strip():
            await cl.Message(content=final_text).send()

        # Log request completion
        duration_ms = int((time.time() - start_time) * 1000)
        _log_user_request(
            "request_complete",
            user_id,
            session_id,
            correlation_id,
            duration_ms=duration_ms,
        )

    except Exception as e:
        logger.exception(f"Error streaming response: {e}")
        status_msg.content = "*Error*"
        await status_msg.update()
        await cl.Message(content=f"**Error**: {e}").send()

        # Log request error
        duration_ms = int((time.time() - start_time) * 1000)
        _log_user_request(
            "request_error",
            user_id,
            session_id,
            correlation_id,
            duration_ms=duration_ms,
            error=str(e)[:100],
        )


async def _show_confirmation(tool_name: str, description: str) -> bool:
    """Show confirmation dialog for write operations."""
    response = await cl.AskActionMessage(
        content=f"**{description}**\n\nTool: {tool_name}",
        actions=[
            cl.Action(name="approve", label="Yes", payload={"approved": True}),
            cl.Action(name="deny", label="No", payload={"approved": False}),
        ],
        timeout=120,
    ).send()

    return response is not None and response.get("name") == "approve"


# Tool name formatting
TOOL_NAMES = {
    "Bash": "Running command",
    "Read": "Reading file",
    "Write": "Writing file",
    "Edit": "Editing file",
    "Grep": "Searching code",
    "Glob": "Finding files",
    "WebSearch": "Searching web",
    "WebFetch": "Fetching URL",
    "Task": "Running agent",
}

ADO_TOOL_NAMES = {
    "get_me": "Getting user info",
    "list_projects": "Listing projects",
    "get_work_item": "Getting work item",
    "search_work_items": "Searching work items",
    "create_work_item": "Creating work item",
    "list_pull_requests": "Listing PRs",
    "get_pipeline": "Getting pipeline",
}


def _format_tool_name(name: str) -> str:
    """Format tool name for display."""
    if name in TOOL_NAMES:
        return TOOL_NAMES[name]

    if name.startswith("mcp__azure-devops__"):
        op = name.replace("mcp__azure-devops__", "")
        return ADO_TOOL_NAMES.get(op, f"Azure DevOps: {op}")

    if name.startswith("mcp__triagent__"):
        op = name.replace("mcp__triagent__", "")
        return f"Triagent: {op}"

    return name
