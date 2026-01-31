# Reference

Quick lookups and reference materials.

## In This Section

| Document | Description |
|----------|-------------|
| [Command Cheatsheet](./command-cheatsheet.md) | All commands in one page |
| [Branch Statuses](./branch-statuses.md) | Status types and meanings |
| [Output Formats](./output-formats.md) | YAML/JSON/CSV options |

## Quick Links

### Most Used Commands

```bash
# List feature branches
uv run dxs source branch list --repo-name "MyRepo" --status feature

# View recent commits
uv run dxs source branch list --repo-name "MyRepo" --status history --sort commit-date --desc --limit 5

# Review commit changes
uv run dxs source changes -b 12345 --with-diffs

# Get work item details
uv run dxs devops workitem 12345 --org myorg --expand All
```

### Status Quick Reference

| To Find | Use |
|---------|-----|
| Recent commits | `--status history` |
| In-progress work | `--status feature` |
| Current release | `--status active` |
| Previous releases | `--status inactive` |
| Main branch | `--status draft` |

## See Also

- [Branch Statuses Detail](./branch-statuses.md)
- [Code Review Workflow](../code-review/)
