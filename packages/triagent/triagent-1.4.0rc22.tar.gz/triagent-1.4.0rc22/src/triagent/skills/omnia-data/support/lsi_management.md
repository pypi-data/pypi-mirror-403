---
name: lsi_management
display_name: "LSI Management"
description: |
  Live Site Incident (LSI) creation and management guide.
  Includes LSI templates, required fields, and service-to-team mapping.
triggers:
  - "LSI"
  - "live site"
  - "incident"
  - "production.*issue"
  - "create.*incident"
version: 1.0.0
---

# Live Site Incident (LSI) Management

## When to Create an LSI

Create an LSI when:
- Production service is degraded or unavailable
- Critical functionality is broken
- Data integrity issues are discovered
- Security incidents occur
- SLA breaches happen

## LSI Title Format

```
[REGION ENV] Service | LSI: Issue Summary
```

Examples:
- `[AME PRD] WorkpaperService | LSI: OutOfMemoryException during purge`
- `[EMA PRD] EngagementService | LSI: API Timeouts exceeding 30s`
- `[APA PRD] StagingService | LSI: Database connection pool exhausted`

## LSI Required Fields

| Field | ADO Path | Required |
|-------|----------|----------|
| **Title** | `System.Title` | Yes |
| **Severity** | `Microsoft.VSTS.Common.Severity` | Yes |
| **Found in Release** | `Custom.FoundinCortexRelease#` | Yes |
| **Target Release** | `Custom.CortexRelease#` | Yes |
| **Environment** | `Custom.CortexEnvironment` | Yes |
| **Parent Epic** | Parent link | Link to 5150584 (Live Site Incidents 2025) |

## Service to Team Mapping

For complete service-to-team mapping, see [Team Information](../../core/team_info.md).

| CloudRoleName | Team | Area Path Suffix |
|---------------|------|------------------|
| `WorkpaperService` | Giga | `Data In Use\Giga` |
| `EngagementService` | Alpha | `Data Acquisition and Preparation\Alpha` |
| `DataKitchenService` | Beta | `Data Acquisition and Preparation\Beta` |
| `StagingService` | Gamma | `Data Management and Activation\Gamma` |
| `SecurityService` | Skyrockets | `Data Management and Activation\Skyrockets` |
| `NotificationService` | Skyrockets | `Data Management and Activation\Skyrockets` |
| `ClientService` | Alpha | `Data Acquisition and Preparation\Alpha` |
| `DataExchangeGateway` | Beta | `Data Acquisition and Preparation\Beta` |

## Create LSI via CLI

```bash
# Create an LSI
az boards work-item create \
  --title "[AME PRD] ServiceName | LSI: Issue Description" \
  --type "Live Site Incident" \
  --project "Audit Cortex 2" \
  --area "Audit Cortex 2\\Omnia Data" \
  --fields "Microsoft.VSTS.Common.Severity=1 - Critical" \
           "Custom.CortexEnvironment=PRD" \
           "Custom.FoundinCortexRelease#=9.6.0" \
  --output tsv

# Link to parent LSI Epic
az boards work-item relation add \
  --id <LSI_ID> \
  --relation-type "System.LinkTypes.Hierarchy-Reverse" \
  --target-id 5150584 \
  --output tsv
```

## LSI Template

```markdown
## Environment
PRD / STG / QAS

## Impact
- **Services Affected**: [list services]
- **Users Affected**: [count or description]
- **Duration**: [start time to resolution]

## Symptoms
[What users/systems observed]

## Root Cause
[Technical explanation - update after investigation]

## Resolution
[Steps taken to resolve]

## Prevention
[Actions to prevent recurrence]
```

## LSI Lifecycle

1. **New** - LSI created, investigation starting
2. **Active** - Investigation in progress
3. **Resolved** - Issue fixed, pending verification
4. **Closed** - Resolution verified, RCA complete

## Parent Epic Reference

All LSIs for 2025 should be linked to:
- **Epic ID**: 5150584
- **Title**: Live Site Incidents 2025
