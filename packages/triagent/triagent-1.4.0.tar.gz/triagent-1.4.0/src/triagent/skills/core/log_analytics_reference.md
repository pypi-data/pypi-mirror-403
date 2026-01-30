# Log Analytics Workspace Reference

**Last Updated:** 2026-01-21

Log Analytics workspace IDs by region and environment for telemetry investigation.

## AME (Americas)

| Environment | Workspace Name | Workspace ID | Subscription |
|-------------|----------------|--------------|--------------|
| DEV, DEV1, DEV2, QAS, QAS1, QAS2, LOD | npdamecortexlaw | `874aa8fb-6d29-4521-920f-63ac7168404e` | US_AUDIT_PREPROD |
| STG, STG2, CNT1, PRD | prdamecortexlaw | `ed9e6912-0544-405b-921b-f2d6aad2155e` | US_AUDIT_PROD |
| BCP | bcpamecortexlaw | `ef540bd5-ce75-4aac-8d29-7aa576b9d537` | US_AUDIT_PROD |

## EMA (Europe/Middle East/Africa)

| Environment | Workspace Name | Workspace ID | Subscription |
|-------------|----------------|--------------|--------------|
| INT | icortexjeemala | `8c9be877-4f75-45ed-b34a-e067a87918c0` | US-AZSUB-EMA-AUD-NPD-01 |
| STG | scortexjeemala | `9cb4fe2f-645d-45ae-83c0-fe5b88309aef` | US-AZSUB-EMA-AUD-PRD-01 |
| PRD | prdemacortexlaw | `b3f751c4-5cce-4caa-a3fb-eccbe019c661` | US-AZSUB-EMA-AUD-PRD-01 |

## APA (Asia Pacific)

| Environment | Workspace Name | Workspace ID | Subscription |
|-------------|----------------|--------------|--------------|
| STG, PRD | prdapacortexlaw | `d333bffc-5984-4bcd-a600-064988e7e2ec` | US_AUDIT_APA |

---

## Quick Reference by Environment

| Environment | Region | Workspace ID |
|-------------|--------|--------------|
| DEV | AME | `874aa8fb-6d29-4521-920f-63ac7168404e` |
| DEV1 | AME | `874aa8fb-6d29-4521-920f-63ac7168404e` |
| DEV2 | AME | `874aa8fb-6d29-4521-920f-63ac7168404e` |
| QAS | AME | `874aa8fb-6d29-4521-920f-63ac7168404e` |
| QAS1 | AME | `874aa8fb-6d29-4521-920f-63ac7168404e` |
| QAS2 | AME | `874aa8fb-6d29-4521-920f-63ac7168404e` |
| LOD | AME | `874aa8fb-6d29-4521-920f-63ac7168404e` |
| STG | AME | `ed9e6912-0544-405b-921b-f2d6aad2155e` |
| STG2 | AME | `ed9e6912-0544-405b-921b-f2d6aad2155e` |
| CNT1 | AME | `ed9e6912-0544-405b-921b-f2d6aad2155e` |
| PRD | AME | `ed9e6912-0544-405b-921b-f2d6aad2155e` |
| BCP | AME | `ef540bd5-ce75-4aac-8d29-7aa576b9d537` |
| INT | EMA | `8c9be877-4f75-45ed-b34a-e067a87918c0` |
| STG | EMA | `9cb4fe2f-645d-45ae-83c0-fe5b88309aef` |
| PRD | EMA | `b3f751c4-5cce-4caa-a3fb-eccbe019c661` |
| STG | APA | `d333bffc-5984-4bcd-a600-064988e7e2ec` |
| PRD | APA | `d333bffc-5984-4bcd-a600-064988e7e2ec` |

---

## Subscription IDs

| Subscription | Subscription ID | Environments |
|--------------|-----------------|--------------|
| US_AUDIT_PREPROD | `d7ac9c0b-155b-42a8-9d7d-87e883f82d5d` | AME DEV, QAS |
| US_AUDIT_PROD | `8c71ef53-4473-4862-af36-bae6e40451b2` | AME STG, PRD |
| US-AZSUB-EMA-AUD-PRD-01 | `62c1dd5c-d918-4a4d-b0ee-18d5e7d5071b` | EMA STG, PRD |
| US_AUDIT_APA | `b2fcc9cc-5757-42d3-980c-d92d66bab682` | APA STG, PRD |

---

## Azure CLI Commands

### Switch Subscription

```bash
# AME Non-Prod (DEV, QAS)
az account set -s d7ac9c0b-155b-42a8-9d7d-87e883f82d5d

# AME Prod (STG, PRD)
az account set -s 8c71ef53-4473-4862-af36-bae6e40451b2

# EMA Prod (STG, PRD)
az account set -s 62c1dd5c-d918-4a4d-b0ee-18d5e7d5071b

# APA (STG, PRD)
az account set -s b2fcc9cc-5757-42d3-980c-d92d66bab682
```

### Query Log Analytics

```bash
# Query exceptions
az monitor log-analytics query \
  --workspace <WORKSPACE_ID> \
  --analytics-query "
    AppExceptions
    | where TimeGenerated > ago(24h)
    | where AppRoleName in ('ServiceName')
    | summarize Count=count() by ProblemId
    | order by Count desc
    | take 20
  " -o json
```

### Common KQL Queries

```kusto
// Exception summary by service
AppExceptions
| where TimeGenerated > ago(24h)
| where AppRoleName == "ServiceName"
| summarize count() by ExceptionType, ProblemId
| order by count_ desc

// Exception timeline
AppExceptions
| where TimeGenerated > ago(24h)
| where AppRoleName == "ServiceName"
| summarize count() by bin(TimeGenerated, 1h)
| order by TimeGenerated desc

// Request failures
AppRequests
| where TimeGenerated > ago(24h)
| where Success == false
| where AppRoleName == "ServiceName"
| summarize count() by ResultCode
| order by count_ desc
```
