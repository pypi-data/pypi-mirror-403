# Chainlit Integration - Session Persistence Implementation

**Document Version:** 1.2
**Last Updated:** 2026-01-11
**Prepared by:** Santosh Dandey
**Branch:** `feature/sandbox-module-v2`

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Option Analysis](#2-option-analysis)
3. [Selected Approach](#3-selected-approach)
4. [Architecture Overview](#4-architecture-overview)
5. [Session State Schema](#5-session-state-schema)
6. [Sequence Diagrams](#6-sequence-diagrams)
7. [Implementation Tasks](#7-implementation-tasks)
8. [API Reference](#8-api-reference)
9. [Testing Strategy](#9-testing-strategy)
10. [Verification Checklist](#10-verification-checklist)
11. [Document History](#11-document-history)

---

## 1. Executive Summary

### 1.1 Problem Statement

When users refresh their browser while using the Triagent Chainlit UI, they lose their session state and must:
1. Re-select team, persona, and model in the configuration modal
2. Re-authenticate via Azure device code flow
3. Wait for SDK re-initialization

This creates a poor user experience, especially for users who accidentally refresh or whose browser auto-refreshes.

### 1.2 Solution

Implement **Server-Side Session Cache with Health Check** to enable seamless session recovery:
- Store preferences in existing session file (`~/.triagent/session.json`)
- Add health check before session resume to detect stale/recycled containers
- Skip config modal if session is healthy and preferences are available

### 1.3 Key Benefits

| Benefit | Description |
|---------|-------------|
| **Seamless Refresh** | Users can refresh browser without losing session |
| **No Re-auth** | Skip Azure device code flow if container still alive |
| **Preferences Restored** | Team, persona, model pre-filled even if re-auth needed |
| **Simple MVP** | No Redis, no browser JavaScript, works within Chainlit constraints |

---

## 2. Option Analysis

### 2.1 Options Evaluated

| Option | Description | Pros | Cons | MVP Suitable |
|--------|-------------|------|------|--------------|
| **A. Server-Side Session Cache** | Store session state in container file, keyed by deterministic user hash | No browser JS needed, works within Chainlit constraints, simple implementation | Lost on container recycle | **Selected** |
| **B. Browser LocalStorage** | Custom JS stores session in browser localStorage | Persists across container recycles (preferences only) | Chainlit doesn't expose HTTP request in callbacks, complex JS-to-Python bridging | Complex |
| **C. Redis Cache** | Centralized session storage in Azure Redis | Survives everything, cross-device support | Additional infrastructure, more code | Future enhancement |
| **D. Chainlit Data Layer** | Use Chainlit's built-in persistence | Native Chainlit pattern | Requires database setup, overkill for MVP | Overkill |

### 2.2 Technical Constraints

**Challenge**: Chainlit doesn't expose HTTP request in callbacks, making it difficult to read browser localStorage directly from Python.

**Solution**: Use server-side session storage instead of browser localStorage. The deterministic session_id (from username hash) already provides user-specific storage.

### 2.3 Accepted Trade-offs

| What Works | What Doesn't |
|------------|--------------|
| Session persists on browser refresh | Session lost on container recycle |
| Preferences restored from session file | Azure CLI auth must re-authenticate after container recycle |
| No additional infrastructure needed | No cross-device session sharing |
| Works within Chainlit constraints | Conversation history lost with container |

---

## 3. Selected Approach

### 3.1 Server-Side Session Cache with Health Check

**Key Insight**: The deterministic session_id (SHA256 hash of username) already provides user-specific storage. We leverage this to:

1. **Store preferences in existing session file** (`~/.triagent/session.json`)
2. **Add health check before session resume** to detect stale/recycled containers
3. **Skip config modal if session is healthy** and preferences are available

### 3.2 How It Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SESSION PERSISTENCE FLOW                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Browser Refresh                                                            │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  1. Generate deterministic session_id = SHA256(username)[:16]       │   │
│  │     (Same user always gets same session_id)                         │   │
│  └──────────────────────────────┬──────────────────────────────────────┘   │
│                                 │                                           │
│                                 ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  2. Call health_check(session_id) via SessionProxy                  │   │
│  │     - Checks Azure CLI auth status                                  │   │
│  │     - Checks session file exists and is initialized                 │   │
│  │     - Returns stored preferences (team, persona, model)             │   │
│  └──────────────────────────────┬──────────────────────────────────────┘   │
│                                 │                                           │
│                    ┌────────────┴────────────┐                              │
│                    │                         │                              │
│                    ▼                         ▼                              │
│  ┌─────────────────────────────┐  ┌─────────────────────────────────────┐  │
│  │  BRANCH A: Session Healthy  │  │  BRANCH B/C: Session Unhealthy      │  │
│  │                             │  │                                     │  │
│  │  - Skip config modal        │  │  - Show config modal                │  │
│  │  - Restore preferences      │  │  - Pre-fill with stored prefs       │  │
│  │  - Show "Session Resumed"   │  │  - Run auth flow                    │  │
│  │  - Ready for chat           │  │  - Save new session                 │  │
│  └─────────────────────────────┘  └─────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Session Persistence Behavior Matrix

| Scenario | Container State | Azure Auth | Session File | Behavior |
|----------|-----------------|------------|--------------|----------|
| First visit | New | None | None | Full flow: config → auth → init |
| Refresh (healthy) | Same | Valid | Exists | Skip config, resume immediately |
| Refresh (auth expired) | Same | Expired | Exists | Config pre-filled, re-auth needed |
| Refresh (container recycled) | New | None | None | Full flow (no stored prefs) |
| Different browser | Same* | Valid | Exists | Skip config, resume immediately |
| Different user | New | None | None | Full flow (different session_id) |

*Same container because deterministic session_id maps to same Azure Dynamic Sessions identifier

---

## 4. Architecture Overview

### 4.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SESSION PERSISTENCE ARCHITECTURE                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  CLIENT LAYER (Browser)                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  Chainlit WebSocket Client                                           │   │
│  │  - Receives messages from server                                     │   │
│  │  - No direct session storage (handled server-side)                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ WebSocket
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CHAINLIT CONTAINER (:8080)                                                 │
│  Image: triagent-chainlit:v4                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────────┐ │
│  │ chainlit_app.py    │  │ session_manager.py │  │ session_proxy.py       │ │
│  │                    │  │                    │  │                        │ │
│  │ • on_chat_start()  │─▶│ • generate_id()    │─▶│ • health_check()       │ │
│  │ • on_message()     │  │ • health_check()   │  │ • execute_code()       │ │
│  │ • show_config()    │  │ • init_session()   │  │ • stream_response()    │ │
│  │ • handle_refresh() │  │ • chat()           │  │ • get_access_token()   │ │
│  └────────────────────┘  └────────────────────┘  └──────────┬─────────────┘ │
│                                                             │               │
│  ┌──────────────────────────────────────────────────────────┼───────────────┐
│  │ MSAL Client Credentials (App-Level Auth)                 │               │
│  │                                                          ▼               │
│  │  ConfidentialClientApplication                                           │
│  │    • client_id: OAUTH_AZURE_AD_CLIENT_ID                                 │
│  │    • client_secret: OAUTH_AZURE_AD_CLIENT_SECRET                         │
│  │    • authority: login.microsoftonline.com/{tenant}                       │
│  │    • scope: https://dynamicsessions.io/.default                          │
│  └──────────────────────────────────────────────────────────────────────────┘
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────────┐
│  │ cl.user_session (in-memory, lost on browser refresh)                     │
│  │   - session_id: "abc123def456..."                                        │
│  │   - team: "omnia-data"                                                   │
│  │   - persona: "developer"                                                 │
│  │   - model: "claude-opus-4-5"                                             │
│  │   - session_manager: ChainlitSessionManager()                            │
│  └──────────────────────────────────────────────────────────────────────────┘
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP POST /code/execute
                                    │ (identifier=session_id)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  AZURE DYNAMIC SESSIONS CONTAINER (:8080)                                   │
│  Image: triagent-sessions:v4                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────────┐ │
│  │ /code/execute      │  │ runner.py          │  │ session_store.py       │ │
│  │ (Azure DS API)     │  │                    │  │                        │ │
│  │                    │─▶│ • run_health_check │─▶│ • load()               │ │
│  │ Executes Python    │  │ • run_check_auth   │  │ • save()               │ │
│  │ code and returns   │  │ • run_init_sdk     │  │ • update()             │ │
│  │ stdout/stderr      │  │ • run_chat         │  │ • clear()              │ │
│  └────────────────────┘  └────────────────────┘  └────────────────────────┘ │
│                                                            │                │
│  ┌─────────────────────────────────────────────────────────┘                │
│  │ ~/.triagent/session.json (persists while container alive)                │
│  │                                                                          │
│  │   {                                                                      │
│  │     "session_id": "934a699a-4fc4-4146-9ce2-473d2fef0b13",               │
│  │     "team": "omnia-data",                                                │
│  │     "persona": "developer",                                              │
│  │     "model": "claude-opus-4-5",                                          │
│  │     "initialized": true,                                                 │
│  │     "conversation_turns": 5,                                             │
│  │     "last_active": 1736621234.567,                                       │
│  │     "azure_user": "sdandey@deloitte.com",                                │
│  │     "metadata": {}                                                       │
│  │   }                                                                      │
│  │                                                                          │
│  └──────────────────────────────────────────────────────────────────────────┘
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────────┐
│  │ ~/.azure/ (Azure CLI token cache) - Used inside Sessions container      │
│  │   - msal_token_cache.json (OAuth tokens from az login)                   │
│  │   - azureProfile.json (subscription info)                                │
│  └──────────────────────────────────────────────────────────────────────────┘
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ MSAL Client Credentials
                                    │ (acquire_token_for_client)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  AZURE AUTHENTICATION (MSAL)                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ MSAL Token Flow for Dynamic Sessions                                   │ │
│  │                                                                        │ │
│  │  SessionProxy.get_access_token()                                       │ │
│  │       │                                                                │ │
│  │       ▼                                                                │ │
│  │  ConfidentialClientApplication.acquire_token_for_client(               │ │
│  │      scopes=["https://dynamicsessions.io/.default"]                    │ │
│  │  )                                                                     │ │
│  │       │                                                                │ │
│  │       ▼                                                                │ │
│  │  login.microsoftonline.com/{tenant}/oauth2/v2.0/token                  │ │
│  │       │                                                                │ │
│  │       ▼                                                                │ │
│  │  Bearer Token → Authorization header for /code/execute                 │ │
│  │                                                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Bearer Token
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  EXTERNAL SERVICES                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────────────────┐  ┌────────────────────────────────────┐ │
│  │ Azure Dynamic Sessions         │  │ Azure AI Foundry                   │ │
│  │                                │  │                                    │ │
│  │ Session Pool Endpoint:         │  │ Claude API Endpoint:               │ │
│  │ triagent-sandbox-session-pool  │  │ usa-s-mgyg1ysp-eastus2            │ │
│  │ .orangemeadow-28f875d9        │  │ .services.ai.azure.com            │ │
│  │ .eastus.azurecontainerapps.io │  │                                    │ │
│  │                                │  │ Models:                            │ │
│  │ Auth: Bearer token from MSAL   │  │ • claude-opus-4-5                  │ │
│  │ Scope: dynamicsessions.io      │  │ • claude-sonnet-4                  │ │
│  └────────────────────────────────┘  └────────────────────────────────────┘ │
│                                                                             │
│  ┌────────────────────────────────┐                                         │
│  │ Azure DevOps                   │                                         │
│  │                                │                                         │
│  │ ADO REST API:                  │                                         │
│  │ dev.azure.com/symphonyvsts     │                                         │
│  │                                │                                         │
│  │ MCP Server:                    │                                         │
│  │ @anthropic/mcp-azure-devops    │                                         │
│  └────────────────────────────────┘                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Component Responsibilities

| Component | File | Responsibilities |
|-----------|------|------------------|
| **Chainlit App** | `src/triagent/web/container/chainlit_app.py` | Handle chat lifecycle, show modals, manage UI state |
| **Session Manager** | `src/triagent/web/container/session_manager.py` | Generate session IDs, coordinate health checks, manage session lifecycle |
| **Session Proxy** | `src/triagent/web/services/session_proxy.py` | Bridge to Azure Dynamic Sessions via /code/execute (health checks included) |
| **Runner** | `src/triagent/sandbox/runner.py` | Execute health check, auth check, SDK init, and chat operations via /code/execute |
| **Session Store** | `src/triagent/sandbox/session_store.py` | Persist and retrieve session state from JSON file |

> **Note**: Azure Dynamic Sessions only exposes `/code/execute`. Health checks are performed by executing `run_health_check()` code, not via a separate HTTP endpoint.

### 4.3 MSAL Authentication for Dynamic Sessions

The Chainlit container uses **MSAL (Microsoft Authentication Library) Client Credentials Flow** to authenticate with Azure Dynamic Sessions. This eliminates the need for Azure CLI on the host machine.

#### 4.3.1 Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  MSAL CLIENT CREDENTIALS FLOW                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────┐      ┌───────────────────────────────────────┐   │
│  │ SessionProxy         │      │ Azure AD (login.microsoftonline.com)  │   │
│  │                      │      │                                       │   │
│  │  get_access_token()  │      │  /oauth2/v2.0/token                   │   │
│  └──────────┬───────────┘      └───────────────────┬───────────────────┘   │
│             │                                      │                        │
│             │  1. Request token                    │                        │
│             │     client_id + client_secret        │                        │
│             │     scope: dynamicsessions.io        │                        │
│             ├─────────────────────────────────────▶│                        │
│             │                                      │                        │
│             │  2. Validate credentials             │                        │
│             │     Check app registration           │                        │
│             │     Verify API permissions           │                        │
│             │                                      │                        │
│             │  3. Return access token              │                        │
│             │◀─────────────────────────────────────┤                        │
│             │                                      │                        │
│             │  4. Use token in Authorization       │                        │
│             │     header for /code/execute         │                        │
│             ▼                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  POST /code/execute                                                   │  │
│  │  Authorization: Bearer {access_token}                                 │  │
│  │  Identifier: {session_id}                                             │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 4.3.2 Configuration Requirements

| Environment Variable | Description | Source |
|---------------------|-------------|--------|
| `OAUTH_AZURE_AD_CLIENT_ID` | Azure AD App Registration Client ID | docker-compose.local.yml |
| `OAUTH_AZURE_AD_CLIENT_SECRET` | Azure AD App Registration Secret | docker-compose.local.yml |
| `AZURE_TENANT_ID` | Azure AD Tenant ID | docker-compose.local.yml |

#### 4.3.3 Azure AD App Registration Requirements

The Azure AD App Registration must have:

1. **API Permission**: `https://dynamicsessions.io/.default` (Application permission, not Delegated)
2. **Admin Consent**: Granted for the Dynamic Sessions permission
3. **Client Secret**: Valid, non-expired secret

#### 4.3.4 Why MSAL Instead of DefaultAzureCredential?

| Aspect | DefaultAzureCredential (Old) | MSAL Client Credentials (New) |
|--------|------------------------------|-------------------------------|
| **Host Dependency** | Requires Azure CLI login on host | No host setup required |
| **Container Mount** | Needs `~/.azure` volume mount | No volume mount needed |
| **Authentication** | User-level (az login) | App-level (service principal) |
| **Token Scope** | General Azure resources | Specific: `dynamicsessions.io` |
| **Error Handling** | Chain of credential attempts | Single, deterministic method |

---

## 5. Session State Schema

### 5.1 SessionState Dataclass

```python
@dataclass
class SessionState:
    """Session state persisted to file.

    Attributes:
        session_id: Claude session ID for resumption
        team: Team profile (e.g., "omnia-data")
        persona: Persona profile (e.g., "developer", "support")
        model: Claude model to use (e.g., "claude-opus-4-5")
        initialized: Whether SDK has been initialized
        conversation_turns: Number of conversation turns
        last_active: Timestamp of last activity (Unix epoch)
        azure_user: Authenticated Azure user email
        metadata: Additional session metadata
    """

    session_id: str
    team: str = "omnia-data"
    persona: str = "developer"
    model: str = "claude-opus-4-5"
    initialized: bool = False
    conversation_turns: int = 0
    last_active: float = 0.0
    azure_user: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
```

### 5.2 JSON File Format

**Location**: `~/.triagent/session.json`

```json
{
  "session_id": "934a699a-4fc4-4146-9ce2-473d2fef0b13",
  "team": "omnia-data",
  "persona": "developer",
  "model": "claude-opus-4-5",
  "initialized": true,
  "conversation_turns": 5,
  "last_active": 1736621234.567,
  "azure_user": "sdandey@deloitte.com",
  "metadata": {}
}
```

### 5.3 Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | Claude SDK session ID for conversation resumption |
| `team` | string | Selected team profile (omnia-data, omnia, levvia) |
| `persona` | string | Selected persona (developer, support) |
| `model` | string | Claude model (claude-opus-4-5, claude-sonnet-4) |
| `initialized` | boolean | Whether SDK has been successfully initialized |
| `conversation_turns` | integer | Number of chat turns in current session |
| `last_active` | float | Unix timestamp of last activity |
| `azure_user` | string | Authenticated user's email address |
| `metadata` | object | Reserved for future extensibility |

---

## 6. Sequence Diagrams

> **Diagram Format**: All sequence diagrams use Mermaid with colored component boundaries matching [web-ui-architecture.md](./web-ui-architecture.md).

### 6.0 User Login and MSAL Token Acquisition

This diagram shows the complete authentication flow from user login through MSAL token acquisition for Azure Dynamic Sessions.

```mermaid
sequenceDiagram
    autonumber

    box rgb(33, 150, 243) Client
        participant User
        participant Browser
    end

    box rgb(76, 175, 80) Chainlit Container
        participant Chainlit as chainlit_app.py
        participant Proxy as SessionProxy
        participant MSAL as ConfidentialClientApplication
    end

    box rgb(156, 39, 176) Azure AD
        participant AzureAD as login.microsoftonline.com
    end

    box rgb(255, 152, 0) Azure Dynamic Sessions
        participant Sessions as Session Pool
    end

    Note over User,Sessions: PHASE 1: User OAuth Login

    User->>Browser: Navigate to app URL
    Browser->>Chainlit: GET /
    Chainlit->>Browser: Redirect to Azure AD OAuth
    Browser->>AzureAD: OAuth Authorization Request
    Note over AzureAD: User authenticates with Azure AD credentials
    AzureAD-->>Browser: Authorization code
    Browser->>Chainlit: Callback with auth code
    Chainlit->>AzureAD: Exchange code for ID token
    AzureAD-->>Chainlit: ID token + user info
    Chainlit->>Chainlit: Create cl.User from token
    Note over Chainlit: User is now logged into Chainlit UI

    Note over User,Sessions: PHASE 2: MSAL Token for Dynamic Sessions

    Chainlit->>Proxy: health_check(session_id)
    Note over Proxy: Need token for Dynamic Sessions
    Proxy->>MSAL: acquire_token_for_client(scope=dynamicsessions.io/.default)
    MSAL->>AzureAD: POST /oauth2/v2.0/token
    Note right of MSAL: client_id, client_secret, grant_type=client_credentials
    AzureAD->>AzureAD: Validate app credentials
    AzureAD->>AzureAD: Check API permissions
    AzureAD-->>MSAL: Access token (expires_in: 3599)
    MSAL-->>Proxy: Bearer token for Dynamic Sessions

    Note over User,Sessions: PHASE 3: Call Dynamic Sessions

    Proxy->>Sessions: POST /code/execute
    Note right of Proxy: Authorization: Bearer {msal_token}
    Note right of Proxy: Identifier: {session_id}
    Sessions-->>Proxy: Execution result
    Proxy-->>Chainlit: Health check response
    Chainlit->>Browser: Display session status
```

#### Key Points

| Phase | Component | Authentication Type | Scope |
|-------|-----------|---------------------|-------|
| 1. User Login | Chainlit OAuth | Authorization Code Flow | User identity for UI |
| 2. MSAL Token | SessionProxy | Client Credentials Flow | `https://dynamicsessions.io/.default` |
| 3. API Call | Dynamic Sessions | Bearer Token | Execute code in container |

#### Token Caching

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  MSAL Token Lifecycle                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  First Request:                                                             │
│    SessionProxy.get_access_token()                                          │
│         │                                                                   │
│         ▼                                                                   │
│    MSAL.acquire_token_for_client() ─────▶ Azure AD ─────▶ New Token         │
│         │                                                                   │
│         └─────▶ Cache token in self._token_cache                            │
│                                                                             │
│  Subsequent Requests:                                                       │
│    SessionProxy.get_access_token()                                          │
│         │                                                                   │
│         ▼                                                                   │
│    Check self._token_cache ─────▶ Token valid? ─────▶ Return cached token   │
│         │                                                                   │
│         └─────▶ Token expired? ─────▶ MSAL handles refresh automatically    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.1 First Visit - New Session Initialization

```mermaid
sequenceDiagram
    autonumber

    box rgb(33, 150, 243) Client
        participant User
        participant Browser
    end

    box rgb(76, 175, 80) Azure Web Apps<br/>Image: triagent-chainlit:v1.0
        participant Chainlit as chainlit_app.py
        participant Manager as SessionManager
        participant Proxy as SessionProxy
    end

    box rgb(255, 152, 0) Azure Dynamic Sessions<br/>Image: triagent-sessions:v1.0
        participant Sessions as /code/execute
        participant Runner as runner.py
    end

    User->>Browser: Navigate to app URL
    Browser->>Chainlit: on_chat_start()
    Chainlit->>Chainlit: session_id = SHA256(username)[:16]

    Chainlit->>Manager: health_check(session_id)
    Manager->>Proxy: health_check(session_id)
    Proxy->>Sessions: POST /code/execute
    Note over Sessions: Execute: run_health_check()
    Sessions->>Runner: exec run_health_check
    Runner-->>Sessions: emit_done(healthy=false)
    Sessions-->>Proxy: stdout: {"type": "done", "healthy": false}
    Proxy-->>Manager: yield done event
    Manager-->>Chainlit: healthy=false

    Chainlit->>Browser: Show Configuration Modal

    Note over Browser: User selects Team, Persona, Model

    User->>Browser: Click "Start Session"
    Browser->>Chainlit: Submit configuration

    Chainlit->>Manager: check_auth_status(session_id, team)
    Manager->>Proxy: check_auth_status()
    Proxy->>Sessions: POST /code/execute
    Note over Sessions: Execute: run_check_auth(team)
    Sessions->>Runner: exec run_check_auth
    Runner->>Runner: az account show (not authenticated)
    Runner->>Runner: nohup az login --use-device-code &
    Runner-->>Sessions: emit_device_code(code, url)
    Sessions-->>Proxy: stdout: {"type": "device_code", "code": "ABC123"}
    Proxy-->>Chainlit: yield device_code event

    Chainlit->>Browser: Show Device Code Modal

    Note over User: User completes auth at microsoft.com

    User->>Browser: Click "Done"
    Browser->>Chainlit: Auth confirmed

    Chainlit->>Manager: init_sdk_session(session_id, team, persona, model)
    Manager->>Proxy: init_sdk_session()
    Proxy->>Sessions: POST /code/execute
    Note over Sessions: Execute: run_init_sdk(team, persona, model)
    Sessions->>Runner: exec run_init_sdk
    Runner->>Runner: Poll az account show (wait for auth)
    Runner->>Runner: Initialize Claude SDK
    Runner->>Runner: Save session to ~/.triagent/session.json
    Runner-->>Sessions: emit_done(session_id, turns=0)
    Sessions-->>Proxy: stdout: {"type": "done", "session_id": "xyz789"}
    Proxy-->>Chainlit: yield done event

    Chainlit->>Browser: "Connected to Claude - Ready to chat!"
```

### 6.2 Browser Refresh - Session Recovery

```mermaid
sequenceDiagram
    autonumber

    box rgb(33, 150, 243) Client
        participant Browser
    end

    box rgb(76, 175, 80) Azure Web Apps<br/>Image: triagent-chainlit:v1.0
        participant Chainlit as chainlit_app.py
        participant Manager as SessionManager
        participant Proxy as SessionProxy
    end

    box rgb(255, 152, 0) Azure Dynamic Sessions<br/>Image: triagent-sessions:v1.0
        participant Sessions as /code/execute
        participant Runner as runner.py
    end

    box rgb(100, 100, 100) File System
        participant SessionFile as ~/.triagent/session.json
    end

    Browser->>Chainlit: Page refresh / on_chat_start()
    Chainlit->>Chainlit: session_id = SHA256(username)[:16] (SAME as before)
    Chainlit->>Browser: "Checking session status..."

    Chainlit->>Manager: health_check(session_id)
    Manager->>Proxy: health_check(session_id)
    Proxy->>Sessions: POST /code/execute
    Note over Sessions: Execute: run_health_check()
    Sessions->>Runner: exec run_health_check
    Runner->>Runner: az account show
    Runner->>SessionFile: Load session state

    alt Session Healthy (Container alive, Azure auth valid)
        SessionFile-->>Runner: SessionState (initialized=true)
        Runner-->>Sessions: emit_done(healthy=true, team, persona, model, turns=5)
        Sessions-->>Proxy: stdout: {"type": "done", "healthy": true, ...}
        Proxy-->>Manager: yield done event
        Manager-->>Chainlit: healthy=true + preferences
        Chainlit->>Chainlit: Restore team, persona, model (skip modal)
        Chainlit->>Browser: "Session Resumed (5 turns) - Ready to chat!"
        Note over Browser: No config modal needed!

    else Auth Expired (Container alive, Azure auth expired)
        Runner-->>Sessions: emit_done(healthy=false, team, persona, ...)
        Sessions-->>Proxy: stdout: {"type": "done", "healthy": false}
        Proxy-->>Manager: yield done event
        Manager-->>Chainlit: healthy=false + stored preferences
        Chainlit->>Browser: "Session expired, reconnecting..."
        Chainlit->>Browser: Show Config Modal (PRE-FILLED with stored prefs)
        Note over Browser: User must re-authenticate

    else Container Recycled (Container gone)
        Sessions-->>Proxy: timeout or 404
        Proxy-->>Chainlit: yield error event
        Chainlit->>Browser: "Creating new session..."
        Chainlit->>Browser: Show Config Modal (empty - no stored prefs)
        Note over Browser: Full auth flow required
    end
```

### 6.3 Health Check Flow

> **Important**: Health checks are performed via `/code/execute`, not a separate `/health` endpoint. Azure Dynamic Sessions only exposes `/code/execute` to external callers.

```mermaid
sequenceDiagram
    autonumber

    box rgb(76, 175, 80) Azure Web Apps<br/>Image: triagent-chainlit:v1.0
        participant Proxy as SessionProxy
    end

    box rgb(255, 152, 0) Azure Dynamic Sessions<br/>Image: triagent-sessions:v1.0
        participant Sessions as /code/execute
        participant Runner as runner.py
        participant Store as SessionStore
    end

    box rgb(100, 100, 100) File System
        participant SessionFile as ~/.triagent/session.json
        participant AzureDir as ~/.azure/
    end

    Proxy->>Sessions: POST /code/execute
    Note over Sessions: body.code = "from triagent.sandbox.runner import run_health_check..."

    Sessions->>Runner: exec run_health_check

    rect rgb(255, 243, 224)
        Note over Runner,AzureDir: Check Azure CLI Authentication
        Runner->>Runner: subprocess.run(["az", "account", "show"])
        Runner->>AzureDir: Read token cache
        AzureDir-->>Runner: Auth status + user email
    end

    rect rgb(230, 240, 255)
        Note over Runner,SessionFile: Load Session State
        Runner->>Store: load()
        Store->>SessionFile: Read JSON
        SessionFile-->>Store: SessionState or None
        Store-->>Runner: session data
    end

    Runner->>Runner: is_healthy = azure_auth AND session.initialized

    Runner->>Runner: emit_done(healthy, azure_auth, team, persona, model, turns, last_active)

    Sessions-->>Proxy: Response
    Note over Proxy: Parse stdout JSON events
    Note over Proxy: {"type": "done", "healthy": true/false, ...}
```

**Health Check Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `healthy` | boolean | Overall health: `azure_auth AND session.initialized` |
| `azure_auth` | boolean | Azure CLI authentication valid |
| `azure_user` | string | Authenticated user email |
| `session_initialized` | boolean | SDK has been initialized |
| `conversation_turns` | integer | Number of chat turns |
| `team` | string | Stored team preference |
| `persona` | string | Stored persona preference |
| `model` | string | Stored model preference |
| `last_active` | float | Unix timestamp of last activity |

---

## 7. Implementation Tasks

### 7.1 Task Overview

| Task | File | Status | Description |
|------|------|--------|-------------|
| 1 | `session_store.py` | **Complete** | Extend SessionState with `last_active` and `azure_user` |
| 2 | `sessions_server.py` | **N/A** | ~~Add /health endpoint~~ - Not possible with Azure Dynamic Sessions |
| 3 | `runner.py` | **Complete** | `run_health_check()` exists at lines 297-344 |
| 4 | `session_manager.py` | **Complete** | `health_check()` exists at lines 142-169 |
| 5 | `chainlit_app.py` | **Complete** | `on_chat_start()` implements health check at lines 212-260 |
| 6 | `session_proxy.py` | **Complete** | `health_check()` exists at lines 427-486 |

> **Note**: Task 2 was removed because Azure Dynamic Sessions only exposes `/code/execute`. Health checks are performed by sending Python code that calls `run_health_check()` in runner.py.

---

### 7.2 Task 1: Extend SessionState (COMPLETE)

**File**: `src/triagent/sandbox/session_store.py`

**Changes Made**:
```python
@dataclass
class SessionState:
    session_id: str
    team: str = "omnia-data"
    persona: str = "developer"
    model: str = "claude-opus-4-5"
    initialized: bool = False
    conversation_turns: int = 0
    # NEW: Track when session was last active
    last_active: float = 0.0
    # NEW: Azure user for display
    azure_user: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
```

---

### 7.3 Task 2: ~~Add /health Endpoint~~ (N/A - REMOVED)

> **Why Removed**: Azure Dynamic Sessions only exposes the `/code/execute` endpoint to external callers. Custom FastAPI endpoints like `/health` are **not accessible** from outside the container.

**Correct Approach**: Health checks are performed via `/code/execute`:

1. `session_proxy.py` sends Python code to `/code/execute`
2. The code calls `run_health_check()` in `runner.py`
3. `runner.py` emits health status via `emit_done()` to stdout
4. `session_proxy.py` parses the stdout and returns the result

**Implementation**: See Task 3 (`run_health_check()`) and Task 6 (`session_proxy.health_check()`).

---

### 7.4 Task 3: Add run_health_check Function (COMPLETE)

**File**: `src/triagent/sandbox/runner.py` (lines 297-344)

**Status**: Already implemented. The function exists in the codebase.

**Implementation**:

```python
import time

async def run_health_check() -> None:
    """Check session health and emit status.

    This function checks:
    1. Azure CLI authentication status
    2. Session file existence and initialization state
    3. Stored preferences (team, persona, model)

    Emits:
        - progress event: "Checking session health..."
        - done event: health check result with all session info
    """
    emit_progress("health_check", "Checking session health...")

    try:
        # Check Azure CLI auth
        is_auth = _is_azure_authenticated()
        user = _get_azure_user() if is_auth else None

        # Check session file
        store = SessionStore()
        session = store.load()

        # Build response
        healthy = is_auth and session is not None and session.initialized

        result = {
            "healthy": healthy,
            "azure_auth": is_auth,
            "azure_user": user,
            "session_initialized": session.initialized if session else False,
            "conversation_turns": session.conversation_turns if session else 0,
            "team": session.team if session else None,
            "persona": session.persona if session else None,
            "model": session.model if session else None,
            "last_active": session.last_active if session else None,
        }

        emit_done(**result)

    except Exception as e:
        emit_error(f"Health check failed: {e}")


def _get_azure_user() -> str | None:
    """Get the authenticated Azure user's email/name.

    Returns:
        str | None: User name/email or None if not authenticated
    """
    try:
        result = subprocess.run(
            ["az", "account", "show", "--query", "user.name", "-o", "tsv"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return None
```

---

### 7.5 Task 4: Add health_check to SessionManager (COMPLETE)

**File**: `src/triagent/web/container/session_manager.py` (lines 142-169)

**Status**: Already implemented. The method exists in the codebase.

**Implementation**:

```python
from typing import AsyncGenerator
from dataclasses import dataclass

@dataclass
class HealthCheckResult:
    """Result of a health check operation."""
    healthy: bool
    azure_auth: bool
    azure_user: str | None
    session_initialized: bool
    conversation_turns: int
    team: str | None
    persona: str | None
    model: str | None
    last_active: float | None
    error: str | None = None


class ChainlitSessionManager:
    """Manages session lifecycle for Chainlit."""

    async def health_check(self, session_id: str) -> AsyncGenerator[dict, None]:
        """Check if session is healthy and can be resumed.

        Args:
            session_id: The deterministic session ID (hash of username)

        Yields:
            dict: Progress and result events

        Returns:
            HealthCheckResult via final event
        """
        async for event in self._proxy.health_check(session_id):
            yield event

            # Extract result from done event
            if event.get("type") == "done":
                return HealthCheckResult(
                    healthy=event.get("healthy", False),
                    azure_auth=event.get("azure_auth", False),
                    azure_user=event.get("azure_user"),
                    session_initialized=event.get("session_initialized", False),
                    conversation_turns=event.get("conversation_turns", 0),
                    team=event.get("team"),
                    persona=event.get("persona"),
                    model=event.get("model"),
                    last_active=event.get("last_active"),
                )
            elif event.get("type") == "error":
                return HealthCheckResult(
                    healthy=False,
                    azure_auth=False,
                    azure_user=None,
                    session_initialized=False,
                    conversation_turns=0,
                    team=None,
                    persona=None,
                    model=None,
                    last_active=None,
                    error=event.get("error"),
                )
```

---

### 7.6 Task 5: Modify chainlit_app.py (COMPLETE)

**File**: `src/triagent/web/container/chainlit_app.py` (lines 212-260)

**Status**: Already implemented. The `on_chat_start()` function includes health check logic.

**Key Changes**:

```python
@cl.on_chat_start
async def on_chat_start():
    """Handle new chat session."""

    # 1. Generate deterministic session_id from user
    user = cl.user_session.get("user")
    username = user.identifier if user else "anonymous"
    session_id = _generate_session_id(username)

    cl.user_session.set("session_id", session_id)

    # 2. Create session manager
    session_manager = ChainlitSessionManager(session_id)
    cl.user_session.set("session_manager", session_manager)

    # 3. Show checking message
    checking_msg = cl.Message(content="Checking session status...")
    await checking_msg.send()

    # 4. Perform health check
    health_result = None
    async for event in session_manager.health_check(session_id):
        if event.get("type") == "done":
            health_result = event
            break
        elif event.get("type") == "error":
            health_result = {"healthy": False, "error": event.get("error")}
            break

    # 5. Remove checking message
    await checking_msg.remove()

    # 6. Handle result
    if health_result and health_result.get("healthy"):
        # Session is healthy - restore preferences and skip config
        team = health_result.get("team", "omnia-data")
        persona = health_result.get("persona", "developer")
        model = health_result.get("model", "claude-opus-4-5")
        turns = health_result.get("conversation_turns", 0)

        cl.user_session.set("team", team)
        cl.user_session.set("persona", persona)
        cl.user_session.set("model", model)

        await cl.Message(
            content=f"**Session Resumed** ({turns} turns)\n\n"
                    f"Team: {team} | Persona: {persona} | Model: {model}\n\n"
                    f"Ready to chat!"
        ).send()

    else:
        # Session not healthy - show config modal
        # Pre-fill with stored preferences if available
        default_team = health_result.get("team") if health_result else "omnia-data"
        default_persona = health_result.get("persona") if health_result else "developer"
        default_model = health_result.get("model") if health_result else "claude-opus-4-5"

        await _show_configuration_modal(
            default_team=default_team,
            default_persona=default_persona,
            default_model=default_model
        )


def _generate_session_id(username: str) -> str:
    """Generate deterministic session ID from username.

    Args:
        username: User identifier

    Returns:
        str: 16-character hex string (first 16 chars of SHA256 hash)
    """
    import hashlib
    return hashlib.sha256(username.encode()).hexdigest()[:16]
```

---

### 7.7 Task 6: Add health_check to SessionProxy (COMPLETE)

**File**: `src/triagent/web/services/session_proxy.py` (lines 427-486)

**Status**: Already implemented. The method uses `/code/execute` to run health checks.

**Implementation**:

```python
async def health_check(self, session_id: str) -> AsyncGenerator[dict, None]:
    """Execute health check in the session container.

    Args:
        session_id: Session identifier

    Yields:
        dict: Progress and result events
    """
    code = """
import asyncio
from triagent.sandbox.runner import run_health_check
asyncio.run(run_health_check())
"""

    async for event in self._execute_code(session_id, code):
        yield event
```

---

## 8. API Reference

### 8.1 Health Check via /code/execute

> **Note**: Azure Dynamic Sessions only exposes `/code/execute`. Health checks are performed by sending Python code that calls `run_health_check()`.

**Endpoint**: `POST /code/execute`

**Request**:
```http
POST /code/execute HTTP/1.1
Host: {session_pool_endpoint}
Content-Type: application/json
Authorization: Bearer {token}
Identifier: {session_id}

{
  "properties": {
    "codeInputType": "inline",
    "executionType": "synchronous",
    "code": "from triagent.sandbox.runner import run_health_check\nimport asyncio\nasyncio.run(run_health_check())"
  }
}
```

**Response** (stdout contains JSON events, one per line):
```json
{
  "properties": {
    "stdout": "{\"type\":\"progress\",\"step\":\"health_check\",\"message\":\"Checking session health...\"}\n{\"type\":\"done\",\"healthy\":true,\"azure_auth\":true,\"azure_user\":\"sdandey@deloitte.com\",\"session_initialized\":true,\"conversation_turns\":5,\"team\":\"omnia-data\",\"persona\":\"developer\",\"model\":\"claude-opus-4-5\",\"last_active\":1736621234.567}",
    "stderr": ""
  }
}
```

**Parsed Events from stdout**:

Event 1 (progress):
```json
{
  "type": "progress",
  "step": "health_check",
  "message": "Checking session health..."
}
```

Event 2 (done - healthy):
```json
{
  "type": "done",
  "healthy": true,
  "azure_auth": true,
  "azure_user": "sdandey@deloitte.com",
  "session_initialized": true,
  "conversation_turns": 5,
  "team": "omnia-data",
  "persona": "developer",
  "model": "claude-opus-4-5",
  "last_active": 1736621234.567
}
```

Event 2 (done - not ready):
```json
{
  "type": "done",
  "healthy": false,
  "azure_auth": false,
  "azure_user": null,
  "session_initialized": false,
  "conversation_turns": 0,
  "team": "omnia-data",
  "persona": "developer",
  "model": null,
  "last_active": null
}
```

Event (error):
```json
{
  "type": "error",
  "error": "Health check failed: Azure CLI check timed out"
}
```

### 8.2 Event Types

| Event Type | Fields | Description |
|------------|--------|-------------|
| `progress` | `step`, `message` | Health check in progress |
| `done` | `healthy`, `azure_auth`, `azure_user`, `session_initialized`, `conversation_turns`, `team`, `persona`, `model`, `last_active` | Health check complete |
| `error` | `error`, `details` | Health check failed |

### 8.3 MSAL Token Acquisition

The `SessionProxy` acquires tokens using MSAL Client Credentials flow before making requests to Azure Dynamic Sessions.

#### 8.3.1 Token Acquisition Flow

```python
from msal import ConfidentialClientApplication

class SessionProxy:
    def _get_msal_app(self) -> ConfidentialClientApplication:
        """Get or create MSAL app for client credentials flow."""
        if self._msal_app is None:
            self._msal_app = ConfidentialClientApplication(
                client_id=self.config.azure_client_id,
                client_credential=self.config.azure_client_secret,
                authority=f"https://login.microsoftonline.com/{self.config.azure_tenant_id}",
            )
        return self._msal_app

    async def get_access_token(self) -> str | None:
        """Get token for dynamicsessions.io scope using client credentials."""
        if not self._use_azure_auth:
            return None

        app = self._get_msal_app()
        result = app.acquire_token_for_client(
            scopes=["https://dynamicsessions.io/.default"]
        )

        if "access_token" in result:
            return result["access_token"]
        else:
            error = result.get("error_description", result.get("error", "Unknown"))
            raise RuntimeError(f"MSAL token acquisition failed: {error}")
```

#### 8.3.2 Token Request (Internal)

**MSAL Request** (handled by library):
```http
POST /36da45f1-dd2c-4d1f-af13-5abe46b99921/oauth2/v2.0/token HTTP/1.1
Host: login.microsoftonline.com
Content-Type: application/x-www-form-urlencoded

client_id=57b5437c-ad58-4520-8b1b-a102ad2d9049
&client_secret={secret}
&scope=https://dynamicsessions.io/.default
&grant_type=client_credentials
```

**Response**:
```json
{
  "token_type": "Bearer",
  "expires_in": 3599,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIs..."
}
```

#### 8.3.3 Token Usage

The acquired token is used in the Authorization header for all `/code/execute` requests:

```http
POST /code/execute HTTP/1.1
Host: triagent-sandbox-session-pool.orangemeadow-28f875d9.eastus.azurecontainerapps.io
Content-Type: application/json
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIs...
Identifier: abc123def456

{
  "properties": {
    "codeInputType": "inline",
    "executionType": "synchronous",
    "code": "..."
  }
}
```

#### 8.3.4 Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| `invalid_client` | Wrong client_id or client_secret | Check environment variables |
| `unauthorized_client` | Missing API permission | Add `dynamicsessions.io` permission in Azure AD |
| `AADSTS700016` | App not found in tenant | Verify tenant ID matches app registration |
| `AADSTS7000215` | Invalid client secret | Regenerate secret in Azure AD |

---

## 9. Testing Strategy

### 9.1 Phase 1: Local Testing

**Purpose**: Test session persistence and health check logic locally.

#### 9.1.1 Local Development Setup

```bash
# Terminal 1: Start local sessions server
cd /Users/sdandey/Documents/code/triagent-web-ui
source .venv/bin/activate
uvicorn triagent.web.sessions_server:app --host 0.0.0.0 --port 8080 --reload

# Terminal 2: Start Chainlit app
cd /Users/sdandey/Documents/code/triagent-web-ui
source .venv/bin/activate
export TRIAGENT_SESSION_ENDPOINT="http://localhost:8080"
export TRIAGENT_LOCAL_MODE=true
chainlit run src/triagent/web/container/chainlit_app.py --port 8000
```

#### 9.1.2 Local Test Cases

| Test ID | Scenario | Steps | Expected Result |
|---------|----------|-------|-----------------|
| L1 | First Visit | Open http://localhost:8000 | Config modal appears |
| L2 | Config Submit | Select team/persona/model, submit | Auth flow starts |
| L3 | Auth Complete | Complete device flow | "Connected to Claude" message |
| L4 | Session File | Check `~/.triagent/session.json` | Contains session_id, team, persona, model |
| L5 | Refresh (Healthy) | Refresh browser | "Session Resumed (N turns)" - NO config modal |
| L6 | Chat After Refresh | Send message | Conversation continues with context |
| L7 | Simulate Unhealthy | Delete `~/.triagent/session.json`, refresh | Config modal with cached preferences |
| L8 | Health Check API | `curl http://localhost:8080/health` | Returns session status JSON |

---

### 9.2 Phase 2: Docker E2E Testing

**Purpose**: Test full containerized flow locally.

#### 9.2.1 Docker Compose Setup

```yaml
# docker-compose.test.yml
version: '3.8'
services:
  sessions:
    build:
      context: .
      dockerfile: Dockerfile.sessions
    ports:
      - "8080:8080"
    environment:
      - CLAUDE_CODE_USE_FOUNDRY=1
      - ANTHROPIC_FOUNDRY_RESOURCE=usa-s-mgyg1ysp-eastus2
      - ANTHROPIC_DEFAULT_OPUS_MODEL=claude-opus-4-5
      - ANTHROPIC_HEADLESS=1
      - CI=true

  chainlit:
    build:
      context: .
      dockerfile: Dockerfile.chainlit
    ports:
      - "8000:8000"
    environment:
      - TRIAGENT_SESSION_ENDPOINT=http://sessions:8080
      - TRIAGENT_LOCAL_MODE=true
    depends_on:
      - sessions
```

#### 9.2.2 E2E Test Commands

```bash
# Build and start
docker-compose -f docker-compose.test.yml up --build

# Run tests
pytest tests/e2e/test_session_persistence.py -v

# Cleanup
docker-compose -f docker-compose.test.yml down
```

---

### 9.3 Phase 3: Sandbox Testing

**Purpose**: Validate in Azure environment.

#### 9.3.1 Deployment

```bash
# Build and push
./scripts/deploy/build-and-push.sh \
  --env sandbox \
  --tag v4-session-persistence \
  --az-cmd az-elevated

# Update session pool
az-elevated containerapp sessionpool update \
  --name triagent-sandbox-session-pool \
  --resource-group triagent-sandbox-rg \
  --container-name triagent-sandbox-session-pool \
  --image triagentsandboxacr.azurecr.io/triagent-sessions:v4-session-persistence
```

#### 9.3.2 Sandbox Test Cases

| Test ID | Scenario | Steps | Expected |
|---------|----------|-------|----------|
| S1 | First Visit | Open sandbox URL | Config modal |
| S2 | Auth | Complete device flow | Authenticated |
| S3 | Chat | Send message | Claude responds |
| S4 | Refresh | Refresh page | Session resumed |
| S5 | Health API | Call /health | `{"status": "ready"}` |

#### 9.3.3 Rollback

```bash
az-elevated containerapp sessionpool update \
  --name triagent-sandbox-session-pool \
  --resource-group triagent-sandbox-rg \
  --container-name triagent-sandbox-session-pool \
  --image triagentsandboxacr.azurecr.io/triagent-sessions:v3-env-fix
```

---

## 10. Verification Checklist

### 10.1 Implementation Checklist

- [x] **Task 1**: Extend `SessionState` with `last_active` and `azure_user` fields
- [x] **Task 2**: ~~Add /health endpoint~~ **N/A** - Azure Dynamic Sessions only supports /code/execute
- [x] **Task 3**: Add `run_health_check()` function to `runner.py` (lines 297-344)
- [x] **Task 4**: Add `health_check()` method to `ChainlitSessionManager` (lines 142-169)
- [x] **Task 5**: Modify `chainlit_app.py` to use health check flow (lines 212-260)
- [x] **Task 6**: Add `health_check()` method to `SessionProxy` (lines 427-486)
- [x] **Task 7**: Replace DefaultAzureCredential with MSAL in `session_proxy.py`
- [x] **Task 8**: Add `msal>=1.24.0` dependency to `pyproject.toml` (already present as msal>=1.26.0)
- [x] **Task 9**: Update `config.py` to load OAuth credentials for MSAL
- [x] **Task 10**: Remove `~/.azure` mount from `docker-compose.local.yml`

> **All implementation tasks complete.** Session persistence and MSAL authentication fully implemented.

### 10.2 Testing Checklist

- [ ] **Phase 1**: Local testing complete
  - [ ] L1-L8 test cases pass
- [ ] **Phase 2**: Docker E2E testing complete
  - [ ] E1-E5 test cases pass
- [ ] **Phase 3**: Sandbox testing complete
  - [ ] S1-S5 test cases pass

### 10.3 Documentation Checklist

- [x] Architecture diagrams updated
- [x] Sequence diagrams created (Mermaid format)
- [x] API reference documented (/code/execute pattern)
- [x] Testing strategy documented

---

## 11. Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-11 | Santosh Dandey | Initial document creation with full implementation plan |
| 1.1 | 2026-01-11 | Santosh Dandey | Fixed architecture: removed /health endpoint (Azure DS only supports /code/execute). Converted ASCII diagrams to Mermaid. Marked all implementation tasks complete. |
| 1.2 | 2026-01-11 | Santosh Dandey | **MSAL Authentication**: Replaced DefaultAzureCredential with MSAL Client Credentials flow. Added Section 4.3 (MSAL Authentication), Section 8.3 (MSAL Token Acquisition API). Updated component diagram to show MSAL flow. Removed ~/.azure mount dependency from Chainlit container. Added Section 6.0 (User Login and MSAL Token Acquisition) sequence diagram showing OAuth + MSAL token flow phases. |
