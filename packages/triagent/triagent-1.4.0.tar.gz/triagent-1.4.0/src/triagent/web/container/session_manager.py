"""Session manager for Chainlit with Dynamic Sessions sandbox pattern.

This module bridges Chainlit's session management with Azure Dynamic Sessions
using the /code/execute pattern with triagent.sandbox.runner.
"""

import hashlib
import logging
from collections.abc import AsyncGenerator
from typing import Any

from triagent.web.services.session_proxy import SessionProxy

logger = logging.getLogger(__name__)


class ChainlitSessionManager:
    """Manages Dynamic Sessions for Chainlit users.

    This class bridges Chainlit's session management with Azure Container Apps
    Dynamic Sessions using the /code/execute pattern.

    The sandbox module (triagent.sandbox.runner) handles:
    - Device flow authentication
    - Claude SDK initialization and resumption
    - Event emission via JSON stdout
    """

    def __init__(self) -> None:
        """Initialize session manager with SessionProxy."""
        self._proxy = SessionProxy()

    @staticmethod
    def generate_session_id(username: str) -> str:
        """Generate deterministic session ID from username.

        Args:
            username: The Chainlit user's identifier.

        Returns:
            16-character hex session ID.
        """
        return hashlib.sha256(username.encode()).hexdigest()[:16]

    # =========================================================================
    # Two-Stage Authentication Flow
    # =========================================================================

    async def check_auth_status(
        self,
        session_id: str,
        team: str = "omnia-data",
        user_id: str | None = None,
        correlation_id: str | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stage 1: Check auth status, return device code if needed.

        This is NON-BLOCKING - returns immediately with auth status.
        If not authenticated, returns device code for user to complete
        authentication externally.

        Executes triagent.sandbox.runner.run_check_auth() via /code/execute.

        Args:
            session_id: The Dynamic Session identifier.
            team: Team profile to use.
            user_id: Optional user identifier for logging.
            correlation_id: Optional correlation ID for request tracing.

        Yields:
            Progress events as dicts.
            Event types: progress, device_code, done, error
            Check done.authenticated to see if auth is complete.
        """
        logger.info(f"Checking auth status for session {session_id}")

        async for event in self._proxy.check_auth_status(
            session_id, team, user_id, correlation_id
        ):
            yield event

    async def init_sdk_session(
        self,
        session_id: str,
        team: str = "omnia-data",
        persona: str = "developer",
        model: str = "claude-opus-4-5",
        user_id: str | None = None,
        correlation_id: str | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stage 2: Initialize SDK after authentication confirmed.

        Executes triagent.sandbox.runner.run_init_sdk() via /code/execute.
        Events are emitted to stdout and streamed back.

        All configuration options (team, persona, model) are passed upfront
        from the frontend configuration modal.

        Args:
            session_id: The Dynamic Session identifier.
            team: Team profile to use (omnia-data, levvia, etc.).
            persona: Persona profile (developer, support).
            model: Claude model to use (claude-opus-4-5, claude-sonnet-4).
            user_id: Optional user identifier for logging.
            correlation_id: Optional correlation ID for request tracing.

        Yields:
            Progress events as dicts during initialization.
            Event types: progress, text, done, error
        """
        logger.info(
            f"Initializing SDK session {session_id} with "
            f"team={team}, persona={persona}, model={model}"
        )

        async for event in self._proxy.init_sdk_session(
            session_id, team, persona, model, user_id, correlation_id
        ):
            yield event

    async def validate_config(
        self,
        session_id: str,
        team: str,
        persona: str,
        model: str,
        user_id: str | None = None,
        correlation_id: str | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Validate configuration options without initializing SDK.

        Executes triagent.sandbox.runner.run_validate_config() via /code/execute.

        Args:
            session_id: The Dynamic Session identifier.
            team: Team profile to validate.
            persona: Persona profile to validate.
            model: Model to validate.
            user_id: Optional user identifier for logging.
            correlation_id: Optional correlation ID for request tracing.

        Yields:
            Validation events as dicts.
            Event types: config_options, config_valid, done, error
        """
        logger.info(
            f"Validating config for session {session_id}: "
            f"team={team}, persona={persona}, model={model}"
        )

        async for event in self._proxy.validate_config(
            session_id, team, persona, model, user_id, correlation_id
        ):
            yield event

    async def health_check(
        self,
        session_id: str,
        user_id: str | None = None,
        correlation_id: str | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Check session health for session resumption.

        Executes triagent.sandbox.runner.run_health_check() via /code/execute.
        Used to determine if session can be resumed without showing config modal.

        Returns health status with:
        - healthy: True if session can be resumed
        - azure_auth: Azure CLI authentication status
        - azure_user: Authenticated user email
        - session_initialized: Whether SDK was initialized
        - conversation_turns: Number of previous turns
        - team, persona, model: Stored preferences

        Args:
            session_id: The Dynamic Session identifier.
            user_id: Optional user identifier for logging.
            correlation_id: Optional correlation ID for request tracing.

        Yields:
            Health check events as dicts.
            Event types: progress, done (with health status), error
        """
        logger.info(f"Health check for session {session_id}")

        async for event in self._proxy.health_check(
            session_id, user_id, correlation_id
        ):
            yield event

    async def send_sdk_message(
        self,
        session_id: str,
        message: str,
        team: str = "omnia-data",
        user_id: str | None = None,
        correlation_id: str | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Send message and stream response.

        Executes triagent.sandbox.runner.run_chat() via /code/execute.
        The runner resumes the existing SDK session from file-based storage.

        Args:
            session_id: The Dynamic Session identifier.
            message: User message to send to Claude.
            team: Team profile (used if no existing session).
            user_id: Optional user identifier for logging.
            correlation_id: Optional correlation ID for request tracing.

        Yields:
            Response events as dicts (text, tool_start, tool_end, done, error).
        """
        logger.info(f"Sending message to session {session_id}")

        async for event in self._proxy.stream_sdk_session_chat(
            session_id, message, team,
            user_id=user_id, correlation_id=correlation_id
        ):
            yield event

    async def get_session_status(self, session_id: str) -> dict[str, Any]:
        """Get status of an SDK session.

        Args:
            session_id: The Dynamic Session identifier.

        Returns:
            Status dict with exists, initialized, conversation_turns, etc.
        """
        return await self._proxy.get_session_status(session_id)

    async def clear_session(self, session_id: str) -> dict[str, str]:
        """Clear session state to start fresh.

        Args:
            session_id: The Dynamic Session identifier.

        Returns:
            Response dict with status.
        """
        return await self._proxy.clear_session(session_id)

    async def close(self) -> None:
        """Close resources."""
        await self._proxy.close()
