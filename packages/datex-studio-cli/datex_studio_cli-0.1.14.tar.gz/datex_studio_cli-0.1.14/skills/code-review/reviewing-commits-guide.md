# Reviewing Commits (Guide)

Step-by-step guide for reviewing recently committed code.

## Overview

This guide covers reviewing commits that have already been merged to the main branch. These appear as "history" branches (WorkspaceHistory status) and represent frozen snapshots of each commit.

## Prerequisites

- Authenticated with `dxs auth login`
- Know the repository name or ID

## Step 1: Find Recent Commits

List history branches sorted by commit date:

```bash
uv run dxs source branch list --repo-name "FootprintManager" --status history --sort commit-date --desc --limit 5
```

### Example Output

```yaml
branches:
- id: 65327
  commitTitle: '[Bugfix] Auto email attachments overwritten on save'
  commitDate: '2026-01-14T10:22:02.4132249+00:00'
  authorDisplayName: Evelin Velikov
  statusName: WorkspaceHistory
  isCommit: true
- id: 65320
  commitTitle: 'Add owner lookup to inbound and outbound grids'
  commitDate: '2026-01-13T23:59:04.8415656+00:00'
  authorDisplayName: Derek Armanious
  isCommit: true
```

Note the `id` values - you'll use these in the next step.

## Step 2: Fetch Changes with Diffs

For each commit you want to review:

```bash
uv run dxs source changes -b 65320 --with-diffs
```

### Example Output

```yaml
feature_branch_changes:
  summary:
    total_config_changes: 1
    has_settings: false
    has_references: false
    branch_type: committed
  all_changes:
  - referenceName: outbound_orders_grid
    configurationTypeId: grid
    modificationTypeId: update
    diff: |-
      --- previous (outbound_orders_grid)
      +++ current (outbound_orders_grid)
      @@ -1,6 +1,6 @@
      -  "agGrid": false,
      +  "agGrid": true,
      @@ -439,7 +439,7 @@
      -          "value": ""
      +          "value": "$row.entity.Project?.Owner?.LookupCode"
    diff_summary:
      lines_added: 79
      lines_removed: 3
```

## Step 3: Classify the Commit

### Real Code Change
- `total_config_changes > 0`
- Has actual config diffs
- Requires thorough review

### Sync/Reference Update
- `total_config_changes: 0`
- Only `has_references: true` or `has_settings: true`
- Usually safe, just library version updates

## Step 4: Analyze Changes

For each real change, look for:

1. **Bugs**
   - Logic errors
   - Missing null checks
   - Off-by-one errors

2. **Incomplete Implementation**
   - Title mentions multiple things, only one done
   - Missing error handling
   - Incomplete validation

3. **Code Quality**
   - Duplicated code
   - Inconsistent patterns
   - Missing cleanup

4. **Risk Assessment**
   - How many files touched?
   - Core functionality affected?
   - Edge cases considered?

## Step 5: Get Work Item Context (Optional)

If the commit references a work item:

```bash
# Extract work item ID from commit title (e.g., "[227421]")
uv run dxs devops workitem 227421 --org datexCorporation
```

Compare the work item requirements against the implementation.

## Step 6: Document Findings

Use the [Review Report Template](./review-report-template.md) to document:

- Changes summary
- Bugs found
- Risk assessment
- Senior review recommendation

## Example Review Workflow

```bash
# 1. Find last 5 commits
uv run dxs source branch list --repo-name "FootprintManager" --status history --sort commit-date --desc --limit 5

# 2. Review each commit (repeat for each id)
uv run dxs source changes -b 65327 --with-diffs
uv run dxs source changes -b 65320 --with-diffs
uv run dxs source changes -b 65291 --with-diffs
# ...

# 3. Get work item details for commits that reference them
uv run dxs devops workitem 227421 --org datexCorporation

# 4. Write report using template
```

## Common Findings

### Missing Inbound/Outbound Symmetry
If title says "inbound and outbound" but only one grid changed.

### Removed Code
Look for `-` lines in the diff that seem important:
```diff
-  // Important logic removed
-  if (condition) { ... }
```

### Inconsistent Patterns
Same pattern implemented differently in different places.

## See Also

- [Review Report Template](./review-report-template.md) - Document your findings
- [Viewing Changes Guide](../source-control/viewing-changes-guide.md) - Understanding diffs
- [Reviewing Feature Branches](./reviewing-feature-branches.md) - For WIP code
