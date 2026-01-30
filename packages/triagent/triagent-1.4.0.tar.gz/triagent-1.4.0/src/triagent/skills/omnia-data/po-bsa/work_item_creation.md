---
name: work_item_creation
display_name: "Work Item Creation"
description: |
  ADO work item creation assistant with AI-powered content generation and templates.
  Guides users through creating Epics, Features, Enablers, PBIs, Defects, DTRs, Issues, and LSIs.
  Uses 5-step workflow with auto-population from team-config and user-mappings.
triggers:
  - "create.*work.*item"
  - "new (PBI|feature|defect|enabler|epic|DTR|issue|LSI)"
  - "delivery team request"
  - "create.*ticket"
  - "work item template"
  - "backlog item"
  - "add.*to.*backlog"
version: 2.1.0
---

# Work Item Creation Workflow

## 5-Step Workflow Overview

| Step | Action | User Input Required |
|------|--------|---------------------|
| 1 | **Gather Intent** | User describes what they want in natural language |
| 2 | **Context Research** | None - AI researches wiki docs, design docs, parent work items |
| 3 | **AI Generates Content** | None - AI auto-generates Title, Description, AC |
| 4 | **Implementation Notes** | User provides technical details (optional) |
| 5 | **Review Preview & Confirm** | Review complete work item, Yes/No confirmation |

## Step 0: Auto-Detect Current User

Use Azure CLI to identify the logged-in user and auto-populate fields:

```bash
# Get current Azure AD user email
az ad signed-in-user show --query "userPrincipalName" -o tsv
```

**Auto-Population Logic:**
1. Get logged-in user email from Azure CLI
2. Look up user in `user-mappings.tsv` (email column)
3. Extract user's team, POD, role, and region
4. Look up team's key roles from `team-config.json`
5. Pre-populate all team-related fields automatically

## Work Item Type Inference

Automatically infer work item type from user's request keywords:

| Keywords/Phrases | Inferred Type | PBI Sub-Type |
|------------------|---------------|--------------|
| bug, issue, broken, error, fails | Defect | - |
| new feature, add capability | Feature | - |
| refactor, clean up, tech debt | PBI | Technical Debt |
| document, wiki, guide | PBI | Documentation |
| deploy, CI/CD, pipeline | PBI | DevOps Effort |
| performance, optimize | PBI | Performance Feature |
| security, vulnerability | PBI | Security |
| test, automation, QA | PBI | Testing Only |
| research, POC, spike | PBI | Technical Discovery |
| production issue, outage | LSI | - |

## AI Content Generation

When user requests a work item, generate:

**Title Generation:**
- Feature: `[Area] | [Capability]`
- PBI: `[Action verb] [Object] [Context]`
- Defect: `[Area] | [Issue Description]`
- DTR: `[Team] | [Type] | [Description]`
- LSI: `[Feature Area] | [Issue description]`

**Description Generation:**
```
As a [role/persona],
I want [feature/capability],
So that [benefit/outcome].

**Background:**
[Context from wiki/design docs/parent work item]

**Technical Context:**
[Context from repository research or user input]
```

**Business Outcome Hypothesis (for Features/Enablers):**
`We believe that [action] will result in [outcome] for [users].`

## Acceptance Criteria Generation

Generate comprehensive AC covering:

### 1. Functional Requirements
```html
<h3>1. Functional Requirements</h3>
<ul>
<li>[Primary capability/feature description]</li>
<li>[Error handling behavior]</li>
<li>[Edge case handling]</li>
</ul>
```

### 2. Unit Testing Requirements
```html
<h3>2. Unit Testing</h3>
<ul>
<li>Unit tests created in <code>[test file path]</code></li>
<li>All methods tested with mock dependencies</li>
<li>Code coverage target: ≥80%</li>
</ul>
```

### 3. Integration Testing Requirements
```html
<h3>3. Integration Testing</h3>
<ul>
<li>Integration tests created</li>
<li>E2E connectivity verification</li>
<li>All operations tested</li>
</ul>
```

### 4. Non-Functional Requirements
```html
<h3>4. Non-Functional Requirements</h3>
<ul>
<li>Performance: [specific metric]</li>
<li>Reliability: [specific behavior]</li>
<li>Security: [specific requirement]</li>
</ul>
```

### 5. Definition of Done
```html
<h3>5. Definition of Done</h3>
<ul>
<li>Code implemented and code reviewed</li>
<li>Unit tests passing (≥80% coverage)</li>
<li>Integration tests passing</li>
<li>Documentation updated</li>
<li>No critical/high severity defects open</li>
</ul>
```

## Work Item Templates

### PBI Template
| Field | ADO Field | Auto-Populate |
|-------|-----------|---------------|
| Title | System.Title | AI-generated |
| Area Path | System.AreaPath | Yes (team) |
| Product Owner | AuditCortexScrum.CortexProductOwner | Yes |
| Cortex Release # | Custom.CortexRelease# | Current release |
| Description | System.Description | AI-generated |
| Acceptance Criteria | Microsoft.VSTS.Common.AcceptanceCriteria | AI-generated |
| Work Item Type | Custom.Type | Inferred |
| Parent | System.Parent | Link to Feature/Enabler |

### Defect Template
| Field | ADO Field | Auto-Populate |
|-------|-----------|---------------|
| Title | System.Title | AI-generated |
| Severity | Microsoft.VSTS.Common.Severity | Inferred |
| Found in Release # | Custom.FoundinCortexRelease# | Ask user |
| Repro Steps | Microsoft.VSTS.TCM.ReproSteps | AI-generated |
| Feature Area | Custom.OmniaDataFeatureArea | Inferred |

### DTR Template
| Field | ADO Field | Auto-Populate |
|-------|-----------|---------------|
| Title | System.Title | AI-generated |
| DTR Type | Custom.DTRType | Inferred or ask |
| Scrum Team | Custom.ScrumTeam | Yes |
| Environment | Custom.CortexEnvironment | Ask user |

### LSI Template
| Field | ADO Field | Auto-Populate |
|-------|-----------|---------------|
| Title | System.Title | AI-generated |
| Feature Area | Custom.OmniaDataFeatureArea | Inferred |
| Geos Impacted | (custom field) | Ask user |
| Parent | System.Parent | Default: 5150584 (LSI Parent Epic) |

## Review Preview Format

```
═══════════════════════════════════════════════════════════════
                    WORK ITEM PREVIEW
═══════════════════════════════════════════════════════════════

Work Item Type: [Type]
Title: [Title]

───────────────────────────────────────────────────────────────
                    ASSIGNMENT DETAILS
───────────────────────────────────────────────────────────────
Area Path:       [Full area path]
Product Owner:   [PO name]
Pod Team:        [POD]

───────────────────────────────────────────────────────────────
                    DESCRIPTION (AI-Generated)
───────────────────────────────────────────────────────────────
[Full description]

───────────────────────────────────────────────────────────────
                    ACCEPTANCE CRITERIA (AI-Generated)
───────────────────────────────────────────────────────────────
[Structured AC in 5 sections]

═══════════════════════════════════════════════════════════════

Would you like to create this work item?
[Yes] [No, modify] [Cancel]
```

## CLI Commands

```bash
# Get work item details
az boards work-item show \
  --id <WORK_ITEM_ID> \
  --query "{id:id,title:fields.\"System.Title\",state:fields.\"System.State\"}" \
  --output tsv

# Create work item
az boards work-item create \
  --title "[Title]" \
  --type "Product Backlog Item" \
  --project "Audit Cortex 2" \
  --area "Audit Cortex 2\\Omnia Data" \
  --output tsv

# Link parent work item
az boards work-item relation add \
  --id <CHILD_ID> \
  --relation-type "System.LinkTypes.Hierarchy-Reverse" \
  --target-id <PARENT_ID> \
  --output tsv
```
