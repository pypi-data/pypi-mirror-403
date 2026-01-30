# Organization Context

**Last Updated:** 2026-01-21

Azure DevOps organization and project constants for Omnia Data skills.

## Core Settings

| Setting | Value |
|---------|-------|
| **Organization URL** | `https://dev.azure.com/symphonyvsts` |
| **Project** | `Audit Cortex 2` |
| **Project ID** | `Audit Cortex 2` (use name, not GUID) |
| **Wiki Identifier** | `Audit-Cortex-2.wiki` |

## URL Patterns

### Work Items
```
https://dev.azure.com/symphonyvsts/Audit%20Cortex%202/_workitems/edit/{WORK_ITEM_ID}
```

### Pull Requests
```
https://dev.azure.com/symphonyvsts/Audit%20Cortex%202/_git/{REPO_NAME}/pullrequest/{PR_ID}
```

### Repositories
```
https://dev.azure.com/symphonyvsts/Audit%20Cortex%202/_git/{REPO_NAME}
```

### Wiki Pages
```
https://dev.azure.com/symphonyvsts/Audit%20Cortex%202/_wiki/wikis/Audit-Cortex-2.wiki/{PAGE_ID}/{PAGE_PATH}
```

### Pipelines
```
https://dev.azure.com/symphonyvsts/Audit%20Cortex%202/_build?definitionId={DEFINITION_ID}
```

## Azure CLI Defaults

When using Azure CLI commands, these defaults apply:

```bash
# Organization (always required)
--org https://dev.azure.com/symphonyvsts

# Project (required for most operations)
--project "Audit Cortex 2"
```

## MCP Tool Defaults

When using Azure DevOps MCP tools:

```python
# Project parameter
project="Audit Cortex 2"

# Wiki identifier
wikiIdentifier="Audit-Cortex-2.wiki"
```

## Area Path Root

All Omnia Data work items use area paths under:
```
Audit Cortex 2\Omnia Data\...
```

## Iteration Path Root

All Omnia Data iterations use paths under:
```
Audit Cortex 2\Program Increment XX
```

Where `XX` is the current Program Increment number (e.g., 22, 23).
