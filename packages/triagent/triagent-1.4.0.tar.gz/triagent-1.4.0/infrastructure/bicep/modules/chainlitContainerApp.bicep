@description('Naming prefix for resources')
param namingPrefix string

@description('Azure region for resources')
param location string

@description('Container Apps Environment ID')
param environmentId string

@description('Container image for Chainlit')
param containerImage string

@description('ACR login server')
param acrLoginServer string

@description('ACR username')
param acrUsername string

@description('ACR password')
@secure()
param acrPassword string

@description('User-assigned managed identity resource ID')
param managedIdentityId string

@description('Redis connection string')
param redisUrl string

@description('Redis password')
@secure()
param redisPassword string

@description('Session Pool management endpoint')
param sessionPoolEndpoint string

@description('Application Insights connection string')
param appInsightsConnectionString string

@description('OAuth Azure AD Client ID')
param oauthClientId string

@description('OAuth Azure AD Client Secret')
@secure()
param oauthClientSecret string

@description('OAuth Azure AD Tenant ID')
param oauthTenantId string

@description('Chainlit auth secret')
@secure()
param chainlitAuthSecret string

@description('Minimum replicas')
param minReplicas int = 1

@description('Maximum replicas')
param maxReplicas int = 3

@description('Request timeout in seconds (max 300 for Container Apps)')
param requestTimeoutSeconds int = 300

resource chainlitApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${namingPrefix}-chainlit'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentityId}': {}
    }
  }
  properties: {
    managedEnvironmentId: environmentId
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8080
        transport: 'http'
        allowInsecure: false
        // 5 min timeout for long-running Claude SDK requests
        // App Service S1 has 230s hard limit; Container Apps allows 300s
        requestTimeoutSeconds: requestTimeoutSeconds
      }
      registries: [
        {
          server: acrLoginServer
          username: acrUsername
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: [
        {
          name: 'acr-password'
          value: acrPassword
        }
        {
          name: 'redis-password'
          value: redisPassword
        }
        {
          name: 'oauth-client-secret'
          value: oauthClientSecret
        }
        {
          name: 'chainlit-auth-secret'
          value: chainlitAuthSecret
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'chainlit'
          image: containerImage
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
          env: [
            { name: 'WEBSITES_PORT', value: '8080' }
            { name: 'PYTHONUNBUFFERED', value: '1' }
            { name: 'TRIAGENT_SESSION_POOL_ENDPOINT', value: sessionPoolEndpoint }
            { name: 'TRIAGENT_LOCAL_MODE', value: 'false' }
            { name: 'REDIS_URL', value: redisUrl }
            { name: 'REDIS_PASSWORD', secretRef: 'redis-password' }
            { name: 'OAUTH_AZURE_AD_CLIENT_ID', value: oauthClientId }
            { name: 'OAUTH_AZURE_AD_CLIENT_SECRET', secretRef: 'oauth-client-secret' }
            { name: 'OAUTH_AZURE_AD_TENANT_ID', value: oauthTenantId }
            { name: 'OAUTH_AZURE_AD_ENABLE_SINGLE_TENANT', value: 'true' }
            { name: 'CHAINLIT_AUTH_SECRET', secretRef: 'chainlit-auth-secret' }
            { name: 'CHAINLIT_COOKIE_SAMESITE', value: 'lax' }
            { name: 'AZURE_CLIENT_ID', value: oauthClientId }
            { name: 'AZURE_TENANT_ID', value: oauthTenantId }
            { name: 'AZURE_CLIENT_SECRET', secretRef: 'oauth-client-secret' }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsightsConnectionString }
            { name: 'CHAINLIT_URL', value: 'https://triagent-sandbox-chainlit.orangemeadow-28f875d9.eastus.azurecontainerapps.io' }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: { path: '/health', port: 8080 }
              initialDelaySeconds: 30
              periodSeconds: 30
            }
            {
              type: 'Readiness'
              httpGet: { path: '/health', port: 8080 }
              initialDelaySeconds: 10
              periodSeconds: 10
            }
          ]
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http-scaling'
            http: { metadata: { concurrentRequests: '10' } }
          }
        ]
      }
    }
  }
  tags: {
    Project: 'Triagent'
    Component: 'ChainlitContainerApp'
  }
}

output fqdn string = chainlitApp.properties.configuration.ingress.fqdn
output url string = 'https://${chainlitApp.properties.configuration.ingress.fqdn}'
output appName string = chainlitApp.name
output appId string = chainlitApp.id
