#!/bin/bash
set -e

# =============================================================================
# Triagent Web UI - Azure Infrastructure Deployment Script
# =============================================================================
# This script deploys the Bicep templates to provision Azure infrastructure
# for the Triagent Web UI with Azure Container Apps dynamic sessions.
#
# Usage:
#   ./deploy.sh --env sandbox                  # Deploy sandbox environment
#   ./deploy.sh --env dev                      # Deploy dev environment
#   ./deploy.sh --env prd                      # Deploy production environment
#   ./deploy.sh --env sandbox --validate-only  # Validate only, no deploy
#   ./deploy.sh --env sandbox --az-cmd az      # Use standard az instead of az-elevated
#
# =============================================================================

# Configuration
ENVIRONMENT="${ENVIRONMENT:-sandbox}"
AZ_CMD="${AZ_CMD:-az-elevated}"
LOCATION="${LOCATION:-eastus}"
VALIDATE_ONLY=false
DEPLOYMENT_NAME=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}==============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}==============================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

show_usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --env <environment>      Environment to deploy (sandbox, dev, prd) [default: sandbox]"
    echo "  --subscription <id>      Azure subscription ID (overrides env file)"
    echo "  --az-cmd <command>       Azure CLI command (az or az-elevated) [default: az-elevated]"
    echo "  --validate-only          Validate templates without deploying"
    echo "  --help                   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --env sandbox                    # Deploy to sandbox"
    echo "  $0 --env sandbox --validate-only    # Validate sandbox deployment"
    echo "  $0 --env dev --az-cmd az            # Deploy dev using standard az"
    echo ""
}

# Parse arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --subscription)
                SUBSCRIPTION_ID="$2"
                shift 2
                ;;
            --az-cmd)
                AZ_CMD="$2"
                shift 2
                ;;
            --validate-only)
                VALIDATE_ONLY=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Load environment file
load_environment() {
    local SCRIPT_DIR="$(dirname "$0")"
    local ENV_FILE="${SCRIPT_DIR}/../../scripts/deploy/environments/${ENVIRONMENT}.env"

    if [[ -f "$ENV_FILE" ]]; then
        print_success "Loading environment from: ${ENVIRONMENT}.env"
        source "$ENV_FILE"
    else
        print_warning "No environment file found at: $ENV_FILE"
        print_warning "Using default values or command line arguments"
    fi

    # Check for parameter file
    PARAM_FILE="${SCRIPT_DIR}/parameters/${ENVIRONMENT}.bicepparam"
    if [[ ! -f "$PARAM_FILE" ]]; then
        print_error "Parameter file not found: $PARAM_FILE"
        echo "Available parameter files:"
        ls -1 "${SCRIPT_DIR}/parameters/"*.bicepparam 2>/dev/null || echo "  None found"
        exit 1
    fi
    print_success "Using parameter file: ${ENVIRONMENT}.bicepparam"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check Azure CLI command
    if ! command -v $AZ_CMD &> /dev/null; then
        if [[ "$AZ_CMD" == "az-elevated" ]]; then
            print_warning "az-elevated not found, falling back to standard az"
            AZ_CMD="az"
        fi
        if ! command -v $AZ_CMD &> /dev/null; then
            print_error "Azure CLI is not installed. Please install it first."
            exit 1
        fi
    fi
    print_success "Using Azure CLI: $AZ_CMD"

    # Check if logged in
    if ! $AZ_CMD account show &> /dev/null; then
        print_error "Not logged in to Azure. Please run '$AZ_CMD login' first."
        exit 1
    fi
    print_success "Logged in to Azure"

    # Check Bicep
    if ! $AZ_CMD bicep version &> /dev/null; then
        print_warning "Bicep CLI not found. Installing..."
        $AZ_CMD bicep install
    fi
    print_success "Bicep CLI is available"
}

# Set subscription
set_subscription() {
    print_header "Setting Subscription"

    # Use subscription from environment file or command line
    if [[ -n "$SUBSCRIPTION_ID" ]]; then
        $AZ_CMD account set --subscription "$SUBSCRIPTION_ID"
        print_success "Set subscription: $SUBSCRIPTION_ID"
    fi

    # Show current subscription
    local CURRENT_SUB=$($AZ_CMD account show --query "{name:name, id:id}" -o json)
    local SUB_NAME=$(echo "$CURRENT_SUB" | grep -o '"name": *"[^"]*"' | cut -d'"' -f4)
    local SUB_ID=$(echo "$CURRENT_SUB" | grep -o '"id": *"[^"]*"' | cut -d'"' -f4)

    echo "Current subscription:"
    echo "  Name: $SUB_NAME"
    echo "  ID:   $SUB_ID"

    # Verify subscription matches environment
    if [[ -n "${SUBSCRIPTION_NAME:-}" ]] && [[ "$SUB_NAME" != *"$SUBSCRIPTION_NAME"* ]]; then
        print_warning "Active subscription doesn't match expected: $SUBSCRIPTION_NAME"
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Validate templates
validate_templates() {
    print_header "Validating Bicep Templates"

    local SCRIPT_DIR="$(dirname "$0")"

    $AZ_CMD deployment sub validate \
        --location "$LOCATION" \
        --template-file "${SCRIPT_DIR}/main.bicep" \
        --parameters "${SCRIPT_DIR}/parameters/${ENVIRONMENT}.bicepparam" \
        --output none

    print_success "Bicep templates are valid"
}

# Deploy infrastructure
deploy_infrastructure() {
    print_header "Deploying Infrastructure"

    local SCRIPT_DIR="$(dirname "$0")"
    DEPLOYMENT_NAME="triagent-${ENVIRONMENT}-$(date +%Y%m%d%H%M%S)"

    echo "Deployment settings:"
    echo "  - Environment: $ENVIRONMENT"
    echo "  - Location: $LOCATION"
    echo "  - Parameter File: ${ENVIRONMENT}.bicepparam"
    echo "  - Deployment Name: $DEPLOYMENT_NAME"
    echo "  - Azure CLI: $AZ_CMD"
    echo ""

    $AZ_CMD deployment sub create \
        --name "$DEPLOYMENT_NAME" \
        --location "$LOCATION" \
        --template-file "${SCRIPT_DIR}/main.bicep" \
        --parameters "${SCRIPT_DIR}/parameters/${ENVIRONMENT}.bicepparam" \
        --verbose

    print_success "Infrastructure deployed successfully"
}

# Get deployment outputs
get_outputs() {
    print_header "Deployment Outputs"

    if [[ -z "$DEPLOYMENT_NAME" ]]; then
        print_warning "No deployment name available, skipping outputs"
        return
    fi

    local RG_NAME=$($AZ_CMD deployment sub show --name "$DEPLOYMENT_NAME" --query 'properties.outputs.resourceGroupName.value' -o tsv 2>/dev/null || echo "N/A")
    local ACR_LOGIN_SERVER=$($AZ_CMD deployment sub show --name "$DEPLOYMENT_NAME" --query 'properties.outputs.acrLoginServer.value' -o tsv 2>/dev/null || echo "N/A")
    local APP_URL=$($AZ_CMD deployment sub show --name "$DEPLOYMENT_NAME" --query 'properties.outputs.appServiceUrl.value' -o tsv 2>/dev/null || echo "N/A")
    local SESSION_POOL_ENDPOINT=$($AZ_CMD deployment sub show --name "$DEPLOYMENT_NAME" --query 'properties.outputs.sessionPoolEndpoint.value' -o tsv 2>/dev/null || echo "N/A")
    local REDIS_HOSTNAME=$($AZ_CMD deployment sub show --name "$DEPLOYMENT_NAME" --query 'properties.outputs.redisHostname.value' -o tsv 2>/dev/null || echo "N/A")
    local AI_FOUNDRY_ENDPOINT=$($AZ_CMD deployment sub show --name "$DEPLOYMENT_NAME" --query 'properties.outputs.aiFoundryEndpoint.value' -o tsv 2>/dev/null || echo "N/A")

    echo ""
    echo "Resource Group:        $RG_NAME"
    echo "ACR Login Server:      $ACR_LOGIN_SERVER"
    echo "App Service URL:       $APP_URL"
    echo "Session Pool Endpoint: $SESSION_POOL_ENDPOINT"
    echo "Redis Hostname:        $REDIS_HOSTNAME"
    if [[ "$AI_FOUNDRY_ENDPOINT" != "N/A" ]] && [[ -n "$AI_FOUNDRY_ENDPOINT" ]]; then
        echo "AI Foundry Endpoint:   $AI_FOUNDRY_ENDPOINT"
    fi
    echo ""
}

# Print next steps
print_next_steps() {
    print_header "Next Steps"

    echo "1. Build and push the session container image:"
    echo ""
    echo "   ./scripts/deploy/build-and-push.sh --env $ENVIRONMENT --tag latest --az-cmd $AZ_CMD"
    echo ""
    echo "2. Deploy containers to Azure:"
    echo ""
    echo "   ./scripts/deploy/deploy-to-azure.sh --env $ENVIRONMENT --tag latest --az-cmd $AZ_CMD"
    echo ""
    echo "3. Or run the full pipeline:"
    echo ""
    echo "   ./scripts/deploy/deploy-all.sh --env $ENVIRONMENT --tag latest --az-cmd $AZ_CMD"
    echo ""
}

# Main execution
main() {
    print_header "Triagent Web UI - Azure Infrastructure Deployment"

    # Change to script directory
    cd "$(dirname "$0")"

    parse_args "$@"
    load_environment
    check_prerequisites
    set_subscription

    if [[ "$VALIDATE_ONLY" == true ]]; then
        validate_templates
        print_success "Validation complete!"
    else
        validate_templates
        deploy_infrastructure
        get_outputs
        print_next_steps
        print_success "Deployment complete!"
    fi
}

# Run main function
main "$@"
