"""File-based session storage for Azure Dynamic Sessions.

Stores session state in ~/.triagent/session.json within the container.
This persists across /code/execute calls within the same Azure Dynamic Session.

When running as:
- triagent user: /home/triagent/.triagent/session.json
- root user: /root/.triagent/session.json
- local testing: ~/.triagent/session.json

Session lifecycle:
1. First run_init() → Creates new session, saves session_id to file
2. Subsequent run_chat() → Loads session_id, resumes conversation
3. Container recycled → New session_id on next init

The session file contains:
{
    "session_id": "abc123...",
    "team": "omnia-data",
    "persona": "developer",
    "model": "claude-opus-4-5",
    "initialized": true,
    "conversation_turns": 5
}
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default session file location
# Uses Path.home() for portability across different users:
# - triagent user: /home/triagent/.triagent/session.json
# - root user: /root/.triagent/session.json
# - local testing: ~/.triagent/session.json
DEFAULT_SESSION_PATH = Path(
    os.environ.get("TRIAGENT_SESSION_FILE", str(Path.home() / ".triagent" / "session.json"))
)


@dataclass
class SessionState:
    """Session state persisted to file.

    Attributes:
        session_id: Claude session ID for resumption
        team: Team profile (e.g., "omnia-data")
        persona: Persona profile (e.g., "developer", "support")
        model: Claude model to use (e.g., "claude-opus-4-5")
        initialized: Whether SDK has been initialized
        conversation_turns: Number of conversation turns
        last_active: Timestamp of last activity (Unix epoch)
        azure_user: Authenticated Azure user email
        metadata: Additional session metadata
    """

    session_id: str
    team: str = "omnia-data"
    persona: str = "developer"
    model: str = "claude-opus-4-5"
    initialized: bool = False
    conversation_turns: int = 0
    last_active: float = 0.0
    azure_user: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionState:
        """Create from dictionary.

        Args:
            data: Dictionary with session state fields

        Returns:
            SessionState instance
        """
        # Filter to only known fields to handle schema changes gracefully
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}

        # Handle metadata field specially (default to empty dict)
        if "metadata" not in filtered:
            filtered["metadata"] = {}

        return cls(**filtered)


class SessionStore:
    """File-based session storage.

    Stores and retrieves session state from a JSON file. This enables
    session resumption across /code/execute calls.

    Example:
        store = SessionStore()

        # Save session
        state = SessionState(
            session_id="abc123",
            team="omnia-data",
            persona="developer",
            model="claude-opus-4-5",
            initialized=True,
            conversation_turns=1
        )
        store.save(state)

        # Load session
        loaded = store.load()
        if loaded:
            print(f"Resuming session: {loaded.session_id}")
    """

    def __init__(self, path: Path | str | None = None):
        """Initialize session store.

        Args:
            path: Path to session file. Defaults to /root/.triagent/session.json
        """
        if path is None:
            self._path = DEFAULT_SESSION_PATH
        else:
            self._path = Path(path)

    @property
    def path(self) -> Path:
        """Get the session file path."""
        return self._path

    def load(self) -> SessionState | None:
        """Load session state from file.

        Returns:
            SessionState if file exists and is valid, None otherwise
        """
        if not self._path.exists():
            logger.debug(f"No session file at {self._path}")
            return None

        try:
            data = json.loads(self._path.read_text())
            state = SessionState.from_dict(data)
            logger.info(
                f"Loaded session: {state.session_id[:8]}... "
                f"(turns={state.conversation_turns})"
            )
            return state
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in session file: {e}")
            return None
        except Exception as e:
            logger.warning(f"Failed to load session: {e}")
            return None

    def save(self, state: SessionState) -> bool:
        """Save session state to file.

        Args:
            state: Session state to save

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Create directory if needed
            self._path.parent.mkdir(parents=True, exist_ok=True)

            # Write atomically (write to temp, then rename)
            temp_path = self._path.with_suffix(".tmp")
            temp_path.write_text(json.dumps(state.to_dict(), indent=2))
            temp_path.rename(self._path)

            logger.info(
                f"Saved session: {state.session_id[:8]}... "
                f"(turns={state.conversation_turns})"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            return False

    def update(self, **kwargs: Any) -> bool:
        """Update session state with new values.

        Args:
            **kwargs: Fields to update

        Returns:
            True if updated successfully, False otherwise
        """
        state = self.load()
        if state is None:
            logger.error("Cannot update: no existing session")
            return False

        # Update fields
        for key, value in kwargs.items():
            if hasattr(state, key):
                setattr(state, key, value)
            else:
                state.metadata[key] = value

        return self.save(state)

    def clear(self) -> bool:
        """Clear session state (delete file).

        Returns:
            True if cleared successfully, False otherwise
        """
        try:
            if self._path.exists():
                self._path.unlink()
                logger.info(f"Cleared session file: {self._path}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear session: {e}")
            return False

    def exists(self) -> bool:
        """Check if session file exists.

        Returns:
            True if session file exists
        """
        return self._path.exists()

    def is_initialized(self) -> bool:
        """Check if session is initialized.

        Returns:
            True if session exists and is initialized
        """
        state = self.load()
        return state is not None and state.initialized
