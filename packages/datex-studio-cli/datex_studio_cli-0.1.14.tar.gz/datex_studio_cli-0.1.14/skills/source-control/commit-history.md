# Commit History

Viewing commit history with the log command.

## Command

```bash
uv run dxs source log [OPTIONS]
```

## Key Options

| Option | Description |
|--------|-------------|
| `--repo, -r <id>` | Repository ID |
| `--branch, -b <id>` | Branch ID |
| `--branches <ids>` | Comma-separated branch IDs |
| `--all-repos` | Search across all repos |
| `--limit, -n <num>` | Max commits (default: 20) |
| `--from-date <date>` | After this date |
| `--to-date <date>` | Before this date |

## Common Examples

```bash
# Repository commit history
uv run dxs source log --repo 10 --limit 20

# Branch-specific history
uv run dxs source log -b 12345

# Date range
uv run dxs source log --repo 10 --from-date 2026-01-01 --to-date 2026-01-15

# Multiple branches
uv run dxs source log --branches 63332,63299,62932 --limit 10

# All repos
uv run dxs source log --all-repos --from-date 2026-01-13 --limit 50
```

## Example Output

```yaml
commits:
- applicationId: 65320
  commitTitle: Add owner lookup to inbound and outbound grids
  commitMessage: Add owner lookup to inbound and outbound grids
  commitDate: '2026-01-13T23:59:04.8415656+00:00'
  author:
    displayName: Derek Armanious
    userPrincipalName: derek@datexcorp.com
  work_item_ids: []
- applicationId: 65291
  commitTitle: '[Bug] - Tasks'
  commitMessage: 'Dims on tasks [227421]'
  commitDate: '2026-01-13T20:53:25.088846+00:00'
  author:
    displayName: Oscar Arias
  work_item_ids:
  - 227421
metadata:
  success: true
  count: 2
  branch_id: 65327
```

## Finding Commits for Code Review

The most effective way to find recent commits:

```bash
# Method 1: List history branches (recommended)
uv run dxs source branch list --repo-name "MyRepo" --status history --sort commit-date --desc --limit 5

# Method 2: Use log command
uv run dxs source log --repo 10 --from-date 2026-01-13
```

Method 1 is often better because it gives you the branch IDs needed for `changes --with-diffs`.

## See Also

- [Viewing Changes](./viewing-changes.md) - Review commit content
- [Listing Branches](../branches/listing-branches.md) - Alternative way to find commits
