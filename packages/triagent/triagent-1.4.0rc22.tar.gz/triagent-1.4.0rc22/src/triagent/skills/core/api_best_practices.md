# API Best Practices

**Last Updated:** 2026-01-21

Consolidated guidelines for using Azure CLI vs MCP tools across all Omnia Data skills.

## Primary Method: Azure CLI with --output tsv

For token efficiency and accuracy, prefer Azure CLI commands with `--output tsv` format over MCP tools.

### Benefits
- **44% fewer tokens** compared to MCP tool responses
- **More accurate** work item relationship retrieval
- **JQL filtering** at source reduces data transfer
- **Consistent format** for parsing

---

## When to Use Azure CLI (Preferred)

| Operation | Use CLI When |
|-----------|-------------|
| Get work item details | Single or batch retrieval |
| Query work items | WIQL-based filtering |
| List PRs | Repository-specific queries |
| Get PR details | PR ID known |
| Create work items | Simple field values |
| Update work items | State changes, field updates |
| Query builds | Pipeline status checks |

### CLI Command Examples

#### Work Item Operations

```bash
# Get work item details
az boards work-item show \
  --org https://dev.azure.com/symphonyvsts \
  --id <WORK_ITEM_ID> \
  --query "{id:id,title:fields.\"System.Title\",state:fields.\"System.State\"}" \
  --output tsv

# Get work item with acceptance criteria
az boards work-item show \
  --id <WORK_ITEM_ID> \
  --fields "System.Title,System.Description,Microsoft.VSTS.Common.AcceptanceCriteria,System.State" \
  --output json

# Get work item with relations (children, parent)
az boards work-item show \
  --id <WORK_ITEM_ID> \
  --expand relations \
  --query "{id:id,title:fields.\"System.Title\",relations:relations}" \
  --output json

# Query work items with WIQL
az boards query \
  --org https://dev.azure.com/symphonyvsts \
  --project "Audit Cortex 2" \
  --wiql "SELECT [System.Id],[System.Title],[System.State] FROM WorkItems WHERE [System.WorkItemType]='Defect' AND [System.State]='Active'" \
  --output tsv

# Search by area path
az boards query \
  --wiql "SELECT [System.Id],[System.Title] FROM WorkItems WHERE [System.AreaPath] UNDER 'Audit Cortex 2\\Omnia Data'" \
  --output tsv

# Create work item
az boards work-item create \
  --org https://dev.azure.com/symphonyvsts \
  --project "Audit Cortex 2" \
  --type "Defect" \
  --title "Work Item Title" \
  --area "Audit Cortex 2\\Omnia Data\\..." \
  --fields "Microsoft.VSTS.Common.Severity=2 - High" \
  --output tsv

# Update work item
az boards work-item update \
  --id <WORK_ITEM_ID> \
  --state "Active" \
  --output tsv

# Link work items (parent-child)
az boards work-item relation add \
  --id <CHILD_ID> \
  --relation-type "System.LinkTypes.Hierarchy-Reverse" \
  --target-id <PARENT_ID> \
  --output tsv
```

#### Pull Request Operations

```bash
# Get PR details
az repos pr show \
  --id <PR_ID> \
  --query "{id:pullRequestId,title:title,status:status,sourceRef:sourceRefName,targetRef:targetRefName}" \
  --output tsv

# List PRs in repository
az repos pr list \
  --repository <REPO_NAME> \
  --project "Audit Cortex 2" \
  --status active \
  --query "[].{id:pullRequestId,title:title,createdBy:createdBy.displayName}" \
  --output tsv

# Get work items linked to PR
az repos pr work-item list \
  --id <PR_ID> \
  --query "[].{id:id,title:fields.\"System.Title\",type:fields.\"System.WorkItemType\"}" \
  --output tsv

# List PR reviewers
az repos pr reviewer list --id <PR_ID> --output tsv
```

#### Telemetry Queries

```bash
# Switch subscription first
# AME Non-Prod (DEV, QAS)
az account set -s d7ac9c0b-155b-42a8-9d7d-87e883f82d5d

# AME Prod (STG, PRD)
az account set -s 8c71ef53-4473-4862-af36-bae6e40451b2

# Query Log Analytics
az monitor log-analytics query \
  --workspace <WORKSPACE_ID> \
  --analytics-query "
    AppExceptions
    | where TimeGenerated > ago(24h)
    | where AppRoleName == 'ServiceName'
    | summarize count() by ProblemId
    | order by count_ desc
    | take 20
  " -o json
```

---

## When to Use MCP Tools (Fallback)

| Operation | Use MCP When |
|-----------|-------------|
| Wiki operations | No CLI equivalent exists |
| Complex batch operations | Response parsing simpler with JSON |
| Interactive exploration | During context research |
| CLI authentication fails | Token/auth issues |
| Adding inline PR comments | Use `az devops invoke` instead |

### MCP Tool Examples

```bash
# Search wiki (no CLI equivalent)
mcp__azure-devops__search_wiki(
  searchText="[feature area] design",
  project=["Audit Cortex 2"],
  top=5
)

# Get wiki page content (no CLI equivalent)
mcp__azure-devops__wiki_get_page_content(
  wikiIdentifier="Audit-Cortex-2.wiki",
  project="Audit Cortex 2",
  path="/Omnia-Data-Wiki/Technical-Documentation/[path]"
)

# Get work item (MCP fallback)
mcp__azure-devops__wit_get_work_item(
  id=<WORK_ITEM_ID>,
  project="Audit Cortex 2",
  expand="relations"
)

# Batch get work items (MCP fallback)
mcp__azure-devops__wit_get_work_items_batch_by_ids(
  project="Audit Cortex 2",
  ids=[id1, id2, id3]
)

# Search code
mcp__azure-devops__search_code(
  searchText="[function/class name]",
  project=["Audit Cortex 2"],
  repository=["repository-name"],
  top=10
)
```

---

## REST API for HTML Content

Use REST API with JSON payload for HTML-formatted fields (Description, Repro Steps, etc.) as Azure CLI has escaping issues.

```bash
# Get access token
PAT=$(az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798 --query accessToken -o tsv)

# Create work item with HTML fields
curl -s -X POST \
  "https://dev.azure.com/symphonyvsts/Audit%20Cortex%202/_apis/wit/workitems/\$Defect?api-version=7.0" \
  -H "Content-Type: application/json-patch+json" \
  -H "Authorization: Bearer $PAT" \
  -d @/tmp/workitem.json

# Add HTML comment to work item
curl -s -X POST \
  "https://dev.azure.com/symphonyvsts/Audit%20Cortex%202/_apis/wit/workItems/{workItemId}/comments?api-version=7.1-preview.4" \
  -H "Authorization: Bearer $PAT" \
  -H "Content-Type: application/json" \
  -d '{"text": "<h3>Header</h3><p>Content</p>"}'
```

---

## JQL Query Tips

- Use WIQL for complex queries with multiple conditions
- Filter by date: `[System.CreatedDate] >= @Today-7`
- Filter by area: `[System.AreaPath] UNDER 'Audit Cortex 2\\Omnia Data'`
- Combine conditions: `AND`, `OR`, `NOT`
- Use `--query` JMESPath to filter at source, reducing response size
- Request only required fields with `--fields` parameter
- Use `--output tsv` for tabular data, `--output json` for structured data

---

## Field Reference

For complete field documentation including:
- Mandatory vs recommended fields by work item type
- Custom field reference names (Custom.*, AuditCortexScrum.*)
- CLI commands for field listing and queries

See: `../reference/ado-field-reference.md`
