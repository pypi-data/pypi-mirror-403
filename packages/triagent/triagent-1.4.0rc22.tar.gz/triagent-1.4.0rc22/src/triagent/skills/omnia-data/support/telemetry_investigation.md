---
name: telemetry_investigation
display_name: "Telemetry Investigation"
description: |
  Guide for investigating telemetry and exceptions using Azure Log Analytics.
  Includes Kusto query patterns, workspace references, and investigation workflow.
triggers:
  - "investigate"
  - "exception"
  - "telemetry"
  - "error.*log"
  - "kusto"
  - "log analytics"
version: 1.0.0
---

# Telemetry Investigation Guide

## Investigation Workflow

1. **Gather Context**
   - Environment (PRD, STG, QAS, DEV)
   - Time range of issue
   - Affected service/AppRoleName
   - Error symptoms or user reports

2. **Query Exceptions**
   ```kusto
   AppExceptions
   | where TimeGenerated > ago(24h)
   | where AppRoleName == "ServiceName"
   | summarize count() by ExceptionType, ProblemId
   | order by count_ desc
   ```

3. **Analyze Patterns**
   - Exception frequency over time
   - Correlation with deployments
   - Impact on request success rates
   - User/client distribution

## Log Analytics Workspace Reference

For complete workspace IDs and query examples, see [Log Analytics Reference](../../core/log_analytics_reference.md).

| Region | Environment | Workspace ID |
|--------|-------------|--------------|
| AME | DEV, QAS | `874aa8fb-6d29-4521-920f-63ac7168404e` |
| AME | STG, PRD | `ed9e6912-0544-405b-921b-f2d6aad2155e` |
| EMA | PRD | `b3f751c4-5cce-4caa-a3fb-eccbe019c661` |
| APA | PRD | `d333bffc-5984-4bcd-a600-064988e7e2ec` |

## Azure CLI Commands

```bash
# Switch to correct subscription first
# AME Non-Prod (DEV, QAS)
az account set -s d7ac9c0b-155b-42a8-9d7d-87e883f82d5d

# AME Prod (STG, PRD)
az account set -s 8c71ef53-4473-4862-af36-bae6e40451b2

# Query exceptions
az monitor log-analytics query \
  --workspace ed9e6912-0544-405b-921b-f2d6aad2155e \
  --analytics-query "
    AppExceptions
    | where TimeGenerated > ago(30d)
    | where AppRoleName in ('WorkpaperService')
    | summarize Count=count() by ProblemId
    | order by Count desc
    | take 20
  " -o json
```

## Common Kusto Queries

### Exception Summary by Service
```kusto
AppExceptions
| where TimeGenerated > ago(24h)
| summarize count() by AppRoleName, ExceptionType
| order by count_ desc
```

### Exception Timeline
```kusto
AppExceptions
| where TimeGenerated > ago(24h)
| where AppRoleName == "ServiceName"
| summarize count() by bin(TimeGenerated, 1h)
| render timechart
```

### Request Failure Rate
```kusto
AppRequests
| where TimeGenerated > ago(24h)
| where AppRoleName == "ServiceName"
| summarize
    Total = count(),
    Failed = countif(Success == false),
    FailureRate = round(100.0 * countif(Success == false) / count(), 2)
    by bin(TimeGenerated, 1h)
```

### Trace Correlation
```kusto
// Find related traces for an exception
let operationId = "abc123";
union AppTraces, AppExceptions, AppRequests
| where OperationId == operationId
| project TimeGenerated, ItemType, Message, ExceptionType, Name
| order by TimeGenerated asc
```

## Clarifying Questions Guidelines

**IMPORTANT**: When a user asks for investigation, use AskUserQuestion to gather:

1. **Environment** (Required)
   - AME Non-Prod: DEV, DEV1, DEV2, QAS, QAS1, QAS2, LOD
   - AME Prod: STG, STG2, CNT1, PRD, BCP

2. **Timeframe** (Required)
   - Last 1 hour (default for active issues)
   - Last 24 hours
   - Last 7 days
   - Custom range

3. **Service** (if not specified)
   - Which CloudRoleName/service is affected?

### Example:
User: "Investigate the staging service errors"
Agent: [Uses AskUserQuestion tool]
  Question 1: "Which environment?" Options: DEV, QAS, STG, PRD
  Question 2: "What timeframe?" Options: Last 1 hour, Last 24 hours, etc.
