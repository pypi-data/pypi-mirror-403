# DevOps Integration

Query Azure DevOps work items linked to branches.

## In This Section

| Document | Description |
|----------|-------------|
| [Work Items](./workitems.md) | Query work item details |

## Quick Start

```bash
# Get single work item
uv run dxs devops workitem 227421 --org datexCorporation

# Get multiple work items
uv run dxs devops workitems 227421,227422 --org datexCorporation --description

# Get work items for a branch
uv run dxs source workitems -b 12345 --description
```

## Prerequisites

- Authenticated with DevOps permissions (`dxs auth login`)
- Know your Azure DevOps organization name

## Commands

| Command | Description |
|---------|-------------|
| `dxs devops workitem <id>` | Get single work item |
| `dxs devops workitems <ids>` | Get multiple work items |
| `dxs source workitems -b <id>` | Work items for branch |

## Use Cases

### Code Review Context
```bash
# Find what feature a commit implements
uv run dxs source workitems -b <commit_id> --description
```

### Requirements Verification
```bash
# Get full work item details
uv run dxs devops workitem 227421 --org datexCorporation --expand All
```

## See Also

- [Work Items](./workitems.md) - Full reference
- [Code Review](../code-review/) - Using work items in reviews
