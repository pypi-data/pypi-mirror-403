# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Deployment Instructions (MANDATORY)

**CRITICAL: Always use the deployment scripts. Never use direct Azure CLI commands for deployment.**

### Build and Push Images

Use `scripts/deploy/build-and-push.sh` to build and push Docker images to Azure Container Registry:

```bash
# Build and push to sandbox environment
./scripts/deploy/build-and-push.sh --env sandbox --tag v1.5.0

# Build and push to production
./scripts/deploy/build-and-push.sh --env prd --tag v1.5.0

# Use elevated Azure account
./scripts/deploy/build-and-push.sh --env sandbox --tag v1.5.0 --az-cmd az-elevated

# Dry run (preview commands without executing)
./scripts/deploy/build-and-push.sh --env sandbox --tag v1.5.0 --dry-run
```

### Deploy to Azure

Use `scripts/deploy/deploy-to-azure.sh` to deploy images and verify health:

```bash
# Deploy to sandbox environment
./scripts/deploy/deploy-to-azure.sh --env sandbox --tag v1.5.0

# Deploy with elevated Azure account
./scripts/deploy/deploy-to-azure.sh --env sandbox --tag v1.5.0 --az-cmd az-elevated

# Skip specific components
./scripts/deploy/deploy-to-azure.sh --env sandbox --tag v1.5.0 --skip-session-pool
./scripts/deploy/deploy-to-azure.sh --env sandbox --tag v1.5.0 --skip-app-service

# Dry run (preview commands without executing)
./scripts/deploy/deploy-to-azure.sh --env sandbox --tag v1.5.0 --dry-run
```

### Important Rules

1. **NEVER** use direct `az webapp`, `az containerapp`, or `az acr` commands for deployment operations
2. **ALWAYS** use the scripts in `scripts/deploy/` for all deployment tasks
3. **If deployment fails**: Modify the deployment scripts to fix the issue, then retry using the scripts
4. **For one-off fixes**: Add the fix to the appropriate script, do not run ad-hoc Azure CLI commands
5. The scripts handle: ACR login, image tagging, platform architecture (linux/amd64), health checks, and app settings

### Script Features

| Script | Purpose |
|--------|---------|
| `build-and-push.sh` | Builds Docker images for `linux/amd64`, tags them, and pushes to ACR |
| `deploy-to-azure.sh` | Updates Session Pool and App Service, configures env vars, runs health checks |
| `health-check.sh` | Standalone health check for deployed services |
| `deploy-all.sh` | Full CI/CD pipeline (build + deploy) |

---

## Project Overview

Triagent is a Claude-powered CLI for Azure DevOps automation. It provides an interactive chat interface that uses Claude AI (via Databricks, Azure AI Foundry, or direct Anthropic API) to automate Azure DevOps operations including work items, pull requests, pipelines, and Kusto queries.

## Build and Development Commands

**IMPORTANT**: Always activate the virtual environment before running any commands.

```bash
# Activate virtual environment (ALWAYS do this first)
source .venv/bin/activate

# Sync dependencies (using uv)
uv sync

# Install with development dependencies (using uv)
uv pip install -e ".[dev]"

# Run the CLI
triagent

# Run tests
pytest tests/ -v

# Run a single test file
pytest tests/test_config.py -v

# Run a single test
pytest tests/test_config.py::TestTriagentConfig::test_default_values -v

# Linting
ruff check src/

# Type checking
mypy src/
```

## Git Commit Guidelines

When creating commits:
- **DO NOT** include "Generated with Claude Code" footer
- **DO NOT** include "Co-Authored-By: Claude" lines
- Use conventional commit format: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
- Keep subject line under 72 characters
- Use body for detailed explanation when needed

## Git Repository Configuration

### Remote Repositories
This project has two remotes configured:
- **origin** (personal): `git@github.com:sdandey/triagent.git` - User: `sdandey`
- **deloitte** (work): `https://github.com/deloitte-technology/triagent.git` - User: `sdandey_deloite`

### Important: Check Git User Before Commit/Push
**ALWAYS** verify the correct Git user is configured before committing or pushing:

```bash
# Check current user
git config user.name
git config user.email

# Check which remote you're pushing to
git remote -v
```

### Switch Users When Needed
```bash
# For personal repo (origin)
git config user.name "sdandey"
git config user.email "<personal-email>"

# For deloitte repo
git config user.name "sdandey_deloite"
git config user.email "<deloitte-email>"
```

### Workflow Reminder

1. Before any commit: Check `git config user.name`
2. Before any push: Verify target remote matches intended user
3. When switching between repos: Update git user config accordingly

## Azure Infrastructure

### Important: Use Elevated Azure Account for Bicep Deployments

**ALWAYS** use `az-elevated` instead of `az` when deploying Bicep templates:

```bash
# Example: Deploy Bicep template
az-elevated deployment group create \
  --resource-group triagent-sandbox-rg \
  --template-file infrastructure/bicep/main.bicep \
  --parameters infrastructure/bicep/parameters/sandbox.bicepparam
```

### Azure Subscriptions

| Subscription | Subscription ID | Resource Group | Purpose |
|--------------|-----------------|----------------|---------|
| US-AZSUB-AME-AA-ODATAOPENAI-SBX | `5eefdd74-582a-411a-9168-6a3b7ac1de4c` | triagent-sandbox-rg | Primary sandbox |
| US-AZSUB-AME-AA-ODATAOPENAI2-SBX | `b58fef94-18c7-41ea-9d9c-424096e3321a` | triagent-sandbox-rg | Secondary sandbox |

### Deployed Components (All Bicep Modules)

- Azure Container Registry (ACR)
- App Service (Chainlit Web UI)
- Container Apps Session Pool
- Redis Cache
- Application Insights
- Log Analytics Workspace
- Managed Identity
- Role Assignments

## Local Development Testing

### Registered Devtunnel for Local Testing

Use the following devtunnel URL for local E2E testing (registered in Azure AD app registration):

```
https://4m2mfr3p-8080.use2.devtunnels.ms
```

### Quick Start for Local Testing

```bash
# 1. Clean up existing containers
docker compose -f docker-compose.local.yml down
docker volume rm triagent-local-config 2>/dev/null || true

# 2. Host the registered devtunnel (in terminal 1)
devtunnel host triagent-team

# 3. Start containers with CHAINLIT_URL (in terminal 2)
export CHAINLIT_URL=https://4m2mfr3p-8080.use2.devtunnels.ms
docker compose -f docker-compose.local.yml up -d --build

# 4. Open in browser
open https://4m2mfr3p-8080.use2.devtunnels.ms
```

**Tunnel Details**:
- Tunnel name: `triagent-team`
- Port 8080 (Chainlit UI): `https://4m2mfr3p-8080.use2.devtunnels.ms`
- Port 8082 (Sessions API): `https://4m2mfr3p-8082.use2.devtunnels.ms`

### Two-Stage Authentication Flow

1. **Stage 1 - MSAL OAuth** (Chainlit container): Azure AD login for web UI
2. **Stage 2 - Device Code Flow** (Sessions container): Azure CLI auth for Claude SDK

## Architecture

### Core Components

- **cli.py**: Main entry point. Implements interactive REPL loop with slash commands (`/init`, `/help`, `/config`, `/team`, `/clear`, `/exit`). Uses prompt-toolkit for input and rich for output.

- **agent.py**: Claude integration layer. `AgentSession` manages conversation state and routes to either:
  - `DatabricksClient`: Custom client for Databricks Foundation Model API (OpenAI-compatible format)
  - Anthropic SDK: Direct API or Azure Foundry

- **config.py**: Configuration management via `ConfigManager`. Stores settings in `~/.triagent/`:
  - `config.json`: Team, project, organization settings (`TriagentConfig`)
  - `credentials.json`: API tokens and provider config (`TriagentCredentials`)
  - `mcp_servers.json`: MCP server configuration

- **teams/config.py**: Team definitions (`levvia`, `omnia`, `omnia-data`) with ADO project mappings and team-specific CLAUDE.md files.

- **prompts/system.py**: Builds system prompts by combining base prompt with team context and team-specific CLAUDE.md content from `prompts/claude_md/`.

- **tools/azure_cli.py**: Azure CLI tool for the agent. Defines `AZURE_CLI_TOOL` schema and `execute_azure_cli()` with automatic consent for reads, confirmation for writes.

### API Provider Flow

The agent supports three providers configured via `TriagentCredentials.api_provider`:
1. `databricks` (default): Uses `DatabricksClient` with OAuth token refresh via `databricks auth token`
2. `azure_foundry`: Sets Foundry environment variables, uses Anthropic SDK
3. `anthropic`: Direct Anthropic API

### Tool Execution

`send_message_with_tools()` implements an agentic loop:
1. Send message with tool definitions
2. Check for tool calls in response
3. Execute tools, collect results
4. Append results to conversation, repeat until no more tool calls

## Claude Agent SDK

### Claude CLI Installation
The `claude-agent-sdk` Python package automatically installs Claude Code CLI as a subprocess.
When the SDK is installed via pip (`pip install claude-agent-sdk`), Claude CLI is included.
No separate npm installation is required.

### SDK Usage in Containers
- The SDK spawns Claude CLI as a subprocess
- Requires `ANTHROPIC_HEADLESS=1` and `CI=true` for non-interactive mode
- Uses Azure Foundry credentials from `~/.triagent/credentials.json`
- Foundry auth mode `azure_cli_token` uses Azure CLI credentials (no API key needed)

### Azure Foundry Configuration
The SDK reads configuration from `~/.triagent/credentials.json`:
```json
{
  "api_provider": "azure_foundry",
  "anthropic_foundry_base_url": "https://{resource}.services.ai.azure.com/",
  "anthropic_foundry_model": "claude-opus-4-5",
  "foundry_auth_mode": "azure_cli_token"
}
```

The `get_foundry_env()` function in `src/triagent/auth.py` extracts the resource name from the base URL
and sets environment variables for the SDK:
- `CLAUDE_CODE_USE_FOUNDRY=1`
- `ANTHROPIC_FOUNDRY_RESOURCE={extracted-resource-name}`
- `ANTHROPIC_DEFAULT_OPUS_MODEL={model}`

## Testing

Tests use pytest with pytest-asyncio. Test files mirror source structure:
- `tests/test_config.py`: Config and credentials serialization
- `tests/test_teams.py`: Team configuration lookups

Configuration tests use `TemporaryDirectory` for isolated file system operations.

## Azure DevOps Repositories (Audit Cortex 2)

### Organization Details
- **Organization**: symphonyvsts
- **Project**: Audit Cortex 2
- **Git SSH Base**: `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/`
- **Local Clone Path**: `~/code/{repo-name}`

### Active Repositories (Monitored Services)

These repositories have active application logs and are prioritized for exception investigation:

| Repository | Branch | AppRoleName | SSH Clone URL |
|------------|--------|-------------|---------------|
| data-exchange-service | master | DataExchangeGateway | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/data-exchange-service` |
| cortex-datamanagement-services | master | AppSupportService, DataPreparationService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/cortex-datamanagement-services` |
| engagement-service | master | EngagementService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/engagement-service` |
| security-service | master | SecurityService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/security-service` |
| data-kitchen-service | master | DataKitchenService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/data-kitchen-service` |
| analytic-template-service | master | AnalyticTemplateService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/analytic-template-service` |
| notification-service | master | NotificationService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/notification-service` |
| staging-service | master | StagingService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/staging-service` |
| spark-job-management | master | SparkJobManagementService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/spark-job-management` |
| cortex-ui | master | Cortex-UI | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/cortex-ui` |
| client-service | master | ClientService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/client-service` |
| workpaper-service | master | WorkpaperService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/workpaper-service` |
| async-workflow-framework | master | async-workflow-function | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/async-workflow-framework` |
| sampling-service | master | SamplingService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/sampling-service` |
| localization-service | master | LocalizationService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/localization-service` |
| scheduler-service | master | SchedulerService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/scheduler-service` |

### Git Commands for Investigation

#### Clone a repository
```bash
git clone git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/{repo-name} ~/code/{repo-name}
```

#### Update existing repository
```bash
cd ~/code/{repo-name}
git fetch origin
git checkout master
git pull origin master
```

#### Checkout release branch
```bash
git fetch --all
git checkout release-{version}
git pull origin release-{version}
```

---

## Issue Creation Workflow

When the user asks to **"create an issue"** or **"create a GitHub issue for..."**, follow this comprehensive workflow to create well-structured, implementation-ready issues.

### Issue Body Template

Create issues with the following structure:

```markdown
## Overview
{Brief description of the feature/fix - what problem does it solve?}

---

## Acceptance Criteria

From user perspective - what does "done" look like?

- [ ] **AC1**: User can {action} and sees {result}
- [ ] **AC2**: When user does {X}, system responds with {Y}
- [ ] **AC3**: Error handling: When {error condition}, user sees {error message}
- [ ] **AC4**: {Additional criteria}

---

## Testing Guide

### Test Scenarios

| ID | Scenario | Type | Expected Result |
|----|----------|------|-----------------|
| T1 | {Happy path scenario} | Unit | {Expected behavior} |
| T2 | {Edge case scenario} | Unit | {Expected behavior} |
| T3 | {Error handling scenario} | Unit | {Expected behavior} |
| T4 | {Integration scenario} | Integration | {Expected behavior} |
| T5 | {End-to-end user flow} | E2E/Manual | {Expected behavior} |

### Unit Tests Required

- [ ] `tests/test_{module}.py::test_{function}__{happy_path}`
- [ ] `tests/test_{module}.py::test_{function}__{edge_case}`
- [ ] `tests/test_{module}.py::test_{function}__{error_handling}`

### Integration Tests Required

- [ ] `tests/test_{feature}_integration.py::test_{scenario_1}`
- [ ] `tests/test_{feature}_integration.py::test_{scenario_2}`

### Manual Validation (E2E)

Human validation test cases:
- [ ] Verify: {User scenario 1 - step by step}
- [ ] Verify: {User scenario 2 - step by step}
- [ ] Verify: {Error scenario - what to test}

---

## Implementation Steps (High-Level)

1. **Step 1**: {High-level description}
2. **Step 2**: {High-level description}
3. **Step 3**: {High-level description}
4. ...

---

## Architecture Reference

{Choose ONE of the following:}
- **Wiki Page**: [Link to architecture/design wiki page]
- **Design Doc**: [Link to design document]
- **Embedded**: See task comments below for detailed implementation

---

## Files to Create/Modify

| File | Purpose |
|------|---------|
| `src/{path}/new_file.py` | {What this file does} |
| `src/{path}/existing_file.py` | {What changes are needed} |
| `tests/test_{feature}.py` | {Test file for new functionality} |

---

## Dependencies

```toml
# pyproject.toml additions (if any)
{package} = "^{version}"
```

**External Dependencies**: {List any external tools/services required}

---

## Implementation Tasks

See issue comments for detailed implementation steps:

- [ ] **Task 1**: {Title} - {Brief description}
- [ ] **Task 2**: {Title} - {Brief description}
- [ ] **Task 3**: {Title} - {Brief description}
- [ ] ...
```

### Task Comment Template

For each task, add a separate comment with this structure:

```markdown
## Task N: {Title}

**File(s)**: `path/to/file.py`

### Implementation Steps

1. {Detailed step 1}
2. {Detailed step 2}
3. {Detailed step 3}

### Code Example

\`\`\`python
# Example implementation
def example_function():
    pass
\`\`\`

### Unit Tests for This Task

| Test Case | Description | Expected |
|-----------|-------------|----------|
| `test_{func}__happy_path` | {What it tests} | {Expected result} |
| `test_{func}__edge_case` | {What it tests} | {Expected result} |
| `test_{func}__error` | {What it tests} | {Expected result} |

### Verification Checklist

- [ ] Implementation complete
- [ ] Unit tests written
- [ ] Unit tests pass
- [ ] Integration tests pass (if applicable)
- [ ] Manual validation complete
```

### Implementation Cycle

When implementing each task, follow this cycle:

```
┌─────────────────────────────────────────────────────────────────┐
│                    IMPLEMENTATION CYCLE                          │
│                    (Repeat for each Task)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. IMPLEMENT                                                    │
│     └─► Write code following task implementation steps           │
│     └─► Follow code examples provided                            │
│                                                                  │
│  2. WRITE UNIT TESTS                                             │
│     └─► Create test file: tests/test_{feature}.py                │
│     └─► Write tests from task's unit test table                  │
│                                                                  │
│  3. VALIDATE UNIT TESTS                                          │
│     └─► Run: pytest tests/test_{feature}.py -v                   │
│     └─► Fix any failures                                         │
│     └─► Ensure 100% of task tests pass                           │
│                                                                  │
│  4. VALIDATE E2E (Human Validation)                              │
│     └─► Run the manual validation scenarios                      │
│     └─► Test user-facing behavior                                │
│     └─► Document any issues found                                │
│                                                                  │
│  5. COMMIT TASK                                                  │
│     └─► git add {files}                                          │
│     └─► git commit -m "feat(#{issue}): implement Task N"         │
│                                                                  │
│  [Move to next Task]                                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### PR Validation Checklist Template

When creating the PR, include this checklist:

```markdown
## PR Validation Checklist

### Code Quality
- [ ] Code follows project style guide (ruff, black)
- [ ] No linting errors: `ruff check src/`
- [ ] Type hints added: `mypy src/`
- [ ] No hardcoded secrets or credentials

### Unit Tests
- [ ] All new code has unit tests
- [ ] All unit tests pass: `pytest tests/ -v`
- [ ] Test coverage maintained/improved

### Integration Tests
- [ ] Integration tests pass
- [ ] No regressions in existing functionality

### Manual Validation (E2E)
- [ ] ✅ {Manual test 1 description}
- [ ] ✅ {Manual test 2 description}
- [ ] ✅ {Manual test 3 description}

### Acceptance Criteria
- [ ] ✅ AC1: {Criteria met}
- [ ] ✅ AC2: {Criteria met}
- [ ] ✅ AC3: {Criteria met}

### Documentation
- [ ] Code comments added where needed
- [ ] README updated (if applicable)
- [ ] CHANGELOG updated (if applicable)

---

**Issue Reference**: Closes #{N}
```

### Commands for Issue Creation

```bash
# Create issue with body from heredoc
gh issue create --title "feat: {title}" --body "$(cat <<'EOF'
{Issue body following template above}
EOF
)" --label "enhancement"

# Add task comments
gh issue comment {N} --body "$(cat <<'EOF'
## Task 1: {Title}
{Task content following template}
EOF
)"

# Repeat for each task...
```

---

## Issue Implementation Workflow

When the user says **"implement Issue #N"** or **"work on Issue #N"**, follow this workflow:

### 1. Create Feature Branch
```bash
# Fetch latest from main
git fetch origin main

# Create new branch from main
git checkout -b feature/issue-{N}-{short-description} origin/main

# Example: git checkout -b feature/issue-23-cortex-auth origin/main
```

### 2. Read Issue Details
```bash
# Get issue details and comments
gh issue view {N}
gh issue view {N} --comments
```

### 3. Implement Tasks
- Follow the implementation steps in issue comments
- Work through tasks in order (Task 1, Task 2, etc.)
- Run tests after each significant change
- Commit logically grouped changes

### 4. Test Changes
```bash
# Run all tests
pytest tests/ -v

# Run specific test file if created
pytest tests/test_{feature}.py -v

# Lint check
ruff check src/

# Type check
mypy src/
```

### 5. Commit Changes
```bash
# Stage changes
git add .

# Commit with descriptive message referencing issue
git commit -m "feat: implement {feature description}

Closes #{N}
"
```

### 6. Create Pull Request
```bash
# Push branch
git push -u origin feature/issue-{N}-{short-description}

# Create PR to main
gh pr create --title "feat: {feature title}" --body "## Summary
{brief description}

## Changes
- {change 1}
- {change 2}

Closes #{N}
" --base main
```

### Example Workflow
```bash
# User says: "implement Issue #23"

# Step 1: Create branch
git fetch origin main
git checkout -b feature/issue-23-cortex-auth origin/main

# Step 2: Read issue
gh issue view 23
gh issue view 23 --comments

# Step 3: Implement (follow task comments)
# ... make changes ...

# Step 4: Test
pytest tests/ -v
ruff check src/

# Step 5: Commit
git add .
git commit -m "feat: implement Cortex authentication and Omnia Data skill

Closes #23
"

# Step 6: Create PR
git push -u origin feature/issue-23-cortex-auth
gh pr create --title "feat: Cortex authentication and Omnia Data skill" \
  --body "## Summary
Implements on-demand Cortex authentication and API tools.

## Changes
- Add cortex_api skill for developer persona
- Add authenticate_cortex and get_cortex_token tools
- Add call_cortex_api tool for API calls
- Add token storage in ~/.triagent/credentials.json

Closes #23
" --base main
```

### Important Notes
- **Always create a new branch** for each issue
- **Never commit directly to main**
- **Reference the issue number** in commits and PRs
- **Run tests before committing**
- **Create PR to main** when implementation is complete
