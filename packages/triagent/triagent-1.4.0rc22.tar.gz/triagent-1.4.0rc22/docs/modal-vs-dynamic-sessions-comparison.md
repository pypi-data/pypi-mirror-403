# Modal Sandbox vs Azure Dynamic Sessions - Architecture Comparison

**Document Version:** 1.0
**Last Updated:** 2026-01-19 10:35:56
**Prepared by:** Santosh Dandey
**Branch:** `feature/sandbox-module-v2`

---

## Table of Contents

1. [Reference Implementation Overview](#1-reference-implementation-overview)
2. [Folder Structure Comparison](#2-folder-structure-comparison)
3. [Required Libraries Comparison](#3-required-libraries-comparison)
4. [Sequence Diagrams](#4-sequence-diagrams)
   - 4.1 [Reference Implementation (Modal) - GIF Generation Flow](#41-reference-implementation-modal---gif-generation-flow)
   - 4.2 [Triagent (Dynamic Sessions) - User Query Execution Flow](#42-triagent-dynamic-sessions---user-query-execution-flow)
5. [Solution Comparison](#5-solution-comparison)
6. [Clarification Questions with Analysis](#6-clarification-questions-with-analysis)
7. [Document History](#7-document-history)

---

## 1. Reference Implementation Overview

### 1.1 Claude Slack GIF Creator (Modal)

The reference implementation is a Slack bot that creates custom GIFs using Claude Agent SDK running inside Modal Sandboxes.

**Repository**: `claude-slack-gif-creator`

**Core Components**:

| Component | Purpose |
|-----------|---------|
| **Slack Bot Server** | Handles Slack events (mentions, thread replies), manages Modal Sandboxes |
| **Claude Agent Sandbox** | Runs Claude SDK client, executes skills (Bash, GIF creation) |
| **Anthropic API Proxy** | Proxies API requests, keeps API key secure outside sandbox |

**Architecture Diagram**:


:::mermaid
graph TB
    subgraph SLACK["Slack Workspace"]
        style SLACK fill:#4a154b,stroke:#4a154b,stroke-width:2px,color:#fff
        User["User<br/>@GIFBot create a GIF"]
    end

    subgraph MODAL["Modal Platform"]
        style MODAL fill:#00a67e,stroke:#006f54,stroke-width:2px,color:#fff

        subgraph FASTAPI["FastAPI ASGI App"]
            style FASTAPI fill:#009688,stroke:#00695c,stroke-width:2px,color:#fff
            SlackBolt["slack_bot()<br/>FastAPI + Slack Bolt"]
        end

        subgraph SANDBOX["Modal Sandbox (per thread)"]
            style SANDBOX fill:#ff9800,stroke:#e65100,stroke-width:2px,color:#000
            AgentEntry["agent_entrypoint.py"]
            ClaudeSDK["ClaudeSDKClient"]
            Skills["Skills<br/>(slack_gif_creator)"]
            Volume["Modal Volume<br/>/workspace"]
        end

        subgraph PROXY["Anthropic Proxy"]
            style PROXY fill:#e91e63,stroke:#880e4f,stroke-width:2px,color:#fff
            ProxyApp["anthropic_proxy()<br/>API Key Exchange"]
        end
    end

    subgraph ANTHROPIC["Anthropic API"]
        style ANTHROPIC fill:#d4a574,stroke:#b8956e,stroke-width:2px,color:#000
        ClaudeAPI["api.anthropic.com"]
    end

    User -->|"Slack Event"| SlackBolt
    SlackBolt -->|"Create/Resume"| AgentEntry
    AgentEntry --> ClaudeSDK
    ClaudeSDK --> Skills
    Skills --> Volume
    ClaudeSDK -->|"Sandbox ID as API Key"| ProxyApp
    ProxyApp -->|"Real API Key"| ClaudeAPI
    Volume -->|"GIF Output"| SlackBolt
    SlackBolt -->|"Upload GIF"| User
:::


---

## 2. Folder Structure Comparison

### 2.1 Reference Implementation (Modal)

```
claude-slack-gif-creator/
├── src/
│   ├── main.py                    # Slack bot server + sandbox orchestration
│   ├── proxy.py                   # Anthropic API proxy (API key security)
│   └── agent/
│       ├── agent_entrypoint.py    # Claude SDK client inside sandbox
│       └── slack_tool_logger.py   # Hook for logging tool use to Slack
├── pyproject.toml                 # Dependencies: modal>=0.65.66
└── README.md
```

**File Count**: 5 Python files
**Lines of Code**: ~450 lines total

### 2.2 Triagent Implementation (Azure Dynamic Sessions)

```
triagent-web-ui/
├── src/triagent/
│   ├── web/
│   │   ├── container/
│   │   │   ├── chainlit_app.py        # Web UI (equivalent to main.py)
│   │   │   └── session_manager.py     # Session coordination
│   │   ├── services/
│   │   │   └── session_proxy.py       # Bridge to Dynamic Sessions (equivalent to proxy.py)
│   │   ├── local_sessions_api.py      # Local mock of Dynamic Sessions
│   │   └── config.py                  # Web configuration
│   ├── sandbox/
│   │   ├── runner.py                  # Code executed in sandbox (equivalent to agent_entrypoint.py)
│   │   ├── events.py                  # JSON event emitters for stdout
│   │   └── session_store.py           # Session persistence
│   ├── auth.py                        # Azure Foundry auth
│   ├── config.py                      # App configuration
│   ├── hooks.py                       # Claude SDK hooks
│   └── sdk_client.py                  # SDK client builder
├── infrastructure/
│   └── bicep/                         # Azure infrastructure as code
├── docker/
│   ├── Dockerfile.chainlit            # Web UI container image
│   └── Dockerfile.sessions            # Sessions container image
└── pyproject.toml
```

**File Count**: 25+ Python files
**Lines of Code**: ~5000+ lines total

### 2.3 Structural Mapping

| Modal Implementation | Triagent Implementation | Purpose |
|---------------------|------------------------|---------|
| `main.py` | `chainlit_app.py` | Entry point, user interaction handler |
| `proxy.py` | `session_proxy.py` | Bridge between UI and sandbox |
| `agent_entrypoint.py` | `runner.py` | Code executed inside sandbox with Claude SDK |
| `slack_tool_logger.py` | `events.py` + `hooks.py` | Logging and event emission |
| Modal Volume | `session_store.py` | Session persistence |
| Modal Secrets | Azure Key Vault + MSAL | Secret management |
| N/A | `local_sessions_api.py` | Local development mock |

---

## 3. Required Libraries Comparison

### 3.1 Modal Sandbox Libraries

**Host (Slack Bot Server)**:
```toml
[project]
dependencies = [
    "modal>=0.65.66",        # Modal platform SDK
]
```

**Sandbox Image** (built dynamically):
```python
sandbox_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git")
    .pip_install(
        "claude-agent-sdk",   # Claude Agent SDK
        "slack-sdk",          # Slack API client
        "rembg[cpu,cli]",     # Background removal
        "sniffio",            # Async detection
    )
)
```

**Proxy**:
```python
proxy_image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "httpx",      # HTTP client for proxying
    "fastapi",    # Web framework
)
```

### 3.2 Azure Dynamic Sessions Libraries

**Chainlit Container** (Web UI):
```toml
dependencies = [
    "chainlit>=1.3.0",           # Web UI framework
    "msal>=1.26.0",              # Azure AD authentication
    "azure-identity>=1.15.0",    # Azure credential management
    "httpx>=0.27.0",             # HTTP client
    "pydantic>=2.0.0",           # Data validation
]
```

**Sessions Container** (Sandbox):
```toml
dependencies = [
    "claude-agent-sdk>=0.1.0",   # Claude Agent SDK
    "azure-cli>=2.60.0",         # Azure CLI for MCP tools
    "fastapi>=0.109.0",          # Local testing server
    "uvicorn>=0.27.0",           # ASGI server
]
```

### 3.3 Library Comparison Table

| Category | Modal | Azure Dynamic Sessions |
|----------|-------|----------------------|
| **Sandbox SDK** | `modal>=0.65.66` | Azure Dynamic Sessions API (REST) |
| **Claude SDK** | `claude-agent-sdk` (inside sandbox) | `claude-agent-sdk` (inside sandbox) |
| **Web Framework** | `fastapi` | `chainlit` |
| **Authentication** | Modal Secrets | `msal` + Azure AD |
| **HTTP Client** | `httpx` | `httpx` |
| **API Proxy** | Custom FastAPI proxy | MSAL token-based auth |
| **Session Storage** | Modal Volume + JSON file | JSON file in container |
| **Image Building** | `modal.Image` (dynamic) | `Dockerfile` (static) |

---

## 4. Sequence Diagrams

### 4.1 Reference Implementation (Modal) - GIF Generation Flow

This diagram shows the complete flow from user request to GIF delivery, including all internal method calls and Anthropic API interactions.


:::mermaid
sequenceDiagram
    autonumber

    box rgb(74, 21, 75) Slack
        participant User
        participant SlackAPI as Slack API
    end

    box rgb(0, 166, 126) Modal Host - FastAPI
        participant SlackBolt as slack_bot()<br/>main.py:167-223
        participant ProcessMsg as process_message()<br/>main.py:120-166
    end

    box rgb(255, 152, 0) Modal Sandbox
        participant SandboxMgr as Sandbox Manager<br/>modal.Sandbox
        participant AgentEntry as agent_entrypoint.py<br/>main():88-126
        participant ClaudeSDK as ClaudeSDKClient<br/>claude_agent_sdk
        participant SlackLogger as SlackLogger<br/>slack_tool_logger.py
    end

    box rgb(233, 30, 99) Anthropic Proxy
        participant Proxy as anthropic_proxy()<br/>proxy.py:14-45
    end

    box rgb(212, 165, 116) Anthropic
        participant Claude as api.anthropic.com<br/>/v1/messages
    end

    Note over User,Claude: PHASE 1: Slack Event Reception

    User->>SlackAPI: @GIFBot create a dancing cat GIF
    SlackAPI->>SlackBolt: POST / (Slack event)
    SlackBolt->>SlackBolt: handle_mention() - Extract message text
    SlackBolt->>ProcessMsg: process_message(body, client, user_message, files)

    Note over ProcessMsg,SandboxMgr: PHASE 2: Sandbox Creation/Resume

    ProcessMsg->>ProcessMsg: sandbox_name = f"gif-{team_id}-{thread_ts}"

    alt Sandbox Exists
        ProcessMsg->>SandboxMgr: modal.Sandbox.from_name(sandbox_name)
        SandboxMgr-->>ProcessMsg: Existing sandbox reference
    else New Sandbox
        ProcessMsg->>SandboxMgr: modal.Sandbox.create()
        Note right of SandboxMgr: image=sandbox_image<br/>secrets=[slack_secret]<br/>volumes={VOL_MOUNT_PATH: vol}<br/>env={ANTHROPIC_BASE_URL: proxy_url}<br/>idle_timeout=20min<br/>timeout=5hr
        SandboxMgr-->>ProcessMsg: New sandbox reference
    end

    ProcessMsg->>SandboxMgr: sb.exec("bash", "-c", "mkdir -p /data && ln -s...")

    opt Files Attached
        ProcessMsg->>ProcessMsg: upload_images_to_sandbox(sb, files, token)
        ProcessMsg->>SandboxMgr: sb.open("/data/image.png", "wb")
    end

    Note over ProcessMsg,Claude: PHASE 3: Claude Agent Execution

    ProcessMsg->>SandboxMgr: run_claude_turn(sb, user_message, channel, thread_ts)
    SandboxMgr->>AgentEntry: sb.exec("python", "/agent/agent_entrypoint.py", "--message", ...)

    rect rgb(255, 243, 224)
        Note over AgentEntry,ClaudeSDK: Inside Sandbox - agent_entrypoint.py

        AgentEntry->>AgentEntry: os.environ["ANTHROPIC_API_KEY"] = MODAL_SANDBOX_ID
        AgentEntry->>AgentEntry: session_id = load_session_id(sandbox_name)
        AgentEntry->>AgentEntry: options = ClaudeAgentOptions(resume=session_id, system_prompt=..., allowed_tools=[...])

        AgentEntry->>ClaudeSDK: async with ClaudeSDKClient(options) as client
        Note right of ClaudeSDK: ClaudeSDKClient.__aenter__()<br/>Spawns Claude CLI subprocess

        AgentEntry->>ClaudeSDK: await client.query(user_msg)

        loop Receive Response Messages
            ClaudeSDK->>AgentEntry: async for msg in client.receive_response()

            alt Tool Use Request
                ClaudeSDK->>SlackLogger: hooks["PreToolUse"] - log_tool_use()
                SlackLogger->>SlackAPI: chat_postMessage(tool info)

                Note over ClaudeSDK: Execute Tool (Bash, Write, Read, Skill)

                ClaudeSDK->>SlackLogger: hooks["PostToolUse"] - log_tool_use()
                SlackLogger->>SlackAPI: chat_postMessage(tool response)
            end

            alt API Call Needed
                ClaudeSDK->>Proxy: POST /v1/messages
                Note right of Proxy: x-api-key = sandbox_id
                Proxy->>Proxy: Validate sandbox still running
                Proxy->>Proxy: Exchange sandbox_id for real API key
                Proxy->>Claude: POST /v1/messages (real API key)
                Claude-->>Proxy: Response with content/tool_use
                Proxy-->>ClaudeSDK: Proxied response
            end

            alt ResultMessage
                AgentEntry->>AgentEntry: save_session_id(sandbox_name, msg.session_id)
            else TextContent
                AgentEntry->>AgentEntry: print(block.text) -> stdout
            end
        end
    end

    SandboxMgr-->>ProcessMsg: stdout lines (generator)

    Note over ProcessMsg,User: PHASE 4: Response Delivery

    loop For each result
        alt Text Response
            ProcessMsg->>SlackAPI: client.chat_postMessage(text)
            SlackAPI->>User: Text message in thread
        end

        alt GIF Generated
            ProcessMsg->>SandboxMgr: sb.exec("test", "-f", "/data/output.gif")
            SandboxMgr-->>ProcessMsg: exit_code == 0
            ProcessMsg->>SandboxMgr: sb.open("/data/output.gif", "rb")
            SandboxMgr-->>ProcessMsg: GIF bytes
            ProcessMsg->>SlackAPI: client.files_upload_v2(gif_path)
            SlackAPI->>User: GIF attachment in thread
        end
    end
:::


### 4.2 Triagent (Dynamic Sessions) - User Query Execution Flow

This diagram shows the user query execution flow assuming initialization and authentication are already complete.


:::mermaid
sequenceDiagram
    autonumber

    box rgb(33, 150, 243) Client
        participant User
        participant Browser
    end

    box rgb(76, 175, 80) Chainlit Container :8080
        participant Chainlit as chainlit_app.py<br/>on_message():275-340
        participant Manager as ChainlitSessionManager<br/>session_manager.py
        participant Proxy as SessionProxy<br/>session_proxy.py
        participant MSAL as ConfidentialClientApplication
    end

    box rgb(255, 152, 0) Azure Dynamic Sessions
        participant DynSessions as /code/execute<br/>Session Pool
    end

    box rgb(255, 87, 34) Sessions Container
        participant Runner as runner.py<br/>run_chat():180-260
        participant Events as events.py<br/>emit_*()
        participant Store as SessionStore<br/>session_store.py
        participant SDKClient as ClaudeSDKClient<br/>claude_agent_sdk
    end

    box rgb(156, 39, 176) Azure AI Foundry
        participant Foundry as Claude API<br/>.services.ai.azure.com
    end

    box rgb(121, 85, 72) Azure Resources
        participant AzureCLI as Azure CLI<br/>MCP Tools
    end

    Note over User,AzureCLI: PHASE 1: User Message Submission

    User->>Browser: Type "List my ADO work items"
    Browser->>Chainlit: WebSocket: on_message(message)
    Chainlit->>Chainlit: session_id = cl.user_session.get("session_id")
    Chainlit->>Manager: chat(session_id, user_message, team, persona, model)

    Note over Manager,Foundry: PHASE 2: MSAL Token Acquisition

    Manager->>Proxy: chat(session_id, message, ...)
    Proxy->>Proxy: _build_chat_code(message, team, persona, model)
    Note right of Proxy: code = "from triagent.sandbox.runner import run_chat..."

    Proxy->>MSAL: acquire_token_for_client(scope=dynamicsessions.io/.default)
    MSAL-->>Proxy: Bearer token

    Note over Proxy,Runner: PHASE 3: Code Execution Request

    Proxy->>DynSessions: POST /code/execute
    Note right of Proxy: Authorization: Bearer {msal_token}<br/>Identifier: {session_id}<br/>Body: {"code": "...run_chat(...)..."}

    DynSessions->>Runner: Execute Python code

    rect rgb(255, 243, 224)
        Note over Runner,AzureCLI: Inside Sessions Container - runner.py

        Runner->>Events: emit_progress("chat", "Processing query...")
        Events->>Events: print(json.dumps({"type": "progress", ...}))

        Runner->>Store: session = store.load()
        Store-->>Runner: SessionState (session_id, turns, ...)

        Runner->>Runner: options = _build_claude_options(team, persona, model)
        Note right of Runner: system_prompt from prompts/system.py<br/>MCP servers from config<br/>resume=session.session_id

        Runner->>SDKClient: async with ClaudeSDKClient(options) as client
        Note right of SDKClient: __aenter__() spawns Claude CLI<br/>Sets CLAUDE_CODE_USE_FOUNDRY=1<br/>Sets ANTHROPIC_FOUNDRY_RESOURCE

        Runner->>SDKClient: await client.query(message)

        loop Agentic Loop - Receive Response
            SDKClient->>Runner: async for msg in client.receive_response()

            alt AssistantMessage with tool_use
                Runner->>Events: emit_tool_use(tool_name, tool_input)

                Note over SDKClient,AzureCLI: Tool Execution
                alt Azure CLI Tool
                    SDKClient->>AzureCLI: az devops work-item list ...
                    AzureCLI-->>SDKClient: JSON result
                else Bash/Read/Write Tool
                    SDKClient->>SDKClient: Execute tool locally
                end

                Runner->>Events: emit_tool_result(result)
            end

            alt TextContent in message
                Runner->>Events: emit_text(block.text)
                Events->>Events: print(json.dumps({"type": "text", "content": ...}))
            end

            alt API Call to Foundry
                SDKClient->>Foundry: POST /claude-opus-4-5/messages
                Note right of Foundry: Azure CLI token auth<br/>via ANTHROPIC_FOUNDRY_RESOURCE
                Foundry-->>SDKClient: Response with content/tool_use
            end

            alt ResultMessage
                Runner->>Store: store.update(session_id=msg.session_id, turns+=1)
                Runner->>Events: emit_done(session_id, turns)
            end
        end
    end

    DynSessions-->>Proxy: HTTP Response
    Note right of Proxy: Body: {"stdout": "{...}\\n{...}\\n...", "stderr": ""}

    Note over Proxy,User: PHASE 4: Response Streaming to UI

    loop Parse stdout JSON lines
        Proxy->>Proxy: Parse each line as JSON event

        alt type == "progress"
            Proxy->>Manager: yield {"type": "progress", ...}
            Manager->>Chainlit: yield event
            Chainlit->>Browser: Update status message
        end

        alt type == "text"
            Proxy->>Manager: yield {"type": "text", "content": ...}
            Manager->>Chainlit: yield event
            Chainlit->>Chainlit: msg.stream_token(content)
            Chainlit->>Browser: Stream text via WebSocket
        end

        alt type == "tool_use"
            Proxy->>Manager: yield {"type": "tool_use", ...}
            Manager->>Chainlit: yield event
            Chainlit->>Browser: Show tool usage element
        end

        alt type == "done"
            Proxy->>Manager: yield {"type": "done", "session_id": ...}
            Manager->>Chainlit: yield event
            Chainlit->>Chainlit: cl.user_session.set("turns", turns)
            Chainlit->>Browser: Message complete
        end
    end

    Browser->>User: Display formatted response
:::


---

## 5. Solution Comparison

### 5.1 Pattern Comparison Matrix

| Pattern | Modal Sandbox | Dynamic Sessions | Identical? |
|---------|--------------|------------------|------------|
| **Claude SDK Location** | Inside sandbox | Inside sandbox | **Identical** |
| **SDK Client Pattern** | `ClaudeSDKClient(options)` | `ClaudeSDKClient(options)` | **Identical** |
| **Session Resumption** | `resume=session_id` | `resume=session_id` | **Identical** |
| **API Key Handling** | Proxy exchanges sandbox_id for real key | Azure Foundry uses Azure CLI token | **Different** |
| **Sandbox Creation** | `modal.Sandbox.create()` | Azure Dynamic Sessions `/code/execute` | **Different** |
| **Image Building** | Dynamic `modal.Image` builder | Static Dockerfile | **Different** |
| **Event Communication** | stdout from `sb.exec()` | stdout from `/code/execute` | **Identical** |
| **Session Storage** | Modal Volume + JSON file | Container filesystem JSON | **Similar** |
| **Tool Execution** | Inside sandbox via SDK | Inside sandbox via SDK | **Identical** |
| **Hooks System** | `HookMatcher` with callbacks | `HookMatcher` with callbacks | **Identical** |

### 5.2 Identical Patterns

#### 5.2.1 Claude SDK Inside Sandbox

Both implementations run `ClaudeSDKClient` **inside** the sandbox environment:

**Modal**:
```python
# agent_entrypoint.py (executed inside Modal Sandbox)
async with ClaudeSDKClient(options=options) as client:
    await client.query(user_msg)
    async for msg in client.receive_response():
        ...
```

**Triagent**:
```python
# runner.py (executed inside Dynamic Sessions container)
async with ClaudeSDKClient(options=options) as client:
    await client.query(message)
    async for msg in client.receive_response():
        ...
```

#### 5.2.2 Session Resumption Pattern

Both use the same session ID persistence mechanism:

**Modal**:
```python
session_id = load_session_id(sandbox_name)
options = ClaudeAgentOptions(resume=session_id, ...)
# After response:
save_session_id(sandbox_name, msg.session_id)
```

**Triagent**:
```python
session = store.load()
options = _build_claude_options(..., resume=session.session_id)
# After response:
store.update(session_id=msg.session_id, turns+=1)
```

#### 5.2.3 stdout-based Event Communication

Both communicate from sandbox to host via stdout JSON events:

**Modal**:
```python
# agent_entrypoint.py
print(block.text)  # Text output to stdout
```

**Triagent**:
```python
# events.py
def emit_text(content: str) -> None:
    print(json.dumps({"type": "text", "content": content}))
```

### 5.3 Non-Identical Patterns

#### 5.3.1 API Key Security

**Modal**: Uses a proxy service that exchanges sandbox ID for real API key:
```python
# proxy.py
sandbox_id = headers.get("x-api-key")
sb = await modal.Sandbox.from_id.aio(sandbox_id)  # Validate sandbox
headers["x-api-key"] = os.environ["ANTHROPIC_API_KEY"]  # Exchange for real key
```

**Triagent**: Uses Azure Foundry with Azure CLI token authentication:
```python
# No API key in sandbox - uses Azure CLI token
os.environ["CLAUDE_CODE_USE_FOUNDRY"] = "1"
os.environ["ANTHROPIC_FOUNDRY_RESOURCE"] = "usa-s-mgyg1ysp-eastus2"
# Claude SDK uses Azure CLI credentials automatically
```

#### 5.3.2 Sandbox/Container Lifecycle

**Modal**: Dynamic sandbox creation and management:
```python
# main.py
try:
    sb = modal.Sandbox.from_name(app_name=app.name, name=sandbox_name)
except modal.exception.NotFoundError:
    sb = modal.Sandbox.create(
        app=app,
        image=sandbox_image,
        idle_timeout=20 * 60,
        timeout=5 * 60 * 60,
        name=sandbox_name,
    )
```

**Triagent**: Stateless code execution via Azure Dynamic Sessions:
```python
# session_proxy.py
async def _execute_code(self, session_id: str, code: str) -> AsyncGenerator:
    # Each request executes code in a pre-provisioned container
    response = await self._client.post(
        f"{self.pool_endpoint}/code/execute",
        headers={"Identifier": session_id},
        json={"properties": {"code": code}}
    )
```

#### 5.3.3 Container Image Building

**Modal**: Dynamic image building in Python code:
```python
sandbox_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git")
    .pip_install("claude-agent-sdk", "slack-sdk")
    .run_commands("git clone ...", "pip install ...")
)
```

**Triagent**: Static Dockerfile:
```dockerfile
# Dockerfile.sessions
FROM python:3.12-slim
RUN pip install claude-agent-sdk azure-cli
COPY src/triagent /app/triagent
```

### 5.4 Summary Comparison Table

| Aspect | Modal Sandbox | Azure Dynamic Sessions |
|--------|--------------|----------------------|
| **SDK Execution Location** | Inside sandbox | Inside container |
| **API Authentication** | Proxy with key exchange | Azure Foundry (Azure CLI token) |
| **Container Lifecycle** | On-demand creation, 20min idle timeout | Session pool, managed by Azure |
| **Image Management** | Dynamic Python DSL | Static Dockerfiles |
| **Scaling** | Modal auto-scales sandboxes | Azure Container Apps Session Pool |
| **Cost Model** | Pay per sandbox-second | Pay per container-second |
| **Secret Management** | Modal Secrets | Azure Key Vault + MSAL |
| **Local Development** | `modal serve` | Local Docker Compose |
| **File Storage** | Modal Volumes | Container filesystem |
| **External API Access** | Via proxy (security) | Direct to Azure Foundry |

---

## 6. Clarification Questions with Analysis

### 6.1 Question 1: Does the reference implementation have claude-agent-sdk within the sandbox (or) outside the sandbox?

**Answer: Claude Agent SDK is INSIDE the sandbox**

**Evidence from `main.py:24-41`**:
```python
sandbox_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git")
    .pip_install("claude-agent-sdk", "slack-sdk")  # SDK installed in sandbox image
    ...
)
```

**Evidence from `agent_entrypoint.py:10`**:
```python
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, HookMatcher, ResultMessage
```

The `agent_entrypoint.py` file is executed **inside** the Modal Sandbox (see `main.py:40`):
```python
.add_local_dir(AGENT_ENTRYPOINT, "/agent")  # Copies agent/ to /agent in sandbox
```

And execution happens inside the sandbox (`main.py:83-97`):
```python
def run_claude_turn(sb: modal.Sandbox, user_message: str, ...):
    args = ["python", "/agent/agent_entrypoint.py", "--message", user_message, ...]
    process = sb.exec(*args)  # Executes inside sandbox
```

**Conclusion**: The Claude Agent SDK runs **entirely inside the Modal Sandbox**. The host (FastAPI server) only orchestrates sandbox creation and reads stdout.

---

### 6.2 Question 2: Does the reference implementation just execute tools and have claude-agent-sdk outside the web API?

**Answer: NO - The SDK runs INSIDE the sandbox, not outside**

The reference implementation does NOT have the SDK outside the sandbox. Here's the architecture:

```
:::mermaid
graph LR
    subgraph HOST["Modal Host (FastAPI)"]
        style HOST fill:#4caf50,stroke:#1b5e20,stroke-width:2px,color:#fff
        A1["slack_bot()"]
        A2["process_message()"]
        A3["NO SDK HERE"]
    end

    subgraph SANDBOX["Modal Sandbox"]
        style SANDBOX fill:#ff9800,stroke:#e65100,stroke-width:2px,color:#000
        B1["agent_entrypoint.py"]
        B2["ClaudeSDKClient"]
        B3["Tool Execution"]
    end

    A1 --> A2
    A2 -->|"sb.exec()"| B1
    B1 --> B2
    B2 --> B3
:::
```

**Key Evidence**:

1. **Host code** (`main.py`) only imports `modal` - no `claude_agent_sdk`:
   ```python
   import modal  # Only Modal SDK on host
   from .proxy import anthropic_proxy, app as proxy_app
   ```

2. **Sandbox code** (`agent_entrypoint.py`) imports the Claude SDK:
   ```python
   from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, ...
   ```

3. **Communication is via stdout**, not API:
   ```python
   # Host reads stdout from sandbox
   for line in process.stdout:
       yield {"response": line}
   ```

**Conclusion**: The reference implementation runs the **full Claude Agent SDK inside the sandbox**. The web API (FastAPI) is just a thin orchestration layer.

---

### 6.3 Question 3: Does the reference implementation create custom Docker images with claude-agent-sdk for the sandbox to work?

**Answer: YES - Custom images are built dynamically with Modal's Python DSL**

**Evidence from `main.py:24-42`**:
```python
sandbox_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git")
    .pip_install("claude-agent-sdk", "slack-sdk")
    .run_commands(
        # Clone skill from GitHub
        "git clone --depth 1 --filter=blob:none --sparse https://github.com/anthropics/skills.git /tmp/skills-repo",
        "cd /tmp/skills-repo && git sparse-checkout set slack-gif-creator",
        # Set up skill for SDK discovery at /app/.claude/skills/
        "mkdir -p /app/.claude/skills",
        "mv /tmp/skills-repo/slack-gif-creator /app/.claude/skills/slack_gif_creator",
        "rm -rf /tmp/skills-repo",
    )
    .run_commands("pip install -r /app/.claude/skills/slack_gif_creator/requirements.txt")
    .pip_install("rembg[cpu,cli]", "sniffio")
    .run_commands("rembg d u2net_human_seg")  # Pre-download ML model
    .add_local_dir(AGENT_ENTRYPOINT, "/agent")  # Add agent entrypoint code
)
```

**What the custom image contains**:

| Layer | Content |
|-------|---------|
| Base | `debian:slim` with Python 3.12 |
| System | `git` (apt-installed) |
| Python Packages | `claude-agent-sdk`, `slack-sdk`, `rembg`, `sniffio` |
| Skills | `slack-gif-creator` skill from Anthropic's repo |
| ML Models | `u2net_human_seg` model for background removal |
| Application Code | `agent_entrypoint.py`, `slack_tool_logger.py` |

**Comparison with Triagent**:

| Aspect | Modal | Triagent |
|--------|-------|----------|
| Image Definition | Python DSL (`modal.Image`) | Dockerfile |
| Build Time | At deployment (`modal deploy`) | CI/CD pipeline |
| SDK Inclusion | `pip_install("claude-agent-sdk")` | `pip install claude-agent-sdk` |
| Skills | Git clone from Anthropic repo | Team-specific CLAUDE.md files |
| Custom Code | `.add_local_dir()` | `COPY` in Dockerfile |

**Conclusion**: Yes, the reference implementation creates a **custom container image** that includes:
1. Claude Agent SDK (`claude-agent-sdk`)
2. Anthropic's `slack-gif-creator` skill
3. Custom agent entrypoint code
4. Pre-downloaded ML models

This is analogous to Triagent's `Dockerfile.sessions` which also builds a custom image with the Claude Agent SDK.

---

## 7. Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-19 | Santosh Dandey | Initial document with complete analysis of Modal vs Azure Dynamic Sessions implementations. Includes folder structure comparison, library comparison, detailed sequence diagrams with color coding, solution comparison matrix, and clarification questions with evidence-based answers. |
