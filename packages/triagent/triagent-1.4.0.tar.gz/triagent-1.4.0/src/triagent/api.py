"""Triagent Public API for Azure Dynamic Sessions.

This module provides a clean abstraction layer over ClaudeSDKClient for
sandbox execution within Azure Dynamic Sessions containers.

Usage:
    session = await TriagentSession.create(
        team="omnia-data",
        persona="developer",
        model="claude-opus-4-5"
    )
    result = await session.query("List active PRs")
    print(result.text)
    await session.close()
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from triagent.sandbox.session_store import SessionState, SessionStore

logger = logging.getLogger(__name__)


@dataclass
class SessionConfig:
    """Configuration for a Triagent session.

    Attributes:
        team: Team profile (omnia-data, omnia, levvia).
        persona: Persona profile (developer, support).
        model: Claude model (claude-opus-4-5, claude-sonnet-4).
    """

    team: str = "omnia-data"
    persona: str = "developer"
    model: str = "claude-opus-4-5"

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class QueryResult:
    """Result of a chat query.

    Attributes:
        text: The response text from Claude.
        tools_used: List of tool names that were invoked.
        turn_count: Total conversation turns after this query.
        session_id: The session ID for resumption.
    """

    text: str
    tools_used: list[str] = field(default_factory=list)
    turn_count: int = 0
    session_id: str = ""


@dataclass
class CommandResult:
    """Result of a command execution.

    Attributes:
        output: Command output text.
        success: Whether the command succeeded.
    """

    output: str
    success: bool


class TriagentSession:
    """Public API for Triagent operations inside Azure Dynamic Sessions.

    This class provides a high-level interface for:
    - Creating and resuming Claude SDK sessions
    - Sending queries and receiving structured responses
    - Executing slash commands
    - Persisting session state

    The session uses file-based storage for state persistence, enabling
    conversation resumption across /code/execute calls.

    Usage:
        # Create new session
        session = await TriagentSession.create(
            team="omnia-data",
            persona="developer",
            model="claude-opus-4-5"
        )

        # Query Claude
        result = await session.query("List active PRs")
        print(result.text)

        # Save for later
        await session.save(Path("/tmp/session.json"))

        # Later: resume session
        session = await TriagentSession.load(Path("/tmp/session.json"))

        # Cleanup
        await session.close()
    """

    def __init__(self, config: SessionConfig) -> None:
        """Initialize session with configuration.

        Args:
            config: Session configuration.
        """
        self._config = config
        self._session_id: str | None = None
        self._initialized: bool = False
        self._turn_count: int = 0
        self._store = SessionStore()
        self._client: Any = None

    @property
    def config(self) -> SessionConfig:
        """Get session configuration."""
        return self._config

    @property
    def session_id(self) -> str | None:
        """Get session ID for resumption."""
        return self._session_id

    @property
    def is_initialized(self) -> bool:
        """Check if session is initialized."""
        return self._initialized

    @property
    def turn_count(self) -> int:
        """Get current conversation turn count."""
        return self._turn_count

    @classmethod
    async def create(
        cls,
        team: str = "omnia-data",
        persona: str = "developer",
        model: str = "claude-opus-4-5",
    ) -> TriagentSession:
        """Create a new Triagent session with the specified configuration.

        Args:
            team: Team profile (omnia-data, omnia, levvia).
            persona: Persona profile (developer, support).
            model: Claude model (claude-opus-4-5, claude-sonnet-4).

        Returns:
            Initialized TriagentSession.

        Raises:
            RuntimeError: If session initialization fails.
        """
        config = SessionConfig(team=team, persona=persona, model=model)
        session = cls(config)
        await session._initialize()
        return session

    @classmethod
    async def load(cls, session_file: Path) -> TriagentSession:
        """Resume a session from a saved state file.

        Args:
            session_file: Path to the session state file.

        Returns:
            Resumed TriagentSession.

        Raises:
            FileNotFoundError: If session file doesn't exist.
            ValueError: If session file is invalid.
        """
        if not session_file.exists():
            raise FileNotFoundError(f"Session file not found: {session_file}")

        try:
            data = json.loads(session_file.read_text())
            state = SessionState.from_dict(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid session file: {e}") from e

        config = SessionConfig(
            team=state.team,
            persona=state.persona,
            model=state.model,
        )
        session = cls(config)
        session._session_id = state.session_id
        session._initialized = state.initialized
        session._turn_count = state.conversation_turns

        logger.info(f"Loaded session {state.session_id[:8]}... with {state.conversation_turns} turns")
        return session

    async def _initialize(self) -> None:
        """Initialize the Claude SDK client.

        This method:
        1. Creates a ClaudeSDKClient with the configured options
        2. Executes an initial query to obtain a session_id
        3. Saves the session state for resumption

        Raises:
            RuntimeError: If initialization fails.
        """
        # Note: Actual SDK initialization happens in sandbox runner
        # This method sets up the session state for tracking
        logger.info(
            f"Initializing session with team={self._config.team}, "
            f"persona={self._config.persona}, model={self._config.model}"
        )

        # Check if we have an existing session in the store
        existing_state = self._store.load()
        if existing_state and existing_state.initialized:
            self._session_id = existing_state.session_id
            self._initialized = True
            self._turn_count = existing_state.conversation_turns
            logger.info(f"Resumed existing session: {self._session_id[:8]}...")
            return

        # Mark as ready for initialization
        # Actual SDK setup happens on first query
        self._initialized = True
        logger.info("Session ready for initialization on first query")

    async def query(self, message: str) -> QueryResult:
        """Send a chat message and get the response.

        Args:
            message: User message to send to Claude.

        Returns:
            QueryResult with response text and metadata.

        Raises:
            RuntimeError: If session is not initialized.
        """
        if not self._initialized:
            raise RuntimeError("Session not initialized. Call create() or load() first.")

        logger.info(f"Query: {message[:50]}...")

        # Note: Actual query execution happens in sandbox runner
        # This is a placeholder for the API structure
        self._turn_count += 1

        return QueryResult(
            text="",
            tools_used=[],
            turn_count=self._turn_count,
            session_id=self._session_id or "",
        )

    async def execute(self, command: str) -> CommandResult:
        """Execute a slash command.

        Args:
            command: Slash command to execute (e.g., "/help", "/init").

        Returns:
            CommandResult with output and success status.

        Raises:
            RuntimeError: If session is not initialized.
        """
        if not self._initialized:
            raise RuntimeError("Session not initialized. Call create() or load() first.")

        logger.info(f"Executing command: {command}")

        # Note: Command execution happens in sandbox runner
        return CommandResult(output="", success=True)

    def help(self) -> list[dict[str, str]]:
        """Get available commands.

        Returns:
            List of command descriptions with name and description.
        """
        return [
            {"name": "/help", "description": "Show available commands"},
            {"name": "/init", "description": "Initialize session with team"},
            {"name": "/team", "description": "Switch team profile"},
            {"name": "/clear", "description": "Clear conversation history"},
            {"name": "/config", "description": "Show current configuration"},
        ]

    async def save(self, session_file: Path) -> None:
        """Save session state for later resumption.

        Args:
            session_file: Path to save the session state.
        """
        state = SessionState(
            session_id=self._session_id or "",
            team=self._config.team,
            persona=self._config.persona,
            model=self._config.model,
            initialized=self._initialized,
            conversation_turns=self._turn_count,
        )

        session_file.parent.mkdir(parents=True, exist_ok=True)
        session_file.write_text(json.dumps(state.to_dict(), indent=2))
        logger.info(f"Saved session to {session_file}")

    async def close(self) -> None:
        """Close session and cleanup resources.

        This method saves the current session state before closing.
        """
        if self._session_id:
            # Save state before closing
            state = SessionState(
                session_id=self._session_id,
                team=self._config.team,
                persona=self._config.persona,
                model=self._config.model,
                initialized=self._initialized,
                conversation_turns=self._turn_count,
            )
            self._store.save(state)
            logger.info(f"Closed session: {self._session_id[:8]}...")

        self._client = None
        self._initialized = False
