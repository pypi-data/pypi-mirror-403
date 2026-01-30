// =============================================================================
// Azure AI Foundry (Cognitive Services AIServices account)
// =============================================================================
// Creates an Azure AI Services account with project management enabled.
// This is the foundation for deploying AI models like Claude and GPT.
//
// Resources created:
// - Microsoft.CognitiveServices/accounts (AIServices kind)
//
// Usage:
//   az-elevated deployment group create \
//     --resource-group triagent-sandbox-rg \
//     --template-file modules/aiFoundry.bicep \
//     --parameters name=triagent-ai
// =============================================================================

@description('Name of the AI Foundry resource')
param name string

@description('Location for the resource. Claude models require eastus2.')
param location string = 'eastus2'

@description('Tags for the resource')
param tags object = {}

@description('Enable public network access')
param publicNetworkAccess string = 'Enabled'

@description('Disable local authentication (API keys). Set to true for managed identity only.')
param disableLocalAuth bool = false

// =============================================================================
// AI FOUNDRY ACCOUNT
// =============================================================================

resource aiFoundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
  name: name
  location: location
  tags: tags
  kind: 'AIServices'
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: name
    publicNetworkAccess: publicNetworkAccess
    allowProjectManagement: true
    disableLocalAuth: disableLocalAuth
  }
}

// =============================================================================
// OUTPUTS
// =============================================================================

@description('Resource ID of the AI Foundry account')
output id string = aiFoundry.id

@description('Name of the AI Foundry account')
output name string = aiFoundry.name

@description('Endpoint URL for the AI Foundry account')
output endpoint string = aiFoundry.properties.endpoint

@description('Principal ID of the system-assigned managed identity')
output principalId string = aiFoundry.identity.principalId
