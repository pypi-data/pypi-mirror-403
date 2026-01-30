---
name: org_structure_generation
display_name: "Organization Structure Generation"
description: "Generate comprehensive organization structure reports showing team hierarchy, FTE/Contractor breakdown, vendor distribution, and geographic details. Supports HTML output with Omnia Design System styling."
version: "1.0.0"
tags: [org-chart, team-structure, fte, contractors, vendors, html-reports]
requires: []
subagents: []
tools: []
triggers:
  - "org chart"
  - "org structure"
  - "organization structure"
  - "team structure"
  - "show me the teams"
  - "team hierarchy"
  - "FTE.*vendor"
  - "contractor.*breakdown"
---

# Organization Structure Report Generation

## Overview

Generate comprehensive organization structure reports for Omnia Data showing:
- Complete team hierarchy (PODs and Teams)
- Cross-POD/Organization-wide roles at the top
- FTE vs Contractor breakdown with percentages
- Vendor distribution and counts
- Geographic distribution by region
- Team leads, architects, BSAs for each team
- Interactive filters (type, region, vendor, search)

---

## Trigger Keywords

**ALWAYS generate org structure report when user mentions:**
- "org chart" / "org structure" / "organization structure"
- "team structure" / "team hierarchy" / "show me the teams"
- "FTE and vendor details" / "contractor breakdown"
- "who is on [team name]" / "team members"

---

## Data Sources

### Primary Data Files

| File | Purpose | Path |
|------|---------|------|
| Team Config | POD/Team hierarchy, area paths, leads | `../data/team-config.json` |
| User Mappings | Member details (email, team, type, vendor, region) | `../data/user-mappings.tsv` |

### Team Config Structure

```json
{
  "pods": {
    "Data In Use": {
      "parent": "Omnia Data Automation",
      "teams": {
        "Giga": {
          "areaPath": "Audit Cortex 2\\Omnia Data\\...",
          "techLead": "Name",
          "bsa": "Name",
          "architect": "Name",
          "memberCount": 18
        }
      }
    }
  }
}
```

### User Mappings TSV Columns

| Column | Description |
|--------|-------------|
| email | User email address |
| displayName | Full name |
| team | Team name (Giga, Delta, etc.) |
| pod | POD name (Data In Use, etc.) |
| role | Job role (Developer, QA, BSA, etc.) |
| region | Geographic region (US, USI, UK, Romania, etc.) |
| type | Employment type (FTE or Contractor) |
| vendor | Vendor name for contractors (Globant, New Vision, etc.) |

---

## Output Format

### Default: HTML Report

**Always generate HTML report** when org structure is requested.

**Template:** `./templates/org-structure-template.html`

**Output location:** `~/.triagent/reports/omnia-data-org-structure.html`

### HTML Report Features

1. **Summary Cards**
   - Total Members
   - FTEs (count and percentage)
   - Contractors (count and percentage)
   - PODs count
   - Teams count
   - Vendors count

2. **Filter Section**
   - Filter by Type (FTE/Contractor)
   - Filter by Region (US, USI, UK, Romania, etc.)
   - Filter by Vendor (Globant, New Vision, Cognizant, etc.)
   - Search by name

3. **Vendor Summary Section**
   - Top vendors with contractor counts
   - Visual cards for each major vendor

4. **Geographic Distribution Section**
   - Region cards with member counts
   - Sorted by count descending

5. **Cross-POD Section (TOP)**
   - Program Management
   - Enterprise Architecture
   - Service & Portfolio Management
   - Release Management
   - UX Design
   - QA Systems (Cross-Team)
   - Cyber / Security
   - Operate / Support

6. **POD Sections (Collapsible)**
   - Data In Use (Giga, Kilo, Peta, Tera)
   - Omnia JE (Utopia, Justice League, Jupiter, Neptune, Saturn, Exa)
   - DevOps (Slayers, Spacebots)
   - Data Management & Activation (Delta, Gamma, SkyRockets)
   - Data Acquisition & Preparation (Alpha, Beta, Megatron)
   - Performance Engineering (Eagles)

7. **Team Cards**
   - Team leads (Tech Lead, BSA, Architect, QA Lead)
   - Member chips grouped by role (Developers, QA, Data Engineers)
   - FTE/Contractor badges with vendor labels

---

## Styling Requirements

### MUST Use Omnia Design System

**Reference CSS:** `./templates/deloitte-omnia.css`

**Critical Style Variables:**
```css
:root {
    --primary: #007CB0;           /* Deloitte Teal */
    --primary-dark: #005A87;      /* Dark Teal */
    --accent: #86BC25;            /* Deloitte Green */
    --bg-light: #F8F8F8;          /* Very light gray */
    --border: #E0E0E0;            /* Light border */
    --border-dark: #D0D0CE;       /* Darker border */
    --text: #000000;              /* Primary Text */
    --text-light: #53565A;        /* Secondary Text */
    --error: #DA291C;             /* Error Red */
    --white: #ffffff;
}
```

**Key Design Principles:**
- WHITE backgrounds (not dark/colored headers)
- Minimal borders (1px solid #E0E0E0)
- Flat design (2px border-radius, no shadows unless subtle)
- Roboto font family
- Primary color for accents and interactive elements

### Header Format

```html
<div class="header">
    <h1><span class="brand">Deloitte.</span> <span class="brand-accent">Omnia Data</span> Organization Structure</h1>
    <p>Comprehensive team hierarchy with FTE and Vendor details</p>
</div>
```

---

## Report Generation Workflow

### Step 1: Read Data Files

```bash
# Read team configuration
Read ../data/team-config.json

# Read user mappings
Read ../data/user-mappings.tsv
```

### Step 2: Parse and Aggregate Data

1. **Count totals:**
   - Total members
   - FTEs vs Contractors
   - PODs and Teams
   - Unique vendors

2. **Group by category:**
   - Cross-POD roles (no team assignment or cross-functional)
   - By POD > Team > Role

3. **Calculate distributions:**
   - Vendor counts
   - Region counts

### Step 3: Identify Cross-POD Members

Cross-POD members are identified by:
- Role contains: "Architect", "Manager", "Lead", "UX", "Cyber", "Operate"
- Team is empty or "Cross-POD"
- Area path doesn't include specific team

**Cross-POD Categories:**
| Category | Role Patterns |
|----------|--------------|
| Program Management | Program Manager, Project Manager, Delivery Lead, Chief Delivery |
| Enterprise Architecture | Enterprise Architect, Cloud Architect |
| Service & Portfolio Management | Portfolio Lead, Service Management |
| Release Management | Release Manager |
| UX Design | UX Designer, UI Designer |
| QA Systems | QA Lead (cross-team) |
| Cyber / Security | Cyber, Security |
| Operate / Support | Operate, Support |

### Step 4: Generate HTML

Use the template with placeholders:

| Placeholder | Description |
|-------------|-------------|
| `{total_members}` | Total member count |
| `{fte_count}` | FTE count |
| `{fte_percentage}` | FTE percentage |
| `{contractor_count}` | Contractor count |
| `{contractor_percentage}` | Contractor percentage |
| `{pod_count}` | Number of PODs |
| `{team_count}` | Number of teams |
| `{vendor_count}` | Number of unique vendors |
| `{vendor_cards}` | Generated vendor summary HTML |
| `{region_cards}` | Generated region summary HTML |
| `{cross_pod_section}` | Generated cross-POD HTML |
| `{pod_sections}` | Generated POD sections HTML |
| `{generation_date}` | Report generation timestamp |

### Step 5: Write and Open Report

```bash
# Write HTML file
Write ~/.triagent/reports/omnia-data-org-structure.html

# Open in browser
open ~/.triagent/reports/omnia-data-org-structure.html
```

---

## HTML Component Templates

### Summary Card

```html
<div class="summary-card">
    <div class="value">{value}</div>
    <div class="label">{label}</div>
</div>
```

### Summary Card with Color Variant

```html
<div class="summary-card fte">
    <div class="value">{fte_count}</div>
    <div class="label">FTEs ({fte_percentage}%)</div>
</div>
```

### Vendor Card

```html
<div class="vendor-card">
    <div class="vendor-name">{vendor_name}</div>
    <div class="vendor-count">{count}</div>
</div>
```

### Cross-POD Card

```html
<div class="cross-pod-card">
    <h3>{category_name}</h3>
    <div class="member">
        <div>
            <span class="member-name">{name}</span><br>
            <span class="member-role">{role}</span>
        </div>
        <span class="member-type fte">{region} FTE</span>
    </div>
</div>
```

### POD Section

```html
<div class="pod-section" data-pod="{pod_id}">
    <div class="pod-header" onclick="togglePod(this)">
        <h2>{pod_name} POD</h2>
        <div class="pod-stats">
            <span class="pod-stat">{member_count} Members</span>
            <span class="pod-stat">{team_count} Teams</span>
            <span class="pod-stat">~{fte_count} FTE / ~{contractor_count} Contractors</span>
        </div>
        <span class="chevron">&#9660;</span>
    </div>
    <div class="pod-content">
        <div class="pod-meta">
            <span><strong>Parent:</strong> {parent}</span>
            <span><strong>Delivery Lead:</strong> {delivery_lead}</span>
        </div>
        <div class="teams-grid">
            {team_cards}
        </div>
    </div>
</div>
```

### Team Card

```html
<div class="team-card" data-team="{team_id}">
    <div class="team-header">
        <h3>{team_name}</h3>
        <span class="team-count">{member_count} members</span>
    </div>
    <div class="team-leads">
        <div class="team-lead">
            <span class="role">Tech Lead</span>
            <span class="name">{tech_lead_name}</span>
            <span class="type-badge {type}">{type_label}</span>
        </div>
    </div>
    <div class="team-members">
        <div class="member-group">
            <div class="member-group-title">Developers</div>
            <div class="member-list">
                {member_chips}
            </div>
        </div>
    </div>
</div>
```

### Member Chip

```html
<!-- FTE -->
<span class="member-chip fte" data-type="fte" data-region="{region}">{name}</span>

<!-- Contractor -->
<span class="member-chip contractor" data-type="contractor" data-vendor="{vendor}" data-region="{region}">
    {name} <span class="vendor">{vendor}</span>
</span>
```

---

## Filter JavaScript

```javascript
function togglePod(header) {
    header.classList.toggle('collapsed');
    header.nextElementSibling.classList.toggle('collapsed');
}

function filterContent() {
    const typeFilter = document.getElementById('typeFilter').value.toLowerCase();
    const regionFilter = document.getElementById('regionFilter').value.toLowerCase();
    const vendorFilter = document.getElementById('vendorFilter').value.toLowerCase();
    const searchFilter = document.getElementById('searchFilter').value.toLowerCase();

    document.querySelectorAll('.member-chip').forEach(chip => {
        const type = chip.getAttribute('data-type') || '';
        const region = chip.getAttribute('data-region') || '';
        const vendor = chip.getAttribute('data-vendor') || '';
        const text = chip.textContent.toLowerCase();

        const typeMatch = !typeFilter || type === typeFilter;
        const regionMatch = !regionFilter || region.includes(regionFilter);
        const vendorMatch = !vendorFilter || vendor.includes(vendorFilter);
        const searchMatch = !searchFilter || text.includes(searchFilter);

        chip.style.display = (typeMatch && regionMatch && vendorMatch && searchMatch) ? '' : 'none';
    });
}
```

---

## Additional CSS for Org Structure

Add these styles to the base Omnia CSS:

```css
/* FTE/Contractor color variants */
.summary-card.fte .value { color: var(--primary); }
.summary-card.contractor .value { color: var(--accent); }
.summary-card.vendor .value { color: #FF9800; }

/* Cross-POD Section */
.cross-pod-section {
    background: var(--bg-light);
    border: 1px solid var(--border-dark);
    border-radius: 2px;
    padding: 20px;
    margin-bottom: 20px;
}
.cross-pod-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 15px;
}
.cross-pod-card {
    background: var(--white);
    border-radius: 2px;
    padding: 15px;
    border-left: 3px solid var(--primary);
}

/* POD Sections */
.pod-section {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 2px;
    margin-bottom: 20px;
}
.pod-header {
    background: var(--white);
    color: var(--primary);
    padding: 15px 20px;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 2px solid var(--primary);
}
.pod-header:hover { background: var(--bg-light); }
.pod-content { padding: 20px; }
.pod-content.collapsed { display: none; }

/* Team Cards */
.teams-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 20px;
}
.team-card {
    border: 1px solid var(--border);
    border-radius: 2px;
}
.team-header {
    background: var(--bg-light);
    padding: 12px 15px;
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
}

/* Member Chips */
.member-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 15px;
    font-size: 11px;
    background: var(--bg-light);
    border: 1px solid var(--border);
}
.member-chip.fte {
    background: #E5F4FB;
    border-color: #B3DCF0;
}
.member-chip.contractor {
    background: #EDF6E4;
    border-color: #C5E1A5;
}
.member-chip .vendor {
    font-size: 9px;
    color: var(--text-light);
}

/* Type Badges */
.type-badge {
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 10px;
    font-weight: 500;
}
.type-badge.fte {
    background: #E5F4FB;
    color: var(--primary);
}
.type-badge.contractor {
    background: #EDF6E4;
    color: var(--accent);
}
```

---

## Example Output Response

After generating the report, respond with:

```
The organization structure HTML report has been generated.

**File:** `~/.triagent/reports/omnia-data-org-structure.html`

**To open:** `open ~/.triagent/reports/omnia-data-org-structure.html`

### Summary
| Metric | Value |
|--------|-------|
| **Total Members** | 394 |
| **FTEs** | 95 (24%) |
| **Contractors** | 299 (76%) |
| **PODs** | 6 |
| **Teams** | 18 |
| **Vendors** | 15+ |

### Report Features
- Cross-POD section at the top (Program Management, Enterprise Architecture, etc.)
- Filterable by employment type, region, vendor, and search
- Collapsible POD sections with team cards
- Member chips with FTE/Contractor badges and vendor labels
- Vendor and geographic distribution summaries
```

---

## Best Practices

1. **Always use Omnia Design System** - Reference `deloitte-omnia.css` for consistent styling
2. **Cross-POD at top** - Organization-wide roles should appear before team-specific sections
3. **Include all filters** - Type, Region, Vendor, and Search filters improve usability
4. **Show vendor labels** - For contractors, always display the vendor name
5. **Collapsible sections** - POD sections should be collapsible to manage large org charts
6. **Print-friendly** - Include print CSS that expands all sections

---

## Error Handling

| Issue | Resolution |
|-------|------------|
| Missing team-config.json | Report error, ask user to provide team data |
| Missing user-mappings.tsv | Report error, fall back to team-config memberCount |
| Empty team | Show team card with "No members assigned" |
| Unknown vendor | Display as-is without vendor card color coding |
