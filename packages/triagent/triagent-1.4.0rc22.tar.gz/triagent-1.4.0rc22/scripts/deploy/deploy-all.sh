#!/usr/bin/env bash
#
# Full CI/CD Pipeline: Build, Push, and Deploy
#
# Usage:
#   ./deploy-all.sh --env sandbox --tag v1.5.0
#   ./deploy-all.sh --env prd --tag v1.5.0 --skip-app-service
#
# This script runs both CI and CD stages sequentially:
#   1. CI Stage: Build and push Docker images to ACR
#   2. CD Stage: Deploy to Session Pool and App Service, run health checks
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ============================================================================
# Functions
# ============================================================================
log_info() { echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $*"; }
log_error() { echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $*" >&2; }

# ============================================================================
# Main
# ============================================================================

log_info "========================================"
log_info "TRIAGENT CI/CD PIPELINE"
log_info "========================================"

# Run CI Stage
log_info "Starting CI Stage..."
if ! "${SCRIPT_DIR}/build-and-push.sh" "$@"; then
    log_error "CI Stage failed!"
    exit 1
fi

# Run CD Stage
log_info "Starting CD Stage..."
if ! "${SCRIPT_DIR}/deploy-to-azure.sh" "$@"; then
    log_error "CD Stage failed!"
    exit 1
fi

log_info "========================================"
log_info "PIPELINE COMPLETE"
log_info "========================================"
