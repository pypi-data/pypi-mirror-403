---
name: omnia-data-developer
description: |
  Developer skills for code review, PR management, and release investigation.
  Auto-activates for: code review requests, PR mentions, pipeline issues, file extensions.
triggers:
  - "review.*PR"
  - "review.*pull request"
  - "code review"
  - "PR #?\\d+"
  - "\\.py$|\\.cs$|\\.ipynb$"
  - "\\.sql$"
  - "\\.csproj$"
  - "dotnet.*review"
  - "sql.*review"
  - "pre-deployment"
  - "post-deployment"
  - "release.*investigation"
  - "pipeline.*issue"
  - "check.*code"
  - "refactor"
  - "comprehensive.*review"
  - "full.*review"
  - "design.*document"
  - "acceptance.*criteria"
  - "implementation.*notes"
  - "review.*against"
  - "PR report"
  - "PR contribution"
  - "generate PR report"
  - "developer contributions"
  - "team contributions"
  - "pod contributions"
version: 2.1.0
---

## On-Demand Sub-Skill Loading

This skill uses contextual loading to minimize token usage. Load sub-skills based on the context of the task.

### Code Review Sub-Skills

| Context | Sub-Skill to Load | Path |
|---------|-------------------|------|
| `.py`/`.ipynb` with `pyspark`/`spark`/`delta` imports | PySpark Code Review | `./pyspark_code_review.md` |
| `.py` without Spark imports | Python Code Review | `./python_code_review.md` |
| `.cs`, `.sql`, `.csproj`, `.config` files | .NET Code Review | `./dotnet_code_review.md` |

### Pipeline Sub-Skills

| Context | Sub-Skill to Load | Path |
|---------|-------------------|------|
| Pipeline failure, build error, "why did build fail" | Release Investigation | `./release_investigation.md` |
| "which pipeline", "find pipeline", pipeline identification | Release Pipeline | `./release_pipeline.md` |

### PR Report Sub-Skills

| Context | Sub-Skill to Load | Path |
|---------|-------------------|------|
| "PR report", "generate PR report", "PR contribution" | PR Report Generation | `./pr_report_generation.md` |
| "team contributions", "pod contributions", "developer contributions" | PR Report Generation | `./pr_report_generation.md` |
| "html report", "interactive report", "web report" for PRs | PR Report Generation | `./pr_report_generation.md` |
| PI/iteration-based PR queries | PR Report Generation | `./pr_report_generation.md` |

### Loading Instructions

When performing code review:
1. **Identify file types** in the PR or request
2. **Check for Spark imports** in Python files (`import pyspark`, `from pyspark`, `from delta`)
3. **Load appropriate sub-skill** using the Read tool before applying guidelines
4. **Apply guidelines** from the loaded sub-skill

Example:
```
# If PR contains .py files with spark imports:
Read ./pyspark_code_review.md

# If PR contains .py files without spark imports:
Read ./python_code_review.md

# If PR contains .cs or .sql files:
Read ./dotnet_code_review.md
```

When generating PR reports:
1. **Detect PR report keywords** in user request: "PR report", "contribution report", "generate report"
2. **Check for format keywords**: "html", "interactive", "web report" → HTML output
3. **Load the sub-skill** using the Read tool:
   ```
   Read ./pr_report_generation.md
   ```
4. **Apply guidelines** from the loaded sub-skill including:
   - Team/Pod structure
   - Repository mappings
   - HTML template usage
   - Filtering logic

---

## Core References

- [API Best Practices](../core/api-best-practices.md) - CLI vs MCP guidelines
- [Organization Context](../core/organization-context.md) - ADO org/project constants
- [Release Strategy](../core/release-strategy.md) - Branch/release patterns
- [Team Information](../core/team-info.md) - Team hierarchy and structure
- [ADO Field Reference](../reference/ado-field-reference.md) - Complete field documentation

---

## API Preference Guidelines

For comprehensive CLI vs MCP tool guidelines, see [API Best Practices](../core/api-best-practices.md).

### Quick Reference - PR Review Commands

```bash
# Get PR details
az repos pr show \
  --id <PR_ID> \
  --query "{id:pullRequestId,title:title,status:status,sourceRef:sourceRefName,targetRef:targetRefName}" \
  --output tsv

# Get work items linked to PR
az repos pr work-item list \
  --id <PR_ID> \
  --query "[].{id:id,title:fields.\"System.Title\",type:fields.\"System.WorkItemType\"}" \
  --output tsv

# Get work item with acceptance criteria
az boards work-item show \
  --id <WORK_ITEM_ID> \
  --fields "System.Title,System.Description,Microsoft.VSTS.Common.AcceptanceCriteria,System.State" \
  --output json
```

### When to Use MCP Tools (Fallback)
- Adding inline PR comments (use az devops invoke)
- Wiki search for design documents
- Complex relationship traversal
- When CLI doesn't support specific operation

---

# Developer Skills

## Pull Request Review Workflow

### Review Process

1. **List PRs**: Use `mcp__azure-devops__list_pull_requests` to find active PRs
2. **Get PR Details**: Use `mcp__azure-devops__repo_get_pull_request_by_id` for work item links
3. **Context Discovery**: (see Comprehensive PR Review Workflow)
   - Query work item description, comments, and custom fields
   - Query parent Feature/Epic if applicable
   - Search wiki for design documents
4. **Design Document Review**: Validate against design specifications
5. **AC Coverage Review**: Check acceptance criteria coverage
6. **Implementation Notes Review**: Validate technical approach
7. **Get Changes**: Use `mcp__azure-devops__get_pull_request_changes` to see files modified
8. **Code Review Against Guidelines**: (see Phase 6)
   - Load PySpark/Python/.NET guidelines from skill or use defaults
   - Generate findings with severity (CRITICAL/HIGH/MEDIUM/LOW)
   - Format with current code and proposed fix
   - Prompt user to select findings for inline comments
9. **Unit Test Requirements**: Identify methods needing tests, add inline comments
10. **Check Status**: Use `mcp__azure-devops__get_pull_request_checks` for CI status
11. **Generate Summary**: Create comprehensive review report (8 phases)
12. **Set Vote**: Based on review findings

### Adding Inline Comments

When posting review comments:

- Use `mcp__azure-devops__add_pull_request_comment` for inline feedback
- Specify file path and line numbers for precise placement
- Include severity: info, suggestion, warning, or issue
- Provide actionable feedback with code examples when possible

### Voting

After review, set appropriate vote:
- **Approved**: Code meets standards
- **Approved with suggestions**: Minor improvements recommended
- **Wait for author**: Changes required before merge
- **Rejected**: Significant issues that block merge

---

## Comprehensive PR Review Workflow

### Overview

When performing code review, conduct a multi-faceted analysis covering:
1. **Design Document Compliance** - Code aligns with architectural decisions
2. **Acceptance Criteria Coverage** - All AC from PBI/Feature are addressed
3. **Implementation Notes Validation** - Technical approach matches documented plans
4. **Unit Test Requirements** - Test scenarios for each new/modified method

### Phase 1: Context Discovery

Before reviewing code, gather all relevant context from the work item hierarchy.

#### 1.1 Get PR and Linked Work Items

**Preferred: Azure CLI (44% fewer tokens)**

```bash
# Get PR details with work item links (CLI preferred)
az repos pr show \
  --id [pr_id] \
  --query "{id:pullRequestId,title:title,status:status,sourceRef:sourceRefName,targetRef:targetRefName,createdBy:createdBy.displayName}" \
  --output tsv

# Get work items linked to PR (CLI preferred)
az repos pr work-item list \
  --id [pr_id] \
  --query "[].{id:id,title:fields.\"System.Title\",type:fields.\"System.WorkItemType\",state:fields.\"System.State\"}" \
  --output tsv
```

**Fallback: MCP Tools**

```bash
# Get PR details with work item links (MCP fallback)
mcp__azure-devops__repo_get_pull_request_by_id(
  repositoryId="[repo_id]",
  pullRequestId=[pr_id]
)
```

#### 1.2 Query Work Item for Review Context

**Preferred: Azure CLI (44% fewer tokens)**

```bash
# Get work item with full details (CLI preferred)
az boards work-item show \
  --id [work_item_id] \
  --expand relations \
  --query "{id:id,title:fields.\"System.Title\",description:fields.\"System.Description\",ac:fields.\"Microsoft.VSTS.Common.AcceptanceCriteria\",state:fields.\"System.State\",relations:relations}" \
  --output json
```

**Fallback: MCP Tools**

```bash
# Get work item with full details (MCP fallback)
mcp__azure-devops__wit_get_work_item(
  id=[work_item_id],
  project="Audit Cortex 2",
  expand="relations,fields"
)
```

**Extract from work item:**
- `System.Description` - Contains implementation notes
- `Microsoft.VSTS.Common.AcceptanceCriteria` - AC to validate
- `Custom.ImplementationNotes` - Technical approach (if exists)
- Comments - May contain design doc links
- Relations - Parent Feature/Epic links

#### 1.3 Query Work Item Comments

**Preferred: Azure CLI**

```bash
# Get all comments for design doc references (CLI preferred)
az boards work-item show \
  --id [work_item_id] \
  --expand all \
  --query "comments" \
  --output json
```

**Fallback: MCP Tools**

```bash
# Get all comments for design doc references (MCP fallback)
mcp__azure-devops__wit_list_work_item_comments(
  project="Audit Cortex 2",
  workItemId=[work_item_id]
)
```

**Search patterns in comments:**
- Wiki URLs: `/Omnia-Data-Wiki/Technical-Documentation/*`
- SharePoint links: `*.sharepoint.com/*`
- Design document mentions: "design doc", "technical design", "architecture"

#### 1.4 Query Parent Work Item (Feature/Epic)

If the PR work item is a PBI, get the parent Feature/Epic which often contains design docs.

**Preferred: Azure CLI (44% fewer tokens)**

```bash
# Get parent work item (CLI preferred)
az boards work-item show \
  --id [parent_id] \
  --expand relations \
  --query "{id:id,title:fields.\"System.Title\",description:fields.\"System.Description\",ac:fields.\"Microsoft.VSTS.Common.AcceptanceCriteria\",relations:relations}" \
  --output json
```

**Fallback: MCP Tools**

```bash
# Get parent work item (MCP fallback)
mcp__azure-devops__wit_get_work_item(
  id=[parent_id],
  project="Audit Cortex 2",
  expand="relations,fields"
)
```

**Extract from parent:**
- Feature Description (may contain design overview)
- Feature Acceptance Criteria (high-level requirements)
- Comments (design document links)
- Design document custom fields

#### 1.5 Search Wiki for Design Documents

**Note:** Wiki operations require MCP tools as Azure CLI doesn't have direct wiki API support.

```bash
# Search wiki for related design documentation (MCP required)
mcp__azure-devops__search_wiki(
  searchText="[feature area] design",
  project=["Audit Cortex 2"],
  top=5
)
```

### Phase 2: Design Document Discovery

#### 2.1 Document Sources (Search Order)

| Priority | Source | Fields to Search |
|----------|--------|------------------|
| 1 | PBI Description | "Design Document", "Technical Design" sections |
| 2 | PBI Comments | Wiki URLs, SharePoint links |
| 3 | PBI Custom Fields | `Custom.DesignDocument`, hyperlinks |
| 4 | Parent Feature Description | Architecture overview, design links |
| 5 | Parent Feature Comments | Design doc references |
| 6 | Wiki Search | "[feature area] design", "[component] architecture" |

#### 2.2 Design Document URL Patterns

| Source | Pattern | Example |
|--------|---------|---------|
| ADO Wiki | `/Omnia-Data-Wiki/Technical-Documentation/*` | `/Omnia-Data-Wiki/Technical-Documentation/DIC-V2-Design` |
| SharePoint | `*.sharepoint.com/*` | `https://deloitte.sharepoint.com/sites/OmniaData/design.docx` |
| Confluence | `*.atlassian.net/wiki/*` | `https://company.atlassian.net/wiki/spaces/OD/pages/123` |

#### 2.3 When Design Document NOT Found

Display status and prompt user:

```
═══════════════════════════════════════════════════════════════
            DESIGN DOCUMENT NOT FOUND
═══════════════════════════════════════════════════════════════

I searched the following locations for design documentation:

✗ PBI #[ID] Description: No design doc section found
✗ PBI #[ID] Comments: No design doc links found
✗ Parent Feature #[ID]: No design doc attached
✗ Wiki Search "[keywords]": No matching design pages

To provide comprehensive code review aligned with architectural
decisions, please provide the design document link(s):

[Use AskUserQuestion with options:]
- "Provide design document link" → Prompt for URL
- "Proceed without design document" → Standard review only
- "Cancel review" → Abort
═══════════════════════════════════════════════════════════════
```

### Phase 3: Review Against Design Document

If design document is found, extract and validate:

#### 3.1 Design Compliance Checklist

| Check | Description |
|-------|-------------|
| Architecture Alignment | Code follows documented architecture patterns |
| API Contracts | Interfaces match design specifications |
| Data Models | Schema matches documented models |
| Error Handling | Follows documented error handling strategy |
| Performance | Meets documented performance requirements |
| Security | Implements documented security measures |

#### 3.2 Design Review Comment Format

```
**Design Document Review**

📄 Design Doc: [link]

**Compliance Status:**
✅ Architecture: Code follows documented pattern
✅ API Contract: Interface matches specification
⚠️ Error Handling: Missing retry logic per design doc section 3.2
❌ Performance: Missing caching per design doc section 4.1

**Required Changes:**
1. Add retry logic as specified in design doc section 3.2
2. Implement caching per design doc section 4.1
```

### Phase 4: Review Against Acceptance Criteria

#### 4.1 Parse Acceptance Criteria

Extract AC from work item `Microsoft.VSTS.Common.AcceptanceCriteria` field.
Parse into individual criteria items (AC-1, AC-2, etc.)

#### 4.2 Map Code Changes to AC

For each file in PR changes:
1. Identify which AC the changes address
2. Check if implementation fully satisfies the criterion
3. Flag gaps where AC is not addressed

#### 4.3 AC Coverage Report

```
═══════════════════════════════════════════════════════════════
            ACCEPTANCE CRITERIA COVERAGE
═══════════════════════════════════════════════════════════════

PBI #[ID]: [Title]

| AC # | Criterion | Covered | Files |
|------|-----------|---------|-------|
| AC-1 | [Summary] | ✅ Yes | file1.py, file2.py |
| AC-2 | [Summary] | ⚠️ Partial | file1.py |
| AC-3 | [Summary] | ❌ No | - |

**Coverage:** 1/3 Fully Covered (33%), 1 Partial, 1 Gap

**Gaps Identified:**
- AC-3: "[Criterion text]" - No code changes address this requirement
═══════════════════════════════════════════════════════════════
```

### Phase 5: Review Against Implementation Notes

#### 5.1 Extract Implementation Notes

Look for implementation notes in:
- PBI Description under "Implementation Notes" heading
- `Custom.ImplementationNotes` field
- Parent Feature technical details
- PR description

#### 5.2 Implementation Validation

| Check | Description |
|-------|-------------|
| Technical Approach | Code follows documented implementation approach |
| Dependencies | Uses documented libraries/frameworks |
| Patterns | Follows documented coding patterns |
| Edge Cases | Handles documented edge cases |

#### 5.3 Implementation Notes Review Comment

```
**Implementation Notes Review**

📋 Implementation Notes Source: PBI #[ID] Description

**Validation:**
✅ Technical Approach: Follows cascading autocorrect pattern
✅ Dependencies: Uses Spark SQL as documented
⚠️ Edge Cases: Missing null handling for empty DataFrames
❌ Error Handling: Not using documented retry pattern

**Required Changes:**
1. Add null DataFrame handling per implementation notes
2. Implement retry pattern per section "Error Handling Strategy"
```

### Phase 6: Code Review Against Guidelines

#### 6.1 Load Code Review Guidelines

Load language-specific guidelines from the skill or use defaults:

```
# Priority order for loading guidelines:
1. For .NET files (.cs, .sql, .csproj, .config):
   Load from `./dotnet_code_review.md`
   - C# Code Review Guidelines (DN-01 to DN-44)
   - SQL Script Review Guidelines (SQL-01 to SQL-19)
   - Entity Framework Patterns
   - Resource Management

2. For PySpark/Python files (.py, .ipynb):
   Load from this SKILL.md file:
   - PySpark Code Review Guidelines (Section: PySpark Code Review Guidelines)
   - Python Code Review Guidelines (Section: Python Code Review Guidelines)
   - Code Review Checklist (Section: Code Review Checklist)

3. If skill not available, use Claude Code default review capabilities:
   - OWASP security patterns
   - Language-specific best practices
   - Performance anti-patterns
   - Code quality standards
```

#### 6.2 Review Categories by Language

| Language | Categories to Review |
|----------|---------------------|
| **PySpark** | UDF usage, join optimization, broadcast hints, caching, serverless compatibility, credentials |
| **Python** | Type annotations, error handling, naming conventions, DRY, SRP |
| **.NET** | SOLID principles, async/await, LINQ efficiency, DI patterns, SQL injection, Entity Framework |
| **SQL** | Pre-deployment checks, object existence, data safety, deployment order, parameterized queries |

#### 6.3 Severity Classifications

| Severity | Criteria | Action Required |
|----------|----------|-----------------|
| **CRITICAL** | Security vulnerabilities, data loss risks, production blockers | Must fix before merge |
| **HIGH** | Performance issues (>50% degradation), major code quality violations | Should fix before merge |
| **MEDIUM** | Minor performance issues, code style violations, missing best practices | Recommended to fix |
| **LOW** | Suggestions, minor improvements, cosmetic issues | Nice to have |

#### 6.4 Code Review Findings Report Format

```
═══════════════════════════════════════════════════════════════
            CODE REVIEW FINDINGS
═══════════════════════════════════════════════════════════════

PR #[ID]: [Title]
Language(s): [PySpark, Python, .NET]
Guidelines Source: [Skill/Default]

───────────────────────────────────────────────────────────────
                    SUMMARY
───────────────────────────────────────────────────────────────

| Severity | Count |
|----------|-------|
| CRITICAL | 2     |
| HIGH     | 3     |
| MEDIUM   | 5     |
| LOW      | 4     |
| **Total**| **14**|

───────────────────────────────────────────────────────────────
                    FINDINGS
───────────────────────────────────────────────────────────────

### CRITICAL (2)

**[CR-1]** Security: Hardcoded Credentials
- **File:** `src/data_processor.py:45`
- **Category:** Security
- **Current:**
  \`\`\`python
  password = "my_secret_password"
  connection_string = f"server=db;password={password}"
  \`\`\`
- **Proposed Fix:**
  \`\`\`python
  password = dbutils.secrets.get(scope="my-scope", key="db-password")
  connection_string = f"server=db;password={password}"
  \`\`\`

**[CR-2]** Security: SQL Injection Vulnerability
- **File:** `src/query_builder.py:112`
- **Category:** Security
- **Current:**
  \`\`\`python
  query = f"SELECT * FROM users WHERE id = {user_id}"
  \`\`\`
- **Proposed Fix:**
  \`\`\`python
  query = "SELECT * FROM users WHERE id = ?"
  cursor.execute(query, (user_id,))
  \`\`\`

### HIGH (3)

**[CR-3]** Performance: Python UDF Instead of Native Function
- **File:** `src/transformer.py:78`
- **Category:** Performance
- **Current:**
  \`\`\`python
  @udf(returnType=DoubleType())
  def calculate_ratio(a, b):
      return a / b if b != 0 else 0.0
  df = df.withColumn("ratio", calculate_ratio(F.col("a"), F.col("b")))
  \`\`\`
- **Proposed Fix:**
  \`\`\`python
  df = df.withColumn("ratio",
      F.when(F.col("b") != 0, F.col("a") / F.col("b")).otherwise(0.0))
  \`\`\`

**[CR-4]** Performance: Missing Broadcast Hint
- **File:** `src/joiner.py:156`
- **Category:** Performance
- **Current:**
  \`\`\`python
  result = large_df.join(small_lookup_df, "key")
  \`\`\`
- **Proposed Fix:**
  \`\`\`python
  result = large_df.join(F.broadcast(small_lookup_df), "key")
  \`\`\`

**[CR-5]** Performance: Unnecessary collect() in Loop
- **File:** `src/aggregator.py:89`
- **Category:** Performance
- **Current:**
  \`\`\`python
  for row in df.collect():
      process_row(row)
  \`\`\`
- **Proposed Fix:**
  \`\`\`python
  df.foreach(process_row)
  # Or use foreachPartition for batched processing
  \`\`\`

### MEDIUM (5)

**[CR-6]** Code Quality: Missing Type Annotations
- **File:** `src/helper.py:23`
- **Category:** Code Quality
- **Current:**
  \`\`\`python
  def process_data(data, options):
      return transform(data)
  \`\`\`
- **Proposed Fix:**
  \`\`\`python
  def process_data(data: DataFrame, options: dict[str, Any]) -> DataFrame:
      return transform(data)
  \`\`\`

**[CR-7]** Code Quality: Bare Exception Handler
- **File:** `src/loader.py:67`
- **Category:** Code Quality
- **Current:**
  \`\`\`python
  try:
      load_data()
  except:
      pass
  \`\`\`
- **Proposed Fix:**
  \`\`\`python
  try:
      load_data()
  except SpecificException as e:
      logger.error(f"Failed to load data: {e}")
      raise
  \`\`\`

[... additional findings ...]

### LOW (4)

**[CR-12]** Style: Non-descriptive Variable Name
- **File:** `src/utils.py:34`
- **Category:** Code Style
- **Current:** `x = get_count()`
- **Proposed Fix:** `record_count = get_count()`

[... additional findings ...]

───────────────────────────────────────────────────────────────
                    SELECT FINDINGS FOR INLINE COMMENTS
───────────────────────────────────────────────────────────────

Enter finding numbers to add as inline PR comments (comma-separated):
Example: CR-1, CR-3, CR-5, CR-7

[Use AskUserQuestion with options:]
- "Add all CRITICAL and HIGH" → Add CR-1 through CR-5
- "Add all findings" → Add all 14 comments
- "Select specific findings" → Prompt for comma-separated list
- "Skip inline comments" → Continue without adding comments

═══════════════════════════════════════════════════════════════
```

#### 6.5 PySpark-Specific Checks

| Check ID | Category | Rule |
|----------|----------|------|
| PS-01 | Performance | No Python UDFs when native functions exist |
| PS-02 | Performance | Broadcast hints for tables < 100MB |
| PS-03 | Performance | No unnecessary `collect()` or `toPandas()` |
| PS-04 | Performance | No `SELECT *` in production |
| PS-05 | Security | Credentials via `dbutils.secrets.get()` |
| PS-06 | Security | Unity Catalog three-level namespace |
| PS-07 | Compatibility | Check serverless vs classic compute features |
| PS-08 | Quality | Method chaining for transformations |

#### 6.6 Python-Specific Checks

| Check ID | Category | Rule |
|----------|----------|------|
| PY-01 | Quality | Type annotations on all public functions |
| PY-02 | Quality | Specific exception handling (no bare except) |
| PY-03 | Quality | DRY - no duplicate code blocks |
| PY-04 | Naming | snake_case for functions and variables |
| PY-05 | Naming | PascalCase for classes |
| PY-06 | Naming | UPPER_SNAKE_CASE for constants |
| PY-07 | Security | No hardcoded secrets |
| PY-08 | Quality | Single Responsibility Principle |

#### 6.7 .NET-Specific Checks

For comprehensive .NET code review guidelines including C#, SQL, and Entity Framework patterns,
see [dotnet_code_review.md](./dotnet_code_review.md).

**Quick Reference - Check ID Ranges:**

| Check Range | Category |
|-------------|----------|
| DN-01 to DN-08 | Architecture & Patterns (SOLID, DI, layers) |
| DN-09 to DN-16 | Performance (async/await, LINQ, HttpClient) |
| DN-17 to DN-24 | Security (SQL injection, secrets, auth) |
| DN-25 to DN-28 | Resource Management (IDisposable, streams) |
| DN-29 to DN-32 | Null Handling (nullable types, operators) |
| DN-33 to DN-36 | Logging & Observability (structured logging) |
| DN-37 to DN-44 | Entity Framework (DbContext, N+1, transactions) |
| SQL-01 to SQL-13 | Deployment-Breaking (Priority 1) |
| SQL-14 to SQL-17 | Data Safety (Priority 2) |
| SQL-18 to SQL-19 | Code Quality (Priority 3) |

**Critical .NET Checks (Always Verify):**

| Check ID | Category | Rule |
|----------|----------|------|
| DN-09 | Performance | No blocking async calls (.Result, .Wait()) |
| DN-15 | Performance | HttpClient via IHttpClientFactory only |
| DN-17 | Security | Parameterized SQL queries |
| DN-19 | Security | No hardcoded credentials |
| DN-37 | EF Core | DbContext scoped, not singleton |
| DN-39 | EF Core | No N+1 queries (use Include) |

**Critical SQL Checks (Always Verify):**

| Check ID | Category | Rule |
|----------|----------|------|
| SQL-01 | Deployment | EXISTS clauses with OBJECT_ID check |
| SQL-04 | Deployment | SELECT/UPDATE/DELETE with OBJECT_ID check |
| SQL-05 | Deployment | Column existence check before reference |
| SQL-14 | Data Safety | DELETE with WHERE clause |
| SQL-15 | Data Safety | UPDATE with WHERE clause |
| SQL-19 | Security | Parameterized dynamic SQL |

---

### Phase 7: Unit Test Requirements

#### 7.1 Identify Methods Requiring Tests

For each new/modified method in the PR:
1. Extract method signature and docstring
2. Identify input parameters and return types
3. Determine test scenarios based on:
   - Input variations
   - Edge cases
   - Error conditions
   - Integration points

#### 7.2 Generate Unit Test Comments

Add inline PR comments for each method requiring tests:

```
**Unit Test Required: `[method_name]`**

Based on implementation notes and method signature, add unit tests covering:

**Test Scenarios:**
1. [Scenario 1] - Happy path with valid inputs
2. [Scenario 2] - Edge case handling
3. [Scenario 3] - Error condition
4. [Scenario 4] - Boundary conditions

**Edge Cases:**
- Empty inputs
- Null values
- Maximum size inputs
- Invalid parameter combinations

**Reference:** Implementation notes section "[section name]"
```

#### 7.3 Aggregation-Specific Test Requirements (for PySpark)

When reviewing PySpark code with aggregation rules:

```
**Aggregation Rule Testing Required**

Test scenarios for aggregation-based autocorrection:
1. Single rule per column with aggregation
2. Multiple rules per column with mixed types
3. Row-level rules only (no aggregation)
4. Aggregation rules with GROUP BY
5. Cascading corrections across columns
6. Empty DataFrame handling
7. Null value propagation
```

### Phase 8: Generate Review Summary

After completing all phases, generate a comprehensive review summary:

```
═══════════════════════════════════════════════════════════════
            COMPREHENSIVE PR REVIEW SUMMARY
═══════════════════════════════════════════════════════════════

PR #[ID]: [Title]
Work Item: #[WI_ID]
Repository: [repo_name]

───────────────────────────────────────────────────────────────
                    REVIEW CHECKLIST
───────────────────────────────────────────────────────────────

**1. Design Document Compliance** [✅/⚠️/❌]
   - Document: [link or "Not Found"]
   - Status: [Compliant/Partially Compliant/Non-Compliant]
   - Issues: [count]

**2. Acceptance Criteria Coverage** [✅/⚠️/❌]
   - Coverage: [X/Y] criteria addressed
   - Gaps: [count]

**3. Implementation Notes Validation** [✅/⚠️/❌]
   - Source: [PBI Description/Custom Field/Not Found]
   - Status: [Validated/Partially Validated/Not Validated]
   - Issues: [count]

**4. Code Review Findings** [✅/⚠️/❌]
   - Guidelines: [Skill/Default]
   - CRITICAL: [count] | HIGH: [count] | MEDIUM: [count] | LOW: [count]
   - Inline comments added: [count] (user selected)

**5. Unit Test Requirements** [✅/⚠️/❌]
   - Methods requiring tests: [count]
   - Test scenarios identified: [count]
   - Inline comments added: [count]

───────────────────────────────────────────────────────────────
                    OVERALL RECOMMENDATION
───────────────────────────────────────────────────────────────

[ ] Approved - All checks passed
[ ] Approved with Suggestions - Minor issues identified
[X] Wait for Author - Required changes identified
[ ] Rejected - Critical issues

**Critical Issues:**
1. [Issue 1]
2. [Issue 2]

**Suggested Improvements:**
1. [Improvement 1]
2. [Improvement 2]

═══════════════════════════════════════════════════════════════
```

---

## .NET Code Review Guidelines

> **📄 Comprehensive Guidelines:** See [dotnet_code_review.md](./dotnet_code_review.md) for complete .NET and SQL review guidelines with 44 C# checks and 19 SQL checks.

### Quick Reference

| Category | Key Checks |
|----------|-----------|
| **Architecture** | SOLID principles, DI, repository/service layers, interfaces |
| **Performance** | Async/await (no .Result/.Wait()), LINQ efficiency, IHttpClientFactory, object pooling |
| **Security** | Input validation, parameterized queries, secrets management, auth checks |
| **Resource Management** | IDisposable/using, stream handling, connection management |
| **Null Handling** | Nullable reference types, null-conditional operators |
| **Entity Framework** | Scoped DbContext, N+1 prevention, AsNoTracking, transactions |
| **SQL Scripts** | OBJECT_ID checks, WHERE clauses, parameterized dynamic SQL |

---

## PySpark Code Review Guidelines

> **Full Guidelines:** See [pyspark_code_review.md](./pyspark_code_review.md) for comprehensive PySpark and Databricks review guidelines.

### Quick Reference - Key Checks

| Check ID | Category | Rule |
|----------|----------|------|
| PS-01 | Performance | No Python UDFs when native functions exist |
| PS-02 | Performance | Broadcast hints for tables < 100MB |
| PS-03 | Performance | No unnecessary `collect()` or `toPandas()` |
| PS-05 | Security | Credentials via `dbutils.secrets.get()` |
| PS-06 | Security | Unity Catalog three-level namespace |
| PS-07 | Compatibility | Check serverless vs classic compute features |

### Critical Checks (Always Verify)

- No hardcoded credentials (use `dbutils.secrets.get()`)
- No Python UDFs when native functions exist
- Broadcast hints for small dimension tables
- Method chaining for transformations
- Unity Catalog three-level namespace (`catalog.schema.table`)

---

## Python Code Review Guidelines

> **Full Guidelines:** See [python_code_review.md](./python_code_review.md) for comprehensive Python clean code review guidelines.

### Quick Reference - Key Checks

| Check ID | Category | Rule |
|----------|----------|------|
| PY-01 | Quality | Type annotations on all public functions |
| PY-02 | Quality | Specific exception handling (no bare except) |
| PY-03 | Quality | DRY - no duplicate code blocks |
| PY-07 | Security | No hardcoded secrets |
| PY-08 | Quality | Single Responsibility Principle |
| PY-09 | Quality | Modern type syntax (Python 3.9+) |

### Critical Checks (Always Verify)

- Type annotations using modern Python 3.9+ syntax (`list[str]` not `List[str]`)
- Specific exception handling (no bare `except:`)
- No hardcoded credentials
- Single Responsibility Principle for functions
- Descriptive naming conventions

---

## Release Pipeline Investigation

> **Full Guidelines:** See [release_investigation.md](./release_investigation.md) for comprehensive pipeline investigation workflow.

### Quick Reference - Investigation Steps

1. **Identify Pipeline**: Use `mcp__azure-devops__build_get_definitions` or CLI
2. **Get Recent Runs**: Use `mcp__azure-devops__build_get_builds` for history
3. **Analyze Run**: Use `mcp__azure-devops__build_get_status` for details
4. **Read Logs**: Use `mcp__azure-devops__build_get_log_by_id` for error details

### Common Failure Patterns

| Pattern | Typical Cause |
|---------|--------------|
| Timeout | Long-running tests, slow dependencies |
| Agent offline | Pool capacity, maintenance |
| Test failure | Code regression, flaky tests |
| Deployment error | Environment config, permissions |

---

## Release Pipeline Naming Conventions

> **Full Guidelines:** See [release_pipeline.md](./release_pipeline.md) for comprehensive pipeline identification guide.

### Quick Reference - Pipeline Patterns

| Prefix | Category |
|--------|----------|
| `Omnia-Data-deploy-helm-` | AKS/Kubernetes deployments |
| `Omnia-Data-deploy-databricks-infra-` | Databricks infrastructure |
| `Omnia-Data-deploy-platform-notebooks-` | Databricks notebooks |
| `Omnia-Data-datamangement-services-` | Data Management Services |

### Version Patterns

| Version | Pattern | Status |
|---------|---------|--------|
| 9.5 | `Release-9.5$` | **Production** |
| 9.5.1 | `Release-9.5.1$` | Production Hotfix |
| 9.6 WIP | `Release.9.6.WIP$` | **Development** |

---

## Code Review Checklist

**Performance:**
- [ ] No Python UDFs when native functions exist
- [ ] Broadcast hints for small dimension tables (< 100MB)
- [ ] No unnecessary `collect()` or `toPandas()`
- [ ] No `SELECT *` in production queries

**Security:**
- [ ] Credentials via `dbutils.secrets.get()`
- [ ] Unity Catalog three-level namespace used
- [ ] No hardcoded secrets or connection strings
- [ ] Parameterized queries (no SQL injection)

**Code Quality:**
- [ ] Method chaining for transformations
- [ ] Descriptive variable names
- [ ] Type annotations on functions
- [ ] Specific exception handling

---

## PR Contribution Report Generation

> **📊 Full Guidelines:** Load [pr_report_generation.md](./pr_report_generation.md) before generating any PR reports.

### Auto-Load Triggers

**ALWAYS load `./pr_report_generation.md` when user mentions:**
- "PR report" / "generate PR report" / "contribution report"
- "team contributions" / "pod contributions" / "developer contributions"
- "html report" / "interactive report" / "web report" (for PRs)
- Iteration/PI-based PR queries ("PI 21", "PI 21.3")
- Pod names with report context ("Data In Use pod report")

### Quick Usage (after loading sub-skill)
- "Generate PR report for all Omnia Data" - All teams, all repos
- "Generate PR report for [Pod] pod" - Pod-specific report
- "Generate PR report for [Team] team" - Team-specific report
- "Generate interactive HTML report for PI21" - HTML format output

---

## Team Info Dynamic Loading

**ALWAYS load `../core/team-info.md` when:**
- User mentions team names: Giga, Kilo, Tera, Peta, Alpha, Beta, Gamma, Skyrockets
- User mentions POD names: "Data In Use", "Data Acquisition", "Data Management", "Omnia JE"
- User asks about service ownership or team mappings
- User needs area path for a service or CloudRoleName
- Creating/updating work items that need team assignment

**Load using Read tool:**
```
Read ../core/team-info.md
```
