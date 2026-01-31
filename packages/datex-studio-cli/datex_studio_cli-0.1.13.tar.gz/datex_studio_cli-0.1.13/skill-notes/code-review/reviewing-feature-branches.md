# Reviewing Feature Branches

Guide for reviewing in-progress work in feature branches.

## Overview

Feature branches (WorkspaceActive status) contain work that hasn't been committed yet. Review these to:
- Assess completion status
- Catch issues before commit
- Understand what's being worked on

## Finding Feature Branches

```bash
# All feature branches
uv run dxs source branch list --repo-name "MyRepo" --status feature

# Feature branches by author
uv run dxs source branch list --repo-name "MyRepo" --status feature --author "user@example.com"

# Recently modified
uv run dxs source branch list --repo-name "MyRepo" --status feature --sort modified --desc
```

## Reviewing Changes

```bash
# List changes
uv run dxs source changes -b <branch_id>

# With diffs for detailed review
uv run dxs source changes -b <branch_id> --with-diffs
```

## Understanding Change Summary

```yaml
feature_branch_changes:
  summary:
    total_config_changes: 7
    has_replacements: false
    has_settings: true
    has_operations: false
    has_references: true
    branch_type: feature
  changes_by_type:
    created:
    - rebill_order_flow
    - rebill_order_frontFlow
    updated:
    - order_list_grid
    - order_search_grid
    deleted: []
```

### Key Fields

| Field | Meaning |
|-------|---------|
| `total_config_changes` | Number of configs modified |
| `changes_by_type.created` | New configs added |
| `changes_by_type.updated` | Existing configs modified |
| `changes_by_type.deleted` | Configs removed |
| `has_references` | Library references changed |

## Assessing Completion

1. **Get work item requirements**
   ```bash
   uv run dxs source workitems -b <branch_id> --description
   ```

2. **Compare requirements to implementation**
   - Are all acceptance criteria addressed?
   - Is the scope appropriate?
   - Any missing pieces?

## Example Assessment

For a "Rebill Order Button" feature:

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Add button to order hub | Done | `order_list_grid` updated |
| Show confirmation dialog | Done | `rebill_order_frontFlow` created |
| Call rebill API | Done | `rebill_order_flow` created |
| Check privileges | Not visible | May need verification |

**Estimated Completion: 85-90%**

## Things to Look For

### Positive Signs
- Consistent naming patterns
- Proper error handling
- Complete CRUD operations

### Red Flags
- Empty or stub implementations
- TODO comments
- Hardcoded values
- Missing validation

## Getting More Detail

### View Specific Configuration
```bash
uv run dxs source explore config <config_name> -b <branch_id>
```

### View Configuration Summary
```bash
uv run dxs source explore summary <config_name> -b <branch_id>
```

### Trace Dependencies
```bash
uv run dxs source explore trace <config_name> -b <branch_id>
```

## See Also

- [Reviewing Commits Guide](./reviewing-commits-guide.md) - For committed code
- [Exploring Configs](../exploring-configs/) - Deeper config analysis
- [DevOps Integration](../devops-integration/) - Work item queries
