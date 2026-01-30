using '../main.bicep'

// =============================================================================
// SUBSCRIPTION & ENVIRONMENT IDENTIFICATION
// =============================================================================
// Subscription: US-AZSUB-AME-AA-ODATAOPENAI2-SBX
// Subscription ID: b58fef94-18c7-41ea-9d9c-424096e3321a
// Resource Group: triagent-dev-rg
// =============================================================================

param namingPrefix = 'triagent-dev'
param location = 'eastus'

// App Service
param appServiceSku = 'S1'

// Redis
param redisSku = 'Basic'

// Session Pool
param maxSessions = 50
param readyInstances = 2
param cooldownSeconds = 1800
param imageTag = 'latest'

// Registry (placeholder until ACR created)
param registryType = 'placeholder'

// Role Assignments
param enableSessionPoolRole = true

// AI Foundry - disabled (share with sandbox)
param deployAiFoundry = false
param aiFoundryName = ''
param aiFoundryLocation = 'eastus2'
param deployClaudeOpus = false
param claudeOpusCapacity = 0
param deployClaudeSonnet = false
param claudeSonnetCapacity = 0
