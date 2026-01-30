using '../main.bicep'

// =============================================================================
// SUBSCRIPTION & ENVIRONMENT IDENTIFICATION
// =============================================================================
// Subscription: US-AZSUB-AME-AA-ODATAOPENAI2-SBX
// Subscription ID: b58fef94-18c7-41ea-9d9c-424096e3321a
// Resource Group: triagent-sandbox-rg
// =============================================================================

param namingPrefix = 'triagent-sbx2'
param location = 'eastus'

// App Service
param appServiceSku = 'S1'

// Redis
param redisSku = 'Standard'

// Session Pool
param maxSessions = 100
param readyInstances = 5
param cooldownSeconds = 1800
param imageTag = 'latest'

// Registry (placeholder until ACR created)
param registryType = 'placeholder'

// Role Assignments
param enableSessionPoolRole = true

// AI Foundry - ENABLED for new subscription (fresh Claude quota)
param deployAiFoundry = true
param aiFoundryName = 'triagent-ai2'
param aiFoundryLocation = 'eastus2'
param deployClaudeOpus = true
param claudeOpusCapacity = 2000
param deployClaudeSonnet = true
param claudeSonnetCapacity = 2000
