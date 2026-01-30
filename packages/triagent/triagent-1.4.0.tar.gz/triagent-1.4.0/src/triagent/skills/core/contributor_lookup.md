# Contributor & Repository Lookup

**Last Updated:** 2026-01-25
**Version:** 1.1.0

Find repository point-of-contact (top code contributors by commit history) and person contribution details (PRs, work items, teams).

> **Note:** Use Case 1 uses Git commit history (not PRs) to identify contributors. This ensures we find actual code authors rather than PR reviewers/approvers who may be architects or leads.

---

## Triggers

This skill activates for phrases like:
- "point of contact for [repo]", "POC for [repo]", "who owns [repo]"
- "contact for [repo-name]", "who should I contact for [repo]"
- "contributions of [person]", "contributions by [person]"
- "show me contributions", "PR activity for [person]"
- "work items by [person]", "what has [person] worked on"

---

## Use Case 1: Repository Point of Contact

When asked "who is the point of contact for [repo]?" or similar:

### Step 1: Identify Repository

1. Normalize the repository name (handle variations like `cortex-ui`, `cortexui`, `cortex ui`)
2. Check `../data/repository-mappings.json` for team ownership

### Step 2: Fetch Commit History from develop/release Branches

Use `az devops invoke` to query the Git Commits REST API. This returns actual code authors, not PR creators/reviewers.

```bash
# Get commits from develop branch (last 6 months)
az devops invoke \
  --org https://dev.azure.com/symphonyvsts \
  --area git \
  --resource commits \
  --route-parameters project="Audit Cortex 2" repositoryId="{repo_name}" \
  --query-parameters "searchCriteria.itemVersion.version=develop" "searchCriteria.fromDate=$(date -v-6m +%Y-%m-%dT00:00:00Z)" "\$top=500" "api-version=7.1" \
  --http-method GET \
  --output json
```

**Note:** On Linux, use `date -d '6 months ago' +%Y-%m-%dT00:00:00Z` instead of `-v-6m`.

**Alternative: Query release branches:**
```bash
# For release branches (e.g., release/9.6)
--query-parameters "searchCriteria.itemVersion.version=release/9.6"
```

**Response format:**
```json
{
  "value": [
    {
      "commitId": "abc123...",
      "author": {
        "name": "John Doe",
        "email": "johndoe@deloitte.com",
        "date": "2026-01-20T10:30:00Z"
      },
      "comment": "Fix data validation logic"
    }
  ]
}
```

### Step 3: Aggregate Commits by Author

Process the commit data:
- Extract unique author emails from `value[].author.email`
- Group commits by author email
- Count commits per author
- Get most recent commit date per author
- Sort by commit count descending

### Step 4: Enrich Contributors with Team Info

1. Look up each contributor's email in `../data/user-mappings.tsv`
2. Get team, POD, and role information
3. Reference `../core/team_info.md` for POD leadership
4. **Do not filter by role** - commit history naturally reflects who writes code

### Step 5: Get Repository Ownership

From `../data/repository-mappings.json`:
```json
{
  "name": "cortexpy",
  "teams": ["Delta", "Beta"],
  "pod": "Data Management and Activation"
}
```

### Step 6: Format Response

```markdown
## Repository: {repo_name}

**Team Ownership:** {team} ({pod} POD)
**POD Leader:** {pod_leader}

### Top Code Contributors (Last 6 Months)

| Rank | Contributor | Team | Role | Commits | Last Commit |
|------|-------------|------|------|---------|-------------|
| 1 | {name} | {team} | {role} | {count} | {date} |
| 2 | {name} | {team} | {role} | {count} | {date} |
| 3 | {name} | {team} | {role} | {count} | {date} |

**Primary Point of Contact:** {top_contributor_name}
- **Team:** {team}
- **Role:** {role}
- **POD:** {pod}
- **Product Owner:** {product_owner}
```

---

## Use Case 2: Person Contribution Details

When asked "show me contributions of [person]" or similar:

### Step 1: Find Person Information

1. Search `../data/user-mappings.tsv` by name (fuzzy match on displayName)
2. Extract: email, displayName, team, pod, role, region, type, vendor

```bash
# Example: Search user-mappings.tsv for a person
grep -i "{person_name}" ../data/user-mappings.tsv
```

### Step 2: Fetch PR Activity

Get all PRs created by the person in the last 6 months:

```bash
# Get PRs by author email
az repos pr list \
  --org https://dev.azure.com/symphonyvsts \
  --project "Audit Cortex 2" \
  --creator "{person_email}" \
  --status all \
  --top 200 \
  --query "[?creationDate >= '$(date -d '6 months ago' +%Y-%m-%d)'].{repo:repository.name,status:status,creationDate:creationDate,closedDate:closedDate,targetBranch:targetRefName,title:title}" \
  --output json
```

Aggregate by repository:
- Group by repository name
- Count total PRs and completed PRs
- Identify primary target branches

### Step 3: Fetch Work Item Activity

Query assigned and created work items using WIQL:

```bash
# Get work items assigned to person
az boards query \
  --org https://dev.azure.com/symphonyvsts \
  --project "Audit Cortex 2" \
  --wiql "SELECT [System.Id], [System.Title], [System.WorkItemType], [System.State], [System.AreaPath], [System.CreatedDate]
          FROM WorkItems
          WHERE [System.AssignedTo] = '{person_email}'
          AND [System.ChangedDate] >= @Today - 180
          ORDER BY [System.ChangedDate] DESC" \
  --output json
```

```bash
# Get work items created by person
az boards query \
  --org https://dev.azure.com/symphonyvsts \
  --project "Audit Cortex 2" \
  --wiql "SELECT [System.Id], [System.Title], [System.WorkItemType], [System.State], [System.AreaPath]
          FROM WorkItems
          WHERE [System.CreatedBy] = '{person_email}'
          AND [System.CreatedDate] >= @Today - 180
          ORDER BY [System.CreatedDate] DESC" \
  --output json
```

### Step 4: Format Response

```markdown
## Contributor: {displayName}

**Team:** {team}
**POD:** {pod}
**Role:** {role}
**Region:** {region}
**Type:** {type} {vendor if contractor}
**Email:** {email}

### PR Activity (Last 6 Months)

| Repository | PRs Merged | PRs Open | Primary Branch |
|------------|------------|----------|----------------|
| {repo} | {merged_count} | {open_count} | {branch} |
| {repo} | {merged_count} | {open_count} | {branch} |
| **Total** | **{total_merged}** | **{total_open}** | |

### Work Item Activity (Last 6 Months)

| Type | Assigned | Created | Completed |
|------|----------|---------|-----------|
| PBI | {assigned} | {created} | {completed} |
| Defect | {assigned} | {created} | {completed} |
| Task | {assigned} | {created} | {completed} |

### Recent Work Items

| ID | Type | Title | State |
|----|------|-------|-------|
| {id} | {type} | {title} | {state} |
| {id} | {type} | {title} | {state} |
```

---

## Data File References

| File | Purpose | Format |
|------|---------|--------|
| `../data/user-mappings.tsv` | Email → Team/POD/Role lookup | TSV with headers |
| `../data/repository-mappings.json` | Repo → Team/POD ownership | JSON array |
| `../data/team-config.json` | Team hierarchy and roles | JSON object |
| `../core/team_info.md` | POD leadership, domain ownership | Markdown tables |

---

## POD Leadership Quick Reference

| POD | Leader | Product Owners |
|-----|--------|----------------|
| Data Acquisition and Preparation | Henry Benson | Kevin Koshy (Alpha), Zac Murphy (Beta), Prakash Kailash (Megatron) |
| Data Management and Activation | Leela Modali | Steven Matthies (SkyRockets), Gaurav Malik (Gamma), Paul Vithayathil (Delta) |
| Data In Use | Allie Longfritz | Rakesh Thorat (Giga/Kilo), Virnica Gautam (Tera), Allie Longfritz (Peta) |
| Omnia JE | Harrison Zucker | Steve Vandervalk (Justice League/Jupiter), Harrison Zucker (Neptune/Saturn), Jessie Lim (Utopia), Vijaya Panapana (Exa) |

---

## Example Outputs

### Repository POC Example

**Query:** "Who is the point of contact for cortexpy?" or "Find me a developer who can help with data-checks issue"

**Response:**
```
## Repository: cortexpy

**Team Ownership:** Delta, Beta (Data Management and Activation POD)
**POD Leader:** Leela Modali

### Top Code Contributors (Last 6 Months)

| Rank | Contributor | Team | Role | Commits | Last Commit |
|------|-------------|------|------|---------|-------------|
| 1 | Reddy, Ramireddygari Sai Navadeep | Delta | Developer | 45 | 2026-01-20 |
| 2 | Gaikwad, Manjusha Mayur | Beta | Developer | 32 | 2026-01-18 |
| 3 | J, Vikas | Delta | Developer | 28 | 2026-01-12 |

**Primary Point of Contact:** Reddy, Ramireddygari Sai Navadeep
- **Team:** Delta
- **Role:** Developer
- **POD:** Data Management and Activation
- **Product Owner:** Paul Vithayathil
```

> **Why commits instead of PRs?** Using commit history ensures we find actual code authors. With PRs, architects or leads who review/approve PRs might appear as top contributors even if they don't write the code.

### Person Contributions Example

**Query:** "Show me contributions of Manjusha Gaikwad"

**Response:**
```
## Contributor: Gaikwad, Manjusha Mayur

**Team:** Beta
**POD:** Data Acquisition and Preparation
**Role:** Developer
**Type:** Contractor (Cognizant)
**Email:** mgaikwad@deloitte.com

### PR Activity (Last 6 Months)

| Repository | PRs Merged | PRs Open | Primary Branch |
|------------|------------|----------|----------------|
| cortex-datamanagement-services | 12 | 1 | develop |
| cortexpy | 8 | 0 | develop |
| analytic-notebooks | 4 | 0 | develop |
| **Total** | **24** | **1** | |

### Work Item Activity (Last 6 Months)

| Type | Assigned | Created | Completed |
|------|----------|---------|-----------|
| PBI | 8 | 3 | 6 |
| Defect | 5 | 2 | 5 |
| Task | 15 | 8 | 12 |
```

---

## Notes

- **Commit data** comes from Azure DevOps Git REST API via `az devops invoke` (Use Case 1)
- **PR data** comes from Azure DevOps REST API via `az repos pr list` (Use Case 2)
- Work item queries use WIQL (Work Item Query Language)
- User-to-team mapping is maintained in `user-mappings.tsv`
- Repository ownership is maintained in `repository-mappings.json`
- For cross-team repositories (like `cortexpy`, `analytic-notebooks`), list all owning teams
- Commit history from develop/release branches provides more accurate developer identification than PR data
