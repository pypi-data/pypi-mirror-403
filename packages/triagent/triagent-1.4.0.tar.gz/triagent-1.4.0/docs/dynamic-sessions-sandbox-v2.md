# Azure Dynamic Sessions Sandbox Module v2

**Document Version:** 1.0
**Prepared by:** sdandey
**Last Updated:** 2026-01-08 09:32:28
**Branch:** feature/sandbox-module-v2

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Statement](#problem-statement)
3. [Solution Architecture](#solution-architecture)
4. [Module Structure](#module-structure)
5. [Sequence Diagrams](#sequence-diagrams)
6. [API Reference](#api-reference)
7. [Testing Guide](#testing-guide)
8. [Deployment Guide](#deployment-guide)
9. [Document History](#document-history)

---

## Executive Summary

Azure Container Apps Dynamic Sessions does NOT run container CMD/ENTRYPOINT. Custom HTTP endpoints (`/init`, `/chat`) are NOT accessible via the Session Pool management endpoint. Only the `/code/execute` endpoint works.

This document describes the **sandbox module** solution that:
1. Executes via `/code/execute` Python execution
2. Stores Claude session IDs in local files within the container
3. Resumes conversations using Claude Agent SDK's `resume` parameter
4. Emits JSON events to stdout for parent process parsing

---

## Problem Statement

### Discovery

When deploying a custom container to Azure Container Apps Session Pool:

1. **CMD/ENTRYPOINT not executed**: The container starts but the CMD is never run
2. **Custom HTTP endpoints inaccessible**: POST/GET requests to `/init`, `/chat`, `/health` return 404
3. **Only `/code/execute` works**: This is the only endpoint Azure Dynamic Sessions exposes

### Root Cause

Azure Dynamic Sessions is designed for **code execution**, not custom HTTP services. The Session Pool infrastructure:
- Manages container lifecycle internally
- Only exposes the `/code/execute` endpoint
- Does not forward custom HTTP routes to the container

### Impact

The previous architecture using FastAPI with custom endpoints (`triagent.web.sessions.app`) cannot work in Azure Dynamic Sessions.

---

## Solution Architecture

### Code Execution Pattern

Instead of custom HTTP endpoints, we use `/code/execute` to run Python code that invokes the sandbox module:

```
Browser → Chainlit → SessionProxy → Azure Session Pool → Container
                         │                                   │
                         │ POST /code/execute                │
                         │ code="run_init('team')"           │
                         │──────────────────────────────────>│
                         │                                   │
                         │                                   │ Execute Python
                         │                                   │ Check az auth
                         │                                   │ Init Claude SDK
                         │                                   │ Emit JSON events
                         │                                   │
                         │ Response: {stdout: "...JSON..."}  │
                         │<──────────────────────────────────│
                         │                                   │
                         │ Parse JSON events                 │
Browser <────────────────│                                   │
```

### Session Resumption

Session state is persisted to a file (`/root/.triagent/session.json`) inside the container:

```json
{
    "session_id": "abc123...",
    "team": "omnia-data",
    "initialized": true,
    "conversation_turns": 5
}
```

On subsequent `/code/execute` calls, the runner:
1. Loads session state from file
2. Uses `ClaudeAgentOptions.resume = session_id` to resume conversation
3. Updates session state with new turn count

---

## Module Structure

### New Module: `src/triagent/sandbox/`

```
src/triagent/sandbox/
├── __init__.py         # Package exports and convenience functions
├── events.py           # JSON event emitters (progress, text, tool_*, done, error)
├── session_store.py    # File-based session persistence
└── runner.py           # Core functions: run_init(), run_chat()
```

### Updated Module: `src/triagent/web/`

```
src/triagent/web/
├── __init__.py         # Package exports
├── config.py           # WebConfig from environment variables
└── services/
    ├── __init__.py
    └── session_proxy.py  # SessionProxy using /code/execute pattern
```

### Key Files

| File | Purpose |
|------|---------|
| `sandbox/__init__.py` | Exports `run_init`, `run_chat`, `EventType`, `SessionStore` |
| `sandbox/events.py` | `emit_event()`, `emit_progress()`, `emit_text()`, `emit_done()` |
| `sandbox/session_store.py` | `SessionStore` class, `SessionState` dataclass |
| `sandbox/runner.py` | `run_init()` - init with device flow, `run_chat()` - resume and chat |
| `web/services/session_proxy.py` | `SessionProxy` - executes code via Azure Session Pool |

---

## Sequence Diagrams

### Initialization Flow

:::mermaid
sequenceDiagram
    participant B as Browser
    participant C as Chainlit
    participant P as SessionProxy
    participant A as Azure Session Pool
    participant D as Container

    B->>C: Click "Start Session"
    C->>P: init_sdk_session(session_id, team)
    P->>A: POST /code/execute<br/>code="run_init('team')"
    A->>D: Execute Python
    D->>D: Check Azure CLI auth

    alt Not authenticated
        D-->>A: stdout: {"type":"device_code","code":"ABC123",...}
        A-->>P: Response with stdout
        P-->>C: Yield device_code event
        C-->>B: Show device code modal
        B->>B: User completes auth
        D->>D: az login completes
    end

    D->>D: Initialize Claude SDK
    D->>D: Save session to file
    D-->>A: stdout: {"type":"done","session_id":"abc123",...}
    A-->>P: Response with stdout
    P-->>C: Yield done event
    C-->>B: Show "Connected!"
:::

### Chat Flow

:::mermaid
sequenceDiagram
    participant B as Browser
    participant C as Chainlit
    participant P as SessionProxy
    participant A as Azure Session Pool
    participant D as Container

    B->>C: Send message
    C->>P: stream_sdk_session_chat(session_id, message)
    P->>A: POST /code/execute<br/>code="run_chat('message')"
    A->>D: Execute Python
    D->>D: Load session from file
    D->>D: Resume Claude SDK with session_id
    D->>D: Send message to Claude

    loop Response chunks
        D-->>A: stdout: {"type":"text","content":"..."}
        D-->>A: stdout: {"type":"tool_start","name":"..."}
        D-->>A: stdout: {"type":"tool_end","name":"..."}
    end

    D->>D: Update session file
    D-->>A: stdout: {"type":"done","session_id":"...","turns":5}
    A-->>P: Response with stdout
    P->>P: Parse JSON events from stdout
    P-->>C: Yield events
    C-->>B: Stream response
:::

---

## API Reference

### Events Module (`triagent.sandbox.events`)

#### Event Types

| Type | Description | Fields |
|------|-------------|--------|
| `progress` | Initialization progress | `step`, `message`, optional `model`, `session_id` |
| `device_code` | Azure CLI auth required | `code`, `url`, `message` |
| `text` | Claude response text | `content` |
| `tool_start` | Tool execution started | `name`, `input` |
| `tool_end` | Tool execution ended | `name`, `success` |
| `confirm_request` | Write operation needs confirmation | `request_id`, `tool_name`, `description`, `details` |
| `done` | Operation complete | `session_id`, `turns` |
| `error` | Error occurred | `error` |

#### Functions

```python
def emit_event(event_type: EventType | str, **kwargs) -> None:
    """Emit JSON event to stdout."""

def emit_progress(step: str, message: str = "", **kwargs) -> None:
    """Emit progress event."""

def emit_text(content: str) -> None:
    """Emit text content event."""

def emit_done(session_id: str, turns: int = 0, **kwargs) -> None:
    """Emit completion event."""

def emit_error(error: str, **kwargs) -> None:
    """Emit error event."""
```

### Session Store (`triagent.sandbox.session_store`)

#### SessionState

```python
@dataclass
class SessionState:
    session_id: str
    team: str = "omnia-data"
    initialized: bool = False
    conversation_turns: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
```

#### SessionStore

```python
class SessionStore:
    def __init__(self, path: Path | str | None = None):
        """Initialize store. Default path: /root/.triagent/session.json"""

    def load(self) -> Optional[SessionState]:
        """Load session from file."""

    def save(self, state: SessionState) -> bool:
        """Save session to file."""

    def clear(self) -> bool:
        """Delete session file."""

    def exists(self) -> bool:
        """Check if session file exists."""
```

### Runner (`triagent.sandbox.runner`)

```python
async def run_init(team: str = "omnia-data") -> None:
    """Initialize SDK session with device flow authentication.

    Events emitted:
        - progress: Various initialization steps
        - device_code: If Azure CLI auth needed
        - done: On successful initialization
        - error: If initialization fails
    """

async def run_chat(message: str, team: str = "omnia-data") -> None:
    """Send chat message with automatic session resumption.

    Events emitted:
        - progress: Session resumption status
        - text: Claude response content
        - tool_start/tool_end: Tool execution
        - done: On completion with updated session_id
        - error: If chat fails
    """
```

### SessionProxy (`triagent.web.services.session_proxy`)

```python
class SessionProxy:
    async def init_sdk_session(
        self, session_id: str, team: str = "omnia-data"
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Initialize SDK session via /code/execute."""

    async def stream_sdk_session_chat(
        self, session_id: str, message: str, team: str = "omnia-data"
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream chat via /code/execute."""

    async def get_session_status(self, session_id: str) -> dict[str, Any]:
        """Get session status via /code/execute."""

    async def clear_session(self, session_id: str) -> dict[str, str]:
        """Clear session state via /code/execute."""
```

---

## Testing Guide

### Phase 1: Local Docker Testing

```bash
# Build image
docker build -f Dockerfile.sessions -t triagent-session:local .

# Test imports
docker run --rm triagent-session:local python -c "
from triagent.sandbox import run_init, run_chat, EventType
from triagent.sandbox.session_store import SessionStore, SessionState
print('Imports OK')
"

# Test events
docker run --rm triagent-session:local python -c "
from triagent.sandbox.events import emit_event, EventType
emit_event(EventType.PROGRESS, step='test', message='Testing')
"
# Expected: {"type": "progress", "step": "test", "message": "Testing"}

# Test session store
docker run --rm triagent-session:local python -c "
import json
from triagent.sandbox.session_store import SessionStore, SessionState

store = SessionStore('/tmp/test.json')
state = SessionState(session_id='test-123', initialized=True)
store.save(state)
loaded = store.load()
print(json.dumps({'session_id': loaded.session_id, 'initialized': loaded.initialized}))
"
# Expected: {"session_id": "test-123", "initialized": true}
```

### Phase 2: Integration Testing

```bash
# Test run_init (requires Azure CLI credentials)
docker run -it --rm \
  -v ~/.azure:/root/.azure:ro \
  triagent-session:local python -c "
from triagent.sandbox import run_init
import asyncio
asyncio.run(run_init('omnia-data'))
"
```

### Phase 3: Azure Deployment Testing

```bash
# Get token
TOKEN=$(az-elevated account get-access-token \
  --resource https://dynamicsessions.io \
  --query accessToken -o tsv)

# Test /code/execute
curl -X POST "${POOL_ENDPOINT}/code/execute?identifier=test-123" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "properties": {
      "codeInputType": "inline",
      "executionType": "synchronous",
      "code": "from triagent.sandbox.events import emit_event; emit_event(\"progress\", step=\"test\")"
    }
  }'
```

---

## Deployment Guide

### 1. Build and Push Image

```bash
# Login to ACR
az-elevated acr login --name triagentsandboxacr

# Build and tag
docker build -f Dockerfile.sessions -t triagentsandboxacr.azurecr.io/triagent-session:v2.0 .

# Push
docker push triagentsandboxacr.azurecr.io/triagent-session:v2.0
```

### 2. Update Session Pool

Via Azure Portal or CLI:
- Navigate to Session Pool resource
- Update container image to `triagentsandboxacr.azurecr.io/triagent-session:v2.0`

### 3. Verify Deployment

```bash
# Test code execution
curl -X POST "${POOL_ENDPOINT}/code/execute?identifier=verify-123" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "properties": {
      "code": "from triagent.sandbox import run_init; print(\"OK\")"
    }
  }'
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-08 | sdandey | Initial document - sandbox module v2 design |
