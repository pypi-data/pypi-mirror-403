---
name: requirements_analysis
display_name: "Requirements Analysis"
description: |
  Requirements analysis with AC coverage tracking and gap identification.
  Maps acceptance criteria to child PBIs and identifies coverage gaps.
triggers:
  - "understand.*requirement"
  - "what's the requirement for"
  - "requirements for (feature|PBI)"
  - "AC coverage"
  - "feature requirements"
  - "show.*acceptance criteria"
  - "gap analysis"
version: 2.1.0
---

# Requirements Analysis Mode

## When to Use

**Trigger Phrases:**
- "I want to understand what's the requirement for Feature X"
- "What are the requirements for Feature 12345"
- "Show me the acceptance criteria for Feature X"
- "AC coverage for Feature 12345"

## Analysis Process

1. Fetch Feature work item details (description, AC)
2. Parse and list each AC criterion (AC-1, AC-2, etc.)
3. Get all child PBIs
4. Map AC criteria to child PBIs
5. Get PR links for each PBI
6. Show coverage matrix and gaps

## AC Coverage Analysis

For each acceptance criterion in the Feature:

1. Parse Feature AC into numbered criteria (AC-1, AC-2, etc.)
2. For each child PBI:
   - Search PBI title and description for AC keywords
   - Check if PBI explicitly references AC number
   - Use semantic matching to map PBI to relevant AC
3. Classify coverage:
   - ✓ **Covered**: PBI fully addresses the AC criterion
   - ⚠ **Partial**: PBI addresses some aspects but not all
   - ✗ **Not Covered**: No PBI addresses this AC

## CLI Commands

```bash
# Get Feature details with AC
az boards work-item show \
  --id [feature_id] \
  --expand relations \
  --query "{id:id,title:fields.\"System.Title\",description:fields.\"System.Description\",ac:fields.\"Microsoft.VSTS.Common.AcceptanceCriteria\",relations:relations}" \
  --output json

# Get child work items
az boards work-item show \
  --id [id1] [id2] [id3] \
  --query "[].{id:id,title:fields.\"System.Title\",state:fields.\"System.State\",assignedTo:fields.\"System.AssignedTo\"}" \
  --output tsv

# Get PRs linked to a work item
az repos pr list \
  --project "Audit Cortex 2" \
  --status all \
  --query "[?workItemRefs[?id=='[work_item_id]']].{id:pullRequestId,title:title,status:status}" \
  --output tsv
```

## Requirements Analysis Report

```
═══════════════════════════════════════════════════════════════
              FEATURE REQUIREMENTS ANALYSIS
═══════════════════════════════════════════════════════════════

Feature: [ID] - [Title]
State: [State]
Target Release: [Release #]
Product Owner: [Name] ([email])

───────────────────────────────────────────────────────────────
                    DESCRIPTION
───────────────────────────────────────────────────────────────
[Feature description from work item]

───────────────────────────────────────────────────────────────
                    ACCEPTANCE CRITERIA
───────────────────────────────────────────────────────────────
AC-1: [First acceptance criterion]
AC-2: [Second acceptance criterion]
AC-3: [Third acceptance criterion]
...

───────────────────────────────────────────────────────────────
                    AC COVERAGE MATRIX
───────────────────────────────────────────────────────────────
| AC # | Criterion Summary | Covered By | Status |
|------|-------------------|------------|--------|
| AC-1 | [Summary] | PBI-123, PBI-456 | ✓ Covered |
| AC-2 | [Summary] | PBI-789 | ⚠ Partial |
| AC-3 | [Summary] | - | ✗ Not Covered |

Overall Coverage: X/Y Fully Covered (Z%), N Partial, M Gaps

───────────────────────────────────────────────────────────────
                    CHILD WORK ITEMS STATUS
───────────────────────────────────────────────────────────────
| ID | Title | State | Assigned To | PR # | PR Status | Covers |
|----|-------|-------|-------------|------|-----------|--------|
| 123456 | [PBI Title] | Done | [User] | PR-789 | Completed | AC-1 |
| 123457 | [PBI Title] | Active | [User] | PR-790 | In Review | AC-2 |

Progress: X/Y items complete (Z%)

═══════════════════════════════════════════════════════════════
```

## Gap Analysis

Identify and report:
1. **Uncovered AC**: AC criteria with no PBI addressing them
2. **Partially Covered AC**: AC criteria only partially addressed
3. **Blocked Items**: PBIs that are blocked or at risk
4. **Unassigned Items**: PBIs without assignee
5. **Missing PRs**: Active PBIs without linked PRs

## Gap Analysis Report

```
───────────────────────────────────────────────────────────────
                    GAP ANALYSIS
───────────────────────────────────────────────────────────────
⚠ GAPS IDENTIFIED:

1. AC-3 "[Criterion text]" - NOT COVERED
   ❌ No PBI exists for this requirement
   Recommendation: Create new PBI to implement this functionality

2. AC-2 "[Criterion text]" - PARTIALLY COVERED
   ⚠ PBI-123457 in progress but only covers [specific aspect]
   Recommendation: Update PBI or create additional PBI for full coverage

───────────────────────────────────────────────────────────────
                    RECOMMENDED ACTIONS
───────────────────────────────────────────────────────────────
1. ➕ Create new PBI: "[Suggested title]" (for AC-3)
2. 📝 Update PBI-123457: Add [missing aspect] for full AC-2 coverage
3. 👤 Assign PBI-123458 to a developer
4. 🔍 Review PR-790 to unblock AC-2 completion

Would you like me to create PBIs for the missing requirements?

───────────────────────────────────────────────────────────────
                    KEY CONTACTS
───────────────────────────────────────────────────────────────
Product Owner: [Name] ([email])
Architect: [Name] ([email])
Tech Lead: [Name] ([email])
QA Lead: [Name] ([email])

═══════════════════════════════════════════════════════════════
```

## Generating Recommendations

Based on gap analysis, generate actionable recommendations:

| Gap Type | Recommendation |
|----------|----------------|
| Uncovered AC | Create new PBI with suggested title and description |
| Partial Coverage | Update existing PBI or create supplementary PBI |
| Blocked PBI | Identify blocker, suggest escalation |
| Unassigned PBI | Suggest team member based on expertise |
| Missing PR | Flag for developer follow-up |

## Integration with Work Item Creation

After gap analysis, offer to create PBIs:

```
Would you like me to create PBIs for the missing requirements?

1. Create PBI for AC-3: "[Suggested title]"
2. Create all missing PBIs (3 items)
3. No, just show the report
```

If user selects option 1 or 2, invoke the work_item_creation workflow with pre-populated context from the Feature.
