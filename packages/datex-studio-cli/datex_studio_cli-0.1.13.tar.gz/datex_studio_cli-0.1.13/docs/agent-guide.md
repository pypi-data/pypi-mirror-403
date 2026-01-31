# DXS Agent Guide: Exploring Datex Studio Applications

This guide explains how LLM-based agents can use the `dxs` CLI to explore and understand Datex Studio application codebases.

## Overview

Datex Studio applications are built from **configurations** - JSON definitions that describe UI components, business logic flows, data access layers, and more. The `dxs source explore` commands provide structured access to these configurations for analysis.

### Key Concepts

- **Branch**: A versioned snapshot of an application (identified by branch ID)
- **Configuration**: A JSON definition for a component (e.g., grid, form, flow, datasource)
- **Reference Name**: The unique identifier for a configuration within a branch
- **Owned vs Referenced**: Configs can be owned by the branch or referenced from library dependencies

### Configuration Types

Datex Studio supports 28 configuration types:

| Category | Types |
|----------|-------|
| UI Components | `shell`, `hub`, `grid`, `form`, `editor`, `wizard`, `card`, `list`, `widget`, `selector`, `calendar`, `embed`, `codeeditor`, `visualization`, `report` |
| Logic | `flow`, `frontendflow`, `footprintflow`, `footprintworkflow`, `backendtest` |
| Data | `datasource`, `footprintdatasource`, `customtype`, `storage`, `endpoint` |
| Other | `localization`, `securitypolicy` |

## Authentication

Before using most commands, authenticate:

```bash
dxs auth login
```

Check authentication status:

```bash
dxs auth status
```

## Exploration Workflow

### Step 1: Get Application Overview

Start by understanding what the application contains:

```bash
dxs source explore info --branch <BRANCH_ID>
```

**Output includes:**
- Application name, description, type (Application or Library)
- Referenced library modules
- Configuration counts by type (owned vs referenced)

**Example response:**
```yaml
data:
  application:
    name: SalesOrderManagement
    branch_id: 63393
    type: Application
  references:
    - Utilities
    - Footprint
  config_counts:
    owned:
      hub: 5
      grid: 12
      flow: 45
    referenced:
      datasource: 30
      flow: 100
```

### Step 2: List Configurations

Browse available configurations:

```bash
# List all configurations
dxs source explore configs --branch <BRANCH_ID>

# Filter by type
dxs source explore configs --branch <BRANCH_ID> --type grid

# Search by name
dxs source explore configs --branch <BRANCH_ID> --search "order"

# Only owned configs (excludes library references)
dxs source explore configs --branch <BRANCH_ID> --owned-only

# Limit results
dxs source explore configs --branch <BRANCH_ID> --limit 20
```

**When to use:**
- Discovering what functionality exists
- Finding configs by name pattern
- Understanding the scope of owned vs library code

### Step 3: View Configuration Content

Get the full JSON definition of a specific configuration:

```bash
# Auto-detect type
dxs source explore config <REFERENCE_NAME> --branch <BRANCH_ID>

# Specify type for faster lookup
dxs source explore config create_order_flow --branch <BRANCH_ID> --type flow

# Raw JSON only (no metadata envelope)
dxs source explore config my_grid --branch <BRANCH_ID> --raw
```

**When to use:**
- Examining exact implementation details
- Understanding field mappings, validations, flow logic
- Debugging specific component behavior

### Step 4: Get Structural Summary

Get a type-specific overview without the full JSON:

```bash
dxs source explore summary <REFERENCE_NAME> --branch <BRANCH_ID>
```

**Type-specific summaries include:**

| Type | Summary Fields |
|------|----------------|
| `grid` | datasource, columns (field/header), toolbar buttons, row actions |
| `form` | fields (id/control/label), submit flow, cancel flow |
| `editor` | datasource, sections with fields, save flow |
| `flow` | inParams, outParams, called flows, called datasources |
| `datasource` | endpoint, query, return fields |
| `hub` | tabs (id/title/content), toolbar actions |
| `shell` | home view, menubar structure, toolbar |
| `customtype` | fields (id/type/required), enum values, base types |

**When to use:**
- Quick understanding of component structure
- Identifying entry points (flows, datasources)
- Mapping UI to backend operations

### Step 5: Trace Dependencies

Find what a configuration references:

```bash
dxs source explore trace <REFERENCE_NAME> --branch <BRANCH_ID>
```

**Output includes references to:**
- `datasources` - Data access configurations
- `backend_flows` - Server-side logic
- `frontend_flows` - Client-side logic
- `private_frontend_flows` - Inline flows within the config
- `forms`, `editors`, `grids`, `hubs` - UI components
- `selectors` - Dropdown/lookup components
- `dialogs` - Modal/flyout references
- `types` - Custom type references
- `operations` - Security policy checks
- `database_tables` - Direct DB access
- `settings` - Application settings

Each reference includes its source library when applicable.

**When to use:**
- Understanding data flow through the application
- Finding all components involved in a feature
- Mapping dependencies for impact analysis

### Step 6: Generate Dependency Graph

Visualize the application structure:

```bash
# Output to stdout
dxs source explore graph --branch <BRANCH_ID>

# Save as Mermaid diagram
dxs source explore graph --branch <BRANCH_ID> --format mermaid --output-dir ./docs

# Save as YAML
dxs source explore graph --branch <BRANCH_ID> --format yaml --output-dir ./docs

# Only owned configs
dxs source explore graph --branch <BRANCH_ID> --owned-only

# Control traversal depth
dxs source explore graph --branch <BRANCH_ID> --max-depth 5
```

**When to use:**
- Getting a visual map of the application
- Understanding navigation paths (shell → hub → grid → flow)
- Identifying isolated or highly-connected components

## Bulk Export for Offline Analysis

### Document Build

Download all configurations for local analysis, including library dependencies:

```bash
# Basic export
dxs source document build --branch <BRANCH_ID>

# Custom output directory
dxs source document build --branch <BRANCH_ID> --output-dir ./exploration

# With structural summaries
dxs source document build --branch <BRANCH_ID> --include-summaries

# Overwrite existing output
dxs source document build --branch <BRANCH_ID> --force
```

This downloads:
- All owned configurations (in `local/` directory)
- All library configurations (transitive dependencies, organized by library name)
- Library reference index (`libraries.yaml`)
- Application info (`info.yaml`)

**Output structure:**
```
exploration/<AppName>/<BranchId>/
├── local/
│   ├── grid/
│   │   └── orders_grid.yaml
│   ├── flow/
│   │   └── create_order.yaml
│   └── ...
├── <LibraryName>/<BranchId>/
│   ├── flow/
│   └── datasource/
├── libraries.yaml
└── info.yaml
```

## Advanced Analysis Workflow

For systematic codebase analysis, use these commands in sequence:

### 1. Build Documentation

```bash
dxs source document build --branch <BRANCH_ID> -o ./exploration
```

### 2. Generate Trace Files (if not using document build)

```bash
dxs source explore trace --offline --batch ./exploration
```

### 3. Build Dependency Graph

```bash
dxs source document graph --output-dir ./exploration
```

### 4. Generate Analysis Manifest

Create a prioritized work list from specific entry points:

```bash
dxs source explore manifest \
  --graph ./exploration/graph/dependency-graph.yaml \
  --roots sales_hub,orders_hub \
  --section "order-management" \
  --output manifest.yaml
```

**Manifest includes:**
- All reachable components from roots
- Priority levels (critical/high/medium/low)
- Analysis status (existing `.analysis.md` files)
- Code presence and line counts

### 5. Extract Code for Analysis

```bash
dxs source explore extract-code \
  --manifest manifest.yaml \
  --output ./code-files
```

Creates `.code.ts` files with:
- Header comments (flow name, parameters)
- Extracted TypeScript code from flows

### 6. Verify Analysis Coverage

```bash
dxs source explore verify --manifest manifest.yaml --priority high
```

Reports:
- Coverage percentage
- Missing analyses by priority
- List of unanalyzed components

## Cache Management

The CLI caches data for immutable branches to improve performance:

```bash
# View cache statistics
dxs source explore cache --stats

# Clear all cache
dxs source explore cache --clear

# Clear specific branch
dxs source explore cache --clear-branch <BRANCH_ID>
```

**Cached branches:** INACTIVE, ACTIVE, WORKSPACE_HISTORY (immutable states)
**Never cached:** Draft, WorkspaceActive (mutable states)

## Output Formats

All commands support multiple output formats:

```bash
# YAML (default, best for readability)
dxs source explore configs --branch <BRANCH_ID> --output yaml

# JSON (for programmatic parsing)
dxs source explore configs --branch <BRANCH_ID> --output json

# Save to file
dxs source explore configs --branch <BRANCH_ID> --save configs.yaml
```

### Concise Mode

Reduce token usage by stripping null values and verbose metadata:

```bash
dxs source explore config my_flow --branch <BRANCH_ID>  # Default: concise
dxs source explore config my_flow --branch <BRANCH_ID> --full  # Include all fields
```

## Common Investigation Patterns

### "How does feature X work?"

1. Search for related configs: `dxs source explore configs --branch <ID> --search "feature_name"`
2. Get summary of entry point: `dxs source explore summary feature_hub --branch <ID>`
3. Trace dependencies: `dxs source explore trace feature_hub --branch <ID>`
4. Examine specific flows: `dxs source explore config process_feature_flow --branch <ID>`

### "What calls this flow?"

Use the dependency graph or trace back from potential callers:

1. Build graph: `dxs source explore graph --branch <ID> --output-dir ./docs`
2. Search the YAML for the flow name as a target

### "What data does this grid display?"

1. Get grid summary: `dxs source explore summary my_grid --branch <ID>`
2. Examine the datasource: `dxs source explore config <datasource_name> --branch <ID>`
3. Check the endpoint/query for data source

### "What happens when user clicks Save?"

1. Get form/editor summary to find the save flow
2. Trace the flow: `dxs source explore trace save_flow --branch <ID>`
3. Examine flow content: `dxs source explore config save_flow --branch <ID>`

## Error Handling

Common errors and solutions:

| Error | Solution |
|-------|----------|
| "Not authenticated" | Run `dxs auth login` |
| "Branch ID required" | Add `--branch <ID>` or set `DXS_BRANCH` environment variable |
| "Configuration not found" | Check spelling, try `--search` to find similar names |
| "API error" | Check network, verify branch ID exists |

## Environment Variables

Set defaults to reduce command verbosity:

```bash
export DXS_BRANCH=63393      # Default branch ID
export DXS_ORG=my-org        # Default organization
export DXS_ENV=production    # Default environment
```

## Tips for Effective Exploration

1. **Start broad, then narrow**: Use `info` → `configs` → `summary` → `config`
2. **Use concise mode**: Default output strips nulls to save tokens
3. **Leverage caching**: Repeated queries on published branches are fast
4. **Export for complex analysis**: Use `document build` for multi-file analysis
5. **Trace from entry points**: Start with shells/hubs and trace outward
6. **Filter by ownership**: Use `--owned-only` to focus on application-specific code
