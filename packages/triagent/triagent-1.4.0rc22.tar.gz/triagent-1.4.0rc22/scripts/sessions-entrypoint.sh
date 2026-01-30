#!/bin/bash
# sessions-entrypoint.sh - Container startup script for sessions API
#
# Clears ALL session state when container starts to ensure a clean state.
# This handles multiple failure scenarios:
# 1. Container rebuilt but session.json persists (orphaned session)
# 2. Session state corrupted from failed/timed-out requests
# 3. Claude CLI session in broken state after crash
#
# Strategy: Always start fresh on container startup. Users will need to
# re-authenticate via device code flow, but this ensures reliability.

set -e

echo "[entrypoint] Starting sessions container..."

# Session state locations
SESSION_FILE="/home/triagent/.triagent/session.json"
CLAUDE_PROJECTS_DIR="/home/triagent/.claude/projects"

# Always clear session state on container start for reliability
# This ensures we never try to resume a potentially corrupted session
if [ -f "$SESSION_FILE" ] || [ -d "$CLAUDE_PROJECTS_DIR" ]; then
    echo "[entrypoint] Clearing previous session state for clean start..."
    rm -f "$SESSION_FILE"
    rm -rf "$CLAUDE_PROJECTS_DIR"
    echo "[entrypoint] Session state cleared - will create fresh session"
else
    echo "[entrypoint] No existing session - starting fresh"
fi

# Execute the main command
exec "$@"
