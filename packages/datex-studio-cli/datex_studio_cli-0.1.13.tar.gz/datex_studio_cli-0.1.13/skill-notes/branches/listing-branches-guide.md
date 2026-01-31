# Listing Branches (Guide)

Deep dive into listing and filtering branches with real output examples.

## Overview

The `dxs source branch list` command is the primary way to find branches in a repository. It supports filtering by status, date, author, and various sort options. This guide shows real-world usage patterns.

## Prerequisites

- Authenticated with `dxs auth login`
- Know the repository name or ID

## Finding Recent Commits (for Code Review)

To review recent commits, list history branches sorted by commit date:

```bash
uv run dxs source branch list --repo-name "FootprintManager" --status history --sort commit-date --desc --limit 5
```

### Example Output

```yaml
branches:
- id: 65327
  applicationStatusId: 4
  createdDate: '2026-01-14T10:16:35.3221248+00:00'
  commitTitle: '[Bugfix] Auto email attachments overwritten on save'
  commitDescription: '[Bugfix] Auto email attachments overwritten on save'
  commitDate: '2026-01-14T10:22:02.4132249+00:00'
  authorDisplayName: Evelin Velikov
  authorExternalId: ba0d1eb4-7628-4b62-a3f0-2a724db9f0e2
  buildStatus: none
  statusName: WorkspaceHistory
  statusContext: Commit snapshot - represents a single commit to the main branch
  isCommit: true
  isRelease: false
  isCurrentRelease: false
  isFeatureBranch: false
  isMainBranch: false
- id: 65320
  applicationStatusId: 4
  createdDate: '2026-01-13T23:40:38.7958249+00:00'
  commitTitle: Add owner lookup to inbound and outbound grids
  commitDate: '2026-01-13T23:59:04.8415656+00:00'
  authorDisplayName: Derek Armanious
  statusName: WorkspaceHistory
  isCommit: true
metadata:
  timestamp: '2026-01-14T19:21:32.362734Z'
  cli_version: 0.1.0
  success: true
  count: 5
  total_count: 1310
  filtered_count: 1310
  repository_id: 87
  sort_field: commit-date
  sort_direction: desc
```

## Finding Active Feature Branches

To see work in progress:

```bash
uv run dxs source branch list --repo-name "FootprintManager" --status feature --limit 10
```

### Example Output

```yaml
branches:
- id: 64925
  applicationStatusId: 5
  createdDate: '2025-12-26T22:24:35.7152848+00:00'
  commitTitle: '[Feature] rebill order button on the order hub'
  commitDescription: Rebill
  authorDisplayName: Evelin Velikov
  statusName: WorkspaceActive
  statusContext: Feature branch - active development work in progress
  isCommit: false
  isFeatureBranch: true
- id: 65357
  applicationStatusId: 5
  createdDate: '2026-01-14T15:58:14.5221248+00:00'
  commitTitle: '[Feature] recurring appointments'
  authorDisplayName: Remon Shokry
  statusName: WorkspaceActive
  isFeatureBranch: true
metadata:
  count: 10
  total_count: 41
  filtered_count: 41
```

## Filtering by Author

Find branches created by a specific person:

```bash
uv run dxs source branch list --repo 87 --status feature --author "evelin@datexcorp.com"
```

## Filtering by Date

Find branches created after a specific date:

```bash
uv run dxs source branch list --repo 87 --status feature --created-after 2026-01-01
```

Find branches modified in a date range:

```bash
uv run dxs source branch list --repo 87 --modified-after 2026-01-10 --modified-before 2026-01-15
```

### Date Filter Behavior

**Important:** The `--created-after` filter uses the branch's `createdDate` field:
- For **history branches** (commits): This is when the commit snapshot was created, effectively "when the commit was made"
- For **feature branches**: This is when the feature branch was created

To find "commits in the last 3 days":
```bash
uv run dxs source branch list --repo-name "MyRepo" --status history --created-after 2026-01-11
```

This returns history branches where `createdDate >= 2026-01-11`.

## Including Change Counts

To see how many changes each branch has:

```bash
uv run dxs source branch list --repo 87 --status feature --with-changes --sort changes --desc --limit 5
```

This adds change count fields but is slower (requires additional API calls).

## Common Patterns

### Code Review Workflow
```bash
# Step 1: Find recent commits
uv run dxs source branch list --repo-name "MyRepo" --status history --sort commit-date --desc --limit 5

# Step 2: Review changes in each commit
uv run dxs source changes -b <commit_id> --with-diffs
```

### Find Baseline for Release Notes
```bash
# Find the most recent previous release
uv run dxs source branch list --repo 87 --status inactive --sort commit-date --desc --limit 1

# Or use the baseline command
uv run dxs source branch baseline <current_branch_id>
```

### Find All Branches Across Repos
```bash
uv run dxs source branch list --all-repos --status feature --modified-after 2026-01-01
```

## Understanding the Output

### Key Fields

| Field | Description |
|-------|-------------|
| `id` | Branch ID (use with other commands) |
| `applicationStatusId` | Numeric status (1-5) |
| `statusName` | Human-readable status |
| `commitTitle` | Branch/commit title |
| `commitDate` | When committed (history only) |
| `authorDisplayName` | Who created it |
| `isCommit` | True for history branches |
| `isFeatureBranch` | True for feature branches |

### Metadata

| Field | Description |
|-------|-------------|
| `count` | Number of results returned |
| `total_count` | Total branches in repo |
| `filtered_count` | Branches matching filter |
| `sort_field` | How results are sorted |

## Troubleshooting

### No Results Returned
- Check the status filter is correct
- Try `--status all` to see if branches exist
- Verify repo name/ID is correct

### Slow Response
- Avoid `--with-changes` unless needed
- Use `--limit` to reduce results
- Filter by status to narrow scope

### Best Practice: Always Use --limit

When iterating through multiple repos or reviewing commits, always use `--limit` to avoid huge responses:

```bash
# Good - bounded response
uv run dxs source branch list --repo-name "MyRepo" --status history --limit 20

# Risky - could return thousands
uv run dxs source branch list --repo-name "MyRepo" --status history
```

Repos with long histories may have 1000+ history branches. The `metadata.total_count` shows how many exist.

## See Also

- [Branch Statuses](./branch-statuses.md) - Status reference
- [Viewing Changes](../source-control/viewing-changes.md) - Next step after finding branches
- [Code Review Workflow](../code-review/) - Complete review process
