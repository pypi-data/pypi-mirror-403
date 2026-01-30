"""Local mock for Azure Dynamic Sessions /code/execute endpoint.

This provides a simple HTTP wrapper around Python code execution
for local testing of the sandbox pattern.

IMPORTANT: This implementation mirrors sessions_server.py to ensure
local testing matches production behavior.

Usage:
    uvicorn triagent.web.local_sessions_api:app --host 0.0.0.0 --port 8082
"""

import asyncio
import io
import json
import re
import subprocess
import time
import traceback
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Local Dynamic Sessions Mock")


class CodeExecuteRequest(BaseModel):
    """Request to execute Python code."""

    properties: dict[str, Any]


class CodeExecuteResponse(BaseModel):
    """Response from code execution."""

    properties: dict[str, Any]


@app.post("/code/execute")
async def execute_code(request: CodeExecuteRequest) -> CodeExecuteResponse:
    """Execute Python code and return stdout/stderr.

    This mirrors sessions_server.py implementation for accurate local testing.
    Code is executed in the current process with full access to installed packages.

    Async support (matching sessions_server.py):
    - Code with asyncio.run() is transformed to use await directly
    - Code is wrapped to run in the current event loop
    """
    code = request.properties.get("code", "")

    if not code:
        raise HTTPException(status_code=400, detail="No code provided")

    start_time = time.time()

    # Capture stdout/stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    result = None

    try:
        # Execute code with output capture
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            # Execute in a new namespace with asyncio pre-imported
            namespace = {
                "__name__": "__main__",
                "asyncio": asyncio,
            }

            # Transform asyncio.run(x) to await x for async context
            if "asyncio.run(" in code:
                # Replace asyncio.run(expr) with (await expr)
                # Handle multi-line and nested parentheses
                transformed = re.sub(
                    r'asyncio\.run\((.+)\)',
                    r'await \1',
                    code
                )
                # Wrap in async function
                indented = "\n    ".join(transformed.split("\n"))
                wrapper = f"async def __run__():\n    {indented}\n"
                exec(wrapper, namespace)
                await namespace["__run__"]()
            elif "await " in code:
                # Code contains await, wrap in async function
                indented = "\n    ".join(code.split("\n"))
                wrapper = f"async def __run__():\n    {indented}\n"
                exec(wrapper, namespace)
                await namespace["__run__"]()
            else:
                # Regular sync code
                exec(code, namespace)

            # Check for 'result' variable in namespace
            if "result" in namespace:
                result = namespace["result"]
    except Exception:
        # Capture exception in stderr
        stderr_capture.write(traceback.format_exc())

    elapsed_ms = int((time.time() - start_time) * 1000)

    return CodeExecuteResponse(
        properties={
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue(),
            "result": result,
            "executionResult": "Success" if not stderr_capture.getvalue() else "Failed",
            "executionTimeInMilliseconds": elapsed_ms,
        }
    )


@app.get("/health")
async def health():
    """Check if session is healthy and Azure CLI is authenticated.

    This mirrors sessions_server.py health check for accurate local testing.

    Returns comprehensive session status including:
    - Azure CLI authentication state
    - Session file existence and initialization
    - Stored preferences (team, persona, model)
    """
    try:
        # Check Azure CLI auth
        result = subprocess.run(
            ["az", "account", "show", "--query", "user.name", "-o", "tsv"],
            capture_output=True,
            text=True,
            timeout=10
        )
        azure_auth = result.returncode == 0 and bool(result.stdout.strip())
        azure_user = result.stdout.strip() if azure_auth else None

        # Check session file
        session_file = Path.home() / ".triagent" / "session.json"
        session_data = {}

        if session_file.exists():
            try:
                session_data = json.loads(session_file.read_text())
            except json.JSONDecodeError:
                pass

        # Determine overall status
        session_initialized = session_data.get("initialized", False)
        is_ready = azure_auth and session_initialized

        return {
            "status": "ready" if is_ready else "not_ready",
            "azure_auth": azure_auth,
            "azure_user": azure_user,
            "session_initialized": session_initialized,
            "conversation_turns": session_data.get("conversation_turns", 0),
            "team": session_data.get("team"),
            "persona": session_data.get("persona"),
            "model": session_data.get("model"),
            "last_active": session_data.get("last_active"),
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "Azure CLI check timed out"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "triagent-sessions-local",
        "status": "ready",
        "endpoints": [
            "/health - Session health check with Azure auth and preferences",
            "/code/execute - Execute Python code in sandbox",
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8082, log_level="info")
