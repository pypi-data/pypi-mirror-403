# Viewing Changes (Guide)

Deep dive into viewing and understanding branch changes with real diff examples.

## Overview

The `dxs source changes` command shows what configurations have changed in a branch compared to its base. Use `--with-diffs` to see the actual changes for code review.

## Prerequisites

- Authenticated with `dxs auth login`
- Know the branch ID (from `branch list`)

## Basic Changes View

```bash
uv run dxs source changes -b 65320
```

### Example Output (Summary Only)

```yaml
feature_branch_changes:
  summary:
    total_config_changes: 1
    has_replacements: false
    has_settings: false
    has_operations: false
    has_references: false
    has_roles: false
    branch_type: committed
  changes_by_type:
    created: []
    updated: []
    deleted: []
  all_changes:
  - id: 6680226
    baseConfigId: 126975
    referenceName: outbound_orders_grid
    configurationTypeId: grid
    modificationTypeId: update
  base_branch_id: 3339
metadata:
  success: true
  branch_id: 65320
  includes_diffs: false
```

## Changes with Diffs (For Code Review)

```bash
uv run dxs source changes -b 65320 --with-diffs
```

### Example Output (With Diffs)

```yaml
feature_branch_changes:
  summary:
    total_config_changes: 1
    branch_type: committed
  all_changes:
  - id: 6680226
    referenceName: outbound_orders_grid
    configurationTypeId: grid
    modificationTypeId: update
    diff: |-
      --- previous (outbound_orders_grid)
      +++ current (outbound_orders_grid)
      @@ -1,6 +1,6 @@
       {
         "accessModifier": "public",
      -  "agGrid": false,
      +  "agGrid": true,
         "baseConfiguration": null,
      @@ -439,7 +439,7 @@
                   "formatType": null,
                   "hasFormat": false,
                   "tooltip": "",
      -          "value": ""
      +          "value": "$row.entity.Project?.Owner?.LookupCode"
               },
    diff_summary:
      lines_added: 79
      lines_removed: 3
    has_changes: true
    compared_to_commit: '235387'
```

## Understanding Sync Commits vs Real Changes

### Sync Commit (No Config Changes)

When `total_config_changes: 0` but has settings/references changes:

```yaml
feature_branch_changes:
  summary:
    total_config_changes: 0
    has_settings: true
    has_references: true
    branch_type: committed
  entity_diffs:
    settings:
      has_changes: true
      changes_summary:
        modified:
        - DateFormat
        - FootprintApi
      compared_to_commit: '[Previous Commit]'
    references:
      has_changes: true
      changes_summary:
        modified:
        - Notifications  # Library version updated
```

This means:
- No application code changed
- Just updated library references or settings
- Usually a "sync" or "component update" commit

### Real Code Changes

When `total_config_changes > 0`:

```yaml
feature_branch_changes:
  summary:
    total_config_changes: 11
    branch_type: committed
  all_changes:
  - referenceName: sales_order_editor
    configurationTypeId: editor
    modificationTypeId: update
    diff: |
      ... actual code changes ...
```

## Reading the Diffs

Diffs use standard unified diff format:

```diff
--- previous (config_name)
+++ current (config_name)
@@ -line_num,count +line_num,count @@
 unchanged line
-removed line
+added line
 unchanged line
```

### Key Patterns to Look For

**Property Changes:**
```diff
-  "agGrid": false,
+  "agGrid": true,
```

**Code Block Changes (in flows):**
```diff
-              "code": "const result = await $flows.SalesOrders.complete_sales_order_flow(...);"
+              "code": "const result = await $flows.SalesOrders.complete_sales_order_divert_billing_flow(...);"
```

**New Sections Added:**
```diff
+    {
+      "contentConfig": {
+        "configId": "new_grid",
```

## Common Patterns

### Code Review Workflow

```bash
# 1. Find recent commits
uv run dxs source branch list --repo-name "MyRepo" --status history --sort commit-date --desc --limit 5

# 2. Review each commit
uv run dxs source changes -b <commit_id> --with-diffs

# 3. Check for linked work items
uv run dxs source workitems -b <commit_id>
```

### Identifying What Changed

1. Check `summary.total_config_changes` - is there real code?
2. Look at `changes_by_type` - created, updated, or deleted?
3. Review `all_changes` - which configs were modified?
4. Read the `diff` - what specifically changed?

## Troubleshooting

### Empty Changes

If `total_config_changes: 0`:
- Might be a sync/reference-only commit
- Check `entity_diffs.references` for library updates
- Check if branch type is appropriate

### Large Diffs

For complex changes:
- Focus on `diff_summary.lines_added/removed`
- Look for the `compared_to_commit` field to understand context
- Consider reviewing the config directly with `explore config`

## See Also

- [Commit History](./commit-history.md) - Finding commits to review
- [Code Review Workflow](../code-review/) - Complete review process
- [Exploring Configs](../exploring-configs/) - Viewing full config content
