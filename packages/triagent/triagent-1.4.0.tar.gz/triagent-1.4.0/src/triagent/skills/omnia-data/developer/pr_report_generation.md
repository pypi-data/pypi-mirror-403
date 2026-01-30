---
name: pr_report_generation
display_name: "PR Report Generation"
description: "Generate comprehensive PR contribution reports showing PRs merged to develop/release branches with work item links, author attribution, and team filtering. Supports markdown, HTML, and CSV output formats."
version: "1.0.0"
tags: [pr-reports, contribution-tracking, teams, iterations, html-reports]
requires: []
subagents: []
tools:
  - mcp__azure-devops__list_pull_requests
  - mcp__azure-devops__list_repositories
  - mcp__azure-devops__get_work_item
  - mcp__azure-devops__list_work_items
triggers:
  - "PR report"
  - "PR contribution"
  - "generate PR report"
  - "team contributions"
  - "pod contributions"
  - "interactive.*report"
  - "html.*report"
---

# PR Contribution Report Generation

## Overview

Generate comprehensive PR contribution reports for Omnia Data teams showing:
- PRs merged to develop/release branches
- Work items linked to each PR
- Author attribution and contribution counts
- Grouping by iteration/sprint/pod/team

---

## Omnia Data Organization

### Pods and Teams

| Pod | Parent | Teams |
|-----|--------|-------|
| Data In Use | Omnia Data Automation | Giga, Peta, Kilo, Tera |
| Omnia JE | Omnia Data Automation | Utopia, Exa, Justice League, Jupiter, Neptune, Saturn |
| DevOps | DevOps | Slayers, Spacebots |
| Data Management and Activation | Omnia Data Management | Delta, Gamma, SkyRockets |
| Data Acquisition and Preparation | Omnia Data Management | Beta, Megatron, Alpha |
| Performance Engineering | Performance Engineering | Eagles |

**Reference:** `../data/team-config.json`

---

## Repository Configuration

### Repository Strategy

**Default Behavior:** Query ALL repositories in the target project dynamically.

**Reference:** See `../data/repository-mappings.json` for team-to-repository mappings.

#### Dynamic Repository Discovery

```bash
# Get ALL repositories in Audit Cortex 2
az repos list --project "Audit Cortex 2" --query "[].{name:name,id:id}" --output json

# Get ALL repositories in Project Omnia (for JE)
az repos list --project "Project Omnia" --query "[].{name:name,id:id}" --output json
```

#### Known Omnia Data Repositories (from omnia-data-core skill)

| Repository | Team(s) |
|------------|---------|
| data-exchange-service | Alpha, Kilo |
| cortex-datamanagement-services | Gamma |
| engagement-service | Alpha, Skyrockets |
| security-service | Skyrockets |
| data-kitchen-service | Beta, Megatron |
| analytic-template-service | Tera |
| notification-service | Beta, Skyrockets |
| staging-service | Gamma, Alpha |
| spark-job-management | Alpha, Beta |
| cortex-ui | Tera |
| client-service | Beta |
| workpaper-service | Giga |
| async-workflow-framework | Alpha, Giga |
| sampling-service | Giga |
| localization-service | Justice League, Skyrockets |
| scheduler-service | Alpha |
| cortexpy | Delta, Beta |
| analytic-notebooks | Beta |
| content-library-artifacts | All Teams |
| databricks-configuration | All Teams |
| deloitte-omnia-je (Project Omnia) | JE Teams |

**Note:** Always use dynamic discovery to capture ALL repos including any new ones not listed above.

---

## Usage Examples

### Basic Requests (Markdown output - default)

| Request | Scope | Output Format |
|---------|-------|---------------|
| "Generate PR report for all Omnia Data" | ALL AC2 repos + JE repos, all teams | Markdown (default) |
| "Generate PR report for Data In Use pod" | ALL AC2 repos, filtered by pod teams | Markdown (default) |
| "Generate PR report for Omnia JE pod" | ALL JE repos + AC2 repos | Markdown (default) |
| "Generate PR report for Delta team" | ALL AC2 repos, filtered to Delta | Markdown (default) |
| "Generate PR report for Kilo team" | ALL AC2 repos, filtered to Kilo | Markdown (default) |
| "Generate PR report for DevOps" | ALL AC2 repos, filtered to Slayers + Spacebots | Markdown (default) |
| "Generate PR report for [Author]" | Specific contributor across ALL repos | Markdown (default) |

### Format-Specific Requests

| Request | Scope | Output Format |
|---------|-------|---------------|
| "Generate **interactive** PR report for Kilo team for PI21" | Kilo team, PI21 | **HTML** |
| "Generate PR report in **html format** for Delta team" | Delta team, all PIs | **HTML** |
| "Generate **web report** for all Omnia Data for PI20" | All teams, PI20 | **HTML** |
| "Generate **rich report** for Data In Use pod" | DIU pod teams | **HTML** |
| "Generate **markdown** PR report for Kilo team" | Kilo team | Markdown |
| "Generate **simple** PR report for Delta" | Delta team | Markdown |
| "Export PR data as **csv** for all teams" | All teams, all PIs | **CSV** |
| "Generate comprehensive PR report with JE team" | Omnia Data + JE teams | **HTML** (use JE styling) |

---

## Output Format Selection

### Format Detection Keywords

| User Keywords | Output Format | Action |
|---------------|---------------|--------|
| "interactive", "html", "html format", "web report", "rich report" | **HTML** | Use template from `templates/pr-report-template.html` |
| "markdown", "md", "text", "simple" | **Markdown** | Inline display in conversation |
| "csv", "excel", "spreadsheet", "export" | **CSV** | Data export for analysis |
| (default - no format specified) | **Markdown** | Default to inline markdown |

### Report Scope Options

| User Request | Scope | Filter |
|--------------|-------|--------|
| "for Kilo team for PI21" | Single team, single PI | Team = Kilo, Iteration = PI21.* |
| "for Delta team" | Single team, all PIs | Team = Delta |
| "for PI21" | All teams, single PI | Iteration = PI21.* |
| "for all Omnia Data" | All teams, all PIs | No filter |
| "for Data In Use pod" | Pod-level (multiple teams) | Teams in DIU pod |

### HTML Report Generation

**Template file:** `./templates/pr-report-template.html`

**Output location:** `~/.triagent/reports/{scope}-pr-report.html`

**Naming convention:**
- `kilo-team-pi21-pr-report.html`
- `delta-team-pr-report.html`
- `comprehensive_pr_report_pi19-21.html`

### Template Placeholders

| Placeholder | Description |
|-------------|-------------|
| `{report_title}` | Report title (e.g., "Kilo Team PR Report - PI21") |
| `{report_subtitle}` | Subtitle with repos and date info |
| `{generation_date}` | Report generation timestamp |
| `{total_prs}` | Total PR count |
| `{work_items}` | Total work item count |
| `{authors}` | Author count |
| `{iterations}` | Iteration count |
| `{author_chips}` | Generated author chip HTML |
| `{iteration_options}` | Generated iteration dropdown options |
| `{author_options}` | Generated author dropdown options |
| `{iteration_sections}` | Generated iteration section HTML with tables |

---

## Filtering Options

### Time-Based Filters

| Filter | CLI Parameter | Example |
|--------|---------------|---------|
| By iteration | `--iteration-path` | "Audit Cortex 2\\Program Increment 21" |
| Last N months | Date calculation | `--min-time`, `--max-time` |
| Specific date range | ISO datetime | `2025-01-01` to `2025-12-31` |

### Scope Filters

| Filter | Description |
|--------|-------------|
| By repository | Single or multiple repos |
| By pod | Data In Use, Omnia JE, DevOps, etc. |
| By team | Giga, Delta, Utopia, etc. |
| By author | Individual contributor email |
| By branch | develop, release/*, master |

### Target Branch Patterns

| Branch | Pattern | Description |
|--------|---------|-------------|
| Develop | `refs/heads/develop` | Main development branch |
| Release | `refs/heads/release/*` | Release branches |
| Master | `refs/heads/master` | Production branch |

---

## Dynamic Repository Discovery

### Fetch All Repositories

Always query repositories dynamically rather than using a hardcoded list:

```bash
# Get all repositories in a project
az repos list --project "Audit Cortex 2" --query "[].{name:name,id:id}" --output json
```

### Benefits of Dynamic Discovery

1. **Complete Coverage** - Captures PRs from ALL repos, not just known ones
2. **Future-Proof** - Automatically includes new repositories
3. **Accurate Reports** - No missing contributions from lesser-known repos

### Caching Strategy

Cache repository list for the session to avoid repeated API calls:

```python
_repo_cache = {}

def get_repositories_cached(project):
    """Fetch repositories with caching."""
    if project not in _repo_cache:
        _repo_cache[project] = get_all_repositories(project)
    return _repo_cache[project]
```

### MCP Tool Alternative

When MCP tools are available, use them instead of CLI:

```python
# Using MCP tool for repository listing
repos = mcp__azure-devops__repo_list_repos_by_project(project="Audit Cortex 2")
```

---

## Report Generation Workflow

### Step 1: Identify Scope

```
1. Parse user request for:
   - Target scope (all/pod/team/individual)
   - Time range (iteration/months/custom)
   - Repositories (all/specific)
   - Target branch (develop/release)
```

### Step 2: Determine Repositories

```python
def get_all_repositories(project):
    """Dynamically fetch all repositories from a project."""
    cmd = [
        "az", "repos", "list",
        "--project", project,
        "--query", "[].{name:name,id:id}",
        "--output", "json"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error fetching repositories for {project}: {result.stderr}")
        return []
    return json.loads(result.stdout)

def get_repositories_for_scope(scope, include_je=False):
    """Get repositories based on scope - queries ALL repos by default."""
    # Always fetch all AC2 repositories dynamically
    ac2_repos = get_all_repositories("Audit Cortex 2")

    if include_je or scope == "all" or scope == "Omnia JE":
        je_repos = get_all_repositories("Project Omnia")
        return ac2_repos + je_repos

    return ac2_repos
```

### Step 3: Query PRs (Parallel)

Use ThreadPoolExecutor for parallel API calls to multiple repositories.

### Step 4: Filter by Target Branch

Filter PRs by target branch pattern:
- `refs/heads/develop` for development PRs
- `refs/heads/release/*` for release PRs

### Step 5: Get Work Items (Parallel)

For each PR, retrieve linked work items using parallel processing.

### Step 6: Filter by Team/Author

Apply team or author filters based on work item area path or PR creator.

### Step 7: Group PRs by Work Item

Aggregate PRs under their linked work items for the report.

### Step 8: Generate HTML Report

Create interactive HTML report with filters and summary cards.

---

## Azure CLI Commands

### List PRs from Repository

```bash
# List completed PRs targeting develop branch
az repos pr list \
  --repository <repo_name> \
  --project "Audit Cortex 2" \
  --status completed \
  --target-branch develop \
  --query "[].{id:pullRequestId,title:title,createdBy:createdBy.displayName,email:createdBy.uniqueName,mergeStatus:mergeStatus,closedDate:closedDate}" \
  --output json

# List PRs with date filter
az repos pr list \
  --repository <repo_name> \
  --project "Audit Cortex 2" \
  --status completed \
  --target-branch develop \
  --query "[?closedDate >= '2025-01-01']" \
  --output json
```

### Get Work Items for PR

```bash
# Get work items linked to a PR
az repos pr work-item list \
  --id <PR_ID> \
  --query "[].{id:id,title:fields.\"System.Title\",type:fields.\"System.WorkItemType\",areaPath:fields.\"System.AreaPath\",iteration:fields.\"System.IterationPath\"}" \
  --output json
```

### Get Work Item Details

```bash
# Get work item with iteration and area path
az boards work-item show \
  --id <WORK_ITEM_ID> \
  --fields "System.Title,System.AreaPath,System.IterationPath,System.State" \
  --output json
```

---

## Python Script Template

### Parallel PR Fetching

```python
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

def fetch_prs_for_repo(repo_name, project, target_branch="develop", min_date=None):
    """Fetch completed PRs for a repository."""
    cmd = [
        "az", "repos", "pr", "list",
        "--repository", repo_name,
        "--project", project,
        "--status", "completed",
        "--target-branch", target_branch,
        "--output", "json"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error fetching PRs for {repo_name}: {result.stderr}")
        return []

    prs = json.loads(result.stdout)

    # Filter by date if specified
    if min_date:
        prs = [pr for pr in prs if pr.get("closedDate", "") >= min_date]

    # Add repo info to each PR
    for pr in prs:
        pr["repository"] = repo_name
        pr["project"] = project

    return prs

def fetch_work_items_for_pr(pr_id):
    """Fetch work items linked to a PR."""
    cmd = [
        "az", "repos", "pr", "work-item", "list",
        "--id", str(pr_id),
        "--output", "json"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return []

    return json.loads(result.stdout)

def generate_pr_report(repos, project, target_branch="develop", months=3):
    """Generate PR report for multiple repositories."""
    min_date = (datetime.now() - timedelta(days=months*30)).isoformat()

    all_prs = []

    # Fetch PRs in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(fetch_prs_for_repo, repo, project, target_branch, min_date): repo
            for repo in repos
        }

        for future in as_completed(futures):
            repo = futures[future]
            try:
                prs = future.result()
                all_prs.extend(prs)
                print(f"Fetched {len(prs)} PRs from {repo}")
            except Exception as e:
                print(f"Error fetching {repo}: {e}")

    # Fetch work items for each PR in parallel
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {
            executor.submit(fetch_work_items_for_pr, pr["pullRequestId"]): pr
            for pr in all_prs
        }

        for future in as_completed(futures):
            pr = futures[future]
            try:
                work_items = future.result()
                pr["workItems"] = work_items
            except Exception as e:
                pr["workItems"] = []

    return all_prs
```

---

## HTML Report Template

### Summary Cards

```html
<div class="summary-cards">
  <div class="card">
    <h3>Total PRs</h3>
    <p class="count">{pr_count}</p>
  </div>
  <div class="card">
    <h3>Work Items</h3>
    <p class="count">{wi_count}</p>
  </div>
  <div class="card">
    <h3>Contributors</h3>
    <p class="count">{author_count}</p>
  </div>
  <div class="card">
    <h3>Repositories</h3>
    <p class="count">{repo_count}</p>
  </div>
</div>
```

### Author Summary Section

```html
<div class="author-summary">
  <h2>Contributor Summary</h2>
  <table>
    <thead>
      <tr>
        <th>Author</th>
        <th>Team</th>
        <th>PR Count</th>
        <th>Work Items</th>
      </tr>
    </thead>
    <tbody>
      <!-- Dynamically generated rows -->
    </tbody>
  </table>
</div>
```

### Filter Dropdowns

```html
<div class="filters">
  <select id="iteration-filter">
    <option value="">All Iterations</option>
    <option value="PI 20">PI 20</option>
    <option value="PI 21">PI 21</option>
  </select>

  <select id="author-filter">
    <option value="">All Authors</option>
    <!-- Dynamically populated -->
  </select>

  <select id="repo-filter">
    <option value="">All Repositories</option>
    <option value="cortexpy">cortexpy</option>
    <option value="analytic-notebooks">analytic-notebooks</option>
  </select>

  <input type="text" id="search" placeholder="Search PRs...">
</div>
```

### Collapsible Iteration Sections

```html
<div class="iteration-section">
  <h3 class="collapsible">Program Increment 21 ({pr_count} PRs)</h3>
  <div class="content">
    <!-- Work item cards with PR chips -->
  </div>
</div>
```

### PR Chips with Indicators

```html
<div class="pr-chip" data-repo="{repo}" data-author="{author}">
  <span class="repo-badge">{repo}</span>
  <a href="{pr_url}">PR #{pr_id}</a>
  <span class="author">{author}</span>
</div>
```

---

## URL Patterns

### Azure DevOps URLs

| Entity | Project | URL Pattern |
|--------|---------|-------------|
| PR (AC2) | Audit Cortex 2 | `https://dev.azure.com/symphonyvsts/Audit%20Cortex%202/_git/{repo_name}/pullrequest/{pr_id}` |
| PR (PO) | Project Omnia | `https://dev.azure.com/symphonyvsts/Project%20Omnia/_git/{repo_name}/pullrequest/{pr_id}` |
| WI (AC2) | Audit Cortex 2 | `https://dev.azure.com/symphonyvsts/Audit%20Cortex%202/_workitems/edit/{wi_id}` |
| WI (PO) | Project Omnia | `https://dev.azure.com/symphonyvsts/Project%20Omnia/_workitems/edit/{wi_id}` |

### URL Construction Functions

```python
def get_pr_url(project, repo_name, pr_id):
    """Generate PR URL based on project."""
    project_encoded = project.replace(" ", "%20")
    return f"https://dev.azure.com/symphonyvsts/{project_encoded}/_git/{repo_name}/pullrequest/{pr_id}"

def get_work_item_url(project, wi_id):
    """Generate work item URL based on project."""
    project_encoded = project.replace(" ", "%20")
    return f"https://dev.azure.com/symphonyvsts/{project_encoded}/_workitems/edit/{wi_id}"
```

---

## Report Output Options

### Format Selection Priority

1. **Explicit user request** - "html", "interactive", "web report" -> Generate HTML file
2. **Explicit markdown request** - "markdown", "text", "simple" -> Inline markdown
3. **Default** - No format keyword -> Markdown (displayed inline)

### HTML Report Generation

**Trigger keywords:** "interactive", "html", "html format", "web report", "rich report"

**Template:** See `./templates/pr-report-template.html`

**When HTML is requested:**
1. Query ADO for PRs using the scope filters (team, PI)
2. Read the HTML template file
3. Replace placeholders with generated data
4. Save to `~/.triagent/reports/{scope}-pr-report.html`
5. Provide file path and open command to user

**Example response:**
```
The interactive HTML report has been generated.

**File:** `~/.triagent/reports/kilo-team-pi21-pr-report.html`

**To open:** `open ~/.triagent/reports/kilo-team-pi21-pr-report.html`

The report includes:
- 32 PRs from 10 contributors
- Interactive filters by iteration, author, and search
- Collapsible iteration sections
- Work item links with associated PRs
```

**HTML Features:**
- Summary statistics cards
- Author contribution chips (sorted by PR count)
- Filter dropdowns (iteration, author)
- Search functionality
- Collapsible sections by iteration
- Clickable links to PRs and work items

### Markdown Report (Default)

Simple markdown format for inline display:

```markdown
# PR Contribution Report

## Summary
- **Period:** 2025-01-01 to 2025-03-31
- **Total PRs:** 150
- **Work Items:** 75
- **Contributors:** 25

## Contributions by Author

| Author | Team | PRs | Work Items |
|--------|------|-----|------------|
| John Doe | Delta | 15 | 8 |
| Jane Smith | Giga | 12 | 6 |

## PRs by Iteration

### Program Increment 21

#### WI #12345: Feature Title
- PR #100 (cortexpy) - John Doe
- PR #101 (analytic-notebooks) - Jane Smith
```

### CSV Export

For data analysis and spreadsheet import:

```csv
PR_ID,Repository,Title,Author,Team,Work_Item_ID,Work_Item_Title,Iteration,Closed_Date
100,cortexpy,Feature implementation,John Doe,Delta,12345,Feature Title,PI 21,2025-01-15
```

---

## Team Filtering Logic

### Filter by Pod

```python
POD_TEAMS = {
    "Data In Use": ["Giga", "Peta", "Kilo", "Tera"],
    "Omnia JE": ["Utopia", "Exa", "Justice League", "Jupiter", "Neptune", "Saturn"],
    "DevOps": ["Slayers", "Spacebots"],
    "Data Management and Activation": ["Delta", "Gamma", "SkyRockets"],
    "Data Acquisition and Preparation": ["Beta", "Megatron", "Alpha"],
    "Performance Engineering": ["Eagles"]
}

def filter_by_pod(prs, pod_name):
    """Filter PRs by pod based on work item area path."""
    teams = POD_TEAMS.get(pod_name, [])
    return [pr for pr in prs if any(
        team in wi.get("fields", {}).get("System.AreaPath", "")
        for wi in pr.get("workItems", [])
        for team in teams
    )]
```

### Filter by Team

```python
def filter_by_team(prs, team_name):
    """Filter PRs by team based on work item area path."""
    return [pr for pr in prs if any(
        team_name in wi.get("fields", {}).get("System.AreaPath", "")
        for wi in pr.get("workItems", [])
    )]
```

### Filter by Author

```python
def filter_by_author(prs, author_email):
    """Filter PRs by author email."""
    return [pr for pr in prs
            if pr.get("createdBy", {}).get("uniqueName", "").lower() == author_email.lower()]
```

---

## Iteration Mapping

| Release | Iteration Path |
|---------|----------------|
| 9.5 | Program Increment 20 |
| 9.6 | Program Increment 21 |
| Current | Program Increment 21 |

### Iteration Path Pattern

```
Audit Cortex 2\Program Increment {pi_number}\Sprint {sprint_number}
```

---

## Error Handling

### Common Issues

| Issue | Cause | Resolution |
|-------|-------|------------|
| Empty PR list | No completed PRs in date range | Expand date range |
| Missing work items | PRs not linked to work items | Note in report |
| API rate limiting | Too many parallel requests | Reduce workers |
| Permission denied | Insufficient ADO permissions | Check user access |

### Retry Logic

```python
import time
from functools import wraps

def retry_on_failure(max_retries=3, delay=1):
    """Decorator for retrying failed API calls."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))
                    else:
                        raise
        return wrapper
    return decorator
```

---

## Best Practices

### Performance

1. Use parallel execution for independent API calls
2. Limit ThreadPoolExecutor workers (10-20 max)
3. Cache repository IDs to avoid repeated lookups
4. Filter early to reduce data processing

### Accuracy

1. Always verify target branch pattern
2. Check work item area paths for team filtering
3. Handle PRs without linked work items
4. Validate date ranges before querying

### Reporting

1. Include report generation timestamp
2. Show filter criteria applied
3. Provide clickable links to ADO
4. Export options (HTML, Markdown, CSV)
