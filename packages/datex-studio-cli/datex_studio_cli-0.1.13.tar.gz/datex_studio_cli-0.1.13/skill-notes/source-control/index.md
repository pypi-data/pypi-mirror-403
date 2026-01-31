# Source Control

Commands for viewing changes, history, and dependencies.

## In This Section

| Document | Description |
|----------|-------------|
| [Viewing Changes](./viewing-changes.md) | Quick reference for changes/diff |
| [Viewing Changes Guide](./viewing-changes-guide.md) | Deep dive with diff examples |
| [Commit History](./commit-history.md) | Log command and history |
| [Dependencies](./dependencies.md) | deps, deps-diff, graph commands |

## Quick Start

```bash
# View pending changes in a feature branch
uv run dxs source changes -b 12345

# View changes with actual diffs (for code review)
uv run dxs source changes -b 12345 --with-diffs

# View commit history
uv run dxs source log --repo 10 --limit 20

# View dependencies
uv run dxs source deps -b 12345 --tree
```

## Commands Overview

| Command | Description |
|---------|-------------|
| `changes` | Show pending changes in feature branch |
| `diff` | Show upstream changes (from base branch) |
| `log` | Show commit history |
| `history` | Show version history for a config |
| `locks` | Show locked configurations |
| `deps` | List dependencies |
| `deps-diff` | Compare dependencies between branches |
| `graph` | Generate dependency graph |
| `workitems` | List linked work items |
| `compare` | Compare marketplace versions |

## Key Concepts

### Changes vs Diff

- **`changes`**: What's different in THIS branch from its base
- **`diff`**: What's available in the BASE branch to pull

### Branch Types and Changes

| Branch Type | Has Changes? | Notes |
|-------------|--------------|-------|
| Feature (WorkspaceActive) | Yes | Pending work |
| History (WorkspaceHistory) | Yes | What was committed |
| Draft | No | Receives commits |
| Active/Inactive | No | Published snapshots |

## See Also

- [Branches](../branches/) - Understanding branch types
- [Code Review](../code-review/) - Using changes for review
