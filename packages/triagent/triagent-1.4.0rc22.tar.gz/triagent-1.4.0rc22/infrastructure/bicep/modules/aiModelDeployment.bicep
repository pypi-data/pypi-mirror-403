// =============================================================================
// Azure AI Model Deployment
// =============================================================================
// Deploys an AI model (Claude, GPT, etc.) to an Azure AI Foundry account.
//
// Supported models:
// - Claude Opus 4.5 (Anthropic format, version 20251101)
// - Claude Sonnet 4.5 (Anthropic format, version 20250929)
// - GPT-5-pro (OpenAI format, version 2025-10-06)
//
// Resources created:
// - Microsoft.CognitiveServices/accounts/deployments
//
// Prerequisites:
// - An existing AI Foundry account (aiFoundry.bicep)
//
// Usage:
//   az-elevated deployment group create \
//     --resource-group triagent-sandbox-rg \
//     --template-file modules/aiModelDeployment.bicep \
//     --parameters aiFoundryName=triagent-ai deploymentName=claude-opus-4-5 \
//                  modelName=claude-opus-4-5 modelVersion=20251101
// =============================================================================

@description('Name of the deployment (e.g., claude-opus-4-5)')
param deploymentName string

@description('Name of the parent AI Foundry account')
param aiFoundryName string

@description('Model name (e.g., claude-opus-4-5, claude-sonnet-4-5, gpt-5-pro)')
param modelName string

@description('Model format')
@allowed(['Anthropic', 'OpenAI'])
param modelFormat string = 'Anthropic'

@description('Model version (e.g., 20251101 for Claude Opus 4.5)')
param modelVersion string

@description('Deployment SKU name')
@allowed(['GlobalStandard', 'Standard', 'ProvisionedManaged'])
param skuName string = 'GlobalStandard'

@description('Deployment capacity (tokens per minute / 1000)')
param capacity int = 2000

@description('Version upgrade option')
@allowed(['OnceNewDefaultVersionAvailable', 'OnceCurrentVersionExpired', 'NoAutoUpgrade'])
param versionUpgradeOption string = 'OnceNewDefaultVersionAvailable'

// =============================================================================
// PARENT REFERENCE
// =============================================================================

resource aiFoundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' existing = {
  name: aiFoundryName
}

// =============================================================================
// MODEL DEPLOYMENT
// =============================================================================

resource deployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: aiFoundry
  name: deploymentName
  sku: {
    name: skuName
    capacity: capacity
  }
  properties: {
    model: {
      format: modelFormat
      name: modelName
      version: modelVersion
    }
    versionUpgradeOption: versionUpgradeOption
  }
}

// =============================================================================
// OUTPUTS
// =============================================================================

@description('Resource ID of the model deployment')
output id string = deployment.id

@description('Name of the model deployment')
output name string = deployment.name

@description('Provisioning state of the deployment')
output provisioningState string = deployment.properties.provisioningState
