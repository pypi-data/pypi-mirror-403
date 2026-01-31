# Viewing Changes

Quick reference for viewing branch changes.

## Commands

| Command | Description |
|---------|-------------|
| `dxs source changes -b <id>` | Show changes in branch |
| `dxs source changes -b <id> --with-diffs` | Include actual diffs |
| `dxs source diff -b <id>` | Show upstream changes |

## Basic Usage

```bash
# List what changed
uv run dxs source changes -b 12345

# Include the actual diffs (for code review)
uv run dxs source changes -b 12345 --with-diffs
```

## Output Structure

```yaml
feature_branch_changes:
  summary:
    total_config_changes: 3
    has_replacements: false
    has_settings: true
    has_operations: false
    has_references: true
    branch_type: feature  # or "committed"
  changes_by_type:
    created: []
    updated: []
    deleted: []
  all_changes:
    - id: 12345
      referenceName: my_grid
      configurationTypeId: grid
      modificationTypeId: update
      diff: "..."  # Only with --with-diffs
```

## When to Use

| Scenario | Command |
|----------|---------|
| Quick overview of changes | `changes -b <id>` |
| Code review | `changes -b <id> --with-diffs` |
| See what to pull | `diff -b <id>` |

## See Also

- [Viewing Changes Guide](./viewing-changes-guide.md) - Deep dive with examples
- [Code Review Workflow](../code-review/) - Using changes for review
