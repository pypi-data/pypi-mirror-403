# Release Branch Strategy

**Last Updated:** 2026-01-21

Branch and release patterns for investigation and development.

## Current Releases

| Release | Status | Branch | Environments |
|---------|--------|--------|--------------|
| 9.5.x | **Production** | `RELEASE_9.5` | PROD, BCP, CNT1 |
| 9.6.x | Development | `develop` | DEV, QAS, STG2 |

---

## Investigation by Environment

| Environment | Release | Branch to Checkout |
|-------------|---------|-------------------|
| PROD, BCP, CNT1 | 9.5.x | `RELEASE_9.5` |
| STG | 9.5.x | `RELEASE_9.5` |
| DEV, DEV1, DEV2 | 9.6.x | `develop` |
| QAS, QAS1, QAS2 | 9.6.x | `develop` |

---

## Release Pipeline Naming Conventions

| Prefix | Category | Example |
|--------|----------|---------|
| `Omnia-Data-deploy-helm-` | AKS/Kubernetes deployments | `Omnia-Data-deploy-helm-9.5` |
| `Omnia-Data-deploy-databricks-infra-` | Databricks infrastructure | `Omnia-Data-deploy-databricks-infra-Release-9.5` |
| `Omnia-Data-deploy-platform-notebooks-` | Databricks notebooks | `Omnia-Data-deploy-platform-notebooks-Release-9.5` |
| `Omnia-Data-datamangement-services-` | Data Management Services | `Omnia-Data-datamangement-services-Release-9.5` |

---

## Version Patterns

| Version | Pattern | Status |
|---------|---------|--------|
| 9.5 | `Release-9.5$` | **Production** |
| 9.5.1 | `Release-9.5.1$` | Production Hotfix |
| 9.6 WIP | `Release.9.6.WIP$` | **Development** |

---

## Branch Workflow

```
master (protected)
    │
    ├── RELEASE_9.5 (production)
    │   └── hotfix branches → merge to RELEASE_9.5
    │
    └── develop (development)
        └── feature branches → merge to develop
```

---

## Common Pipeline Issues by Category

| Category | Common Issues |
|----------|---------------|
| helm | AKS node issues, helm chart errors, image pull failures |
| databricks-infra | Workspace provisioning, cluster issues, permissions |
| platform-notebooks | Notebook deployment, library installation |
| datamangement-services | App Service deployment, configuration errors |

---

## Useful Commands

### Checkout Production Branch
```bash
git fetch origin
git checkout RELEASE_9.5
```

### Checkout Development Branch
```bash
git fetch origin
git checkout develop
```

### Find Commits Between Releases
```bash
git log RELEASE_9.5..develop --oneline
```

### Compare Branches
```bash
git diff RELEASE_9.5..develop --stat
```
