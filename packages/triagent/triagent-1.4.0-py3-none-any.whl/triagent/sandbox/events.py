"""Event types and emitters for sandbox execution.

This module provides JSON event emission to stdout for communication
between the sandbox runner (inside Azure Dynamic Sessions container)
and the parent process (SessionProxy in Chainlit).

Events are emitted as JSON lines, one per line:
    {"type": "progress", "step": "validating", "message": "..."}
    {"type": "device_code", "code": "ABC123", "url": "https://..."}
    {"type": "text", "content": "I'll help you with that."}
    {"type": "done", "session_id": "abc123", "turns": 5}

The parent process parses stdout to extract these events.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """Event types emitted by sandbox runner.

    These map to the events expected by SessionProxy and Chainlit UI.
    """

    # Progress events (during initialization)
    PROGRESS = "progress"

    # Device code event (Azure CLI authentication required)
    DEVICE_CODE = "device_code"

    # Text content from Claude response
    TEXT = "text"

    # Tool execution events
    TOOL_START = "tool_start"
    TOOL_END = "tool_end"

    # Confirmation request for write operations
    CONFIRM_REQUEST = "confirm_request"

    # Configuration validation events
    CONFIG_VALID = "config_valid"
    CONFIG_OPTIONS = "config_options"

    # Completion event (includes session_id for resumption)
    DONE = "done"

    # Error event
    ERROR = "error"


@dataclass
class Event:
    """Base event structure for type safety."""

    type: EventType
    data: dict[str, Any]

    def to_json(self) -> str:
        """Serialize event to JSON string."""
        return json.dumps({"type": self.type.value, **self.data})


def emit_event(event_type: EventType | str, **kwargs: Any) -> None:
    """Emit JSON event to stdout for parent process.

    Args:
        event_type: The event type (EventType enum or string)
        **kwargs: Additional event data fields

    Example:
        emit_event(EventType.PROGRESS, step="validating", message="Checking...")
        # Output: {"type": "progress", "step": "validating", "message": "Checking..."}
    """
    type_value = event_type.value if isinstance(event_type, EventType) else event_type
    event = {"type": type_value, **kwargs}
    print(json.dumps(event))
    sys.stdout.flush()


# Convenience functions for common event types


def emit_progress(step: str, message: str = "", **kwargs: Any) -> None:
    """Emit progress event.

    Args:
        step: Progress step identifier (e.g., "validating", "auth_ok", "ready")
        message: Human-readable progress message
        **kwargs: Additional data (e.g., model="claude-opus-4-5")

    Common steps:
        - "validating": Start of initialization
        - "checking_auth": Checking Azure CLI authentication
        - "auth_required": Device flow needed
        - "auth_waiting": Waiting for user to complete device flow
        - "auth_ok": Azure CLI authenticated
        - "auth_timeout": Device flow timed out
        - "creating_sdk": Initializing Claude SDK
        - "ready": Session ready for chat
        - "resuming": Resuming existing session
    """
    emit_event(EventType.PROGRESS, step=step, message=message, **kwargs)


def emit_device_code(code: str, url: str, message: str = "") -> None:
    """Emit device code event for Azure CLI authentication.

    This event triggers the device code modal in the Chainlit UI.

    Args:
        code: The device code (e.g., "ABCD1234")
        url: The verification URL (e.g., "https://microsoft.com/devicelogin")
        message: Optional message to display

    Example:
        emit_device_code("ABCD1234", "https://microsoft.com/devicelogin")
        # UI shows: "Enter code ABCD1234 at https://microsoft.com/devicelogin"
    """
    emit_event(EventType.DEVICE_CODE, code=code, url=url, message=message)


def emit_text(content: str) -> None:
    """Emit text content from Claude response.

    Args:
        content: The text content to display

    Example:
        emit_text("I'll help you with that Azure DevOps query.")
    """
    emit_event(EventType.TEXT, content=content)


def emit_tool_start(name: str, input_preview: str = "") -> None:
    """Emit tool execution start event.

    Args:
        name: Tool name (e.g., "Bash", "Read", "mcp__azure-devops__get_me")
        input_preview: Preview of tool input (truncated for display)

    Example:
        emit_tool_start("Bash", "az account list")
    """
    emit_event(EventType.TOOL_START, name=name, input=input_preview)


def emit_tool_end(name: str, success: bool = True) -> None:
    """Emit tool execution end event.

    Args:
        name: Tool name
        success: Whether tool execution succeeded

    Example:
        emit_tool_end("Bash", success=True)
    """
    emit_event(EventType.TOOL_END, name=name, success=success)


def emit_confirm_request(
    request_id: str,
    tool_name: str,
    description: str,
    details: dict[str, Any] | None = None,
) -> None:
    """Emit confirmation request for write operations.

    This event triggers a confirmation dialog in the Chainlit UI.

    Args:
        request_id: Unique ID for this request (for response correlation)
        tool_name: Name of the tool requesting confirmation
        description: Human-readable description of the operation
        details: Additional details about the operation

    Example:
        emit_confirm_request(
            request_id="abc123",
            tool_name="Bash",
            description="Create work item in Azure DevOps",
            details={"command": "az boards work-item create ..."}
        )
    """
    emit_event(
        EventType.CONFIRM_REQUEST,
        request_id=request_id,
        tool_name=tool_name,
        description=description,
        details=details or {},
    )


def emit_done(
    session_id: str | None = None, turns: int = 0, **kwargs: Any
) -> None:
    """Emit completion event.

    This event signals that the operation is complete and optionally includes
    the session_id for future resumption.

    Args:
        session_id: Claude session ID for resumption (optional for auth-only flows)
        turns: Number of conversation turns
        **kwargs: Additional completion data (e.g., authenticated=True)

    Example:
        emit_done(session_id="abc123def456", turns=5)
        emit_done(authenticated=True)  # For auth check flow
    """
    data: dict[str, Any] = {"turns": turns, **kwargs}
    if session_id:
        data["session_id"] = session_id
    emit_event(EventType.DONE, **data)


def emit_error(error: str, **kwargs: Any) -> None:
    """Emit error event.

    Args:
        error: Error message
        **kwargs: Additional error context

    Example:
        emit_error("Azure authentication timed out after 15 minutes")
    """
    emit_event(EventType.ERROR, error=error, **kwargs)


def emit_config_valid(valid: bool, errors: list[str] | None = None) -> None:
    """Emit configuration validation result.

    This event reports whether the provided configuration options are valid.

    Args:
        valid: True if all configuration options are valid
        errors: List of validation error messages (if not valid)

    Example:
        emit_config_valid(valid=True)
        emit_config_valid(valid=False, errors=["Invalid team 'foo'"])
    """
    emit_event(EventType.CONFIG_VALID, valid=valid, errors=errors or [])


def emit_config_options(
    teams: list[str],
    personas: list[str],
    models: list[str],
) -> None:
    """Emit available configuration options.

    This event provides the available options for team, persona, and model
    selection in the configuration modal.

    Args:
        teams: List of available team identifiers
        personas: List of available persona identifiers
        models: List of available model identifiers

    Example:
        emit_config_options(
            teams=["omnia-data", "omnia", "levvia"],
            personas=["developer", "support"],
            models=["claude-opus-4-5", "claude-sonnet-4"]
        )
    """
    emit_event(
        EventType.CONFIG_OPTIONS,
        teams=teams,
        personas=personas,
        models=models,
    )
