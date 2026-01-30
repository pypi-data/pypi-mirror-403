---
name: feature_investigation
display_name: "Feature Investigation"
description: |
  Feature search, investigation, and status tracking capabilities.
  Search features by title/description, investigate ownership, and check progress.
triggers:
  - "investigate (feature|PBI|work item)"
  - "who owns"
  - "status of (feature|PBI)"
  - "find.*feature.*(with|about|for)"
  - "search.*feature"
  - "look up feature"
  - "which feature.*handles"
version: 2.1.0
---

# Feature Investigation Mode

## Feature Search

When user wants to find a feature by title or description.

**Trigger Phrases:**
- "Find the feature with bulk export functionality"
- "Search for features related to data validation"
- "Which feature handles user authentication?"

### Search via Azure CLI (Preferred)

```bash
# Search for features by keywords
az boards query \
  --wiql "SELECT [System.Id],[System.Title],[System.State],[Custom.CortexRelease#],[Custom.PodTeam] FROM WorkItems WHERE [System.WorkItemType]='Feature' AND [System.Title] CONTAINS '[search_terms]' ORDER BY [System.Id] DESC" \
  --output tsv

# Search features by state and area
az boards query \
  --wiql "SELECT [System.Id],[System.Title],[System.State] FROM WorkItems WHERE [System.WorkItemType]='Feature' AND [System.State]='Active' AND [System.AreaPath] UNDER 'Audit Cortex 2\\Omnia Data'" \
  --output tsv
```

### Search Results Format

```
═══════════════════════════════════════════════════════════════
                    FEATURE SEARCH RESULTS
═══════════════════════════════════════════════════════════════

Search: "[user's search terms]"
Found: X matching features

───────────────────────────────────────────────────────────────
| # | ID      | Title                  | State  | Release | POD         |
|---|---------|------------------------|--------|---------|-------------|
| 1 | 6234567 | Bulk Export Analytics  | Active | 10.0    | Data In Use |
| 2 | 6345678 | Data Export Features   | Done   | 9.5     | Giga        |

───────────────────────────────────────────────────────────────

Which feature would you like to analyze? (Enter 1, 2, or 3)
═══════════════════════════════════════════════════════════════
```

## Feature Investigation

When user asks about a specific feature.

**Trigger Phrases:**
- "investigate feature 12345"
- "who owns PBI 67890"
- "status of feature 12345"

### Investigation Process

1. Fetch Feature work item details (description, AC)
2. Get all child PBIs with their states
3. Get PR links for each PBI
4. Show ownership and progress summary

### CLI Commands

```bash
# Get Feature details with relations
az boards work-item show \
  --id [feature_id] \
  --expand relations \
  --query "{id:id,title:fields.\"System.Title\",description:fields.\"System.Description\",ac:fields.\"Microsoft.VSTS.Common.AcceptanceCriteria\",relations:relations}" \
  --output json

# Get child work items in batch
az boards work-item show \
  --id [id1] [id2] [id3] \
  --query "[].{id:id,title:fields.\"System.Title\",state:fields.\"System.State\",assignedTo:fields.\"System.AssignedTo\"}" \
  --output tsv
```

## Quick Status Check

For simple status checks without full requirements analysis.

**Trigger Phrases:**
- "status of feature 12345"
- "what's the status of 12345"

### Quick Status Format

```
═══════════════════════════════════════════════════════════════
                    QUICK STATUS: Feature [ID]
═══════════════════════════════════════════════════════════════

[Title]
State: [State] | Release: [X.X] | POD: [POD Name]

Child Items: X total
├── ✓ Done: Y (Z%)
├── ⟳ Active: N (M%)
└── ○ New: P (Q%)

AC Coverage: X/Y Covered (Z%) | N Gap(s) identified

⚠ Actions Needed:
- [Action item 1]
- [Action item 2]

═══════════════════════════════════════════════════════════════
```

## Full Investigation Report

```
═══════════════════════════════════════════════════════════════
                    FEATURE INVESTIGATION
═══════════════════════════════════════════════════════════════

Feature: [ID] - [Title]

───────────────────────────────────────────────────────────────
                    STATUS & OWNERSHIP
───────────────────────────────────────────────────────────────
State:           [State]
Product Owner:   [Name] ([email])
Architect:       [Name]
Pod Team:        [POD]
Target Release:  [Release #]

───────────────────────────────────────────────────────────────
                    CHILD WORK ITEMS
───────────────────────────────────────────────────────────────
| ID | Type | Title | State | Assigned To | PR # |
|----|------|-------|-------|-------------|------|
| [ID] | PBI | [Title] | [State] | [User] | [PR] |

Progress: X/Y items complete (Z%)

───────────────────────────────────────────────────────────────
                    KEY CONTACTS
───────────────────────────────────────────────────────────────
Product Owner: [Name] ([email])
Architect: [Name] ([email])

───────────────────────────────────────────────────────────────
                    OBSERVATIONS
───────────────────────────────────────────────────────────────
- [Status observation]
- [Blockers if any]
- [Next steps]

═══════════════════════════════════════════════════════════════
```

## Related Work Items

For each Feature, also show:
- Parent Epic
- Related Defects (Affects relationship)
- Related Enablers

```bash
# Get related work items
az boards query \
  --wiql "SELECT [System.Id],[System.Title],[System.WorkItemType] FROM WorkItemLinks WHERE ([Source].[System.Id] = [feature_id]) AND ([System.Links.LinkType] = 'Related') MODE (MayContain)" \
  --output tsv
```
