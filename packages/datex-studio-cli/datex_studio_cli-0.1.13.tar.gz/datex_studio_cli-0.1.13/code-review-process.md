# Code Review Process

Standard operating procedure for AI-assisted code review of Datex Studio branches using the `dxs` CLI.

## Step 1: Gather Context

Run these commands in parallel to understand intent and scope:

```bash
uv run dxs source changes --branch <ID>
uv run dxs source workitems --branch <ID> --description --comments
```

**Purpose:** Understand the intent (bug/feature), who's assigned, sprint context, and get a quick inventory of changed configs.

## Step 2: Trace Dependencies of Changed Configs

```bash
# Trace each significantly changed or deleted config
uv run dxs source explore trace <config_name> --branch <ID>
```

**Purpose:** Understand the dependency surface of changed configs before reading diffs. Trace shows what each config references — datasources, flows, grids, dialogs, backend flows — and which library they come from.

**When to use:**
- **Deleted configs** — trace to see what they depended on (forward deps). Cross-reference with traces of other configs to check if anything still references the deleted config by name.
- **Configs with significant changes** — trace to understand the structure (what flows does this editor call? what datasources does this grid use?) before reading the diff.
- **Cross-library references** — trace reveals when a config depends on shared platform flows (e.g., `crud_create_flow` from `Utilities`) or dialogs from other modules.

**Limitations:** Trace shows forward dependencies only (what a config references), not reverse dependents (what references it). To check if a deleted config is safe to remove, trace the configs that *might* reference it and look for the deleted name in their dependency lists.

**Example from branch 66894:**
```bash
# Trace the grid that had its datasource inlined
uv run dxs source explore trace custom_field_options_grid --branch 66894
# Revealed: still lists ds_get_custom_field_options as a datasource reference,
# even though that datasource was deleted — flagging a potential issue.

# Trace the editor with the bug fix
uv run dxs source explore trace custom_field_editor --branch 66894
# Revealed: references crud_create_flow (Utilities), custom_field_options_grid,
# Toaster dialog — maps the full dependency surface of the fix.
```

## Step 3: Review Diffs

```bash
uv run dxs source changes --branch <ID> --with-diffs
```

**Purpose:** Full unified diffs for every changed configuration.

## Step 4: Analyze Each Change

For each changed config, evaluate against these dimensions:

### A. Bugs
- Logic errors, off-by-one, incorrect conditions
- Unhandled edge cases (null entities, empty collections)
- Error handling gaps (missing catch blocks, unchecked results)
- Dead code or unreachable paths introduced

### B. Code Quality
- Clarity of intent — can you understand what the code does?
- Consistent patterns with surrounding code
- Unnecessary duplication
- Meaningful variable names
- Proper use of platform APIs/patterns

### C. Security Concerns
- Unsanitized user input in expressions/templates
- Injection risks in dynamic filter expressions
- Sensitive data exposure in params or logging
- Missing authorization checks

### D. Performance
- Unnecessary API calls or redundant data fetches
- N+1 query patterns in datasources
- Large payloads when only subset needed (missing selects/filters)
- Inefficient loops or repeated DOM operations

### E. Simplification Opportunities
- Overly complex expressions that could be clearer
- Redundant null checks / optional chaining
- Duplicate logic across configs that could be shared
- Unused parameters or dead config properties

### F. Alignment & Risk
- **Work item alignment** — does the change actually address the stated bug/feature?
- **Scope creep** — are there unrelated changes bundled in?
- **Regression risk** — could this break existing behavior?
- **Deleted config safety** — is the deleted config truly unused elsewhere?

## Step 5: Produce Review Summary

Structure the output as:

1. **Branch Overview** — ID, work item, assignee, sprint
2. **Changes Table** — config name, type, action, one-line summary
3. **Detailed Findings** — per-dimension findings with severity:
   - `[ISSUE]` — Must fix before merge
   - `[WARNING]` — Should fix, potential problem
   - `[INFO]` — Observation, no action required
   - `[OK]` — Reviewed, no concerns
4. **Questions for Developer** — things that need clarification
5. **Verdict** — Approve / Request Changes / Needs Discussion

---

## Example Review: Branch 66894

### Branch Overview
- **Branch:** 66894 (committed)
- **Work Item:** Bug 231879 — UDF creation with Type "Text" incorrectly creates "Selection list"
- **Assigned to:** Dominic Kirschbaum
- **Sprint:** Delta 26.01.29

### Changes Table
| Config | Type | Action | Summary |
|--------|------|--------|---------|
| `custom_field_editor` | editor | update | Core bug fix: remap TypeId 5→1, add outParams, save initial option on create |
| `custom_field_options_grid` | grid | update | Inline datasource, switch to agGrid, add optional chaining |
| `custom_fields_configuration_hub` | hub | update | Await editor dialog, refresh hub on close |
| `custom_fields_for_category_hub` | hub | update | Same pattern: await + refresh |
| `custom_fields_subcategory_configuration_hub` | hub | update | Same pattern: await + refresh |
| `ds_get_custom_field_options` | datasource | delete | Removed — inlined into grid |

### Detailed Findings

#### Bugs

**[ISSUE] Duplicate error check in save flow (`custom_field_editor`)**
The new create path checks `result.reason` twice:
```js
if (result.reason) {
    // show error
} else {
    // save UDF option value...
}
if (result.reason) {    // <-- checked again
    // show error (duplicate)
} else {
    // show toaster, close, reopen
}
```
If `result.reason` is truthy, the error dialog shows **twice**. This appears to be a refactoring artifact — the original had a single `if/else`, and the new option-saving logic was inserted in the middle, duplicating the error branch.

**[WARNING] `save_result` is unused (`custom_field_editor`)**
The result of `crud_create_flow` for the UDF option value is captured but never checked:
```js
const save_result = await $flows.Utilities.crud_create_flow({...});
```
If this fails silently, the UDF is created but its initial option value is lost with no error shown.

**[INFO] outParams lack names**
The two new outParams (confirm/cancel booleans) have no `description` or visible name property. This may work fine if the platform identifies them by index, but named params would be clearer.

#### Code Quality

**[INFO] TypeId remapping at binding level**
`$editor.entity.TypeId === 5 ? 1 : $editor.entity.TypeId` — this remaps the display value so the dropdown shows "Text" (1) instead of "Selection list" (5). It's a UI-level workaround. The root cause may be that the entity arrives with TypeId=5 when it should be 1. Worth confirming this is intentional vs. a data-layer fix being needed.

**[OK] Hub changes are consistent**
All three hubs apply the same pattern: `await` the dialog, check for response, refresh. Good consistency.

**[OK] Optional chaining additions**
`$editor.entity?.Label`, `$row.entity?.UdfValue`, `$grid.inParams?.custom_field_id` — defensive and appropriate.

#### Security Concerns

**[OK] No new injection vectors.** The datasource filter uses template literal with `$datasource.inParams.custom_field_id` which is a typed number param — low risk.

#### Performance

**[INFO] Datasource inlining is neutral.** Moving from a shared datasource reference to an inline datasource doesn't change runtime behavior. The `agGrid: true` switch may improve rendering for large option lists.

#### Simplification Opportunities

**[WARNING] Save flow restructure recommended.** The duplicated error handling could be simplified to a single `if/else` with the option-saving nested in the success path:
```js
if (result.reason) {
    // show error once
} else {
    // save option if needed
    // show toaster
    // close + reopen
}
```

**[INFO] Trailing whitespace changes.** Several code blocks have only whitespace diffs (leading `\r\n` removed, trailing `\r\n` added). These are noise but harmless.

#### Work Item Alignment

**[OK]** The core fix (TypeId 5→1 remapping) directly addresses the bug. The additional changes (outParams, hub refresh, datasource inlining) are reasonable supporting changes to improve the UDF creation workflow.

#### Scope

**[INFO]** The datasource inlining + agGrid switch is ancillary to the bug fix. Not problematic but worth noting as beyond the stated scope.

### Questions for Developer
1. The TypeId 5→1 remapping — is this a UI display fix or is there a deeper issue where the API returns TypeId=5 for Text fields? Should this be fixed at the data layer instead?
2. The `save_result` from creating the initial UDF option value is never checked — is failure acceptable here, or should it show an error?
3. The duplicate `result.reason` check appears unintentional — can the save flow be restructured to a single error check?

### Verdict
**Request Changes** — The duplicate error handling is a bug that would show two error dialogs on failure. The unchecked `save_result` is a secondary concern worth addressing.
