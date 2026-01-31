# Release Notes Generation Process

Instructions for using the `dxs` CLI to explore changes between releases and generate release notes.

## Overview

Generating release notes requires three sources of information:

1. **Commits** - What branches were merged and what configs changed
2. **Work Items** - The requirements, context, and user-facing problem being solved
3. **Source Diffs** - The actual code/configuration changes

Commit titles are a starting point, but developers don't always write great commit messages. Work items provide the "why" and user context. Source diffs show exactly what changed technically.

## Prerequisites

You need two branch IDs representing the releases to compare:
- `--from`: The older release (baseline)
- `--to`: The newer release (what changed)

Branch IDs can be found via `dxs source compare` output from previous comparisons, or by listing releases for an application.

## Step 1: Compare Releases

```bash
dxs source compare --from <old_branch_id> --to <new_branch_id>
```

This returns:
- **releases**: Intermediate releases between the two branches
- **committed_branches**: Feature branch commits with their configuration changes
- **dependency_changes**: Which dependencies were updated, with branch IDs for drilling down

### Understanding the Output

**`committed_branches`** lists each merged feature branch:
- `id`: Branch ID (use this to fetch work items)
- `title`: Commit message (use as a signal, but verify with work items)
- `author`: Who made the change
- `changes`: List of configurations modified (reference_name, type, modification)

**Commits WITH `changes`**: Direct code changes to this module.

**Commits WITHOUT `changes`**: Sync commits pulling in dependency updates.

## Step 2: Get Work Items for Each Commit

For each interesting commit, fetch the linked work items:

```bash
dxs source workitems --branch <commit_branch_id> --description
```

This returns:
- **title**: Work item title (often more descriptive than commit message)
- **type**: Development, Bug, Wavelength Component, etc.
- **state**: Done, Committed, etc.
- **assigned_to**: Who worked on it
- **description**: Full requirements, steps to reproduce, mockups, etc.

**This is the most valuable source for release notes.** Work items contain:
- User-facing problem description
- Detailed requirements
- Steps to reproduce (for bugs)
- Acceptance criteria
- Screenshots/mockups

Example:
```bash
# Get work items for Mobile Configurator commit
dxs source workitems --branch 66644 --description

# Get work items for a bug fix
dxs source workitems --branch 66852 --description
```

## Step 3: View Source Diffs

For key changes, look at the actual configuration diff:

```bash
dxs source diff --from <old_branch_id> --to <new_branch_id> --config <reference_name>
```

This returns:
- **change_type**: "created", "modified", "deleted", or "unchanged"
- **content**: Full configuration (for created configs)
- **diff**: Unified diff format (for modified configs)

### When to Use Diffs

**Always diff newly created configs** - See the structure of new features:
```bash
# See the structure of a new hub
dxs source diff --from 64919 --to 67159 --config mobile_configurator_hub

# See new flow logic
dxs source diff --from 64876 --to 67102 --config create_annotation_task_action
```

**Diff heavily modified configs** - Understand what changed:
```bash
# A flow modified by many commits
dxs source diff --from 64876 --to 67102 --config execute_process_waves_flow
```

**Diff bug fixes** - Understand the actual fix:
```bash
# Sometimes fixes are surprisingly simple
dxs source diff --from 64919 --to 67159 --config outbound_orders_eligible_for_return_grid
# Result: agGrid: null → agGrid: true
```

## Step 4: Drill Into Dependencies

For each updated dependency, repeat steps 1-3:

```bash
# Get commits for the dependency
dxs source compare --from <dep_from_branch> --to <dep_to_branch>

# Get work items for interesting commits
dxs source workitems --branch <commit_id> --description

# View diffs for key configs
dxs source diff --from <dep_from_branch> --to <dep_to_branch> --config <ref_name>
```

Focus on dependencies with many commits - they likely have significant changes.

## Workflow Summary

```
1. source compare --from A --to B
   ├── Identify commits with changes (not just syncs)
   ├── Note dependency_changes.updated
   │
2. For each significant commit:
   │   source workitems --branch <commit_id> --description
   │   └── Get requirements, context, user problem
   │
3. For key configs:
   │   source diff --from A --to B --config <ref_name>
   │   └── See actual code/structure
   │
4. For each updated dependency:
       Repeat steps 1-3
```

## Writing Release Notes

### Structure

#### 1. Summary Section
- Release version/date range
- Number of intermediate releases
- Number of dependencies updated

#### 2. New Features
For each feature:
- **Title** from work item (not commit message)
- **Work Item link** for traceability
- **Author** attribution
- **Description** from work item requirements
- **Technical details** from source diffs (new configs created, structure)

#### 3. Improvements
- Enhancements to existing functionality
- UI/UX improvements
- Performance optimizations

#### 4. Bug Fixes
For each bug:
- **Work Item link** and title
- **Problem** - What users experienced (from work item description)
- **Fix** - What was actually changed (from source diff)

#### 5. Dependencies Updated
- Table showing which dependencies had significant changes
- Link to sub-release notes if needed

### Example Feature Entry

```markdown
### Mobile Configurator Hub
**Work Item:** [#234705](https://dev.azure.com/DatexCorporation/_apis/wit/workItems/234705)
**Author:** Aleksandar Todorov

A centralized configuration screen for mobile warehouse settings,
accessible via Settings → Mobile Configuration.

**Structure:**
- Warehouses tab - Configure mobile settings per warehouse
- Owners tab - Configure mobile settings per owner
- Order Classes tab - Inbound/Outbound subtabs
- Equipment Types tab - Configure per equipment type

**New configurations:** 29 configs including grids, editors, flows,
and selectors.
```

### Example Bug Fix Entry

```markdown
### InRMA Return Date Filters Not Working
**Work Item:** [#238852](https://dev.azure.com/DatexCorporation/_apis/wit/workItems/238852)
**Author:** Jay Agno Jr

**Problem:** Date filters on the InRMA Order Create page did not
filter shipment-completed outbound orders.

**Fix:** Enabled AG Grid on `outbound_orders_eligible_for_return_grid`.
```

## Tips

1. **Work items are the source of truth** - Commit titles are signals, work items have the real context.

2. **Every feature branch should have a work item** - If a commit has no linked work items, flag it as missing traceability.

3. **Diff new configs to understand structure** - A hub's tabs, a flow's logic, a grid's columns are all visible in the diff.

4. **Bug fixes reveal themselves in diffs** - Sometimes a complex-sounding bug has a one-line fix.

5. **Config types guide where to look**:
   - `hub`: Navigation structure, tabs, action bars
   - `flow`/`footprintFlow`: Backend business logic
   - `frontendFlow`: UI interactions and navigation
   - `form`/`editor`: User interface screens
   - `grid`: Data display, columns, filters
   - `selector`: Dropdown/picker options
   - `datasource`: Data fetching queries
   - `storage`: State management (often MongoDB)

6. **Modification types**:
   - `add`: New configuration - likely new feature, always diff it
   - `update`: Modified - may be significant or trivial, check diff
   - `delete`: Removed - potential breaking change

## Example Session

```bash
# Step 1: Compare main app releases
dxs source compare --from 64920 --to 67162
# Shows 16 committed_branches, 19 updated dependencies

# Step 2: Get work items for a feature commit
dxs source workitems --branch 66644 --description
# Returns work item #234705 with full Mobile Configurator requirements

# Step 3: See the new hub structure
dxs source diff --from 64919 --to 67159 --config mobile_configurator_hub
# Shows tabs: Warehouses, Owners, Order Classes, Equipment Types

# Step 4: Drill into Waves dependency
dxs source compare --from 64876 --to 67102
# Shows 12 commits with wave planning features

# Get work items for wave planning
dxs source workitems --branch 67099 --description
# Returns work item #180436 with detailed wave creation requirements

# See the new annotation task flow
dxs source diff --from 64876 --to 67102 --config create_annotation_task_action
# Shows the actual code that creates annotation tasks

# Check a bug fix
dxs source workitems --branch 66852 --description
# Returns bug #238852 - date filters not working

dxs source diff --from 64919 --to 67159 --config outbound_orders_eligible_for_return_grid
# Shows the fix: agGrid: null → agGrid: true
```
