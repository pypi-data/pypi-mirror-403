---
name: ado_work_items
display_name: "ADO Work Items"
description: |
  Azure DevOps work item management for support tasks.
  Includes CLI commands, templates, and WIQL queries for defects and incidents.
triggers:
  - "work.*item"
  - "defect"
  - "create.*bug"
  - "ADO"
  - "azure.*devops"
version: 1.0.0
---

# Work Item Management

## Creating Work Items

When creating work items, gather required information:

| Field | Description | Required |
|-------|-------------|----------|
| Title | Clear, descriptive summary | Yes |
| Work Item Type | Bug, Task, User Story, etc. | Yes |
| Description | Detailed explanation | Yes |
| Area Path | Team/component area | Recommended |
| Priority | 1 (Critical) to 4 (Low) | Recommended |

## CLI Commands for Work Item Management (Preferred)

**44% fewer tokens compared to MCP tools**

```bash
# Get work item by ID (CLI preferred)
az boards work-item show \
  --id <WORK_ITEM_ID> \
  --query "{id:id,title:fields.\"System.Title\",state:fields.\"System.State\",type:fields.\"System.WorkItemType\"}" \
  --output tsv

# Create a defect (CLI preferred)
az boards work-item create \
  --title "[AME PRD] ServiceName | Issue Description" \
  --type "Defect" \
  --project "Audit Cortex 2" \
  --area "Audit Cortex 2\\Omnia Data" \
  --fields "Microsoft.VSTS.Common.Severity=2 - High" \
  --output tsv

# Create an LSI (CLI preferred)
az boards work-item create \
  --title "[AME PRD] ServiceName | LSI: Issue Description" \
  --type "Live Site Incident" \
  --project "Audit Cortex 2" \
  --area "Audit Cortex 2\\Omnia Data" \
  --fields "Microsoft.VSTS.Common.Severity=1 - Critical" \
  --output tsv

# Update work item state (CLI preferred)
az boards work-item update \
  --id <WORK_ITEM_ID> \
  --state "Active" \
  --output tsv

# Query work items by WIQL (CLI preferred)
az boards query \
  --wiql "SELECT [System.Id],[System.Title],[System.State] FROM WorkItems WHERE [System.WorkItemType]='Defect' AND [System.State]='Active' AND [System.AreaPath] UNDER 'Audit Cortex 2\\Omnia Data' ORDER BY [System.CreatedDate] DESC" \
  --output tsv

# Link parent work item (CLI preferred)
az boards work-item relation add \
  --id <CHILD_ID> \
  --relation-type "System.LinkTypes.Hierarchy-Reverse" \
  --target-id <PARENT_ID> \
  --output tsv
```

## Defect Template

```markdown
## Environment
[PRD/STG/QAS/DEV]

## Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Impact
[User/business impact]

## Related Information
- Logs: [link]
- Screenshot: [if applicable]
- Related work items: [IDs]
```

## REST API for HTML Fields

```bash
# Get access token
PAT=$(az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798 --query accessToken -o tsv)

# Create work item with HTML fields
curl -s -X POST \
  "https://dev.azure.com/symphonyvsts/Audit%20Cortex%202/_apis/wit/workitems/\$Defect?api-version=7.0" \
  -H "Content-Type: application/json-patch+json" \
  -H "Authorization: Bearer $PAT" \
  -d @/tmp/workitem.json
```

## Common WIQL Queries

### Active Defects by Team
```sql
SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo]
FROM WorkItems
WHERE [System.WorkItemType] = 'Defect'
  AND [System.State] = 'Active'
  AND [System.AreaPath] UNDER 'Audit Cortex 2\Omnia Data'
ORDER BY [Microsoft.VSTS.Common.Severity] ASC, [System.CreatedDate] DESC
```

### LSIs by Severity
```sql
SELECT [System.Id], [System.Title], [System.State], [Microsoft.VSTS.Common.Severity]
FROM WorkItems
WHERE [System.WorkItemType] = 'Live Site Incident'
  AND [System.State] <> 'Closed'
ORDER BY [Microsoft.VSTS.Common.Severity] ASC
```

### Recent Work Items
```sql
SELECT [System.Id], [System.Title], [System.WorkItemType], [System.CreatedDate]
FROM WorkItems
WHERE [System.CreatedDate] >= @Today - 7
  AND [System.AreaPath] UNDER 'Audit Cortex 2\Omnia Data'
ORDER BY [System.CreatedDate] DESC
```

## Priority and Severity Mapping

| Severity | Priority | Response |
|----------|----------|----------|
| 1 - Critical | 1 | Immediate |
| 2 - High | 2 | Within 4 hours |
| 3 - Medium | 3 | Within sprint |
| 4 - Low | 4 | Backlog |
