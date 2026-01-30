---
name: root_cause_analysis
display_name: "Root Cause Analysis"
description: |
  Framework for conducting Root Cause Analysis (RCA) for production incidents.
  Includes 5 Whys methodology, RCA template, and documentation guidelines.
triggers:
  - "RCA"
  - "root cause"
  - "incident.*analysis"
  - "post.*mortem"
version: 1.0.0
---

# Root Cause Analysis Process

## RCA Framework

Follow the 5 Whys methodology to find the true root cause:

1. **What happened?** - Describe the incident impact
2. **Why did it happen?** - Technical cause
3. **Why wasn't it caught?** - Detection gap
4. **Why wasn't it prevented?** - Prevention gap
5. **What will prevent recurrence?** - Action items

## RCA Document Template

```markdown
## Incident Summary
[Brief description of what happened]

## Timeline
| Time | Event |
|------|-------|
| HH:MM | First symptom |
| HH:MM | Detection |
| HH:MM | Resolution |

## Impact
- Services: [list]
- Users affected: [count]
- Duration: [time]

## Root Cause
[Technical explanation]

## Contributing Factors
- [Factor 1]
- [Factor 2]
- [Factor 3]

## Action Items
| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| [Action] | [Name] | [Date] | [Status] |

## Lessons Learned
- [Lesson 1]
- [Lesson 2]
```

## Severity Classification

| Severity | Criteria | Response Time |
|----------|----------|---------------|
| 1 - Critical | Complete service outage, data loss | 15 min |
| 2 - High | Major feature broken, significant impact | 1 hour |
| 3 - Medium | Minor feature broken, workaround exists | 4 hours |
| 4 - Low | Cosmetic issue, no user impact | Next sprint |

## RCA Meeting Guidelines

1. **Pre-meeting**
   - Gather timeline from logs
   - Identify all contributing factors
   - Document impact metrics

2. **During meeting**
   - Focus on process, not blame
   - Use facts from logs/metrics
   - Capture all action items

3. **Post-meeting**
   - Create ADO work items for actions
   - Share RCA document with stakeholders
   - Schedule follow-up if needed

## Integration with ADO

Link RCA to related work items:
- Parent LSI (Live Site Incident)
- Related defects
- Action item tasks

```bash
# Create RCA-related task
az boards work-item create \
  --title "[RCA] Action: Implement circuit breaker" \
  --type "Task" \
  --project "Audit Cortex 2" \
  --area "Audit Cortex 2\\Omnia Data" \
  --output tsv
```
