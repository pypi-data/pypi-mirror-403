# Branch Statuses

Reference for all branch status types.

## Status Types

| Status | ID | CLI Filter | Description |
|--------|-----|------------|-------------|
| Draft | 1 | `--status draft` | Main development branch |
| Inactive | 2 | `--status inactive` | Previous published releases |
| Active | 3 | `--status active` | Current published release |
| WorkspaceHistory | 4 | `--status history` | Commit snapshots (frozen) |
| WorkspaceActive | 5 | `--status feature` | Feature branches (WIP) |

## When to Use Each

| Goal | Status Filter |
|------|---------------|
| Review recent commits | `--status history` |
| Find in-progress work | `--status feature` |
| Find current release | `--status active` |
| Find baseline for release notes | `--status inactive` |
| Find main branch | `--status draft` |

## Semantic Fields in Output

Each branch includes helpful boolean flags:

```yaml
statusName: WorkspaceHistory
statusContext: Commit snapshot - represents a single commit to the main branch
isCommit: true
isRelease: false
isCurrentRelease: false
isFeatureBranch: false
isMainBranch: false
```

## Examples

```bash
# Recent commits
uv run dxs source branch list --repo-name "MyRepo" --status history --sort commit-date --desc --limit 5

# Active feature branches
uv run dxs source branch list --repo-name "MyRepo" --status feature

# Current release
uv run dxs source branch list --repo-name "MyRepo" --status active
```

## See Also

- [Listing Branches](./listing-branches.md)
- [Reference: Branch Statuses](../reference/branch-statuses.md) - Full details
