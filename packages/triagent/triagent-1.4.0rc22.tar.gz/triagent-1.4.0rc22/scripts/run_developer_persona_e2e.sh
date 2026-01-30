#!/bin/bash
# E2E Integration Tests for Developer Persona
# Requires Azure CLI authentication
#
# Usage:
#   ./scripts/run_developer_persona_e2e.sh                    # Run all tests
#   ./scripts/run_developer_persona_e2e.sh -k "scenario1"     # Run specific test
#   ./scripts/run_developer_persona_e2e.sh --help             # Show pytest help
#
# Prerequisites:
#   - Azure CLI installed and authenticated (az login)
#   - Python virtual environment activated
#   - pytest-timeout installed (uv sync or pip install pytest-timeout)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "============================================================"
echo "Developer Persona E2E Integration Tests"
echo "============================================================"
echo ""

# Check Azure CLI installation
echo "Checking Azure CLI installation..."

if ! command -v az &> /dev/null; then
    echo "WARNING: Azure CLI not installed."
    echo "Install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    echo ""
    echo "Skipping E2E tests (Azure CLI required)."
    exit 0
fi

AZ_VERSION=$(az --version 2>/dev/null | head -1 | awk '{print $2}')
echo "Azure CLI version: $AZ_VERSION"

# Check Azure CLI authentication
echo ""
echo "Checking Azure CLI authentication..."

if ! az account show &> /dev/null 2>&1; then
    echo "WARNING: Not logged in to Azure CLI."
    echo "Run 'az login' to authenticate."
    echo ""
    echo "Skipping E2E tests (Azure authentication required)."
    exit 0
fi

AZURE_USER=$(az account show --query user.name -o tsv 2>/dev/null)
AZURE_SUB=$(az account show --query name -o tsv 2>/dev/null)
echo "Authenticated as: $AZURE_USER"
echo "Subscription: $AZURE_SUB"

# Check Python virtual environment
echo ""
echo "Checking Python environment..."

if [[ -z "$VIRTUAL_ENV" ]]; then
    # Try to activate virtual environment
    if [[ -f "$PROJECT_ROOT/.venv/bin/activate" ]]; then
        echo "Activating virtual environment..."
        source "$PROJECT_ROOT/.venv/bin/activate"
    else
        echo "WARNING: No virtual environment found at $PROJECT_ROOT/.venv"
        echo "Run: uv venv && uv sync"
        exit 1
    fi
fi

PYTHON_VERSION=$(python --version 2>&1)
echo "Python: $PYTHON_VERSION"
echo "Virtual env: $VIRTUAL_ENV"

# Verify pytest-timeout is installed
if ! python -c "import pytest_timeout" 2>/dev/null; then
    echo ""
    echo "WARNING: pytest-timeout not installed."
    echo "Installing with: uv pip install pytest-timeout"
    uv pip install pytest-timeout
fi

# Run the E2E tests
echo ""
echo "============================================================"
echo "Running Developer Persona E2E tests..."
echo "============================================================"
echo ""
echo "Test file: tests/e2e/test_developer_persona_e2e.py"
echo "Arguments: $@"
echo ""

cd "$PROJECT_ROOT"

# Pass through any additional arguments to pytest
# -v: verbose output
# -s: show print statements (captures AI responses)
# --tb=short: short traceback on failures
pytest tests/e2e/test_developer_persona_e2e.py -v --tb=short -s "$@"

echo ""
echo "============================================================"
echo "E2E tests completed!"
echo "============================================================"
