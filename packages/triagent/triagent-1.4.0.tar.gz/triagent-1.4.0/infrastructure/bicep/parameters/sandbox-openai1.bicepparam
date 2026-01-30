using '../main.bicep'

// Sandbox Environment Parameters
// Use with: az deployment sub create --parameters parameters/sandbox.bicepparam

param namingPrefix = 'triagent-sandbox'
param location = 'eastus'
param appServiceSku = 'S1'
param redisSku = 'Standard'
param maxSessions = 100
param readyInstances = 5
param cooldownSeconds = 1800
param imageTag = 'latest'

// Enable Session Pool role assignment (requires Owner permissions)
param enableSessionPoolRole = true

// AI Foundry settings
// Set deployAiFoundry = true to deploy Azure AI Foundry with Claude models
// Note: Quota is shared with analyzeai_poc (1000 TPM each for Claude Opus 4.5)
param deployAiFoundry = true
param aiFoundryName = 'triagent-ai'
param aiFoundryLocation = 'eastus2'
param deployClaudeOpus = true
param claudeOpusCapacity = 1000
param deployClaudeSonnet = false
param claudeSonnetCapacity = 1000
