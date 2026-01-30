using '../main.bicep'

// =============================================================================
// SUBSCRIPTION & ENVIRONMENT IDENTIFICATION
// =============================================================================
// Subscription: (TBD - Production subscription)
// Subscription ID: (TBD)
// Resource Group: triagent-prd-rg
// =============================================================================

param namingPrefix = 'triagent-prd'
param location = 'eastus'

// App Service
param appServiceSku = 'P1v3'

// Redis
param redisSku = 'Premium'

// Session Pool
param maxSessions = 500
param readyInstances = 10
param cooldownSeconds = 3600
param imageTag = 'stable'

// Registry (use ACR for production)
param registryType = 'acr'

// Role Assignments
param enableSessionPoolRole = true

// AI Foundry - separate production instance
param deployAiFoundry = true
param aiFoundryName = 'triagent-prd-ai'
param aiFoundryLocation = 'eastus2'
param deployClaudeOpus = true
param claudeOpusCapacity = 2000
param deployClaudeSonnet = true
param claudeSonnetCapacity = 2000
