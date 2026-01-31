# Listing Branches

Quick reference for the branch list command.

## Command

```bash
uv run dxs source branch list [OPTIONS]
```

## Key Options

| Option | Description |
|--------|-------------|
| `--repo, -r <id>` | Repository ID |
| `--repo-name <name>` | Repository name (resolved to ID) |
| `--org <name>` | Organization (to scope repo search) |
| `--status <type>` | Filter by status (see below) |
| `--limit, -n <num>` | Max results (default: 10, 0=unlimited) |
| `--sort <field>` | Sort by field (see below) |
| `--asc / --desc` | Sort direction (default: desc) |
| `--author <email>` | Filter by author email |
| `--with-changes` | Include change counts |

## Status Filters

| Filter | Description |
|--------|-------------|
| `--status draft` | Main branch |
| `--status active` | Current release |
| `--status inactive` | Previous releases |
| `--status history` | Commit snapshots |
| `--status feature` | Feature branches |
| `--status all` | All branches |

## Sort Fields

| Field | Description |
|-------|-------------|
| `name` | Branch name |
| `created` | Creation date (default) |
| `modified` | Modification date |
| `commit-date` | Last commit date |
| `status` | Status type |
| `changes` | Change count (requires `--with-changes`) |

## Common Examples

```bash
# List feature branches
uv run dxs source branch list --repo-name "MyRepo" --status feature

# Recent commits (for code review)
uv run dxs source branch list --repo-name "MyRepo" --status history --sort commit-date --desc --limit 5

# Branches by author
uv run dxs source branch list --repo 10 --status feature --author "user@example.com"

# All branches with change counts
uv run dxs source branch list --repo 10 --with-changes --sort changes --desc
```

## See Also

- [Listing Branches Guide](./listing-branches-guide.md) - Deep dive with output examples
- [Branch Statuses](./branch-statuses.md) - Status reference
