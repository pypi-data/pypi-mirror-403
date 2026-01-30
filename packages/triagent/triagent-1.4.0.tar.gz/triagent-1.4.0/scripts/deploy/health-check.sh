#!/usr/bin/env bash
#
# Standalone Health Check Script
#
# Usage:
#   ./health-check.sh --env sandbox
#   ./health-check.sh --env prd --verbose
#
# This script can be run independently to verify the health of deployed
# triagent infrastructure without performing any deployments.
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVIRONMENT=""
VERBOSE=false

# ============================================================================
# Functions
# ============================================================================
log_info() { echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $*"; }
log_error() { echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $*" >&2; }
log_debug() { [[ "$VERBOSE" == "true" ]] && echo "$(date '+%Y-%m-%d %H:%M:%S') [DEBUG] $*" || true; }
log_step() { echo ""; echo "===> $*"; }

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Run health checks against deployed triagent infrastructure.

Required:
  --env <environment>     Environment name (sandbox, dev, prd)

Optional:
  --verbose               Show detailed output
  --help                  Show this help message

Examples:
  $(basename "$0") --env sandbox
  $(basename "$0") --env prd --verbose
EOF
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --env) ENVIRONMENT="$2"; shift 2 ;;
        --verbose) VERBOSE=true; shift ;;
        --help) usage ;;
        *) log_error "Unknown option: $1"; usage ;;
    esac
done

if [[ -z "$ENVIRONMENT" ]]; then
    log_error "Missing required argument: --env"
    usage
fi

# Load environment
ENV_FILE="${SCRIPT_DIR}/environments/${ENVIRONMENT}.env"
if [[ ! -f "$ENV_FILE" ]]; then
    log_error "Environment file not found: $ENV_FILE"
    exit 1
fi

# shellcheck source=/dev/null
source "$ENV_FILE"

log_info "============================================"
log_info "Triagent Health Check - ${ENVIRONMENT^^}"
log_info "============================================"

# Check Azure login
if ! az account show &>/dev/null; then
    log_error "Not logged in to Azure. Run: az login"
    exit 1
fi

az account set --subscription "$SUBSCRIPTION_ID"

# Get endpoints
log_step "Gathering endpoint information"

SESSION_POOL_ENDPOINT=$(az containerapp sessionpool show \
    --name "$SESSION_POOL_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query "properties.poolManagementEndpoint" -o tsv 2>/dev/null || echo "")

APP_URL=$(az webapp show \
    --name "$APP_SERVICE_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query "defaultHostName" -o tsv 2>/dev/null || echo "")

echo ""
echo "Endpoints:"
echo "  Session Pool: ${SESSION_POOL_ENDPOINT:-N/A}"
echo "  App Service:  https://${APP_URL:-N/A}"
echo ""

TOKEN=$(az account get-access-token --query accessToken -o tsv)
TEST_SESSION_ID="health-$(date +%s)"

all_checks_passed=true

# -------------------------------------------------------------------------
# 1. App Service Health Check
# -------------------------------------------------------------------------
log_step "1. Checking Chainlit App Service health"

if [[ -n "$APP_URL" ]]; then
    if curl -sf "https://${APP_URL}/health" &>/dev/null; then
        log_info "   ✓ Chainlit App Service health check passed"
    else
        log_error "   ✗ Chainlit App Service health check failed"
        all_checks_passed=false
    fi
else
    log_info "   ⚠ App Service URL not available"
fi

# -------------------------------------------------------------------------
# 2. Sessions API Health Check
# -------------------------------------------------------------------------
log_step "2. Checking Sessions API health"

if [[ -n "$SESSION_POOL_ENDPOINT" ]]; then
    health_response=$(curl -sf -X GET \
        "${SESSION_POOL_ENDPOINT}/health" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" 2>/dev/null || echo "")

    if [[ -n "$health_response" ]]; then
        log_info "   ✓ Sessions API health endpoint responding"
        log_debug "   Response: $health_response"
    else
        log_error "   ✗ Sessions API health check failed"
        all_checks_passed=false
    fi
else
    log_error "   ✗ Session Pool endpoint not available"
    all_checks_passed=false
fi

# -------------------------------------------------------------------------
# 3. Create Test Session & Verify Azure CLI
# -------------------------------------------------------------------------
log_step "3. Creating test session to verify Azure CLI"

if [[ -n "$SESSION_POOL_ENDPOINT" ]]; then
    create_response=$(curl -sf -X POST \
        "${SESSION_POOL_ENDPOINT}/code/execute?api-version=2024-02-02-preview&identifier=${TEST_SESSION_ID}" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{
            "properties": {
                "codeInputType": "inline",
                "executionType": "synchronous",
                "code": "import subprocess; result = subprocess.run([\"az\", \"--version\"], capture_output=True, text=True); print(result.stdout[:200] if result.returncode == 0 else \"ERROR: \" + result.stderr)"
            }
        }' 2>/dev/null || echo "")

    if echo "$create_response" | grep -q "azure-cli"; then
        log_info "   ✓ Test session created successfully"
        log_info "   ✓ Azure CLI installed and accessible in container"

        az_version=$(echo "$create_response" | grep -o 'azure-cli[[:space:]]*[0-9.]*' | head -1)
        log_info "   ✓ Azure CLI version: $az_version"
        log_debug "   Response: $create_response"
    else
        log_error "   ✗ Test session failed or Azure CLI not found"
        log_debug "   Response: ${create_response:0:200}"
        all_checks_passed=false
    fi
else
    log_error "   ✗ Cannot create test session - no endpoint"
    all_checks_passed=false
fi

# -------------------------------------------------------------------------
# 4. Verify Python & triagent package
# -------------------------------------------------------------------------
log_step "4. Verifying Python and triagent package"

if [[ -n "$SESSION_POOL_ENDPOINT" ]]; then
    python_check=$(curl -sf -X POST \
        "${SESSION_POOL_ENDPOINT}/code/execute?api-version=2024-02-02-preview&identifier=${TEST_SESSION_ID}" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{
            "properties": {
                "codeInputType": "inline",
                "executionType": "synchronous",
                "code": "import sys; print(f\"Python {sys.version}\"); from triagent.config import ConfigManager; print(\"triagent package: OK\")"
            }
        }' 2>/dev/null || echo "")

    if echo "$python_check" | grep -q "triagent package: OK"; then
        log_info "   ✓ Python environment verified"
        log_info "   ✓ triagent package installed correctly"
        log_debug "   Response: $python_check"
    else
        log_error "   ✗ Python or triagent package verification failed"
        log_debug "   Response: ${python_check:0:200}"
        all_checks_passed=false
    fi
fi

# -------------------------------------------------------------------------
# 5. Verify Sessions API custom endpoints
# -------------------------------------------------------------------------
log_step "5. Verifying Sessions API endpoints"

if [[ -n "$SESSION_POOL_ENDPOINT" ]]; then
    status_check=$(curl -sf -X GET \
        "${SESSION_POOL_ENDPOINT}/session/${TEST_SESSION_ID}/status" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" 2>/dev/null || echo "")

    if [[ -n "$status_check" ]]; then
        log_info "   ✓ Session status endpoint responding"
        log_debug "   Response: $status_check"
    else
        log_info "   ⚠ Session status endpoint not available (may be custom endpoint)"
    fi
fi

# -------------------------------------------------------------------------
# Summary
# -------------------------------------------------------------------------
log_step "Health Check Summary"
echo ""
echo "Environment: $ENVIRONMENT"
echo "Session Pool: $SESSION_POOL_NAME"
echo "App Service: ${APP_SERVICE_NAME:-N/A}"
echo ""

if [[ "$all_checks_passed" == "true" ]]; then
    log_info "All health checks passed ✓"
    exit 0
else
    log_error "Some health checks failed ✗"
    exit 1
fi
