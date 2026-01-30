#!/usr/bin/env bash
#
# CI Stage: Build Docker images and push to Azure Container Registry
#
# Usage:
#   ./build-and-push.sh --env sandbox --tag v1.5.0
#   ./build-and-push.sh --env prd --tag v1.5.0 --skip-chainlit
#
# Environment Variables (override via env file or CLI):
#   ACR_NAME            - Azure Container Registry name
#   ACR_LOGIN_SERVER    - ACR login server (e.g., triagentsandboxacr.azurecr.io)
#   SUBSCRIPTION_ID     - Azure subscription ID
#

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Default values
ENVIRONMENT=""
IMAGE_TAG=""
SKIP_CHAINLIT=false
SKIP_SESSIONS=false
DRY_RUN=false
AZ_CMD="az"  # Default Azure CLI command (use az-elevated for elevated access)

# Image names
CHAINLIT_IMAGE="triagent-chainlit"
SESSIONS_IMAGE="triagent-sessions"

# ============================================================================
# Functions
# ============================================================================
log_info() { echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $*"; }
log_error() { echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $*" >&2; }
log_step() { echo ""; echo "===> $*"; }

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Build and push Docker images to Azure Container Registry.

Required:
  --env <environment>     Environment name (sandbox, dev, prd)
  --tag <version>         Image tag (e.g., v1.5.0, latest)

Optional:
  --skip-chainlit         Skip building Chainlit image
  --skip-sessions         Skip building Sessions API image
  --az-cmd <command>      Azure CLI command (default: az, use az-elevated for elevated access)
  --dry-run               Print commands without executing
  --help                  Show this help message

Examples:
  $(basename "$0") --env sandbox --tag v1.5.0
  $(basename "$0") --env prd --tag latest --skip-chainlit
EOF
    exit 0
}

load_environment() {
    local env_file="${SCRIPT_DIR}/environments/${ENVIRONMENT}.env"
    if [[ -f "$env_file" ]]; then
        log_info "Loading environment from $env_file"
        # shellcheck source=/dev/null
        source "$env_file"
    else
        log_error "Environment file not found: $env_file"
        exit 1
    fi
}

validate_prerequisites() {
    log_step "Validating prerequisites"

    # Check required tools
    for cmd in "$AZ_CMD" docker; do
        if ! command -v "$cmd" &>/dev/null; then
            log_error "Required command not found: $cmd"
            exit 1
        fi
    done

    # Check Azure login
    if ! $AZ_CMD account show &>/dev/null; then
        log_error "Not logged in to Azure. Run: $AZ_CMD login"
        exit 1
    fi

    # Validate required variables
    for var in ACR_NAME ACR_LOGIN_SERVER SUBSCRIPTION_ID; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Required variable not set: $var"
            exit 1
        fi
    done

    log_info "All prerequisites validated"
}

login_to_acr() {
    log_step "Logging in to Azure Container Registry"

    if [[ "$DRY_RUN" == "true" ]]; then
        echo "DRY-RUN: $AZ_CMD acr login --name $ACR_NAME"
        return
    fi

    $AZ_CMD account set --subscription "$SUBSCRIPTION_ID"
    $AZ_CMD acr login --name "$ACR_NAME"
    log_info "Logged in to $ACR_LOGIN_SERVER"
}

build_image() {
    local dockerfile="$1"
    local image_name="$2"
    local full_tag="${ACR_LOGIN_SERVER}/${image_name}:${IMAGE_TAG}"
    local latest_tag="${ACR_LOGIN_SERVER}/${image_name}:latest"

    log_step "Building ${image_name} from ${dockerfile}"

    if [[ "$DRY_RUN" == "true" ]]; then
        echo "DRY-RUN: docker build --platform linux/amd64 -f $dockerfile -t $full_tag -t $latest_tag $PROJECT_ROOT"
        return
    fi

    docker build \
        --no-cache \
        --platform linux/amd64 \
        -f "${PROJECT_ROOT}/${dockerfile}" \
        -t "$full_tag" \
        -t "$latest_tag" \
        "$PROJECT_ROOT"

    log_info "Built: $full_tag"
}

push_image() {
    local image_name="$1"
    local full_tag="${ACR_LOGIN_SERVER}/${image_name}:${IMAGE_TAG}"
    local latest_tag="${ACR_LOGIN_SERVER}/${image_name}:latest"

    log_step "Pushing ${image_name} to ACR"

    if [[ "$DRY_RUN" == "true" ]]; then
        echo "DRY-RUN: docker push $full_tag"
        echo "DRY-RUN: docker push $latest_tag"
        return
    fi

    docker push "$full_tag"
    docker push "$latest_tag"

    log_info "Pushed: $full_tag"
    log_info "Pushed: $latest_tag"
}

# ============================================================================
# Main
# ============================================================================
main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --env) ENVIRONMENT="$2"; shift 2 ;;
            --tag) IMAGE_TAG="$2"; shift 2 ;;
            --skip-chainlit) SKIP_CHAINLIT=true; shift ;;
            --skip-sessions) SKIP_SESSIONS=true; shift ;;
            --az-cmd) AZ_CMD="$2"; shift 2 ;;
            --dry-run) DRY_RUN=true; shift ;;
            --help) usage ;;
            *) log_error "Unknown option: $1"; usage ;;
        esac
    done

    # Validate required arguments
    if [[ -z "$ENVIRONMENT" ]]; then
        log_error "Missing required argument: --env"
        usage
    fi
    if [[ -z "$IMAGE_TAG" ]]; then
        log_error "Missing required argument: --tag"
        usage
    fi

    log_info "============================================"
    log_info "CI Stage: Build and Push"
    log_info "Environment: $ENVIRONMENT"
    log_info "Image Tag: $IMAGE_TAG"
    log_info "============================================"

    # Execute pipeline
    load_environment
    validate_prerequisites
    login_to_acr

    # Build and push Chainlit image
    if [[ "$SKIP_CHAINLIT" != "true" ]]; then
        build_image "Dockerfile.chainlit" "$CHAINLIT_IMAGE"
        push_image "$CHAINLIT_IMAGE"
    else
        log_info "Skipping Chainlit image"
    fi

    # Build and push Sessions API image
    if [[ "$SKIP_SESSIONS" != "true" ]]; then
        build_image "Dockerfile.sessions" "$SESSIONS_IMAGE"
        push_image "$SESSIONS_IMAGE"
    else
        log_info "Skipping Sessions API image"
    fi

    log_step "CI Stage Complete"
    echo ""
    echo "Images pushed to ACR:"
    [[ "$SKIP_CHAINLIT" != "true" ]] && echo "  - ${ACR_LOGIN_SERVER}/${CHAINLIT_IMAGE}:${IMAGE_TAG}"
    [[ "$SKIP_SESSIONS" != "true" ]] && echo "  - ${ACR_LOGIN_SERVER}/${SESSIONS_IMAGE}:${IMAGE_TAG}"
}

main "$@"
