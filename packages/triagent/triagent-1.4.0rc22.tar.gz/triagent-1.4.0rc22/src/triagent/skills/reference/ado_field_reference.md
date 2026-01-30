# Azure DevOps Work Item Field Reference

**Last Updated:** 2026-01-20
**Based on Analysis:** Cortex Release 9.5 work items in Audit Cortex 2 project

---

## Field Listing Commands

```bash
# List all work item fields
az devops invoke \
  --area wit \
  --resource fields \
  --route-parameters project="Audit Cortex 2" \
  --api-version 7.0 \
  --output json | jq '.value[] | {name: .name, referenceName: .referenceName, type: .type}'

# Get fields for a specific work item (see what's populated)
az boards work-item show \
  --id <WORK_ITEM_ID> \
  --query "fields | keys(@)" \
  --output tsv

# Get custom fields only
az devops invoke \
  --area wit \
  --resource fields \
  --route-parameters project="Audit Cortex 2" \
  --api-version 7.0 \
  --output json | jq '.value[] | select(.referenceName | test("Custom\\.|AuditCortexScrum\\.")) | {name: .name, referenceName: .referenceName}'
```

---

## Field Reference by Work Item Type

### Legend
- **M** = Mandatory (Required for creation)
- **R** = Recommended (Commonly populated by team)
- **O** = Optional (Used in specific scenarios)

---

## 1. Epic Fields

| Field Name | Reference Name | Type | Required | Notes |
|------------|----------------|------|----------|-------|
| **System Fields** |||||
| Title | `System.Title` | string | **M** | Format: `[Category] \| [Epic Name]` |
| State | `System.State` | string | **M** | New, Active, Done, Removed |
| Area Path | `System.AreaPath` | string | **M** | `Audit Cortex 2\Omnia Data\[POD]` |
| Iteration Path | `System.IterationPath` | string | **M** | Default: `Audit Cortex 2` |
| Description | `System.Description` | html | R | Overview, business context |
| **Custom Fields** |||||
| Product Owner | `AuditCortexScrum.CortexProductOwner` | identity | **M** | Lead Product Owner |
| Cortex Release # | `Custom.CortexRelease#` | string | **M** | Target release: 9.5, 10.0, Future |
| Priority | `Microsoft.VSTS.Common.Priority` | integer | R | 1-4 |
| Considered Must Have | `Custom.ConsideredMustHave` | boolean | O | Strategic importance flag |
| Start Date | `Microsoft.VSTS.Scheduling.StartDate` | dateTime | O | Epic start date |
| ART | `Custom.ART` | string | O | Omnia Data Management/Automation |
| Pod Team | `Custom.PodTeam` | string | O | Pod assignment |

---

## 2. Feature Fields

| Field Name | Reference Name | Type | Required | Notes |
|------------|----------------|------|----------|-------|
| **System Fields** |||||
| Title | `System.Title` | string | **M** | Format: `[Area] \| [Feature Name]` |
| State | `System.State` | string | **M** | New, Active, Done, Removed |
| Area Path | `System.AreaPath` | string | **M** | Full team path |
| Iteration Path | `System.IterationPath` | string | **M** | Sprint iteration |
| Description | `System.Description` | html | **M** | User story format |
| Acceptance Criteria | `Microsoft.VSTS.Common.AcceptanceCriteria` | html | **M** | Structured AC list |
| Parent | `System.Parent` | integer | **M** | Link to Epic |
| **Custom Fields** |||||
| Product Owner | `AuditCortexScrum.CortexProductOwner` | identity | **M** | Feature PO |
| Cortex Release # | `Custom.CortexRelease#` | string | **M** | Target release |
| Business Outcome Hypothesis | `Custom.BusinessOutcomeHypothesis` | html | R | Business value statement |
| T-Shirt Size | `Custom.CortexTShirtSize` | string | R | XS, S, M, L, XL |
| Cortex Priority | `Custom.CortexPriority` | integer | R | 1-4 |
| Design Document Status | `Custom.DesignDocumentStatus` | string | O | Blank, In Progress, Complete |
| Deployed to Production | `Custom.DeployedtoProduction` | string | O | Yes/No |
| WSJF | `Custom.WSJF` | double | O | Weighted Shortest Job First score |

---

## 3. Enabler Fields

| Field Name | Reference Name | Type | Required | Notes |
|------------|----------------|------|----------|-------|
| **System Fields** |||||
| Title | `System.Title` | string | **M** | Format: `[Type] Enabler \| [Name]` |
| State | `System.State` | string | **M** | New, Active, Done, Removed |
| Area Path | `System.AreaPath` | string | **M** | Full team path |
| Description | `System.Description` | html | **M** | Technical description |
| Acceptance Criteria | `Microsoft.VSTS.Common.AcceptanceCriteria` | html | **M** | Structured AC |
| Parent | `System.Parent` | integer | **M** | Link to Epic |
| **Custom Fields** |||||
| Product Owner | `AuditCortexScrum.CortexProductOwner` | identity | **M** | Enabler owner |
| Cortex Release # | `Custom.CortexRelease#` | string | **M** | Target release |
| Business Outcome Hypothesis | `Custom.BusinessOutcomeHypothesis` | html | R | Technical justification |
| T-Shirt Size | `Custom.CortexTShirtSize` | string | R | Size estimate |
| Deployed to Production | `Custom.DeployedtoProduction` | string | O | Yes/No |
| WSJF | `Custom.WSJF` | double | O | Priority score |

**Enabler Types:** Exploration, Architectural, Infrastructure, Compliance, Design

---

## 4. Product Backlog Item (PBI) Fields

| Field Name | Reference Name | Type | Required | Notes |
|------------|----------------|------|----------|-------|
| **System Fields** |||||
| Title | `System.Title` | string | **M** | Clear, action-oriented |
| State | `System.State` | string | **M** | New, Active, Done, Removed |
| Area Path | `System.AreaPath` | string | **M** | Full team path |
| Iteration Path | `System.IterationPath` | string | **M** | Sprint iteration |
| Assigned To | `System.AssignedTo` | identity | R | Developer assigned |
| Description | `System.Description` | html | **M** | User story format |
| Acceptance Criteria | `Microsoft.VSTS.Common.AcceptanceCriteria` | html | **M** | Testable criteria |
| Parent | `System.Parent` | integer | **M** | Link to Feature/Enabler |
| **Custom Fields** |||||
| Product Owner | `AuditCortexScrum.CortexProductOwner` | identity | **M** | PBI owner |
| Cortex Release # | `Custom.CortexRelease#` | string | **M** | Target release |
| Release Scope Approved | `Custom.ReleaseScopeApproved` | string | **M** | In Triage, X.X Approved |
| Type | `Custom.Type` | string | **M** | See PBI Types below |
| ART | `Custom.ART` | string | R | Omnia Data Management/Automation |
| Pod Team | `Custom.PodTeam` | string | R | Pod assignment |
| Scrum Team | `Custom.ScrumTeam` | string | R | Specific team |
| Feature Area | `Custom.OmniaDataFeatureArea` | string | R | Functional area |
| Feature Sub Area | `Custom.OmniaDataFeatureSubArea` | string | O | Sub-area |
| Architect | `Custom.CortexArchitect` | identity | R | Technical architect |
| Implementation Notes | `Custom.Implementationnotes` | html | R | Technical details |
| Delivery Confidence | `Custom.CortexDeliveryConfidence` | string | O | 1. Green, 2. Yellow, 3. Red |
| QA Testing | `Custom.QATesting` | string | O | Yes/No |
| Priority | `Microsoft.VSTS.Common.Priority` | integer | R | 1-4 |
| Effort | `Microsoft.VSTS.Scheduling.Effort` | double | O | Story points |
| Architecture Review TA | `Custom.ArchitectureReviewTA` | string | O | Approved/Not Required |
| Security Approved | `AuditCortexScrum.CortexSecurityApproved` | string | O | Review status |
| Tech Controls Approved | `AuditCortexScrum.CortexTechControlsApproved` | string | O | Review status |
| Work Category | `Custom.WorkCategory` | string | O | Feature/Defect/Technical |

### PBI Types (Custom.Type)
- Feature Development
- Documentation
- Technical Debt
- Performance Feature
- Security
- DevOps Effort
- Monitoring
- Production Support
- Technical Discovery
- Testing Only
- UI/UX or Architectural Design
- Standard Analytics
- CDM or Data Check
- Data Prep Script
- Bundles
- Data Input Template
- KT or Training

---

## 5. Defect Fields

| Field Name | Reference Name | Type | Required | Notes |
|------------|----------------|------|----------|-------|
| **System Fields** |||||
| Title | `System.Title` | string | **M** | Format: `[Area] \| [Issue Description]` |
| State | `System.State` | string | **M** | New, Active, Resolved, Done |
| Area Path | `System.AreaPath` | string | **M** | Full team path |
| Assigned To | `System.AssignedTo` | identity | R | Developer assigned |
| Description | `System.Description` | html | R | Issue details |
| **Custom Fields - Mandatory** |||||
| Product Owner | `AuditCortexScrum.CortexProductOwner` | identity | **M** | Defect owner |
| Severity | `Microsoft.VSTS.Common.Severity` | string | **M** | 1-Critical, 2-High, 3-Medium, 4-Low |
| Cortex Release # | `Custom.CortexRelease#` | string | **M** | Fix release |
| Found in Release # | `Custom.FoundinCortexRelease#` | string | **M** | Discovery release |
| Testing Phase | `Custom.TestingPhase` | string | **M** | When found |
| Feature Area | `Custom.OmniaDataFeatureArea` | string | **M** | Functional area |
| Environment | `Custom.CortexEnvironment` | string | **M** | DEV, QAS, STG, PRD |
| Release Scope Approved | `Custom.ReleaseScopeApproved` | string | **M** | Approval status |
| **Custom Fields - Recommended** |||||
| Repro Steps | `Microsoft.VSTS.TCM.ReproSteps` | html | R | Steps to reproduce |
| System Info | `Microsoft.VSTS.TCM.SystemInfo` | html | O | Environment details |
| Feature Sub Area | `Custom.OmniaDataFeatureSubArea` | string | R | Sub-area |
| Pod Team | `Custom.PodTeam` | string | R | Pod assignment |
| Scrum Team | `Custom.ScrumTeam` | string | R | Specific team |
| Defect Category | `Custom.DefectCategory` | string | R | Category |
| Root Cause | `Custom.CortexRootCause` | html | R | Analysis |
| Root Cause Category | `Custom.CortexRootCauseCategory` | string | R | Category |
| Resolution Type | `Custom.ResolutionType` | string | R | Code Issue, Data Issue, etc. |
| QA Lead | `Custom.QALead` | identity | O | QA lead |
| Architect | `Custom.CortexArchitect` | identity | O | Technical review |
| Delivery Lead | `Custom.DeliveryLead` | identity | O | Delivery contact |
| Workaround | `Custom.Workaround` | html | O | Temporary fix |
| **Defect Tracking Fields** |||||
| Defect Closed Date | `Custom.DefectClosedDate` | dateTime | O | Auto/manual close date |
| Deferral Reason | `Custom.DeferralReason` | html | O | If deferred |
| Defect Grouping | `Custom.OmniaDataDefectGrouping` | string | O | Grouping category |
| KB Needed | `Custom.OmniaDataKBNeeded` | string | O | Yes/No |
| Will Defect Be Seen in Prod | `Custom.OmniaDatawillthedefectbeseeninproduction` | string | O | Yes/No |
| QA Testing | `Custom.QATesting` | string | O | Yes/No |
| BVT Results | `Custom.BVTResults` | string | O | Pass/Fail |

### Severity Levels
| Value | Description | SLA |
|-------|-------------|-----|
| 1 - Critical | System down, no workaround | Immediate fix |
| 2 - High | Major feature broken | Within sprint |
| 3 - Medium | Feature impaired, workaround exists | Next sprint |
| 4 - Low | Minor issue, cosmetic | Backlog |

### Testing Phases
- Unit Testing
- Integration Testing
- System Testing
- Regression Testing
- Performance
- UAT
- Production

---

## 6. Test Case Fields

| Field Name | Reference Name | Type | Required | Notes |
|------------|----------------|------|----------|-------|
| **System Fields** |||||
| Title | `System.Title` | string | **M** | Test case name |
| State | `System.State` | string | **M** | Design, Ready, Closed |
| Area Path | `System.AreaPath` | string | **M** | Full team path |
| **Custom Fields** |||||
| Product Owner | `AuditCortexScrum.CortexProductOwner` | identity | R | Test owner |
| Cortex Release # | `Custom.CortexRelease#` | string | **M** | Test release |
| Feature Area | `Custom.OmniaDataFeatureArea` | string | **M** | Functional area |
| Feature Sub Area | `Custom.OmniaDataFeatureSubArea` | string | R | Sub-area |
| Pod Team | `Custom.PodTeam` | string | R | Pod assignment |
| Scrum Team | `Custom.ScrumTeam` | string | R | Specific team |
| ART | `Custom.ART` | string | R | ART assignment |
| Automated Status | `Custom.AutomatedStatus` | string | R | Automated/Manual/In Progress |
| Automation Tosca | `Custom.AutomationTosca` | string | O | Tosca automation flag |
| Business Use Case | `Custom.BusinessUseCase` | string | O | Use case description |
| Dataset | `Custom.Dataset` | string | O | Test data set |
| Execution Effort | `Custom.OmniaDataExecutionEffort` | double | O | Hours |
| Testing Phase | `Custom.OmniaDataTestingPhase` | string | R | Phase |
| Testing Sub Phase | `Custom.OmniaDataTestingSubPhase` | string | O | Sub-phase |
| TC Category | `Custom.TCCategory` | string | O | Category |
| Approved for Release | `Custom.OmniaDataApprovedforRelease` | string | O | Yes/No |
| Regression Testing | `Custom.OmniaDataRegressionTesting` | string | O | Yes/No |
| Smoke Suite Must Pass | `Custom.SmokeSuiteTCMustPass` | string | O | Yes/No |

---

## 7. Live Site Incident (LSI) Fields

| Field Name | Reference Name | Type | Required | Notes |
|------------|----------------|------|----------|-------|
| **System Fields** |||||
| Title | `System.Title` | string | **M** | Format: `[Feature Area] \| [Issue]` |
| State | `System.State` | string | **M** | New, Analyzing, Remediating, Done |
| Area Path | `System.AreaPath` | string | **M** | Full team path |
| Description | `System.Description` | html | **M** | Incident details |
| Parent | `System.Parent` | integer | **M** | Default: 5150584 (LSI Epic) |
| **Custom Fields** |||||
| Product Owner | `AuditCortexScrum.CortexProductOwner` | identity | **M** | LSI owner |
| Severity | `Microsoft.VSTS.Common.Severity` | string | **M** | 1-Critical, 2-High, 3-Medium |
| Feature Area | `Custom.OmniaDataFeatureArea` | string | **M** | Affected area |
| Feature Sub Area | `Custom.OmniaDataFeatureSubArea` | string | R | Sub-area |
| Pod Team | `Custom.PodTeam` | string | **M** | Pod assignment |
| Environment | `Custom.CortexEnvironment` | string | **M** | PRD, STG |

### LSI Timing Rules
- Max 1 week in "New" state
- Max 10 days in "Analyzing" state
- Time-bound remediation within release

---

## Common Field Patterns

### Team Assignment Fields
```bash
# All work items use these for team routing
Custom.ART                    # Omnia Data Management, Omnia Data Automation
Custom.PodTeam               # Data In Use, Data Acquisition, etc.
Custom.ScrumTeam             # Specific team name
```

### Release Management Fields
```bash
# Release tracking
Custom.CortexRelease#        # Target release: 9.5, 10.0, Future
Custom.FoundinCortexRelease# # For defects - discovery release
Custom.ReleaseScopeApproved  # In Triage, X.X Approved, Deferred
```

### Feature Classification
```bash
Custom.OmniaDataFeatureArea     # Home Page, Data Library, Analytics, etc.
Custom.OmniaDataFeatureSubArea  # Detailed sub-area
```

### Review and Approval Fields
```bash
AuditCortexScrum.CortexSecurityApproved     # Security review
AuditCortexScrum.CortexTechControlsApproved # Tech controls review
Custom.ArchitectureReviewTA                  # Architecture approval
Custom.CortexDeliveryConfidence             # Delivery status
```

---

## CLI Query Examples

```bash
# Get work item with specific fields
az boards work-item show \
  --id <WORK_ITEM_ID> \
  --fields "System.Title,Custom.CortexRelease#,Custom.PodTeam,Custom.OmniaDataFeatureArea" \
  --output json

# Query work items by custom field
az boards query \
  --wiql "SELECT [System.Id],[System.Title] FROM WorkItems WHERE [Custom.CortexRelease#] = '9.5' AND [Custom.PodTeam] = 'Data In Use'" \
  --output tsv

# Create work item with custom fields
az boards work-item create \
  --title "[Title]" \
  --type "Product Backlog Item" \
  --project "Audit Cortex 2" \
  --area "Audit Cortex 2\\Omnia Data" \
  --fields "Custom.CortexRelease#=9.5" "Custom.PodTeam=Data In Use" \
  --output tsv
```

---

## Field Population Summary by Type

| Field Category | Epic | Feature | Enabler | PBI | Defect | Test Case |
|----------------|------|---------|---------|-----|--------|-----------|
| **Core System** | 4 | 6 | 5 | 7 | 6 | 5 |
| **Team Assignment** | 3 | 3 | 3 | 5 | 5 | 4 |
| **Release Mgmt** | 2 | 3 | 2 | 3 | 4 | 2 |
| **Feature Classification** | 1 | 2 | 1 | 2 | 2 | 2 |
| **Review/Approval** | 1 | 2 | 1 | 4 | 3 | 2 |
| **Type-Specific** | 1 | 3 | 2 | 3 | 12+ | 15+ |
| **Total Commonly Used** | ~12 | ~19 | ~14 | ~24 | ~32 | ~30 |
