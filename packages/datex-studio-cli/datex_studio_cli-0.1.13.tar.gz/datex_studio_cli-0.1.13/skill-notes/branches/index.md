# Branches

Working with branches (Applications) in Datex Studio.

## What is a Branch?

In Datex Studio, a **branch** (internally called an `Application`) represents a working copy of a repository at a specific point in time. Branches can be:

- **Feature branches** - Active development work
- **Commit snapshots** - Frozen records of commits
- **Releases** - Published versions (active or inactive)
- **Main branch** - The draft branch receiving commits

## In This Section

| Document | Description |
|----------|-------------|
| [Listing Branches](./listing-branches.md) | Quick reference for list command |
| [Listing Branches Guide](./listing-branches-guide.md) | Deep dive with output examples |
| [Branch Statuses](./branch-statuses.md) | Status types reference |

## Quick Start

```bash
# List all feature branches in a repo
uv run dxs source branch list --repo-name "MyRepo" --status feature

# List recent commits (history branches)
uv run dxs source branch list --repo-name "MyRepo" --status history --sort commit-date --desc --limit 5

# Show branch details
uv run dxs source branch show 12345
```

## Branch Statuses at a Glance

| Status | CLI Filter | What It Is |
|--------|------------|------------|
| Draft | `--status draft` | Main development branch |
| Active | `--status active` | Current published release |
| Inactive | `--status inactive` | Previous releases |
| WorkspaceHistory | `--status history` | Commit snapshots |
| WorkspaceActive | `--status feature` | Feature branches |

See [Branch Statuses](./branch-statuses.md) for full details.

## Data Model

```
Repository (ApplicationDefinition)
    │
    └── Branch Container (ApplicationGroup)
            │
            ├── Draft Branch (main)
            ├── Active Branch (current release)
            ├── Inactive Branches (old releases)
            ├── History Branches (commits)
            └── Feature Branches (WIP)
```

## See Also

- [Source Control](../source-control/) - Viewing changes and history
- [Code Review](../code-review/) - Reviewing branch changes
