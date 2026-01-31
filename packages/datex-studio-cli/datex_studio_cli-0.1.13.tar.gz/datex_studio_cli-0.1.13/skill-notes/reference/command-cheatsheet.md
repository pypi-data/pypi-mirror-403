# Command Cheatsheet

All `dxs` commands at a glance. Run with `uv run dxs`.

## Authentication

| Command | Description |
|---------|-------------|
| `dxs auth login` | Authenticate with Azure Entra |
| `dxs auth logout` | Clear stored credentials |
| `dxs auth status` | Show current auth status |

## Repositories

| Command | Description |
|---------|-------------|
| `dxs source repo list` | List all repositories |
| `dxs source repo list --org-name "Org"` | List repos for organization |
| `dxs source repo show <id>` | Show repo details |
| `dxs source repo search "query"` | Search repos by name |

## Branches

| Command | Description |
|---------|-------------|
| `dxs source branch list --repo <id>` | List branches in repo |
| `dxs source branch list --repo-name "Name"` | List by repo name |
| `dxs source branch list --status feature` | Filter by status |
| `dxs source branch list --status history --sort commit-date` | Recent commits |
| `dxs source branch show <id>` | Show branch details |
| `dxs source branch validate <id>` | Validate branch config |
| `dxs source branch baseline <id>` | Find previous release |

### Branch Status Filters

| Filter | Description |
|--------|-------------|
| `--status draft` | Main development branch |
| `--status active` | Current published release |
| `--status inactive` | Previous releases |
| `--status history` | Commit snapshots |
| `--status feature` | Feature branches |
| `--status all` | All branches |

## Source Control

| Command | Description |
|---------|-------------|
| `dxs source status -b <id>` | Branch status and locks |
| `dxs source changes -b <id>` | Pending changes |
| `dxs source changes -b <id> --with-diffs` | Changes with diffs |
| `dxs source diff -b <id>` | Upstream changes |
| `dxs source log --repo <id>` | Commit history |
| `dxs source log -b <id>` | Branch commit history |
| `dxs source history <config> -b <id>` | Config version history |
| `dxs source locks --repo <id>` | Show locked configs |
| `dxs source deps -b <id>` | List dependencies |
| `dxs source deps -b <id> --tree` | Dependency tree |
| `dxs source deps-diff --from <id> --to <id>` | Compare dependencies |
| `dxs source graph -b <id>` | Dependency graph |
| `dxs source workitems -b <id>` | Linked work items |

## Explore Configurations

| Command | Description |
|---------|-------------|
| `dxs source explore info -b <id>` | Branch overview |
| `dxs source explore configs -b <id>` | List all configs |
| `dxs source explore configs -b <id> --type grid` | Filter by type |
| `dxs source explore configs -b <id> --owned-only` | Only local configs |
| `dxs source explore config <name> -b <id>` | View config content |
| `dxs source explore summary <name> -b <id>` | Config summary |
| `dxs source explore trace <name> -b <id>` | Trace dependencies |
| `dxs source explore graph -b <id>` | Generate dep graph |
| `dxs source explore cache --stats` | Cache statistics |

## DevOps Integration

| Command | Description |
|---------|-------------|
| `dxs devops workitem <id> --org <org>` | Get work item |
| `dxs devops workitems <ids> --org <org>` | Get multiple items |
| `dxs devops workitems <ids> --org <org> --description` | Include descriptions |

## Global Options

| Option | Description |
|--------|-------------|
| `--format yaml` | YAML output (default) |
| `--format json` | JSON output |
| `--format csv` | CSV output |
| `--concise` | Strip nulls/verbose fields |
| `-h, --help` | Show command help |

## Common Patterns

```bash
# List recent commits
uv run dxs source branch list --repo-name "MyRepo" --status history --sort commit-date --desc --limit 5

# Review a commit's changes
uv run dxs source changes -b 12345 --with-diffs

# Find feature branches by author
uv run dxs source branch list --repo 10 --status feature --author "user@example.com"

# Get work item details for a branch
uv run dxs source workitems -b 12345 --description

# Explore what's in a branch
uv run dxs source explore info -b 12345
uv run dxs source explore configs -b 12345 --owned-only
```

## See Also

- [Branch Statuses](../branches/branch-statuses.md)
- [Output Formats](./output-formats.md)
- [Config Types](../exploring-configs/config-types.md)
