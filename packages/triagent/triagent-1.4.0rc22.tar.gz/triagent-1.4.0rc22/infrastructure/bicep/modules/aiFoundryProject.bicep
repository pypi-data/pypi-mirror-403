// =============================================================================
// Azure AI Foundry Project
// =============================================================================
// Creates a project within an Azure AI Foundry account.
// Projects group related resources, deployments, and configurations for a use case.
//
// Resources created:
// - Microsoft.CognitiveServices/accounts/projects
//
// Prerequisites:
// - An existing AI Foundry account (aiFoundry.bicep)
//
// Usage:
//   az-elevated deployment group create \
//     --resource-group triagent-sandbox-rg \
//     --template-file modules/aiFoundryProject.bicep \
//     --parameters aiFoundryName=triagent-ai projectName=triagent-ai_project
// =============================================================================

@description('Name of the AI Foundry project')
param projectName string

@description('Name of the parent AI Foundry account')
param aiFoundryName string

@description('Location for the resource. Must match parent AI Foundry location.')
param location string = 'eastus2'

@description('Tags for the resource')
param tags object = {}

// =============================================================================
// PARENT REFERENCE
// =============================================================================

resource aiFoundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' existing = {
  name: aiFoundryName
}

// =============================================================================
// AI FOUNDRY PROJECT
// =============================================================================

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
  parent: aiFoundry
  name: projectName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {}
}

// =============================================================================
// OUTPUTS
// =============================================================================

@description('Resource ID of the AI Foundry project')
output id string = project.id

@description('Name of the AI Foundry project')
output name string = project.name

@description('Principal ID of the system-assigned managed identity')
output principalId string = project.identity.principalId
