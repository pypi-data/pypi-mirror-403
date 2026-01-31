# Code Review

Workflows for reviewing code changes in Datex Studio.

## In This Section

| Document | Description |
|----------|-------------|
| [Reviewing Commits Guide](./reviewing-commits-guide.md) | Step-by-step for history branches |
| [Reviewing Feature Branches](./reviewing-feature-branches.md) | Review in-progress work |
| [Multi-Repository Review](./multi-repo-review-guide.md) | Org-wide code audits |
| [Review Report Template](./review-report-template.md) | Markdown format for reports |

## Overview

Code review in Datex Studio involves:
1. Finding the branches to review
2. Fetching changes with diffs
3. Analyzing configuration modifications
4. Documenting findings in a structured report

## Quick Start

```bash
# 1. Find recent commits
uv run dxs source branch list --repo-name "MyRepo" --status history --sort commit-date --desc --limit 5

# 2. Review each commit's changes
uv run dxs source changes -b <commit_id> --with-diffs

# 3. Get related work item details
uv run dxs devops workitem <id> --org myorg
```

## Review Scenarios

### Single Repository Reviews

#### Reviewing Commits (History Branches)
Already committed code - use `--status history` to find commits.
See [Reviewing Commits Guide](./reviewing-commits-guide.md).

#### Reviewing Feature Branches (In Progress)
Work in progress - use `--status feature` to find active branches.
See [Reviewing Feature Branches](./reviewing-feature-branches.md).

### Organization-Wide Reviews

For periodic audits across all repositories in an organization:
- Batch repos into groups for efficient processing
- Use parallel subagents for large orgs (100+ repos)
- Generate consolidated report with executive summary
See [Multi-Repository Review Guide](./multi-repo-review-guide.md).

## Key Concepts

### Sync Commits vs Real Changes

| Indicator | Meaning |
|-----------|---------|
| `total_config_changes: 0` | No app code changed |
| `has_references: true` only | Library version update |
| `total_config_changes > 0` | Real code changes |

### What to Look For

- **Bugs**: Logic errors, missing null checks
- **Incomplete work**: Missing features mentioned in title
- **Code quality**: Duplication, inconsistent patterns
- **Risk**: Impact scope, complexity

## See Also

- [Branch Statuses](../branches/branch-statuses.md) - Understanding branch types
- [Viewing Changes](../source-control/viewing-changes.md) - Getting diffs
