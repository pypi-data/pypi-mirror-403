---
name: finops
display_name: "FinOps Cost Analysis"
description: Use this skill when the user asks about Azure costs, subscription costs, FinOps reporting, cost breakdown by region (AME, EMA, APA), Databricks costs, SQL Database costs, Virtual Machine costs, elastic pool costs, storage costs, HANA costs, JE costs, Data Engineering costs, Specialist Tools costs, or needs Azure CLI commands for cost management. Also use when user says "finops", "cost analysis", "spend report", "billing", "show costs", "DBX costs", "DATAENG costs", "DATASPEC costs", "Data Engineering", "Specialist Tools", "generate Databricks daily report", "generate Databricks weekly report", "generate Databricks monthly report", "Databricks report for Omnia Data", "Omnia Data cost report", or asks about subscription information, resource inventory, or environment costs (DEV, DEV1, DEV2, QAS, STG, PRD).
version: "2.2.0"
tags: [finops, azure-costs, databricks-costs, cost-analysis, subscription-costs]
requires: []
triggers:
  - "finops"
  - "cost analysis"
  - "Azure costs"
  - "Databricks costs"
  - "subscription costs"
  - "spend report"
  - "billing"
  - "DBX costs"
  - "DATAENG costs"
  - "DATASPEC costs"
---

# FinOps - Azure Cost Management Skill

This skill provides Azure cost management capabilities, subscription information, and generates appropriate Azure CLI commands for FinOps reporting.

---

## Report Generation Workflow

**IMPORTANT**: Before following manual instructions, use this automated workflow for standard reports.

### Step 1: Check for Existing Script

```bash
SCRIPT_PATH="$HOME/.claude/skills/finops/scripts/generate_finops_report.py"
if [ -f "$SCRIPT_PATH" ]; then
    echo "Script found - use automated generation"
else
    echo "Script not found - use manual fallback"
fi
```

### Step 2: Automated Generation (Preferred)

If the script exists, use it for standard reports:

```bash
# Daily report (last 30 days) - most common
python ~/.claude/skills/finops/scripts/generate_finops_report.py --open-browser

# Weekly report (last 8 weeks)
python ~/.claude/skills/finops/scripts/generate_finops_report.py --report-type weekly --open-browser

# Monthly report (last 6 months)
python ~/.claude/skills/finops/scripts/generate_finops_report.py --report-type monthly --open-browser

# Custom date range
python ~/.claude/skills/finops/scripts/generate_finops_report.py \
    --start-date 2025-12-01 --end-date 2026-01-21 --open-browser

# Verbose output for debugging
python ~/.claude/skills/finops/scripts/generate_finops_report.py --verbose --open-browser
```

### Script Command-Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--start-date` | 30 days ago | Start date (YYYY-MM-DD) |
| `--end-date` | Today | End date (YYYY-MM-DD) |
| `--output` | `audit-cortex-2-wiki/finops-cost-report.html` | Output file path |
| `--report-type` | `daily` | Report type: daily, weekly, monthly |
| `--regions` | `ame,ema` | Comma-separated regions |
| `--open-browser` | False | Open report in browser after generation |
| `--config` | `finops_config.json` | Path to config file |
| `--verbose` | False | Enable verbose output |

### Step 3: Manual Fallback (Special Cases Only)

Use the manual workflow in the "Interactive HTML Report Generation" section below ONLY when:
- Script file is missing
- Non-PROD subscriptions are requested (STAGE, NPD, LOAD)
- APA region is requested
- Custom filters (specific resource groups, meter categories)
- Comparison reports (PROD vs STAGE)

### Smart Routing Decision Tree

```
User Request Received
        │
        ▼
Check: Does generate_finops_report.py exist?
        │
   ┌────┴────┐
   │         │
  YES        NO
   │         │
   ▼         ▼
Can script   Use Manual
handle it?   Workflow
   │
┌──┴──┐
YES   NO
│     │
▼     ▼
Run   Use Manual
Script Workflow
```

**Script CAN handle:**
- Daily/Weekly/Monthly reports
- AME PROD and EMA PROD subscriptions
- Custom date ranges
- White theme (Deloitte Omnia)
- Open in browser

**Script CANNOT handle (use manual):**
- Non-PROD subscriptions (STAGE, NPD, LOAD)
- APA region
- Custom resource group filters
- Custom meter category filters
- Comparison reports

---

## CLI Selection Guide

| Scenario | CLI Command | Notes |
|----------|-------------|-------|
| General access | `az` | Regular account |
| Elevated access | `az-elevated` | Use for DATAENG, cost queries |
| Cost Management denied | Use resource enumeration | US_AUDIT_PROD/PREPROD |

---

## Domain Definitions

| Domain Code | Domain Name | Description | Resource Group Pattern |
|-------------|-------------|-------------|------------------------|
| DATAENG | Data Engineering | Core data engineering workloads | Contains "DATAENG" in RG name |
| DATASPEC | Specialist Tools | Specialized tooling and analytics | Contains "DATASPEC" in RG name |

**Domain Classification Rules:**
- If resource group name contains `DATAENG` → **Data Engineering**
- If resource group name contains `DATASPEC` → **Specialist Tools**
- Other resource groups (NetworkWatcherRG, VAULT-RG, etc.) → **Infrastructure/Shared**

---

## Subscription Quick Reference

### Elevated Account (az-elevated)

#### AME Region
| Environment | Subscription Name | ID |
|-------------|-------------------|-----|
| PROD | US_AUDIT_PROD | `8c71ef53-4473-4862-af36-bae6e40451b2` |
| NON-PROD | US_AUDIT_PREPROD | `d7ac9c0b-155b-42a8-9d7d-87e883f82d5d` |
| DATAENG-PROD | CORTEX AME DATAENGDBX PROD1-PRD | `39d5984b-c003-4b98-9e3a-434538adb961` |
| DATAENG-STAGE | CORTEX AME DATAENGDBX STAGE-PRD | `d0987589-0bfb-474a-8ed6-81970143a96b` |
| DATAENG-NPD | CORTEX AME DATAENGDBX NONPROD-NPD | `893331bc-b8fe-4898-97be-ba5246250d6b` |
| DATAENG-LOAD | CORTEX AME DATAENGDBX LOAD-NPD | `c09f5025-1f53-433b-b509-7dd09aecf784` |
| SBX | ODATAOPENAI-SBX | `5eefdd74-582a-411a-9168-6a3b7ac1de4c` |

#### EMA Region
| Environment | Subscription Name | ID |
|-------------|-------------------|-----|
| PROD | EMA-AUD-PRD-01 | `62c1dd5c-d918-4a4d-b0ee-18d5e7d5071b` |
| NON-PROD | EMA-AUD-NPD-01 | `429c67ab-6761-4617-a512-a4743395cede` |
| DATAENG-PROD | CORTEX EMA DATAENGDBX PROD-PRD | `e4eefd26-facd-439a-b5a2-adf03917b068` |
| DATAENG-STAGE | CORTEX EMA DATAENGDBX STAGE-PRD | `b2b82846-3553-4541-be05-db0633ce1a92` |

#### APA Region
| Environment | Subscription Name | ID |
|-------------|-------------------|-----|
| PROD | APA-AUD-PRD-01 | `b2fcc9cc-5757-42d3-980c-d92d66bab682` |
| NON-PROD | APA-AUD-NPD-01 | `579d5d7f-d0b3-4cc6-9c61-6715b876a8fe` |
| DATAENG-STAGE | CORTEX APA DATAENGDBX STAGE-PRD | `159571fe-cab6-4fbe-9f44-51f6bb0f1468` |

### Regular Account (az) - Additional Subscriptions

#### OMNIA Subscriptions
| Region | Environment | Subscription Name | ID |
|--------|-------------|-------------------|-----|
| AME | OMNIA-PROD | OMNIA01-AME-PRD | `0ec5ddb9-8072-4fc5-a323-248cf4edee8b` |
| AME | OMNIA-NPD | OMNIA01-AME-NPD | `0a2ec486-c017-48af-9360-f238ea4b2ad3` |
| EMA | OMNIA-PROD | OMNIA01-EMA-PRD | `8dd5830e-7668-49ae-a32e-c03a595f7112` |
| EMA | OMNIA-NPD | OMNIA01-EMA-NPD | `e1c884d2-9b98-4b33-9f11-6aa45c32e2f5` |
| EMA | OMNIADATA-NPD | OMNIADATA-NPD | `ed789ce9-525c-4d62-8f49-a264b2074f2c` |
| APA | OMNIA-PROD | OMNIA01-APA-PRD | `ba56a799-5bff-488d-9828-f3b954165a80` |
| APA | OMNIA-NPD | OMNIA01-APA-NPD | `ac11c35d-336b-4782-af2f-3c14a7bc9c35` |

### DBX (Databricks) Subscriptions
| Region | Environment | ID |
|--------|-------------|-----|
| AME | PROD | `39d5984b-c003-4b98-9e3a-434538adb961` |
| AME | STAGE | `d0987589-0bfb-474a-8ed6-81970143a96b` |
| AME | NON-PROD | `893331bc-b8fe-4898-97be-ba5246250d6b` |
| AME | LOAD | `c09f5025-1f53-433b-b509-7dd09aecf784` |
| EMA | PROD | `e4eefd26-facd-439a-b5a2-adf03917b068` |
| EMA | STAGE | `b2b82846-3553-4541-be05-db0633ce1a92` |
| APA | STAGE | `159571fe-cab6-4fbe-9f44-51f6bb0f1468` |

---

## Resource Group Inventory by Domain

### AME DATAENG PROD (39d5984b-c003-4b98-9e3a-434538adb961)

#### Data Engineering Resource Groups
| Resource Group | Location |
|----------------|----------|
| AZRG-USE2-AUD-PRDCORTEXAMEDATAENGBCP1-PRD-001 | centralus |
| AZRG-USE2-AUD-CORTEXAMEDATAENGDBXBCPMRG-1 | centralus |
| AZRG-USE2-AUD-CORTEXAMEDATAENGDBXBCPMRG-2 | centralus |
| AZRG-USE2-AUD-PRDCORTEXAMEDATAENGPROD1-PRD-001 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATAENGDBXPRODMRG-1 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATAENGDBXPRODMRG-2 | eastus2 |

#### Specialist Tools Resource Groups
| Resource Group | Location |
|----------------|----------|
| AZRG-USE2-AUD-PRDCORTEXAMEDATASPECBCP-PRD-001 | centralus |
| AZRG-USE2-AUD-CORTEXAMEDATASPECDBXBCPMRG-1 | centralus |
| AZRG-USE2-AUD-PRDCORTEXAMEDATASPECPROD1-PRD-001 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATASPECDBXPRODMRG-1 | eastus2 |

### AME DATAENG STAGE (d0987589-0bfb-474a-8ed6-81970143a96b)

#### Data Engineering Resource Groups
| Resource Group | Location |
|----------------|----------|
| AZRG-CUS-AUD-PRDCORTEXAMEDATAENGSTAGE2-PRD-001 | centralus |
| AZRG-CUS-AUD-CORTEXAMEDATAENGDBXSTAGE2MRG-1 | centralus |
| AZRG-USE2-AUD-PRDCORTEXAMEDATAENGSTAGE-PRD-001 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATAENGDBXSTAGEMRG-1 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATAENGDBXSTAGEMRG-2 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATAENGDBXCNT1MRG-1 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATAENGDBXCNT1MRG-2 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATAENGDBXSTAGE2MRG-1 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATAENGDBXSTAGE2MRG-2 | eastus2 |

#### Specialist Tools Resource Groups
| Resource Group | Location |
|----------------|----------|
| AZRG-CUS-AUD-PRDCORTEXAMEDATASPECSTAGE2-PRD-001 | centralus |
| AZRG-CUS-AUD-CORTEXAMEDATASPECDBXSTAGE2MRG-1 | centralus |
| AZRG-USE2-AUD-PRDCORTEXAMEDATASPECSTAGE-PRD-001 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATASPECDBXCNT1MRG-1 | eastus2 |
| AZRG-USE2-AUD-PRDCORTEXAMEDATASPECDBXSTAGE-STG-001 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATASPECDBXSTAGEMRG-1 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATASPECDBXSTAGE2MRG-1 | eastus2 |

### AME DATAENG NPD (893331bc-b8fe-4898-97be-ba5246250d6b)

#### Data Engineering Resource Groups
| Resource Group | Location |
|----------------|----------|
| AZRG_AUD_ODATA_DIVA_USE2_DBX_DATAENG1_MRG | eastus2 |
| AZRG_AUD_ODATA_DIVA_USE2_DBX_DATAENG2_MRG | eastus2 |
| AZRG_AUD_ODATA_DEVA_USE2_DBX_DATAENG1_MRG | eastus2 |
| AZRG_AUD_ODATA_DEVA_USE2_DBX_DATAENG2_MRG | eastus2 |
| AZRG-USE2-AUD-NPDCORTEXAMEDATAENGDBXNONPROD-DEV-001 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATAENGDBXNONPRODMRG-1 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATAENGDBXNONPRODMRG-2 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATAENGDBXNONPRODMRG-3 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATAENGDBXNONPRODMRG-4 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATAENGDBXNONPRODMRG-5 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATAENGDBXNONPRODMRG-6 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATAENGDBXNONPRODMRG-7 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATAENGDBXNONPRODMRG-8 | eastus2 |
| AZRG-USE2-AUD-cortexAMEDATAENGDBXNONPRODMRG-9 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATAENGDBXNONPRODMRG-10 | eastus2 |
| AZRG-USE2-AUD-cortexAMEDATAENGDBXNONPRODMRG-11 | eastus2 |
| AZRG-USE2-AUD-cortexAMEDATAENGDBXNONPRODMRG-12 | eastus2 |
| AZRG-USE2-AUD-cortexAMEDATAENGDBXNONPRODMRG-13 | eastus2 |
| AZRG-USE2-AUD-cortexAMEDATAENGDBXNONPRODMRG-14 | eastus2 |
| AZRG-CUS-AUD-NPDCORTEXAMEDATAENG-NPD-001 | centralus |
| AZRG-CUS-AUD-cortexAMEDATAENGDBXNONPRODMRG-1 | centralus |
| AZRG-CUS-AUD-cortexAMEDATAENGDBXNONPRODMRG-2 | centralus |

#### Specialist Tools Resource Groups
| Resource Group | Location |
|----------------|----------|
| AZRG_AUD_ODATA_DIVA_USE2_DBX_DATASPEC_MRG | eastus2 |
| AZRG_AUD_ODATA_DEVA_USE2_DBX_DATASPEC_MRG | eastus2 |
| AZRG-USE2-AUD-NPDCORTEXAMEDATASPECDBXNONPROD-DEV-001 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATASPECDBXNONPRODMRG-1 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATASPECDBXNONPRODMRG-2 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATASPECDBXNONPRODMRG-3 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATASPECDBXNONPRODMRG-4 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATASPECDBXNONPRODMRG-5 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATASPECDBXNONPRODMRG-6 | eastus2 |
| AZRG-CUS-AUD-NPDCORTEXAMEDATASPEC-NPD-001 | centralus |
| AZRG-CUS-AUD-cortexAMEDATASPECDBXNONPRODMRG-1 | centralus |

### AME DATAENG LOAD (c09f5025-1f53-433b-b509-7dd09aecf784)

#### Data Engineering Resource Groups
| Resource Group | Location |
|----------------|----------|
| AZRG-USE2-AUD-NPDCORTEXAMEDATAENGLOAD-DEV-001 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATAENGDBXLOADMRG-1 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATAENGDBXLOADMRG-2 | eastus2 |
| AZRG-USE2-AUD-NPDCORTEXAMEDATAENGLOAD2-DEV-001 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATAENGDBXLOAD2MRG-1 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATAENGDBXLOAD2MRG-2 | eastus2 |

#### Specialist Tools Resource Groups
| Resource Group | Location |
|----------------|----------|
| AZRG-USE2-AUD-NPDCORTEXAMEDATASPECLOAD-DEV-001 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATASPECDBXLOADMRG-1 | eastus2 |
| AZRG-USE2-AUD-NPDCORTEXAMEDATASPECLOAD2-DEV-001 | eastus2 |
| AZRG-USE2-AUD-CORTEXAMEDATASPECDBXLOAD2MRG-1 | eastus2 |

### EMA DATAENG PROD (e4eefd26-facd-439a-b5a2-adf03917b068)

#### Data Engineering Resource Groups
| Resource Group | Location |
|----------------|----------|
| AZRG-EUW-AUD-PRDCORTEXEMADATAENGPROD-PRD-001 | westeurope |
| AZRG-EUW-AUD-CORTEXEMADATAENGDBXPRODMRG-1 | westeurope |
| AZRG-EUW-AUD-CORTEXEMADATAENGDBXPRODMRG-2 | westeurope |
| AZRG-EUW-AUD-PRDCORTEXEMADATAENGBCP-PRD-001 | northeurope |
| AZRG-EUW-AUD-CORTEXEMADATAENGDBXBCPMRG-1 | northeurope |
| AZRG-EUW-AUD-CORTEXEMADATAENGDBXBCPMRG-2 | northeurope |

#### Specialist Tools Resource Groups
| Resource Group | Location |
|----------------|----------|
| AZRG-EUW-AUD-PRDCORTEXEMADATASPECPROD-PRD-001 | westeurope |
| AZRG-EUW-AUD-CORTEXEMADATASPECDBXPRODMRG-1 | westeurope |
| AZRG-EUW-AUD-PRDCORTEXEMADATASPECBCP-PRD-001 | northeurope |
| AZRG-EUW-AUD-CORTEXEMADATASPECDBXBCPMRG-1 | northeurope |

### EMA DATAENG STAGE (b2b82846-3553-4541-be05-db0633ce1a92)

#### Data Engineering Resource Groups
| Resource Group | Location |
|----------------|----------|
| AZRG-EUW-AUD-PRDCORTEXEMADATAENGSTAGE-PRD-001 | westeurope |
| AZRG-EUW-AUD-CORTEXEMADATAENGDBXSTAGEMRG-1 | westeurope |
| AZRG-EUW-AUD-CORTEXEMADATAENGDBXSTAGEMRG-2 | westeurope |
| AZRG-EUW-AUD-PRDCORTEXEMADATAENGSTAGEBCP-PRD-001 | northeurope |
| AZRG-EUN-AUD-CORTEXEMADATAENGDBXSTAGEBCPMRG-1 | northeurope |
| AZRG-EUN-AUD-CORTEXEMADATAENGDBXSTAGEBCPMRG-2 | northeurope |
| AZRG_AUD_ODATA_SNX_EUW_DBX_DATAENG1_MRG | westeurope |
| AZRG_AUD_ODATA_SNX_EUW_DBX_DATAENG2_MRG | westeurope |

#### Specialist Tools Resource Groups
| Resource Group | Location |
|----------------|----------|
| AZRG-EUW-AUD-PRDCORTEXEMADATASPECSTAGE-PRD-001 | westeurope |
| AZRG-EUW-AUD-CORTEXEMADATASPECDBXSTAGEMRG-1 | westeurope |
| AZRG-EUW-AUD-PRDCORTEXEMADATASPECSTAGEBCP-PRD-001 | northeurope |
| AZRG-EUN-AUD-CORTEXEMADATASPECDBXSTAGEBCPMRG-1 | northeurope |
| AZRG_AUD_ODATA_SNX_EUW_DBX_DATASPEC_MRG | westeurope |

### APA DATAENG STAGE (159571fe-cab6-4fbe-9f44-51f6bb0f1468)

#### Data Engineering Resource Groups
| Resource Group | Location |
|----------------|----------|
| AZRG-JPE-AUD-PRDCORTEXAPADATAENGSTAGE-PRD-001 | japaneast |
| AZRG-JPE-AUD-CORTEXAPADATAENGDBXSTAGEMRG-1 | japaneast |
| AZRG-JPE-AUD-CORTEXAPADATAENGDBXSTAGEMRG-2 | japaneast |

#### Specialist Tools Resource Groups
| Resource Group | Location |
|----------------|----------|
| AZRG-JPE-AUD-PRDCORTEXAPADATASPECSTAGE-PRD-001 | japaneast |
| AZRG-JPE-AUD-CORTEXAPADATASPECDBXSTAGEMRG-1 | japaneast |

---

## Domain-Based Cost Query Templates

### Query Costs by Resource Group (Daily)
```bash
SUB_ID="<subscription-id>"
START_DATE="YYYY-MM-DD"
END_DATE="YYYY-MM-DD"
az-elevated rest --method POST \
  --uri "https://management.azure.com/subscriptions/${SUB_ID}/providers/Microsoft.CostManagement/query?api-version=2023-03-01" \
  --body '{
    "type": "ActualCost",
    "timeframe": "Custom",
    "timePeriod": {"from": "'${START_DATE}'", "to": "'${END_DATE}'"},
    "dataset": {
      "granularity": "Daily",
      "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}},
      "grouping": [{"type": "Dimension", "name": "ResourceGroup"}]
    }
  }' | jq '.properties.rows'
```

### Query Data Engineering Costs (Daily)
```bash
SUB_ID="<subscription-id>"
START_DATE="YYYY-MM-DD"
END_DATE="YYYY-MM-DD"
az-elevated rest --method POST \
  --uri "https://management.azure.com/subscriptions/${SUB_ID}/providers/Microsoft.CostManagement/query?api-version=2023-03-01" \
  --body '{
    "type": "ActualCost",
    "timeframe": "Custom",
    "timePeriod": {"from": "'${START_DATE}'", "to": "'${END_DATE}'"},
    "dataset": {
      "granularity": "Daily",
      "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}},
      "grouping": [{"type": "Dimension", "name": "ResourceGroup"}, {"type": "Dimension", "name": "MeterSubCategory"}],
      "filter": {
        "dimensions": {
          "name": "ResourceGroup",
          "operator": "Contains",
          "values": ["DATAENG"]
        }
      }
    }
  }' | jq '.properties.rows'
```

### Query Specialist Tools Costs (Daily)
```bash
SUB_ID="<subscription-id>"
START_DATE="YYYY-MM-DD"
END_DATE="YYYY-MM-DD"
az-elevated rest --method POST \
  --uri "https://management.azure.com/subscriptions/${SUB_ID}/providers/Microsoft.CostManagement/query?api-version=2023-03-01" \
  --body '{
    "type": "ActualCost",
    "timeframe": "Custom",
    "timePeriod": {"from": "'${START_DATE}'", "to": "'${END_DATE}'"},
    "dataset": {
      "granularity": "Daily",
      "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}},
      "grouping": [{"type": "Dimension", "name": "ResourceGroup"}, {"type": "Dimension", "name": "MeterSubCategory"}],
      "filter": {
        "dimensions": {
          "name": "ResourceGroup",
          "operator": "Contains",
          "values": ["DATASPEC"]
        }
      }
    }
  }' | jq '.properties.rows'
```

### Query All DBX Subscriptions by Domain
```bash
START_DATE="YYYY-MM-DD"
END_DATE="YYYY-MM-DD"
for SUB_ID in \
  "39d5984b-c003-4b98-9e3a-434538adb961" \
  "d0987589-0bfb-474a-8ed6-81970143a96b" \
  "893331bc-b8fe-4898-97be-ba5246250d6b" \
  "c09f5025-1f53-433b-b509-7dd09aecf784" \
  "e4eefd26-facd-439a-b5a2-adf03917b068" \
  "b2b82846-3553-4541-be05-db0633ce1a92" \
  "159571fe-cab6-4fbe-9f44-51f6bb0f1468"; do
  echo "=== Subscription: $SUB_ID ==="
  az-elevated rest --method POST \
    --uri "https://management.azure.com/subscriptions/${SUB_ID}/providers/Microsoft.CostManagement/query?api-version=2023-03-01" \
    --body '{
      "type": "ActualCost",
      "timeframe": "Custom",
      "timePeriod": {"from": "'${START_DATE}'", "to": "'${END_DATE}'"},
      "dataset": {
        "granularity": "Daily",
        "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}},
        "grouping": [{"type": "Dimension", "name": "ResourceGroup"}]
      }
    }' 2>/dev/null | jq -c '.properties.rows'
done
```

---

## Report Output Format

When generating domain-based cost reports, follow this format:

### Report Structure
1. **Section 1: Data Engineering Costs** - Daily/Monthly breakdown for DATAENG resource groups
2. **Section 2: Specialist Tools Costs** - Daily/Monthly breakdown for DATASPEC resource groups
3. **Section 3: Combined Summary** - Both domains together with totals

### Daily Report Template
```
================================================================================
## DATA ENGINEERING - [REGION] [ENVIRONMENT]
================================================================================
Date       | DBU Compute  | Regional     | Daily Total
-----------|--------------|--------------|-------------
YYYY-MM-DD |    $X,XXX.XX | $X,XXX.XX    | $X,XXX.XX
...
-----------|--------------|--------------|-------------
TOTAL      | $XX,XXX.XX   | $XX,XXX.XX   | $XX,XXX.XX

================================================================================
## SPECIALIST TOOLS - [REGION] [ENVIRONMENT]
================================================================================
Date       | DBU Compute  | Regional     | Daily Total
-----------|--------------|--------------|-------------
YYYY-MM-DD |    $X,XXX.XX | $X,XXX.XX    | $X,XXX.XX
...
-----------|--------------|--------------|-------------
TOTAL      | $XX,XXX.XX   | $XX,XXX.XX   | $XX,XXX.XX

================================================================================
## COMBINED SUMMARY
================================================================================
| Region | Domain           | Period Total | Daily Avg |
|--------|------------------|--------------|-----------|
| AME    | Data Engineering |   $XX,XXX.XX | $X,XXX.XX |
| AME    | Specialist Tools |   $XX,XXX.XX | $X,XXX.XX |
| EMA    | Data Engineering |   $XX,XXX.XX | $X,XXX.XX |
| EMA    | Specialist Tools |   $XX,XXX.XX | $X,XXX.XX |
| APA    | Data Engineering |   $XX,XXX.XX | $X,XXX.XX |
| APA    | Specialist Tools |   $XX,XXX.XX | $X,XXX.XX |
|--------|------------------|--------------|-----------|
| TOTAL  | Data Engineering |   $XX,XXX.XX | $X,XXX.XX |
| TOTAL  | Specialist Tools |   $XX,XXX.XX | $X,XXX.XX |
| TOTAL  | COMBINED         |  $XXX,XXX.XX | $XX,XXX.XX|
```

### Domain Classification Logic
When processing query results, classify resource groups:
```python
def classify_domain(resource_group_name):
    rg_upper = resource_group_name.upper()
    if 'DATAENG' in rg_upper:
        return 'Data Engineering'
    elif 'DATASPEC' in rg_upper:
        return 'Specialist Tools'
    else:
        return 'Infrastructure/Shared'
```

---

## Interactive HTML Report Generation

### Trigger Phrases
Generate an interactive HTML cost report when the user requests:
- "generate Databricks daily report for Omnia Data"
- "generate Databricks weekly report for Omnia Data"
- "generate Databricks monthly report for Omnia Data"
- "Databricks report for Omnia Data"
- "Omnia Data cost report"

### Report Location
- **Output File**: `~/.triagent/reports/finops-cost-report.html`
- **Template Features**: 5 interactive Chart.js visualizations, summary metrics cards, filterable data table, dark theme

### HTML Report Generation Workflow

**Step 1: Query Cost Data**
Query both AME PROD and EMA PROD subscriptions with daily granularity:
```bash
# AME PROD (39d5984b-c003-4b98-9e3a-434538adb961)
START_DATE="YYYY-MM-DD"
END_DATE="YYYY-MM-DD"
az-elevated rest --method POST \
  --uri "https://management.azure.com/subscriptions/39d5984b-c003-4b98-9e3a-434538adb961/providers/Microsoft.CostManagement/query?api-version=2023-03-01" \
  --body '{
    "type": "ActualCost",
    "timeframe": "Custom",
    "timePeriod": {"from": "'${START_DATE}'", "to": "'${END_DATE}'"},
    "dataset": {
      "granularity": "Daily",
      "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}},
      "grouping": [
        {"type": "Dimension", "name": "ResourceGroup"},
        {"type": "Dimension", "name": "MeterSubCategory"}
      ],
      "filter": {
        "dimensions": {
          "name": "ServiceName",
          "operator": "In",
          "values": ["Azure Databricks"]
        }
      }
    }
  }' | jq '.properties.rows'

# EMA PROD (e4eefd26-facd-439a-b5a2-adf03917b068)
az-elevated rest --method POST \
  --uri "https://management.azure.com/subscriptions/e4eefd26-facd-439a-b5a2-adf03917b068/providers/Microsoft.CostManagement/query?api-version=2023-03-01" \
  --body '{
    "type": "ActualCost",
    "timeframe": "Custom",
    "timePeriod": {"from": "'${START_DATE}'", "to": "'${END_DATE}'"},
    "dataset": {
      "granularity": "Daily",
      "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}},
      "grouping": [
        {"type": "Dimension", "name": "ResourceGroup"},
        {"type": "Dimension", "name": "MeterSubCategory"}
      ],
      "filter": {
        "dimensions": {
          "name": "ServiceName",
          "operator": "In",
          "values": ["Azure Databricks"]
        }
      }
    }
  }' | jq '.properties.rows'
```

**Step 2: Data Format for HTML Template**
The API returns rows in this format: `[cost, dateInt, resourceGroup, meterSubCategory, currency]`
Convert to JavaScript arrays:
```javascript
// Each row: [cost, dateInt, resourceGroup, meterSubCategory, currency]
// Example: [217.107892266667, 20260103, "azrg-use2-aud-prdcortexamedataengprod1-prd-001", "Azure Databricks Regional", "USD"]
const ameRawData = [
    [cost1, dateInt1, "resource-group-name", "meter-subcategory", "USD"],
    // ... more rows
];

const emaRawData = [
    [cost1, dateInt1, "resource-group-name", "meter-subcategory", "USD"],
    // ... more rows
];
```

**Date Format**: `YYYYMMDD` as integer (e.g., `20260103` for January 3, 2026)

**Step 3: Domain Classification**
The HTML template automatically classifies costs by domain based on resource group name:
- Resource group contains `DATAENG` → **Data Engineering**
- Resource group contains `DATASPEC` → **Specialist Tools**
- Other → **Infrastructure/Shared** (excluded from domain totals)

**Step 4: Update HTML Template**
1. Read the existing template from `~/.triagent/reports/finops-cost-report.html`
2. Update the `ameRawData` array with AME PROD query results
3. Update the `emaRawData` array with EMA PROD query results
4. Update the header subtitle with the date range
5. Update the footer with generation timestamp

**Step 5: Open Report**
```bash
open ~/.triagent/reports/finops-cost-report.html
```

### HTML Template Features

**5 Interactive Charts:**
1. **Daily Cost Trend** - Line chart showing all 4 domain/region combinations over time
2. **Domain Distribution** - Doughnut chart: Data Engineering vs Specialist Tools
3. **Region Distribution** - Doughnut chart: AME PROD vs EMA PROD
4. **Region Comparison** - Bar chart comparing daily AME vs EMA totals
5. **Stacked Domain** - Stacked bar chart showing domain breakdown by region per day

**Summary Metrics Cards:**
- Grand Total (all costs)
- Data Engineering Total (with % of total)
- Specialist Tools Total (with % of total)
- AME PROD Total (with % of total)
- EMA PROD Total (with % of total)
- Daily Average

**Filterable Data Table:**
- Day-by-day breakdown with all columns
- Filter buttons: All, AME Only, EMA Only, Data Engineering, Specialist Tools
- Daily change percentage (positive/negative highlighting)

### Example Usage

**Daily Report:** "generate Databricks daily report for Omnia Data"
- Date range: Last 14-30 days with daily granularity

**Weekly Report:** "generate Databricks weekly report for Omnia Data"
- Date range: Last 4-8 weeks with daily granularity (aggregated by week in report)

**Monthly Report:** "generate Databricks monthly report for Omnia Data"
- Date range: Last 3-6 months with daily granularity (aggregated by month in report)

**Workflow:**
1. Calculate appropriate date range based on report type (daily/weekly/monthly)
2. Query AME PROD subscription (39d5984b-c003-4b98-9e3a-434538adb961)
3. Query EMA PROD subscription (e4eefd26-facd-439a-b5a2-adf03917b068)
4. Process API responses into ameRawData and emaRawData arrays
5. Update the HTML template with new data
6. Save to `~/.triagent/reports/finops-cost-report.html`
7. Open in browser with `open` command
8. Report ready with interactive charts and filters

---

## Cost Query Templates (General)

### Monthly Cost by Category
```bash
SUB_ID="<subscription-id>"
az-elevated rest --method POST \
  --uri "https://management.azure.com/subscriptions/${SUB_ID}/providers/Microsoft.CostManagement/query?api-version=2023-03-01" \
  --body '{
    "type": "ActualCost",
    "timeframe": "Custom",
    "timePeriod": {"from": "2025-01-01", "to": "2025-12-31"},
    "dataset": {
      "granularity": "Monthly",
      "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}},
      "grouping": [{"type": "Dimension", "name": "MeterCategory"}]
    }
  }' | jq '.properties.rows'
```

### SQL Database Breakdown
```bash
az-elevated rest --method POST \
  --uri "https://management.azure.com/subscriptions/${SUB_ID}/providers/Microsoft.CostManagement/query?api-version=2023-03-01" \
  --body '{
    "type": "ActualCost",
    "timeframe": "Custom",
    "timePeriod": {"from": "2025-07-01", "to": "2025-12-31"},
    "dataset": {
      "granularity": "Monthly",
      "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}},
      "grouping": [{"type": "Dimension", "name": "MeterSubCategory"}],
      "filter": {
        "dimensions": {
          "name": "MeterCategory",
          "operator": "In",
          "values": ["SQL Database", "Azure SQL Database", "SQL Elastic Pools"]
        }
      }
    }
  }' | jq '.properties.rows'
```

### Databricks + VM Costs
```bash
az-elevated rest --method POST \
  --uri "https://management.azure.com/subscriptions/${SUB_ID}/providers/Microsoft.CostManagement/query?api-version=2023-03-01" \
  --body '{
    "type": "ActualCost",
    "timeframe": "Custom",
    "timePeriod": {"from": "2025-01-01", "to": "2025-12-31"},
    "dataset": {
      "granularity": "Monthly",
      "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}},
      "grouping": [{"type": "Dimension", "name": "MeterCategory"}],
      "filter": {
        "dimensions": {
          "name": "MeterCategory",
          "operator": "In",
          "values": ["Virtual Machines", "Azure Databricks", "Virtual Machines Licenses", "Storage", "Bandwidth"]
        }
      }
    }
  }' | jq '.properties.rows'
```

### DBU Cost Breakdown
```bash
az-elevated rest --method POST \
  --uri "https://management.azure.com/subscriptions/${SUB_ID}/providers/Microsoft.CostManagement/query?api-version=2023-03-01" \
  --body '{
    "type": "ActualCost",
    "timeframe": "Custom",
    "timePeriod": {"from": "2025-01-01", "to": "2025-12-31"},
    "dataset": {
      "granularity": "Monthly",
      "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}},
      "grouping": [{"type": "Dimension", "name": "MeterSubCategory"}],
      "filter": {
        "dimensions": {
          "name": "MeterCategory",
          "operator": "In",
          "values": ["Azure Databricks"]
        }
      }
    }
  }' | jq '.properties.rows'
```

---

## Domain-Based Cost Attribution (Legacy)

### Resource Tags (Omnia-Data/Cortex)
| Tag | Description | Example |
|-----|-------------|---------|
| `AUDAPPLICATION` | Application | "OMNIA DATA" |
| `AUDENVIRONMENT` | Environment | "AME DEV", "AME PRD" |
| `AUDPRODUCTGROUP` | Product group | "DATA" |
| `ENVIRONMENT` | Env type | "NPD", "PRD" |
| `BILLINGCODE` | Billing code | "LPX06916-RN-00-AZ-1000" |
| `BillingGroup` | Billing group | "Omnia Data KTLO - V9.4.1 - AME" |

### DATABRICKS Domain
Resources: `Databricks`, `DBX`, `dbx`, `adb-`
```bash
az-elevated resource list --subscription ${SUB_ID} \
  --query "[?contains(name, 'DBX') || contains(name, 'dbx') || contains(type, 'Databricks')].{name:name, type:type, rg:resourceGroup}" -o table
```

### HANA Domain
Resources: `hana`, `HANA`, SAP HANA VMs, storage, disks
```bash
az-elevated resource list --subscription ${SUB_ID} \
  --query "[?contains(name, 'hana') || contains(name, 'HANA')].{name:name, type:type, rg:resourceGroup}" -o table
```

**Known HANA Resources (US_AUDIT_PROD):**
- cortexjehanaame-eus, cortexjehana1ame-eus (VMs)
- cortexjeamehanahaplbip (Load Balancer)
- cortexjehanacockpitame-eus (Cockpit VM)
- prdcortexamejehanaasppe (Private Endpoint)
- hanadevfs (File Share)

### JE (Job Engine) Domain
Resources: `je`, `JE`, `cortexje`
```bash
az-elevated resource list --subscription ${SUB_ID} \
  --query "[?contains(name, 'je') || contains(name, 'JE')].{name:name, type:type, rg:resourceGroup}" -o table
```

**Known JE Resources:**
- cortexjeamestor, cortexjejobs1amestor (Storage)
- dcortexjeame-config, dcortexjeame-secrets (Key Vaults)
- cortexdevamesb (Service Bus)
- devcortexamesqlmaster (SQL Server)
- auditlakeaapsamedevdl (Data Lake)

---

## Environment-Based Queries

### Query by Environment Tag
```bash
az-elevated rest --method POST \
  --uri "https://management.azure.com/subscriptions/${SUB_ID}/providers/Microsoft.CostManagement/query?api-version=2023-03-01" \
  --body '{
    "type": "ActualCost",
    "timeframe": "Custom",
    "timePeriod": {"from": "2025-01-01", "to": "2025-12-31"},
    "dataset": {
      "granularity": "Monthly",
      "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}},
      "grouping": [{"type": "Dimension", "name": "ResourceGroup"}],
      "filter": {
        "tags": {
          "name": "AUDENVIRONMENT",
          "operator": "In",
          "values": ["AME DEV", "AME DEV1", "AME DEV2"]
        }
      }
    }
  }' | jq '.properties.rows'
```

### Query by Resource Group
```bash
az-elevated rest --method POST \
  --uri "https://management.azure.com/subscriptions/${SUB_ID}/providers/Microsoft.CostManagement/query?api-version=2023-03-01" \
  --body '{
    "type": "ActualCost",
    "timeframe": "Custom",
    "timePeriod": {"from": "2025-01-01", "to": "2025-12-31"},
    "dataset": {
      "granularity": "Monthly",
      "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}},
      "grouping": [{"type": "Dimension", "name": "ResourceGroup"}]
    }
  }' | jq '.properties.rows'
```

---

## Resource Inventory Queries

### List All Resources with Tags
```bash
az-elevated resource list --subscription ${SUB_ID} \
  --query "[?tags != null].{name:name, type:type, rg:resourceGroup, env:tags.AUDENVIRONMENT}" -o table
```

### List SQL Databases
```bash
az-elevated resource list --subscription ${SUB_ID} \
  --resource-type "Microsoft.Sql/servers/databases" -o table
```

### List Elastic Pools with SKU
```bash
az-elevated resource list --subscription ${SUB_ID} \
  --resource-type "Microsoft.Sql/servers/elasticPools" -o json | \
  jq -r '.[] | "\(.name)|\(.sku.name)|\(.sku.capacity)"'
```

### Azure Advisor Cost Recommendations
```bash
az advisor recommendation list --subscription ${SUB_ID} --category Cost -o table
```

---

## Access Limitations

| Subscription | Cost Access | Workaround |
|--------------|-------------|------------|
| US_AUDIT_PROD | RBAC Denied | Resource enumeration, Advisor |
| US_AUDIT_PREPROD | RBAC Denied | Resource enumeration, Advisor |
| EMA-AUD-PRD-01 | RBAC Denied | Resource enumeration, Advisor |
| All other subscriptions | Available | Direct cost queries |

**Note:** Cost Management API has 1-year time period limit. Split queries for longer periods.
