# Branch Statuses Reference

Complete reference for branch status types in Datex Studio.

## Status Types

| Status | ID | CLI Filter | Description |
|--------|-----|------------|-------------|
| Draft | 1 | `--status draft` | Main development branch - receives commits from feature branches |
| Inactive | 2 | `--status inactive` | Previous published releases - superseded by newer Active version |
| Active | 3 | `--status active` | Current published release - latest version available to users |
| WorkspaceHistory | 4 | `--status history` | Commit snapshots - frozen after commit, represents single commits |
| WorkspaceActive | 5 | `--status feature` | Feature branches - active development work in progress |

## Semantic Fields

Each branch includes semantic fields for easier interpretation:

| Field | Type | Description |
|-------|------|-------------|
| `statusName` | string | Human-readable status name |
| `statusContext` | string | Explanation of what this status means |
| `isCommit` | boolean | True for WorkspaceHistory branches |
| `isRelease` | boolean | True for Active/Inactive branches |
| `isCurrentRelease` | boolean | True only for Active branch |
| `isFeatureBranch` | boolean | True for WorkspaceActive branches |
| `isMainBranch` | boolean | True for Draft branch |

## Status Lifecycle

```
Feature Branch (WorkspaceActive)
        │
        ▼ [commit]
Commit Snapshot (WorkspaceHistory)
        │
        ▼ [integrated into]
Main Branch (Draft)
        │
        ▼ [publish]
Current Release (Active)
        │
        ▼ [new release published]
Previous Release (Inactive)
```

## Common Queries

### Find Recent Commits
```bash
uv run dxs source branch list --repo-name "MyRepo" --status history --sort commit-date --desc --limit 10
```

### Find Active Feature Branches
```bash
uv run dxs source branch list --repo-name "MyRepo" --status feature
```

### Find Current Release
```bash
uv run dxs source branch list --repo-name "MyRepo" --status active
```

### Find Previous Releases
```bash
uv run dxs source branch list --repo-name "MyRepo" --status inactive --sort commit-date --desc
```

### Find Main/Draft Branch
```bash
uv run dxs source branch list --repo-name "MyRepo" --status draft
```

## Example Output

```yaml
branches:
- id: 65327
  applicationStatusId: 4
  commitTitle: '[Bugfix] Auto email attachments'
  statusName: WorkspaceHistory
  statusContext: Commit snapshot - represents a single commit to the main branch
  isCommit: true
  isRelease: false
  isCurrentRelease: false
  isFeatureBranch: false
  isMainBranch: false
```

## Tips

1. **For code review**: Use `--status history` to find committed changes
2. **For WIP review**: Use `--status feature` to find in-progress work
3. **For release notes**: Use `--status inactive` to find the baseline version
4. **For current state**: Use `--status active` or `--status draft`

## See Also

- [Listing Branches](../branches/listing-branches.md)
- [Listing Branches Guide](../branches/listing-branches-guide.md)
- [Command Cheatsheet](./command-cheatsheet.md)
