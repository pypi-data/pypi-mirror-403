# Work Items

Query Azure DevOps work items.

## Commands

| Command | Description |
|---------|-------------|
| `dxs devops workitem <id>` | Get single work item |
| `dxs devops workitems <ids>` | Get multiple work items |
| `dxs source workitems -b <id>` | Work items for branch |

## Get Single Work Item

```bash
uv run dxs devops workitem 227421 --org datexCorporation
```

### Options

| Option | Description |
|--------|-------------|
| `--org <name>` | Azure DevOps org (required) |
| `--expand <level>` | None, Relations, Links, All |

### Example Output

```yaml
workitem:
  id: 227421
  title: Add rebill button to order hub
  type: User Story
  state: Active
  assignedTo: Evelin Velikov
  description: |
    As a user, I want to rebill orders...
  acceptanceCriteria: |
    - Button visible on order hub
    - Confirmation dialog shown
    - ...
metadata:
  success: true
```

## Get Multiple Work Items

```bash
uv run dxs devops workitems 227421,227422,227423 --org datexCorporation
```

### Options

| Option | Description |
|--------|-------------|
| `--org <name>` | Azure DevOps org (required) |
| `--description` | Include descriptions |
| `--discussions` | Include comments |

### Example

```bash
# With descriptions
uv run dxs devops workitems 227421,227422 --org datexCorporation --description
```

## Work Items for Branch

```bash
uv run dxs source workitems -b 12345
```

Finds work items referenced in commit messages.

### Options

| Option | Description |
|--------|-------------|
| `-b, --branch <id>` | Branch ID |
| `--commits` | Group by commit |
| `--description` | Include descriptions |
| `--comments` | Include discussions |

### Example

```bash
uv run dxs source workitems -b 65320 --description
```

## Use in Code Review

```bash
# 1. Find what a commit implements
uv run dxs source workitems -b <commit_id>

# 2. Get full details
uv run dxs devops workitem <id> --org datexCorporation --expand All

# 3. Compare to implementation
uv run dxs source changes -b <commit_id> --with-diffs
```

## Example Workflow

```bash
# Review a commit
COMMIT_ID=65320

# What work items?
uv run dxs source workitems -b $COMMIT_ID

# Get requirements
uv run dxs devops workitem 227421 --org datexCorporation

# Check implementation
uv run dxs source changes -b $COMMIT_ID --with-diffs
```

## See Also

- [Code Review](../code-review/) - Review workflows
- [Viewing Changes](../source-control/viewing-changes.md) - Compare to requirements
