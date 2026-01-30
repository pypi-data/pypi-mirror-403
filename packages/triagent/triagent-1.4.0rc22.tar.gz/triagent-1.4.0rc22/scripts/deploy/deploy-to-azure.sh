#!/usr/bin/env bash
#
# CD Stage: Deploy images to Azure Container Apps Session Pool and App Service
#
# Usage:
#   ./deploy-to-azure.sh --env sandbox --tag v1.5.0
#   ./deploy-to-azure.sh --env prd --tag v1.5.0 --skip-app-service
#
# Environment Variables (override via env file or CLI):
#   RESOURCE_GROUP        - Azure resource group name
#   SESSION_POOL_NAME     - Container Apps Session Pool name
#   APP_SERVICE_NAME      - App Service name (for Chainlit)
#   ACR_LOGIN_SERVER      - ACR login server
#   SUBSCRIPTION_ID       - Azure subscription ID
#

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default values
ENVIRONMENT=""
IMAGE_TAG=""
SKIP_SESSION_POOL=false
SKIP_SESSION_POOL_ENV=false
SKIP_APP_SERVICE=false
SKIP_APP_SETTINGS=false
SKIP_HEALTH_CHECKS=false
USE_CONTAINER_APP=false
DRY_RUN=false
AZ_CMD="az"  # Default Azure CLI command (use az-elevated for elevated access)
HEALTH_CHECK_TIMEOUT=120

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

Deploy Docker images to Azure Container Apps Session Pool and App Service.

Required:
  --env <environment>     Environment name (sandbox, dev, prd)
  --tag <version>         Image tag to deploy (e.g., v1.5.0)

Optional:
  --skip-session-pool     Skip Session Pool update
  --skip-session-pool-env Skip Session Pool environment variables (Foundry config)
  --skip-app-service      Skip App Service update
  --skip-app-settings     Skip App Settings configuration
  --skip-health-checks    Skip post-deployment health checks
  --use-container-app     Deploy Chainlit to Container App instead of App Service
  --az-cmd <command>      Azure CLI command (default: az, use az-elevated for elevated access)
  --dry-run               Print commands without executing
  --help                  Show this help message

Examples:
  $(basename "$0") --env sandbox --tag v1.5.0
  $(basename "$0") --env prd --tag latest --skip-app-service
  $(basename "$0") --env sandbox --tag v1.5.0 --use-container-app
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

    # Check Azure login
    if ! $AZ_CMD account show &>/dev/null; then
        log_error "Not logged in to Azure. Run: $AZ_CMD login"
        exit 1
    fi

    # Validate required variables
    for var in RESOURCE_GROUP SESSION_POOL_NAME ACR_LOGIN_SERVER SUBSCRIPTION_ID; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Required variable not set: $var"
            exit 1
        fi
    done

    $AZ_CMD account set --subscription "$SUBSCRIPTION_ID"
    log_info "Using subscription: $SUBSCRIPTION_ID"
}

update_session_pool() {
    local image="${ACR_LOGIN_SERVER}/${SESSIONS_IMAGE}:${IMAGE_TAG}"

    log_step "Updating Session Pool: $SESSION_POOL_NAME"
    log_info "New image: $image"

    if [[ "$DRY_RUN" == "true" ]]; then
        echo "DRY-RUN: $AZ_CMD containerapp sessionpool update \\"
        echo "          --name $SESSION_POOL_NAME \\"
        echo "          --resource-group $RESOURCE_GROUP \\"
        echo "          --container-image $image"
        return
    fi

    # Update session pool with new image
    $AZ_CMD containerapp sessionpool update \
        --name "$SESSION_POOL_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --image "$image" \
        --output table

    log_info "Session Pool updated successfully"

    # Get the management endpoint
    local endpoint
    endpoint=$($AZ_CMD containerapp sessionpool show \
        --name "$SESSION_POOL_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "properties.poolManagementEndpoint" -o tsv)

    log_info "Session Pool Endpoint: $endpoint"
}

configure_session_pool_env() {
    log_step "Configuring Session Pool Environment Variables"

    # Extract Foundry resource name from endpoint (e.g., usa-s-mgyg1ysp-eastus2 from https://usa-s-mgyg1ysp-eastus2.services.ai.azure.com)
    local foundry_resource=""
    if [[ -n "${AI_FOUNDRY_ENDPOINT:-}" ]]; then
        # Extract resource name: https://RESOURCE.services.ai.azure.com -> RESOURCE
        foundry_resource=$(echo "$AI_FOUNDRY_ENDPOINT" | sed -n 's|https://\([^.]*\)\.services\.ai\.azure\.com.*|\1|p')
    fi

    # Default model if not set
    local claude_model="${CLAUDE_MODEL:-claude-opus-4-5}"

    if [[ -z "$foundry_resource" ]]; then
        log_error "AI_FOUNDRY_ENDPOINT not set or invalid format. Cannot configure Foundry env vars."
        log_error "Expected format: https://RESOURCE.services.ai.azure.com"
        return 1
    fi

    log_info "Foundry Resource: $foundry_resource"
    log_info "Claude Model: $claude_model"

    if [[ "$DRY_RUN" == "true" ]]; then
        echo "DRY-RUN: $AZ_CMD containerapp sessionpool update \\"
        echo "          --name $SESSION_POOL_NAME \\"
        echo "          --resource-group $RESOURCE_GROUP \\"
        echo "          --env-vars CLAUDE_CODE_USE_FOUNDRY=1 ANTHROPIC_FOUNDRY_RESOURCE=$foundry_resource ..."
        return
    fi

    # Update session pool with Foundry environment variables
    $AZ_CMD containerapp sessionpool update \
        --name "$SESSION_POOL_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --env-vars \
            "CLAUDE_CODE_USE_FOUNDRY=1" \
            "ANTHROPIC_FOUNDRY_RESOURCE=$foundry_resource" \
            "ANTHROPIC_DEFAULT_OPUS_MODEL=$claude_model" \
            "TRIAGENT_SESSION_MODE=true" \
            "PORT=8080" \
        --output table

    log_info "Session Pool environment variables configured successfully"
    log_info "Note: New sessions will use updated env vars. Existing cached sessions may need to be recycled."
}

update_app_service() {
    local image="${ACR_LOGIN_SERVER}/${CHAINLIT_IMAGE}:${IMAGE_TAG}"

    log_step "Updating App Service: $APP_SERVICE_NAME"
    log_info "New image: $image"

    if [[ "$DRY_RUN" == "true" ]]; then
        echo "DRY-RUN: $AZ_CMD webapp config container set \\"
        echo "          --name $APP_SERVICE_NAME \\"
        echo "          --resource-group $RESOURCE_GROUP \\"
        echo "          --container-image-name $image"
        return
    fi

    # Update App Service container image
    $AZ_CMD webapp config container set \
        --name "$APP_SERVICE_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --container-image-name "$image" \
        --container-registry-url "https://${ACR_LOGIN_SERVER}"

    # Restart the app to pick up new image
    $AZ_CMD webapp restart \
        --name "$APP_SERVICE_NAME" \
        --resource-group "$RESOURCE_GROUP"

    log_info "App Service updated and restarted"

    # Get the app URL
    local url
    url=$($AZ_CMD webapp show \
        --name "$APP_SERVICE_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "defaultHostName" -o tsv)

    log_info "App Service URL: https://$url"
}

update_container_app() {
    local image="${ACR_LOGIN_SERVER}/${CHAINLIT_IMAGE}:${IMAGE_TAG}"

    log_step "Updating Container App: $CHAINLIT_CONTAINER_APP_NAME"
    log_info "New image: $image"

    if [[ "$DRY_RUN" == "true" ]]; then
        echo "DRY-RUN: $AZ_CMD containerapp update \\"
        echo "          --name $CHAINLIT_CONTAINER_APP_NAME \\"
        echo "          --resource-group $RESOURCE_GROUP \\"
        echo "          --image $image"
        return
    fi

    # Update Container App with new image
    $AZ_CMD containerapp update \
        --name "$CHAINLIT_CONTAINER_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --image "$image" \
        --output table

    log_info "Container App updated successfully"

    # Get the app URL
    local fqdn
    fqdn=$($AZ_CMD containerapp show \
        --name "$CHAINLIT_CONTAINER_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "properties.configuration.ingress.fqdn" -o tsv)

    log_info "Container App URL: https://$fqdn"
}

configure_app_settings() {
    log_step "Configuring App Service App Settings"

    # Load app settings from environment-specific file
    local appsettings_file="${SCRIPT_DIR}/environments/${ENVIRONMENT}.appsettings.env"
    if [[ ! -f "$appsettings_file" ]]; then
        log_info "App settings file not found: $appsettings_file (skipping app settings)"
        return
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        echo "DRY-RUN: Would configure app settings from $appsettings_file"
        return
    fi

    # Build app settings array from env file
    local settings_args=()
    while IFS='=' read -r key value || [[ -n "$key" ]]; do
        # Skip comments and empty lines
        [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
        # Trim whitespace
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)
        # Skip empty keys
        [[ -z "$key" ]] && continue
        # Handle variable substitution
        value=$(eval echo "$value" 2>/dev/null || echo "$value")
        settings_args+=("$key=$value")
    done < "$appsettings_file"

    # Derive dynamic settings
    local app_url
    app_url=$($AZ_CMD webapp show \
        --name "$APP_SERVICE_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "defaultHostName" -o tsv)
    settings_args+=("CHAINLIT_URL=https://$app_url")

    # Get Session Pool endpoint
    local session_pool_endpoint
    session_pool_endpoint=$($AZ_CMD containerapp sessionpool show \
        --name "$SESSION_POOL_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "properties.poolManagementEndpoint" -o tsv 2>/dev/null || echo "")

    if [[ -n "$session_pool_endpoint" ]]; then
        settings_args+=("TRIAGENT_SESSION_POOL_ENDPOINT=$session_pool_endpoint")
    fi

    # Apply settings
    log_info "Applying ${#settings_args[@]} app settings..."
    $AZ_CMD webapp config appsettings set \
        --name "$APP_SERVICE_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --settings "${settings_args[@]}" \
        --output table

    log_info "App settings configured successfully"
}

run_health_checks() {
    log_step "Running Comprehensive Health Checks"

    if [[ "$DRY_RUN" == "true" ]]; then
        echo "DRY-RUN: Would run comprehensive health checks"
        return
    fi

    local app_url
    local container_app_fqdn
    local session_pool_endpoint
    local all_checks_passed=true

    # Get Chainlit URL based on deployment target
    if [[ "$USE_CONTAINER_APP" == "true" ]] && [[ -n "${CHAINLIT_CONTAINER_APP_NAME:-}" ]]; then
        # Get Container App FQDN
        container_app_fqdn=$($AZ_CMD containerapp show \
            --name "$CHAINLIT_CONTAINER_APP_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --query "properties.configuration.ingress.fqdn" -o tsv 2>/dev/null || echo "")
    else
        # Get App Service URL
        app_url=$($AZ_CMD webapp show \
            --name "$APP_SERVICE_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --query "defaultHostName" -o tsv 2>/dev/null || echo "")
    fi

    # Get Session Pool management endpoint
    session_pool_endpoint=$($AZ_CMD containerapp sessionpool show \
        --name "$SESSION_POOL_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "properties.poolManagementEndpoint" -o tsv 2>/dev/null || echo "")

    # -------------------------------------------------------------------------
    # 1. Chainlit Health Check (Container App or App Service)
    # -------------------------------------------------------------------------
    if [[ "$USE_CONTAINER_APP" == "true" ]] && [[ -n "$container_app_fqdn" ]] && [[ "$SKIP_APP_SERVICE" != "true" ]]; then
        log_info "1. Checking Chainlit Container App health..."

        local attempts=0
        local max_attempts=$((HEALTH_CHECK_TIMEOUT / 10))

        while [[ $attempts -lt $max_attempts ]]; do
            if curl -sf "https://${container_app_fqdn}/health" &>/dev/null; then
                log_info "   ✓ Chainlit Container App health check passed"
                break
            fi
            ((attempts++))
            log_info "   Waiting for Container App... ($attempts/$max_attempts)"
            sleep 10
        done

        if [[ $attempts -eq $max_attempts ]]; then
            log_error "   ✗ Container App health check failed after ${HEALTH_CHECK_TIMEOUT}s"
            all_checks_passed=false
        fi
    elif [[ -n "$app_url" ]] && [[ "$SKIP_APP_SERVICE" != "true" ]]; then
        log_info "1. Checking Chainlit App Service health..."

        local attempts=0
        local max_attempts=$((HEALTH_CHECK_TIMEOUT / 10))

        while [[ $attempts -lt $max_attempts ]]; do
            if curl -sf "https://${app_url}/health" &>/dev/null; then
                log_info "   ✓ Chainlit App Service health check passed"
                break
            fi
            ((attempts++))
            log_info "   Waiting for App Service... ($attempts/$max_attempts)"
            sleep 10
        done

        if [[ $attempts -eq $max_attempts ]]; then
            log_error "   ✗ App Service health check failed after ${HEALTH_CHECK_TIMEOUT}s"
            all_checks_passed=false
        fi
    fi

    # -------------------------------------------------------------------------
    # 2. Sessions API Health Check
    # -------------------------------------------------------------------------
    if [[ -n "$session_pool_endpoint" ]] && [[ "$SKIP_SESSION_POOL" != "true" ]]; then
        log_info "2. Checking Sessions API health..."

        # Get access token for session pool
        local token
        token=$($AZ_CMD account get-access-token --query accessToken -o tsv 2>/dev/null || echo "")

        if [[ -n "$token" ]]; then
            local health_response
            health_response=$(curl -sf -X GET \
                "${session_pool_endpoint}/health" \
                -H "Authorization: Bearer ${token}" \
                -H "Content-Type: application/json" 2>/dev/null || echo "")

            if [[ -n "$health_response" ]]; then
                log_info "   ✓ Sessions API health endpoint responding"
            else
                log_error "   ✗ Sessions API health check failed"
                all_checks_passed=false
            fi
        else
            log_error "   ✗ Could not get access token for Sessions API"
            all_checks_passed=false
        fi
    fi

    # -------------------------------------------------------------------------
    # 3. Create Test Session & Verify Azure CLI
    # -------------------------------------------------------------------------
    if [[ -n "$session_pool_endpoint" ]] && [[ "$SKIP_SESSION_POOL" != "true" ]]; then
        log_info "3. Creating test session to verify container functionality..."

        local token
        token=$($AZ_CMD account get-access-token --query accessToken -o tsv 2>/dev/null || echo "")
        local test_session_id="health-check-$(date +%s)"

        if [[ -n "$token" ]]; then
            # Create test session and check Azure CLI version
            local create_response
            create_response=$(curl -sf -X POST \
                "${session_pool_endpoint}/code/execute?api-version=2024-02-02-preview&identifier=${test_session_id}" \
                -H "Authorization: Bearer ${token}" \
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

                # Extract Azure CLI version
                local az_version
                az_version=$(echo "$create_response" | grep -o 'azure-cli[[:space:]]*[0-9.]*' | head -1)
                log_info "   ✓ Azure CLI version: $az_version"
            else
                log_error "   ✗ Test session failed or Azure CLI not found"
                log_error "   Response: ${create_response:0:200}"
                all_checks_passed=false
            fi

            # -------------------------------------------------------------------------
            # 4. Verify Python & triagent package
            # -------------------------------------------------------------------------
            log_info "4. Verifying Python and triagent package..."

            local python_check
            python_check=$(curl -sf -X POST \
                "${session_pool_endpoint}/code/execute?api-version=2024-02-02-preview&identifier=${test_session_id}" \
                -H "Authorization: Bearer ${token}" \
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
            else
                log_error "   ✗ Python or triagent package verification failed"
                all_checks_passed=false
            fi

            # -------------------------------------------------------------------------
            # 5. Verify Sessions API endpoints
            # -------------------------------------------------------------------------
            log_info "5. Verifying Sessions API endpoints..."

            # Check /session/status endpoint (custom endpoint may not exist)
            local status_check
            status_check=$(curl -sf -X GET \
                "${session_pool_endpoint}/session/${test_session_id}/status" \
                -H "Authorization: Bearer ${token}" \
                -H "Content-Type: application/json" 2>/dev/null || echo "")

            if [[ -n "$status_check" ]]; then
                log_info "   ✓ Session status endpoint responding"
            else
                log_info "   ⚠ Session status endpoint not available (may be custom endpoint)"
            fi
        else
            log_error "   ✗ Could not get access token"
            all_checks_passed=false
        fi
    fi

    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------
    log_step "Health Check Summary"
    if [[ "$all_checks_passed" == "true" ]]; then
        log_info "All health checks passed ✓"
        return 0
    else
        log_error "Some health checks failed ✗"
        return 1
    fi
}

print_summary() {
    log_step "Deployment Summary"
    echo ""
    echo "Environment: $ENVIRONMENT"
    echo "Image Tag: $IMAGE_TAG"
    echo "Deployment Target: $(if [[ "$USE_CONTAINER_APP" == "true" ]]; then echo "Container App"; else echo "App Service"; fi)"
    echo ""
    echo "Resources Updated:"
    [[ "$SKIP_SESSION_POOL" != "true" ]] && echo "  - Session Pool: $SESSION_POOL_NAME"
    if [[ "$SKIP_APP_SERVICE" != "true" ]]; then
        if [[ "$USE_CONTAINER_APP" == "true" ]]; then
            echo "  - Container App: ${CHAINLIT_CONTAINER_APP_NAME:-N/A}"
        else
            echo "  - App Service: ${APP_SERVICE_NAME:-N/A}"
        fi
    fi
    echo ""
    echo "Images Deployed:"
    [[ "$SKIP_SESSION_POOL" != "true" ]] && echo "  - ${ACR_LOGIN_SERVER}/${SESSIONS_IMAGE}:${IMAGE_TAG}"
    [[ "$SKIP_APP_SERVICE" != "true" ]] && echo "  - ${ACR_LOGIN_SERVER}/${CHAINLIT_IMAGE}:${IMAGE_TAG}"
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
            --skip-session-pool) SKIP_SESSION_POOL=true; shift ;;
            --skip-session-pool-env) SKIP_SESSION_POOL_ENV=true; shift ;;
            --skip-app-service) SKIP_APP_SERVICE=true; shift ;;
            --skip-app-settings) SKIP_APP_SETTINGS=true; shift ;;
            --skip-health-checks) SKIP_HEALTH_CHECKS=true; shift ;;
            --use-container-app) USE_CONTAINER_APP=true; shift ;;
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
    log_info "CD Stage: Deploy to Azure"
    log_info "Environment: $ENVIRONMENT"
    log_info "Image Tag: $IMAGE_TAG"
    if [[ "$USE_CONTAINER_APP" == "true" ]]; then
        log_info "Chainlit Target: Container App"
    else
        log_info "Chainlit Target: App Service"
    fi
    log_info "============================================"

    # Execute pipeline
    load_environment
    validate_prerequisites

    # Update Session Pool
    if [[ "$SKIP_SESSION_POOL" != "true" ]]; then
        update_session_pool
        # Configure Foundry environment variables
        if [[ "$SKIP_SESSION_POOL_ENV" != "true" ]]; then
            configure_session_pool_env
        else
            log_info "Skipping Session Pool environment configuration"
        fi
    else
        log_info "Skipping Session Pool update"
    fi

    # Update Chainlit (Container App or App Service)
    if [[ "$USE_CONTAINER_APP" == "true" ]]; then
        # Deploy to Container App
        if [[ "$SKIP_APP_SERVICE" != "true" ]] && [[ -n "${CHAINLIT_CONTAINER_APP_NAME:-}" ]]; then
            update_container_app
        else
            log_info "Skipping Container App update"
        fi
    else
        # Deploy to App Service (default)
        if [[ "$SKIP_APP_SERVICE" != "true" ]] && [[ -n "${APP_SERVICE_NAME:-}" ]]; then
            update_app_service
        else
            log_info "Skipping App Service update"
        fi

        # Configure App Settings (only for App Service)
        if [[ "$SKIP_APP_SETTINGS" != "true" ]] && [[ "$SKIP_APP_SERVICE" != "true" ]] && [[ -n "${APP_SERVICE_NAME:-}" ]]; then
            configure_app_settings
        else
            log_info "Skipping App Settings configuration"
        fi
    fi

    # Run health checks
    if [[ "$SKIP_HEALTH_CHECKS" != "true" ]]; then
        run_health_checks
    else
        log_info "Skipping health checks"
    fi

    # Print summary
    print_summary

    log_step "CD Stage Complete"
}

main "$@"
