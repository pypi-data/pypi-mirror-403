# Dynamic Skill Loading Architecture Design

**Document Version:** 1.0
**Prepared by:** sdandey
**Last Updated:** 2026-01-21 23:07:56 CST
**Status:** Design Phase

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current Architecture Analysis](#current-architecture-analysis)
3. [Proposed Architecture](#proposed-architecture)
4. [Implementation Approach](#implementation-approach)
5. [Critical Files to Modify](#critical-files-to-modify)
6. [Verification Plan](#verification-plan)
7. [Document History](#document-history)

---

## Executive Summary

This document proposes enhancements to Triagent's skill loading system to support:

1. **Intent-based skill auto-activation** - Skills dynamically activate based on user request matching
2. **User-profile-based dynamic loading** - Skills load based on configured persona (developer/support)
3. **Sub-agent routing** - Specialized sub-agents (code-review, investigation) route automatically
4. **Progressive disclosure** - Context optimization by loading skill metadata first, full content on-demand

The design works for both CLI and Web UI entry points with minimal code duplication.

---

## Current Architecture Analysis

### Current Skill Loading Flow

:::mermaid
sequenceDiagram
    participant User
    participant CLI/WebUI
    participant ConfigManager
    participant SkillLoader
    participant SystemPrompt
    participant ClaudeSDKClient
    participant Claude

    User->>CLI/WebUI: Start application
    CLI/WebUI->>ConfigManager: Load config (team, persona)
    CLI/WebUI->>SkillLoader: load_persona(team, persona)

    Note over SkillLoader: Load ALL skills at startup
    SkillLoader->>SkillLoader: Load core skills (*.md)
    SkillLoader->>SkillLoader: Load persona skills (*.md)
    SkillLoader->>SkillLoader: Generate subagents from skills
    SkillLoader-->>CLI/WebUI: LoadedPersona (all skills loaded)

    CLI/WebUI->>SystemPrompt: get_system_prompt(team, persona)
    Note over SystemPrompt: Inject ALL skill content into prompt
    SystemPrompt->>SystemPrompt: Add base prompt
    SystemPrompt->>SystemPrompt: Add team context
    SystemPrompt->>SystemPrompt: Add ALL skill markdown content
    SystemPrompt-->>CLI/WebUI: Full system prompt (large)

    CLI/WebUI->>ClaudeSDKClient: Create client with options
    Note over ClaudeSDKClient: All subagents defined upfront

    User->>CLI/WebUI: Send message
    CLI/WebUI->>ClaudeSDKClient: query(prompt, options)
    ClaudeSDKClient->>Claude: API call with full context
    Claude-->>User: Response
:::

### Current Architecture Issues

| Issue | Impact | Location |
|-------|--------|----------|
| **All skills loaded upfront** | Large system prompts (~10K+ tokens) | `loader.py:load_persona()` |
| **No intent-based routing** | Manual skill invocation required | `system.py:get_system_prompt()` |
| **Static subagent definitions** | Can't adapt to user context | `sdk_client.py:_get_agent_definitions()` |
| **On-demand via MCP only** | Limited to explicit tool calls | `mcp/tools.py:get_code_review_guidelines()` |
| **Triggers field unused** | `SkillMetadata.triggers` exists but not utilized | `models.py:45` |

### Existing Infrastructure (Already in Place)

| Component | Location | Status |
|-----------|----------|--------|
| `SkillMetadata.triggers` | `models.py:45` | Defined but unused |
| `SkillDefinition` separation | `models.py:63-75` | Metadata + content already separate |
| `SubagentConfig.to_agent_definition()` | `models.py:106-117` | SDK integration exists |
| `LoadedPersona.get_agent_definitions()` | `models.py:179-187` | Subagent generation works |
| `detect_code_reviewer()` | `models.py:232-253` | File extension → reviewer mapping |
| `on_demand_skills` in PersonaDefinition | `models.py:133` | On-demand concept exists |

### Current File Structure

```
src/triagent/
  skills/
    models.py           # SkillMetadata, SkillDefinition, PersonaDefinition
    loader.py           # load_persona(), load_skill_by_name()
    system.py           # get_system_prompt() - builds full prompt
    encrypted_loader.py # Optional encrypted skills
    core/               # Shared skills
    {team}/
      _persona_developer.yaml
      _persona_support.yaml
      core/             # Team-specific core skills
      developer/        # Developer persona skills
      support/          # Support persona skills
  sdk_client.py         # TriagentSDKClient - builds ClaudeAgentOptions
  mcp/tools.py          # MCP tools including on-demand skill loading
```

### Current Skill Loading Code Path

1. **CLI**: `cli.py` → `create_sdk_client()` → `SkillLoader.load_persona()` → `SystemPrompt.get_system_prompt()`
2. **Web**: `chainlit_app.py` → `SessionProxy` → `sandbox/runner.py` → Same path as CLI

---

## Proposed Architecture

### Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Skill Activation** | Claude-driven via tool | More flexible, Claude decides what to load based on full context |
| **Web UI Loading** | Pre-load at session start | Simpler, works within Azure Dynamic Sessions sandbox constraints |
| **Sub-agent Routing** | Claude decides | Aligns with SDK patterns, Claude uses Task tool based on descriptions |

### Design Principles

1. **Progressive Disclosure**: Load metadata at startup, full content on-demand via tool
2. **Claude-Driven Loading**: Claude calls `load_skill` tool when it determines a skill is needed
3. **Profile-Aware Metadata**: Skill descriptions filtered by persona at startup
4. **Sub-Agent Delegation**: Claude uses Task tool with subagent descriptions for routing
5. **Platform Agnostic**: Same skill loading works for CLI and Web UI

### Proposed Skill Loading Flow (Claude-Driven)

:::mermaid
sequenceDiagram
    participant User
    participant CLI/WebUI
    participant ConfigManager
    participant SkillRegistry
    participant SystemPrompt
    participant ClaudeSDKClient
    participant Claude
    participant LoadSkillTool

    User->>CLI/WebUI: Start application
    CLI/WebUI->>ConfigManager: Load config (team, persona)
    CLI/WebUI->>SkillRegistry: scan_skills(team, persona)

    Note over SkillRegistry: Load METADATA only at startup
    SkillRegistry->>SkillRegistry: Scan skill files for YAML frontmatter
    SkillRegistry->>SkillRegistry: Build skill index (name, description, triggers)
    SkillRegistry-->>CLI/WebUI: SkillIndex (metadata only ~500 tokens)

    CLI/WebUI->>SystemPrompt: get_base_prompt(team, persona, skill_index)
    Note over SystemPrompt: Compact prompt with skill catalog
    SystemPrompt->>SystemPrompt: Add base instructions
    SystemPrompt->>SystemPrompt: Add skill catalog (names + descriptions)
    SystemPrompt->>SystemPrompt: Add "use load_skill tool" instructions
    SystemPrompt-->>CLI/WebUI: Compact system prompt

    CLI/WebUI->>ClaudeSDKClient: Create client with options
    Note over ClaudeSDKClient: load_skill MCP tool + subagents from metadata

    User->>CLI/WebUI: "Review this PR for security issues"
    CLI/WebUI->>ClaudeSDKClient: query(user_message)
    ClaudeSDKClient->>Claude: API call with compact context

    Note over Claude: Sees skill catalog in prompt
    Claude->>Claude: Determines code_review skill needed
    Claude->>LoadSkillTool: load_skill(name="code_review")
    LoadSkillTool->>SkillRegistry: get_skill_content("code_review")
    SkillRegistry-->>LoadSkillTool: Full skill markdown content
    LoadSkillTool-->>Claude: Skill instructions injected

    Note over Claude: Now has code review guidelines
    Claude->>Claude: Determines subagent needed
    Claude->>ClaudeSDKClient: Task tool (subagent=security-reviewer)
    ClaudeSDKClient->>Claude: Execute subagent with context
    Claude-->>User: Response with code review
:::

### Component Architecture

:::mermaid
graph TB
    subgraph "Entry Points"
        CLI[CLI - cli.py]
        WEB[Web UI - chainlit_app.py]
    end

    subgraph "Skill Management Layer - NEW"
        SR[SkillRegistry - Metadata index + caching]
        LST[load_skill MCP Tool - Claude-invoked loading]
    end

    subgraph "Existing Components - Modified"
        SL[SkillLoader - File operations]
        SP[SystemPrompt - Compact prompt + catalog]
        SC[SDKClient - Claude SDK wrapper]
    end

    subgraph "Claude Agent SDK"
        SDK[ClaudeSDKClient]
        AG[AgentDefinitions - From skill metadata]
        TL[Tools - MCP/Custom]
    end

    CLI --> SR
    WEB --> SR
    SR --> SP
    SR --> LST
    LST --> SL
    SP --> SC
    SC --> SDK
    SR --> AG
    AG --> SDK
    LST --> TL
    TL --> SDK
:::

### New Components

#### 1. SkillRegistry (`src/triagent/skills/registry.py`)

```python
# Proposed interface
class SkillRegistry:
    """Manages skill metadata index for progressive disclosure.

    Scans skill files at startup, extracts only YAML frontmatter,
    and provides on-demand full content loading via MCP tool.
    """

    def __init__(self, team: str, persona: str):
        self.team = team
        self.persona = persona
        self._metadata_index: dict[str, SkillMetadata] = {}
        self._loaded_skills: dict[str, SkillDefinition] = {}  # Cache
        self._subagent_configs: dict[str, SubagentConfig] = {}

    def scan_skills(self) -> SkillIndex:
        """Scan skill files and extract YAML frontmatter only.

        Returns lightweight index (~500 tokens vs ~10K+ for full content).
        Respects persona configuration (core_skills, skills, on_demand_skills).
        """

    def get_skill_catalog(self) -> str:
        """Generate skill catalog for system prompt.

        Format:
        ## Available Skills
        Use the `load_skill` tool to load any skill before using its capabilities.

        | Skill | Description | Use When |
        |-------|-------------|----------|
        | code_review | Review code for quality and security | PR reviews, code analysis |
        | ...
        """

    def get_available_subagents(self) -> dict[str, AgentDefinition]:
        """Return subagent definitions from skill metadata.

        Subagents are registered upfront so Claude can invoke them via Task tool.
        Each skill's `subagents` field lists associated subagent names.
        """

    def is_skill_loaded(self, skill_name: str) -> bool:
        """Check if skill content is already loaded in cache."""

    def load_skill(self, skill_name: str) -> SkillDefinition:
        """Load full skill content on-demand.

        Called by load_skill MCP tool when Claude needs skill instructions.
        Caches loaded skills to avoid repeated file reads.
        """

    def get_loaded_skills_summary(self) -> str:
        """Return summary of currently loaded skills for context tracking."""
```

#### 2. load_skill MCP Tool (`src/triagent/mcp/tools.py`)

```python
# Add to existing MCP tools module
from triagent.skills.registry import get_skill_registry

@tool(
    "load_skill",
    "Load a skill's full instructions and guidelines. "
    "Use this tool when you need specific guidance for a task. "
    "The skill content will be returned and you should follow its instructions.",
    {
        "skill_name": str,  # Name of skill to load from catalog
        "reason": str,      # Brief explanation of why this skill is needed
    }
)
async def load_skill(args: dict[str, Any]) -> dict[str, Any]:
    """Load skill content on-demand when Claude needs it.

    This tool is called by Claude when it determines a skill's
    full instructions are needed for the current task.
    """
    registry = get_skill_registry()
    skill_name = args["skill_name"]
    reason = args.get("reason", "")

    if not registry.has_skill(skill_name):
        return {
            "content": [{
                "type": "text",
                "text": f"Skill '{skill_name}' not found. Available skills: {registry.list_skill_names()}"
            }]
        }

    skill = registry.load_skill(skill_name)

    return {
        "content": [{
            "type": "text",
            "text": f"## Skill Loaded: {skill.metadata.display_name}\n\n"
                    f"**Purpose**: {skill.metadata.description}\n\n"
                    f"**Loaded because**: {reason}\n\n"
                    f"---\n\n{skill.content}"
        }]
    }

@tool(
    "list_loaded_skills",
    "List skills that have been loaded in this session.",
    {}
)
async def list_loaded_skills(args: dict[str, Any]) -> dict[str, Any]:
    """Show which skills are currently loaded in the session."""
    registry = get_skill_registry()
    return {
        "content": [{
            "type": "text",
            "text": registry.get_loaded_skills_summary()
        }]
    }
```

#### 3. SkillIndex Types (`src/triagent/skills/types.py`)

```python
# New type definitions
from dataclasses import dataclass
from typing import Any

@dataclass
class SkillIndex:
    """Lightweight skill index containing only metadata."""

    skills: dict[str, SkillMetadata]  # name -> metadata
    subagents: dict[str, SubagentConfig]  # name -> config

    @property
    def token_estimate(self) -> int:
        """Estimate tokens for this index."""
        # ~50 tokens per skill metadata entry
        return len(self.skills) * 50 + len(self.subagents) * 30

@dataclass
class LoadedSkillContext:
    """Context for skills loaded in current session."""

    loaded_skills: list[str]  # Names of loaded skills
    total_tokens: int  # Estimated tokens added
    timestamp: str  # When skills were loaded
```

### Modified Components

#### 1. SystemPrompt Changes (`src/triagent/skills/system.py`)

**Current:**
```python
def get_system_prompt(team: str, persona: str) -> str:
    # Loads ALL skill content into prompt
    persona_data = load_persona(team, persona)
    prompt = BASE_PROMPT
    prompt += team_context
    for skill in persona_data.skills:
        prompt += skill.content  # FULL content (~10K+ tokens)
    return prompt
```

**Proposed:**
```python
def get_system_prompt(team: str, persona: str, registry: SkillRegistry) -> str:
    """Build compact system prompt with skill catalog.

    Includes only skill metadata, not full content.
    Claude uses load_skill tool to get full instructions when needed.
    """
    prompt = BASE_PROMPT
    prompt += get_team_context(team)
    prompt += get_persona_context(persona)

    # Add skill catalog (metadata only, ~500 tokens)
    prompt += registry.get_skill_catalog()

    # Add instructions for using skills
    prompt += SKILL_USAGE_INSTRUCTIONS

    return prompt

# New constant for skill usage instructions
SKILL_USAGE_INSTRUCTIONS = """
## Using Skills

You have access to a catalog of skills that provide specialized guidance.
When you need detailed instructions for a task:

1. Review the skill catalog above to find relevant skills
2. Use the `load_skill` tool to load the skill's full instructions
3. Follow the loaded instructions to complete the task
4. Use the `list_loaded_skills` tool to see what's already loaded

Example: For a code review task, load the `code_review` skill first.
"""
```

#### 2. SDKClient Changes (`src/triagent/sdk_client.py`)

**Current:**
```python
class TriagentSDKClient:
    def __init__(self, config_manager, console):
        # All skills loaded at startup
        self.system_prompt = get_system_prompt(team, persona)  # Full prompt
        self.agents = self._get_agent_definitions()  # From load_persona()

    def _get_agent_definitions(self) -> dict[str, AgentDefinition]:
        persona = load_persona(self.team, self.persona)  # Loads everything
        return {...}
```

**Proposed:**
```python
class TriagentSDKClient:
    def __init__(self, config_manager, console):
        # Initialize skill registry (metadata only)
        self.registry = SkillRegistry(team, persona)
        self.registry.scan_skills()

        # Compact system prompt with skill catalog
        self.system_prompt = get_system_prompt(team, persona, self.registry)

        # Subagents from metadata (not full skill content)
        self.agents = self.registry.get_available_subagents()

    def _get_mcp_config(self) -> dict[str, Any]:
        """Get MCP configuration including load_skill tool."""
        return {
            "triagent": create_triagent_mcp_server(self.registry),  # Pass registry
            "azure-devops": {...},
        }

    def _get_allowed_tools(self) -> list[str]:
        """Get allowed tools including new skill tools."""
        return [
            # ... existing tools ...
            "mcp__triagent__load_skill",        # NEW
            "mcp__triagent__list_loaded_skills", # NEW
        ]
```

#### 3. MCP Server Changes (`src/triagent/mcp/tools.py`)

**Current:**
```python
def create_triagent_mcp_server() -> Any:
    return create_sdk_mcp_server(
        name="triagent",
        version="1.0.0",
        tools=[
            get_team_config,
            generate_kusto_query,
            list_telemetry_tables,
            get_code_review_guidelines,  # Hardcoded skill loading
        ]
    )
```

**Proposed:**
```python
def create_triagent_mcp_server(registry: SkillRegistry | None = None) -> Any:
    """Create MCP server with dynamic skill loading support.

    Args:
        registry: SkillRegistry instance for dynamic loading.
                 If None, uses global registry.
    """
    # Store registry reference for tools
    if registry:
        set_skill_registry(registry)

    return create_sdk_mcp_server(
        name="triagent",
        version="1.0.0",
        tools=[
            get_team_config,
            generate_kusto_query,
            list_telemetry_tables,
            load_skill,          # NEW - dynamic skill loading
            list_loaded_skills,  # NEW - show loaded skills
        ]
    )
```

### Claude-Driven Skill Loading Mechanism

:::mermaid
sequenceDiagram
    participant User
    participant Client
    participant Claude
    participant LoadSkillTool
    participant Registry

    User->>Client: "Review the authentication module"
    Client->>Claude: Query with skill catalog in system prompt

    Note over Claude: Sees skill catalog - decides code_review needed
    Claude->>Claude: Analyzes task requirements
    Claude->>LoadSkillTool: load_skill(name="code_review", reason="PR review task")

    LoadSkillTool->>Registry: load_skill("code_review")
    Registry->>Registry: Check cache - not loaded
    Registry->>Registry: Read full markdown content
    Registry->>Registry: Cache loaded skill
    Registry-->>LoadSkillTool: SkillDefinition with full content

    LoadSkillTool-->>Claude: "## Skill Loaded: Code Review - [full instructions]"

    Note over Claude: Now has code review guidelines
    Claude->>Claude: May load additional skills if needed
    Claude->>LoadSkillTool: load_skill(name="security_analysis", reason="auth module security")
    LoadSkillTool-->>Claude: Security analysis instructions

    Note over Claude: Uses loaded skill instructions
    Claude-->>User: Code review with security focus
:::

### Skill Catalog in System Prompt

The system prompt includes a compact skill catalog that Claude uses to decide which skills to load:

```markdown
## Available Skills

Use the `load_skill` tool to load detailed instructions for any skill.

| Skill | Description | Use When |
|-------|-------------|----------|
| code_review | Review code for quality, security, and best practices | PR reviews, code analysis, refactoring |
| security_analysis | Identify security vulnerabilities and risks | Security audits, auth reviews, OWASP checks |
| incident_investigation | Investigate production incidents and errors | Telemetry analysis, RCA, incident triage |
| ado_pr_management | Create and manage Azure DevOps pull requests | PR creation, comments, approvals |
| pyspark_optimization | Optimize PySpark and Databricks workloads | Performance tuning, Delta Lake optimization |

**Instructions**: Before starting a complex task, load the relevant skill(s) to get detailed guidance.
```

### Sub-Agent Routing Flow (Claude Decides)

Subagents are registered at startup from skill metadata. Claude uses the Task tool to delegate to specialized agents based on their descriptions.

:::mermaid
sequenceDiagram
    participant User
    participant Client
    participant Claude
    participant TaskTool
    participant SubAgent

    User->>Client: "Create investigation report for incident #123"
    Client->>Claude: Query with subagent definitions in options

    Note over Claude: Sees subagent descriptions in Task tool
    Note over Claude: - investigation-reporter: Create incident RCA reports
    Note over Claude: - code-reviewer: Review code for quality/security
    Note over Claude: - pyspark-analyzer: Analyze PySpark performance

    Claude->>Claude: Determines investigation-reporter subagent is best fit
    Claude->>TaskTool: Task(subagent_type="investigation-reporter", prompt="Investigate incident #123...")

    TaskTool->>SubAgent: Create subagent with inherited context
    Note over SubAgent: Has specialized prompt from skill metadata
    SubAgent->>SubAgent: Load incident_investigation skill
    SubAgent->>SubAgent: Execute investigation steps
    SubAgent->>SubAgent: Generate RCA report
    SubAgent-->>TaskTool: Investigation report result

    TaskTool-->>Claude: Subagent completed with report
    Claude-->>User: Formatted investigation report
:::

### Subagent Definition from Skill Metadata

Subagents are defined in skill YAML frontmatter and extracted during metadata scanning:

```yaml
# src/triagent/skills/omnia-data/support/incident_investigation.md
---
name: incident_investigation
display_name: "Incident Investigation"
description: "Investigate production incidents with telemetry analysis and RCA"
version: "1.0.0"
subagents:
  - investigation-reporter  # Associated subagent
tools:
  - mcp__azure-devops__search_work_items
  - mcp__triagent__generate_kusto_query
---

# Investigation Instructions
...
```

```yaml
# src/triagent/skills/omnia-data/support/_subagents/investigation-reporter.yaml
name: investigation-reporter
description: "Create detailed incident RCA reports with root cause analysis and recommendations. Use for production incidents requiring formal documentation."
prompt: |
  You are an incident investigation specialist. When investigating:
  1. Gather telemetry data from Application Insights
  2. Identify the root cause using timeline analysis
  3. Document findings in RCA format
  4. Provide actionable recommendations
tools:
  - Read
  - Grep
  - Glob
  - mcp__triagent__generate_kusto_query
  - mcp__azure-devops__create_work_item
model: sonnet
```

### Profile-Based Skill Loading

:::mermaid
graph LR
    subgraph "Developer Persona"
        D_CORE[Core Skills - ado_basics, git_ops]
        D_SPEC[Developer Skills - code_review, pr_management]
        D_DEMAND[On-Demand Skills - python_review, pyspark_review]
        D_AGENTS[Subagents - code-reviewer, test-runner]
    end

    subgraph "Support Persona"
        S_CORE[Core Skills - ado_basics, telemetry]
        S_SPEC[Support Skills - incident_investigation, rca]
        S_DEMAND[On-Demand Skills - kusto_queries, log_analysis]
        S_AGENTS[Subagents - investigation-reporter, incident-triager]
    end

    subgraph "SkillRegistry"
        REG[Persona-aware skill index]
    end

    D_CORE --> REG
    D_SPEC --> REG
    D_DEMAND --> REG
    D_AGENTS --> REG

    S_CORE --> REG
    S_SPEC --> REG
    S_DEMAND --> REG
    S_AGENTS --> REG
:::

---

## Implementation Approach

### Phase 1: Core Infrastructure (SkillRegistry)

**New Files:**
- `src/triagent/skills/registry.py` - SkillRegistry class with metadata scanning and caching
- `src/triagent/skills/types.py` - New type definitions (SkillIndex, LoadedSkillContext)

**Key Tasks:**
1. Create SkillRegistry class with metadata-only scanning
2. Implement skill catalog generation for system prompt
3. Add caching for loaded skills
4. Create global registry accessor for MCP tools

### Phase 2: MCP Tool Integration (load_skill)

**Modified Files:**
- `src/triagent/mcp/tools.py` - Add load_skill and list_loaded_skills tools

**Key Tasks:**
1. Implement `load_skill` MCP tool
2. Implement `list_loaded_skills` MCP tool
3. Update `create_triagent_mcp_server()` to accept registry
4. Add global registry management

### Phase 3: System Prompt Changes

**Modified Files:**
- `src/triagent/skills/system.py` - Compact prompt with skill catalog

**Key Tasks:**
1. Update `get_system_prompt()` to use registry
2. Create skill catalog formatting
3. Add skill usage instructions constant
4. Remove full skill content injection

### Phase 4: SDK Client Integration

**Modified Files:**
- `src/triagent/sdk_client.py` - Use SkillRegistry for initialization

**Key Tasks:**
1. Initialize SkillRegistry in `__init__`
2. Update `_get_mcp_config()` to pass registry
3. Update `_get_allowed_tools()` with new tools
4. Update `_get_agent_definitions()` to use registry

### Phase 5: CLI/Web Integration

**CLI Changes (`cli.py`):**
- No changes needed - works through SDK client

**Web Changes (`sandbox/runner.py`):**
- Initialize SkillRegistry at session start
- Pre-scan skills based on user persona
- Pass registry to SDK client

---

## Critical Files to Modify

| File | Type | Changes | Priority |
|------|------|---------|----------|
| `src/triagent/skills/registry.py` | **New** | SkillRegistry class with metadata scanning | P1 |
| `src/triagent/skills/types.py` | **New** | SkillIndex, LoadedSkillContext types | P1 |
| `src/triagent/mcp/tools.py` | Modify | Add load_skill, list_loaded_skills tools | P1 |
| `src/triagent/skills/system.py` | Modify | Compact prompt with skill catalog | P2 |
| `src/triagent/sdk_client.py` | Modify | Initialize registry, update MCP config | P2 |
| `src/triagent/skills/loader.py` | Modify | Add metadata-only loading function | P3 |
| `src/triagent/sandbox/runner.py` | Modify | Pre-scan skills at session start | P3 |

### Files That Do NOT Need Changes

| File | Reason |
|------|--------|
| `src/triagent/cli.py` | Works through SDK client - no changes needed |
| `src/triagent/skills/models.py` | `triggers` field already exists (line 45) |
| `src/triagent/web/container/chainlit_app.py` | Uses SDK client through sandbox |

---

## Verification Plan

### Unit Tests

| Test | File | Purpose |
|------|------|---------|
| `test_skill_registry_scan` | `tests/test_registry.py` | Verify metadata-only scanning |
| `test_skill_registry_catalog` | `tests/test_registry.py` | Verify catalog generation |
| `test_skill_registry_cache` | `tests/test_registry.py` | Verify skill caching |
| `test_load_skill_tool` | `tests/test_mcp_tools.py` | Verify load_skill MCP tool |
| `test_system_prompt_compact` | `tests/test_system.py` | Verify compact prompt generation |

### Integration Tests

| Test | Purpose |
|------|---------|
| SDK client with registry | Verify SDK options include registry |
| MCP server with skills | Verify load_skill tool works end-to-end |
| Subagent definitions | Verify subagents extracted from skill metadata |
| Web sandbox initialization | Verify skills pre-scanned at session start |

### E2E Validation

1. **CLI Test - Skill Loading:**
   ```bash
   triagent
   > Review PR #123 for security issues

   # Expected behavior:
   # 1. Claude sees skill catalog in prompt
   # 2. Claude calls load_skill("code_review", reason="PR review task")
   # 3. Tool returns full code review instructions
   # 4. Claude follows loaded instructions
   ```

2. **CLI Test - Subagent Routing:**
   ```bash
   triagent
   > Create an investigation report for incident #456

   # Expected behavior:
   # 1. Claude sees subagent descriptions in Task tool
   # 2. Claude invokes Task(subagent_type="investigation-reporter")
   # 3. Subagent executes with specialized prompt
   # 4. Report returned to Claude
   ```

3. **Web UI Test:**
   - Login as developer persona
   - Verify skill catalog shows developer skills (not support skills)
   - Send code review request
   - Verify load_skill tool called in session logs
   - Verify response uses loaded skill guidance

4. **Profile Switch Test:**
   ```bash
   triagent
   > /persona support
   > Investigate incident #456

   # Expected behavior:
   # 1. Skill catalog updates to show support skills
   # 2. Different subagents available (investigation-reporter instead of code-reviewer)
   # 3. load_skill("incident_investigation") called
   ```

### Token Efficiency Validation

Compare token usage before/after implementation:

```python
# Test script to measure token reduction
from triagent.skills.registry import SkillRegistry
from triagent.skills.system import get_system_prompt

# Old approach
old_prompt = get_system_prompt_old("omnia-data", "developer")
print(f"Old prompt tokens: ~{len(old_prompt.split()) * 1.3:.0f}")

# New approach
registry = SkillRegistry("omnia-data", "developer")
registry.scan_skills()
new_prompt = get_system_prompt("omnia-data", "developer", registry)
print(f"New prompt tokens: ~{len(new_prompt.split()) * 1.3:.0f}")

# Expected: ~90% reduction in startup tokens
```

---

## Summary

### Key Changes

1. **SkillRegistry**: New class that scans skill files at startup, extracts only YAML frontmatter metadata, and provides on-demand full content loading via caching.

2. **load_skill MCP Tool**: New tool that Claude calls when it determines a skill's full instructions are needed. Returns skill content which Claude then follows.

3. **Compact System Prompt**: System prompt includes skill catalog (name + description table) instead of full skill content. Instructions tell Claude to use load_skill tool.

4. **Subagents from Metadata**: Subagent definitions extracted from skill metadata at startup and registered with SDK. Claude uses Task tool to delegate based on descriptions.

### Architecture Philosophy

- **Claude-Driven**: Claude decides which skills to load based on task context
- **Progressive Disclosure**: Metadata at startup, full content on-demand
- **Profile-Aware**: Skill catalog filtered by team/persona
- **Platform Agnostic**: Same pattern works for CLI and Web UI

### Token Efficiency Comparison

| Scenario | Current Tokens | Proposed Tokens | Savings |
|----------|---------------|-----------------|---------|
| Startup (10 skills) | ~12,000 | ~1,200 | 90% |
| Simple query | ~12,000 | ~1,500 | 88% |
| Code review | ~12,000 | ~3,500 | 71% |
| Multi-skill task | ~12,000 | ~5,000 | 58% |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-21 | sdandey | Initial design document |
