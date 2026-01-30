"""Azure Container Apps Session Pool proxy for Triagent Web API.

Uses /code/execute pattern for Azure Dynamic Sessions.
Custom HTTP endpoints are NOT accessible in Azure Dynamic Sessions -
only /code/execute works. This proxy executes Python code from
triagent.sandbox.runner to initialize and chat with Claude SDK.

Session state is persisted via file (/root/.triagent/session.json) inside
the container, enabling conversation resumption across /code/execute calls.

Supports both Azure Dynamic Sessions (production) and local Docker testing.
Local mode is enabled via TRIAGENT_LOCAL_MODE=true environment variable.

Authentication:
    Uses MSAL (Microsoft Authentication Library) Client Credentials flow
    to acquire tokens for Azure Dynamic Sessions (https://dynamicsessions.io).
    This replaces DefaultAzureCredential to avoid Azure CLI dependency on host.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import AsyncGenerator
from typing import Any

import httpx
from msal import ConfidentialClientApplication

from triagent.web.config import WebConfig

logger = logging.getLogger(__name__)


def _log_operation(
    action: str,
    session_id: str,
    duration_ms: int,
    user_id: str | None = None,
    correlation_id: str | None = None,
    **extra: Any,
) -> None:
    """Log operation with consistent key=value format for grep-friendly filtering.

    Format: user={user_id} session={session_id} correlation_id={id} action={action} duration={ms}ms [extra]

    Args:
        action: The operation name (e.g., "health_check", "execute_code").
        session_id: Session identifier.
        duration_ms: Operation duration in milliseconds.
        user_id: Optional user identifier.
        correlation_id: Optional correlation ID for request tracing.
        **extra: Additional key-value pairs to log.
    """
    parts = []
    if user_id:
        parts.append(f"user={user_id}")
    parts.append(f"session={session_id}")
    if correlation_id:
        parts.append(f"correlation_id={correlation_id}")
    parts.append(f"action={action}")
    parts.append(f"duration={duration_ms}ms")
    for k, v in extra.items():
        parts.append(f"{k}={v}")
    logger.info(" ".join(parts))


class SessionProxy:
    """Proxy requests to Azure Container Apps Session Pool.

    Uses /code/execute to run triagent.sandbox.runner functions inside
    the Dynamic Session container. Events are emitted as JSON to stdout
    and parsed by this proxy to stream back to Chainlit.

    Pattern:
        1. execute_code() → POST /code/execute with Python code
        2. Code runs triagent.sandbox.runner.run_init() or run_chat()
        3. Runner emits JSON events to stdout
        4. This proxy parses stdout and yields events to Chainlit
    """

    def __init__(self) -> None:
        """Initialize session proxy."""
        self.config = WebConfig()
        self._use_azure_auth = not self.config.local_mode
        self._msal_app: ConfidentialClientApplication | None = None
        self._token_cache: dict[str, Any] | None = None
        self._token_expiry: float = 0

        if self.config.local_mode:
            self._endpoint = self.config.local_sessions_url
            logger.info(f"SessionProxy initialized in LOCAL mode: {self._endpoint}")
        else:
            self._endpoint = self.config.session_pool_endpoint
            logger.info(f"SessionProxy initialized in AZURE mode: {self._endpoint}")

    def _get_msal_app(self) -> ConfidentialClientApplication:
        """Get or create MSAL app for client credentials flow.

        Returns:
            ConfidentialClientApplication instance.
        """
        if self._msal_app is None:
            self._msal_app = ConfidentialClientApplication(
                client_id=self.config.azure_client_id,
                client_credential=self.config.azure_client_secret,
                authority=f"https://login.microsoftonline.com/{self.config.azure_tenant_id}",
            )
            logger.debug("MSAL ConfidentialClientApplication created")
        return self._msal_app

    async def get_access_token(self) -> str | None:
        """Get token for dynamicsessions.io scope using MSAL client credentials.

        Uses MSAL ConfidentialClientApplication to acquire tokens via
        client credentials flow. Tokens are cached and reused until expiry.

        Returns:
            Access token string, or None if in local mode.

        Raises:
            RuntimeError: If token acquisition fails.
        """
        if not self._use_azure_auth:
            return None

        # Check if we have a valid cached token (with 5 min buffer)
        current_time = time.time()
        if self._token_cache and current_time < (self._token_expiry - 300):
            return self._token_cache.get("access_token")

        # Acquire new token using client credentials
        app = self._get_msal_app()
        result = app.acquire_token_for_client(
            scopes=["https://dynamicsessions.io/.default"]
        )

        if "access_token" in result:
            self._token_cache = result
            # Calculate expiry time (expires_in is in seconds)
            expires_in = result.get("expires_in", 3600)
            self._token_expiry = current_time + expires_in
            logger.info("Token acquired via MSAL client credentials")
            return result["access_token"]
        else:
            error = result.get("error_description", result.get("error", "Unknown error"))
            logger.error(f"Failed to acquire token: {error}")
            raise RuntimeError(f"MSAL token acquisition failed: {error}")

    def _get_headers(self, token: str | None) -> dict[str, str]:
        """Build request headers.

        Args:
            token: Optional auth token (None for local mode).

        Returns:
            Headers dict.
        """
        headers = {
            "Content-Type": "application/json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def execute_code(
        self,
        session_id: str,
        code: str,
        user_id: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Execute code in session container.

        Args:
            session_id: Session identifier.
            code: Python code to execute.
            user_id: Optional user identifier for logging.
            correlation_id: Optional correlation ID for request tracing.

        Returns:
            Execution result from session pool containing stdout/stderr.
        """
        start_time = time.time()
        token = await self.get_access_token()
        headers = self._get_headers(token)

        logger.debug(f"Executing code in session {session_id} via {self._endpoint}")

        # Azure Dynamic Sessions requires identifier as query parameter
        url = f"{self._endpoint}/code/execute"
        params = {"identifier": session_id}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                params=params,
                headers=headers,
                json={
                    "properties": {
                        "codeInputType": "inline",
                        "executionType": "synchronous",
                        "code": code,
                    }
                },
                timeout=300.0,  # 5 min timeout for SDK operations
            )
            duration_ms = int((time.time() - start_time) * 1000)
            _log_operation(
                "execute_code",
                session_id,
                duration_ms,
                user_id,
                correlation_id,
                status_code=response.status_code,
            )
            if response.status_code >= 400:
                logger.error(
                    f"API error {response.status_code}: {response.text[:500]}"
                )
            response.raise_for_status()
            return response.json()

    def _parse_json_events(self, stdout: str) -> list[dict[str, Any]]:
        """Parse JSON events from stdout.

        The sandbox runner emits JSON objects one per line.

        Args:
            stdout: Raw stdout string from code execution.

        Returns:
            List of parsed event dicts.
        """
        events = []
        for line in stdout.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                events.append(event)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse event line: {line[:100]}")
        return events

    # =========================================================================
    # Two-Stage SDK Session Management via /code/execute
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
        auth externally.

        Executes triagent.sandbox.runner.run_check_auth() inside the container.

        Args:
            session_id: Session identifier for the Dynamic Session.
            team: Team profile to use (omnia-data, levvia, etc.).
            user_id: Optional user identifier for logging.
            correlation_id: Optional correlation ID for request tracing.

        Yields:
            Progress events as dicts.
            Event types: progress, device_code, done, error
            Check done.authenticated to see if auth is complete.
        """
        start_time = time.time()
        logger.info(f"Checking auth status for session {session_id}")

        escaped_team = team.replace("\\", "\\\\").replace('"', '\\"')

        check_auth_code = f'''
from triagent.sandbox.runner import run_check_auth
import asyncio
asyncio.run(run_check_auth("{escaped_team}"))
'''
        authenticated = False
        try:
            result = await self.execute_code(
                session_id, check_auth_code, user_id, correlation_id
            )

            properties = result.get("properties", {})
            stdout = properties.get("stdout", "")
            stderr = properties.get("stderr", "")

            if stderr:
                logger.warning(f"Stderr from check_auth: {stderr[:500]}")

            events = self._parse_json_events(stdout)

            for event in events:
                if event.get("type") == "done":
                    authenticated = event.get("authenticated", False)
                yield event

            if not events:
                if stderr:
                    yield {"type": "error", "error": f"Auth check failed: {stderr[:200]}"}
                else:
                    yield {"type": "error", "error": "No events from auth check"}

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during auth check: {e.response.status_code}")
            yield {"type": "error", "error": f"HTTP error: {e.response.status_code}"}
        except httpx.RequestError as e:
            logger.error(f"Request error during auth check: {e}")
            yield {"type": "error", "error": f"Connection error: {e}"}
        except Exception as e:
            logger.exception("Unexpected error during auth check")
            yield {"type": "error", "error": str(e)}
        finally:
            duration_ms = int((time.time() - start_time) * 1000)
            _log_operation(
                "check_auth_status",
                session_id,
                duration_ms,
                user_id,
                correlation_id,
                authenticated=authenticated,
            )

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

        This assumes user has completed device flow authentication.
        Executes triagent.sandbox.runner.run_init_sdk() inside the container.

        All configuration options (team, persona, model) are passed upfront
        from the frontend configuration modal.

        Args:
            session_id: Session identifier for the Dynamic Session.
            team: Team profile to use (omnia-data, levvia, etc.).
            persona: Persona profile (developer, support).
            model: Claude model to use (claude-opus-4-5, claude-sonnet-4).
            user_id: Optional user identifier for logging.
            correlation_id: Optional correlation ID for request tracing.

        Yields:
            Progress events as dicts during initialization.
            Event types: progress, text, done, error
        """
        start_time = time.time()
        logger.info(
            f"Initializing SDK session {session_id} with "
            f"team={team}, persona={persona}, model={model}"
        )

        escaped_team = team.replace("\\", "\\\\").replace('"', '\\"')
        escaped_persona = persona.replace("\\", "\\\\").replace('"', '\\"')
        escaped_model = model.replace("\\", "\\\\").replace('"', '\\"')

        # Use the new run_init_sdk (stage 2) function with all options
        init_code = f'''
from triagent.sandbox.runner import run_init_sdk
import asyncio
asyncio.run(run_init_sdk("{escaped_team}", "{escaped_persona}", "{escaped_model}"))
'''

        try:
            result = await self.execute_code(
                session_id, init_code, user_id, correlation_id
            )

            properties = result.get("properties", {})
            stdout = properties.get("stdout", "")
            stderr = properties.get("stderr", "")

            if stderr:
                logger.warning(f"Stderr from init: {stderr[:500]}")

            events = self._parse_json_events(stdout)

            for event in events:
                yield event

            if not events:
                if stderr:
                    yield {"type": "error", "error": f"Init failed: {stderr[:200]}"}
                else:
                    yield {"type": "error", "error": "No events received from init"}

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during init: {e.response.status_code}")
            yield {"type": "error", "error": f"HTTP error: {e.response.status_code}"}
        except httpx.RequestError as e:
            logger.error(f"Request error during init: {e}")
            yield {"type": "error", "error": f"Connection error: {e}"}
        except Exception as e:
            logger.exception("Unexpected error during init")
            yield {"type": "error", "error": str(e)}
        finally:
            duration_ms = int((time.time() - start_time) * 1000)
            _log_operation(
                "init_sdk_session",
                session_id,
                duration_ms,
                user_id,
                correlation_id,
                team=team,
                persona=persona,
                model=model,
            )

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

        Executes triagent.sandbox.runner.run_validate_config() inside the
        container to check if the provided options are valid.

        Args:
            session_id: Session identifier for the Dynamic Session.
            team: Team profile to validate.
            persona: Persona profile to validate.
            model: Model to validate.
            user_id: Optional user identifier for logging.
            correlation_id: Optional correlation ID for request tracing.

        Yields:
            Validation events as dicts.
            Event types: config_options, config_valid, done, error
        """
        start_time = time.time()
        logger.info(
            f"Validating config for session {session_id}: "
            f"team={team}, persona={persona}, model={model}"
        )

        escaped_team = team.replace("\\", "\\\\").replace('"', '\\"')
        escaped_persona = persona.replace("\\", "\\\\").replace('"', '\\"')
        escaped_model = model.replace("\\", "\\\\").replace('"', '\\"')

        validate_code = f'''
from triagent.sandbox.runner import run_validate_config
import asyncio
asyncio.run(run_validate_config("{escaped_team}", "{escaped_persona}", "{escaped_model}"))
'''

        try:
            result = await self.execute_code(
                session_id, validate_code, user_id, correlation_id
            )

            properties = result.get("properties", {})
            stdout = properties.get("stdout", "")
            stderr = properties.get("stderr", "")

            if stderr:
                logger.warning(f"Stderr from validate: {stderr[:500]}")

            events = self._parse_json_events(stdout)

            for event in events:
                yield event

            if not events:
                if stderr:
                    yield {"type": "error", "error": f"Validation failed: {stderr[:200]}"}
                else:
                    yield {"type": "error", "error": "No events from validation"}

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during validation: {e.response.status_code}")
            yield {"type": "error", "error": f"HTTP error: {e.response.status_code}"}
        except httpx.RequestError as e:
            logger.error(f"Request error during validation: {e}")
            yield {"type": "error", "error": f"Connection error: {e}"}
        except Exception as e:
            logger.exception("Unexpected error during validation")
            yield {"type": "error", "error": str(e)}
        finally:
            duration_ms = int((time.time() - start_time) * 1000)
            _log_operation(
                "validate_config",
                session_id,
                duration_ms,
                user_id,
                correlation_id,
                team=team,
                persona=persona,
                model=model,
            )

    async def stream_sdk_session_chat(
        self,
        session_id: str,
        message: str,
        team: str = "omnia-data",
        max_retries: int = 3,
        user_id: str | None = None,
        correlation_id: str | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream chat via /code/execute with auto-retry on 504 timeout.

        Executes triagent.sandbox.runner.run_chat() inside the container.
        The runner resumes the existing Claude SDK session from file-based
        storage and streams response events to stdout.

        On 504 Gateway Timeout (Azure Session Pool ~240s limit), automatically
        retries with "continue" message since session state is preserved.

        Args:
            session_id: Session identifier for the Dynamic Session.
            message: User message to send to Claude SDK.
            team: Team profile (used if no existing session).
            max_retries: Maximum number of retries on 504 timeout (default 3).
            user_id: Optional user identifier for logging.
            correlation_id: Optional correlation ID for request tracing.

        Yields:
            Response events as dicts (text, tool_start, tool_end, done, error, progress).
        """
        start_time = time.time()
        message_preview = message[:50].replace("\n", " ")
        logger.info(f"Chat in session {session_id}: {message_preview}...")

        escaped_team = team.replace("\\", "\\\\").replace('"', '\\"')
        events_count = 0

        for attempt in range(max_retries + 1):
            # First attempt uses original message, retries use "continue"
            current_message = message if attempt == 0 else "continue"

            if attempt > 0:
                logger.info(
                    f"Retry {attempt}/{max_retries} after 504 timeout, "
                    f"sending 'continue' to resume"
                )
                yield {
                    "type": "progress",
                    "message": f"Request timed out. Resuming... (attempt {attempt + 1})",
                }

            # Escape message for Python string
            escaped_message = (
                current_message.replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
                .replace("\r", "\\r")
            )

            # Python code to run inside Dynamic Session
            chat_code = f'''
from triagent.sandbox.runner import run_chat
import asyncio
asyncio.run(run_chat("{escaped_message}", "{escaped_team}"))
'''

            try:
                result = await self.execute_code(
                    session_id, chat_code, user_id, correlation_id
                )

                # Extract stdout from result
                properties = result.get("properties", {})
                stdout = properties.get("stdout", "")
                stderr = properties.get("stderr", "")

                if stderr:
                    logger.warning(f"Stderr from chat: {stderr[:500]}")

                # Parse JSON events from stdout
                events = self._parse_json_events(stdout)
                events_count += len(events)

                for event in events:
                    yield event

                # If no events, check for error
                if not events:
                    if stderr:
                        yield {"type": "error", "error": f"Chat failed: {stderr[:200]}"}
                    else:
                        yield {"type": "error", "error": "No response from chat"}

                # Success - break out of retry loop and log
                duration_ms = int((time.time() - start_time) * 1000)
                _log_operation(
                    "stream_chat_end",
                    session_id,
                    duration_ms,
                    user_id,
                    correlation_id,
                    events=events_count,
                )
                return

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 504 and attempt < max_retries:
                    # 504 Gateway Timeout - will retry with "continue"
                    logger.warning(
                        f"504 timeout on attempt {attempt + 1}, will retry with 'continue'"
                    )
                    yield {
                        "type": "progress",
                        "message": "Processing taking longer than expected...",
                    }
                    continue
                else:
                    logger.error(f"HTTP error during chat: {e.response.status_code}")
                    yield {"type": "error", "error": f"HTTP error: {e.response.status_code}"}
                    duration_ms = int((time.time() - start_time) * 1000)
                    _log_operation(
                        "stream_chat_error",
                        session_id,
                        duration_ms,
                        user_id,
                        correlation_id,
                        error=f"HTTP_{e.response.status_code}",
                    )
                    return

            except httpx.RequestError as e:
                logger.error(f"Request error during chat: {e}")
                yield {"type": "error", "error": f"Connection error: {e}"}
                duration_ms = int((time.time() - start_time) * 1000)
                _log_operation(
                    "stream_chat_error",
                    session_id,
                    duration_ms,
                    user_id,
                    correlation_id,
                    error="connection_error",
                )
                return

            except Exception as e:
                logger.exception("Unexpected error during chat")
                yield {"type": "error", "error": str(e)}
                duration_ms = int((time.time() - start_time) * 1000)
                _log_operation(
                    "stream_chat_error",
                    session_id,
                    duration_ms,
                    user_id,
                    correlation_id,
                    error="unexpected_error",
                )
                return

    async def health_check(
        self,
        session_id: str,
        user_id: str | None = None,
        correlation_id: str | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Check session health for session resumption.

        Executes triagent.sandbox.runner.run_health_check() inside the container.
        This checks:
        1. Azure CLI authentication status
        2. Session file existence and initialization
        3. Stored preferences (team, persona, model)

        Used to determine if session can be resumed without showing config modal.

        Args:
            session_id: Session identifier for the Dynamic Session.
            user_id: Optional user identifier for logging.
            correlation_id: Optional correlation ID for request tracing.

        Yields:
            Health check events as dicts.
            Event types: progress, done with health status
            Check done.healthy to see if session can be resumed.
        """
        start_time = time.time()
        logger.info(f"Health check for session {session_id}")

        health_check_code = '''
from triagent.sandbox.runner import run_health_check
import asyncio
asyncio.run(run_health_check())
'''
        healthy = False
        try:
            result = await self.execute_code(
                session_id, health_check_code, user_id, correlation_id
            )

            properties = result.get("properties", {})
            stdout = properties.get("stdout", "")
            stderr = properties.get("stderr", "")

            if stderr:
                logger.warning(f"Stderr from health_check: {stderr[:500]}")

            events = self._parse_json_events(stdout)

            for event in events:
                if event.get("type") == "done":
                    healthy = event.get("healthy", False)
                yield event

            if not events:
                if stderr:
                    yield {"type": "error", "error": f"Health check failed: {stderr[:200]}"}
                else:
                    yield {"type": "error", "error": "No events from health check"}

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during health check: {e.response.status_code}")
            yield {"type": "error", "error": f"HTTP error: {e.response.status_code}"}
        except httpx.RequestError as e:
            logger.error(f"Request error during health check: {e}")
            yield {"type": "error", "error": f"Connection error: {e}"}
        except Exception as e:
            logger.exception("Unexpected error during health check")
            yield {"type": "error", "error": str(e)}
        finally:
            duration_ms = int((time.time() - start_time) * 1000)
            _log_operation(
                "health_check",
                session_id,
                duration_ms,
                user_id,
                correlation_id,
                healthy=healthy,
            )

    async def get_session_status(
        self,
        session_id: str,
        user_id: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Get session status via /code/execute.

        Checks if session file exists and reads state.

        Args:
            session_id: Session identifier.
            user_id: Optional user identifier for logging.
            correlation_id: Optional correlation ID for request tracing.

        Returns:
            Status dict with initialized, conversation_turns, etc.
        """
        start_time = time.time()
        status_code = '''
import json
from triagent.sandbox.session_store import SessionStore

store = SessionStore()
state = store.load()
if state:
    print(json.dumps({
        "exists": True,
        "initialized": state.initialized,
        "session_id": state.session_id[:8] if state.session_id else None,
        "team": state.team,
        "conversation_turns": state.conversation_turns,
    }))
else:
    print(json.dumps({"exists": False, "initialized": False}))
'''

        try:
            result = await self.execute_code(
                session_id, status_code, user_id, correlation_id
            )
            properties = result.get("properties", {})
            stdout = properties.get("stdout", "").strip()

            if stdout:
                return json.loads(stdout)
            return {"exists": False, "initialized": False}

        except Exception as e:
            logger.warning(f"Failed to get session status: {e}")
            return {"exists": False, "initialized": False, "error": str(e)}
        finally:
            duration_ms = int((time.time() - start_time) * 1000)
            _log_operation(
                "get_session_status",
                session_id,
                duration_ms,
                user_id,
                correlation_id,
            )

    async def clear_session(
        self,
        session_id: str,
        user_id: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, str]:
        """Clear session state via /code/execute.

        Deletes the session file to start fresh.

        Args:
            session_id: Session identifier.
            user_id: Optional user identifier for logging.
            correlation_id: Optional correlation ID for request tracing.

        Returns:
            Response dict with status.
        """
        start_time = time.time()
        clear_code = '''
import json
from triagent.sandbox.session_store import SessionStore

store = SessionStore()
success = store.clear()
print(json.dumps({"status": "cleared" if success else "error"}))
'''

        try:
            result = await self.execute_code(
                session_id, clear_code, user_id, correlation_id
            )
            properties = result.get("properties", {})
            stdout = properties.get("stdout", "").strip()

            if stdout:
                return json.loads(stdout)
            return {"status": "cleared"}

        except Exception as e:
            logger.warning(f"Failed to clear session: {e}")
            return {"status": "error", "detail": str(e)}
        finally:
            duration_ms = int((time.time() - start_time) * 1000)
            _log_operation(
                "clear_session",
                session_id,
                duration_ms,
                user_id,
                correlation_id,
            )

    async def submit_confirmation(
        self,
        session_id: str,
        request_id: str,
        approved: bool,
        answers: dict[str, str] | None = None,
        user_id: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Submit confirmation for pending permission request.

        Note: This is a placeholder. The sandbox runner currently handles
        confirmations internally. This method may be used in future
        implementations with async confirmation flows.

        Args:
            session_id: Session identifier.
            request_id: Unique ID of the pending permission request.
            approved: True if user approved, False if denied.
            answers: Optional dict of answers for AskUserQuestion.
            user_id: Optional user identifier for logging.
            correlation_id: Optional correlation ID for request tracing.

        Returns:
            Response dict with status.
        """
        start_time = time.time()
        # TODO: Implement async confirmation flow
        # Current implementation handles confirmations synchronously
        logger.info(
            f"Confirmation submitted: request={request_id}, approved={approved}"
        )
        duration_ms = int((time.time() - start_time) * 1000)
        _log_operation(
            "submit_confirmation",
            session_id,
            duration_ms,
            user_id,
            correlation_id,
            request_id=request_id,
            approved=approved,
        )
        return {
            "status": "noted",
            "request_id": request_id,
            "approved": approved,
        }

    async def close(self) -> None:
        """Clean up resources.

        MSAL ConfidentialClientApplication doesn't require explicit cleanup,
        but we clear cached tokens for security.
        """
        self._token_cache = None
        self._token_expiry = 0
        self._msal_app = None
