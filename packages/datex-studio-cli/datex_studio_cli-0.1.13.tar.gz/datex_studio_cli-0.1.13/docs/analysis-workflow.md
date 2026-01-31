# Analysis Workflow Commands

This document describes the LLM agent analysis workflow implemented in the `dxs source document analyze` command group.

## Overview

The analysis workflow enables an LLM-based agent to systematically analyze all configurations downloaded from a Datex Studio branch. It provides a "todo list" pattern where the agent can:

1. Get a list of configs needing analysis (ordered so dependencies come first)
2. Perform analysis on each config
3. Store the analysis results
4. Track progress until all configs are analyzed

## Commands

### `dxs source document build`

Downloads configurations with optional context generation.

```bash
dxs source document build --branch <id> --include-context -o <dir>
```

**Key Options:**
- `--include-context` - Generate `.context.yaml` files containing structural info and dependency references (required for topological ordering)

### `dxs source document analyze init`

Smart initialization that detects what's needed and runs appropriate setup steps.

```bash
# Full setup from scratch (requires auth)
dxs source document analyze init -o <output-dir> --branch <id>

# Initialize existing directory with configs
dxs source document analyze init -o <output-dir>
```

**What it does automatically:**
- **Empty directory + branch**: Downloads configs, generates context files, builds graph
- **Has configs but no context files**: Generates context files
- **Has context files but no graph**: Builds dependency graph
- **Everything present**: Just initializes progress tracking

**Options:**
- `-b, --branch` - Branch ID (required only if directory is empty)
- `-f, --force` - Re-initialize even if progress exists

**Output:**
- Orders configs topologically (leaves first) so dependencies are analyzed first
- Uses file paths as unique identifiers to handle duplicate reference names
- Creates `graph/progress.yaml` to track analysis state

### `dxs source document analyze next`

Returns the next batch of configurations pending analysis.

```bash
dxs source document analyze next -o <output-dir> [--limit N] [--include-context]
```

**Options:**
- `--limit N` - Maximum configs to return (default: 10)
- `--include-context` - Include path to `.context.yaml` file

**Output:**
```yaml
configs:
  - reference_name: orders_hub
    config_type: hub
    config_file: local/hub/orders_hub.yaml        # Use this for analyze store
    library: null                                  # null for local, library name for external
    context_file: local/hub/orders_hub.context.yaml  # if --include-context
summary:
  total_configs: 150
  pending: 148
  completed: 2
  percent_complete: 1.3
```

Returns empty list when all configs are analyzed.

### `dxs source document analyze store`

Stores analysis for a configuration.

```bash
# From file (use config_file path from analyze next output)
dxs source document analyze store -o <output-dir> -c local/hub/orders_hub.yaml -f <analysis.yaml>

# From stdin
cat analysis.yaml | dxs source document analyze store -o <output-dir> -c local/hub/orders_hub.yaml
```

**Important:** The `-c/--config` option requires the full relative path (e.g., `local/hub/orders_hub.yaml`), not just the reference name. Use the `config_file` value from `analyze next` output.

Saves analysis as `<config>.analysis.yaml` alongside the config file and updates progress tracking.

### `dxs source document analyze status`

Shows overall analysis progress.

```bash
dxs source document analyze status -o <output-dir> [--by-type]
```

## Agent Workflow

```
1. Initialize (handles everything automatically):
   dxs source document analyze init -o ./exploration --branch 23403

2. Analysis loop:
   a. Get next configs to analyze:
      dxs source document analyze next -o ./exploration --limit 5 --include-context

   b. For each config in the returned list:
      - Read the config file (config_file path)
      - Read the context file (for structure and dependencies - dependencies are already analyzed!)
      - Perform analysis
      - Save analysis to temporary file

   c. Store analysis (use config_file path from step 2a):
      dxs source document analyze store -o ./exploration -c local/hub/orders_hub.yaml -f /tmp/analysis.yaml

3. Complete when `analyze next` returns empty configs list
```

## Context Files

The `.context.yaml` file combines structural information and dependency references in a single file:

```yaml
reference_name: cartonize_shipment_flow
config_type: flow
label: Cartonize Shipment Flow
description: Given a mandatory input of shipmentId, cartonize the shipment.
library: Cartonization
source_file: Cartonization/64146/flow/cartonize_shipment_flow.yaml
generated_at: 2024-01-05T01:23:42+00:00

# Type-specific structure
structure:
  inParams: [shipmentId]
  outParams: [reasons]

# Dependencies with library context
references:
  datasources:
    - name: ds_get_picking_tasks_by_shipmentId
      library: Cartonization
  backend_flows:
    - name: create_shipping_containers_for_shipment_flow
      library: Cartonization
  apis:
    - name: ExecuteWorkflow
      library: null
```

## Topological Ordering

Configs are processed in topological order with **leaves first**:
- Configs with no dependencies are analyzed first
- When you analyze a config, all configs it references have already been analyzed
- This allows the agent to reference previous analysis when analyzing dependent configs

The ordering requires a dependency graph, which is built from:
1. Existing `graph/dependency-graph.yaml` (if available)
2. `.context.yaml` files (generated with `--include-context` during build)

If no graph is available, configs are processed in filesystem discovery order (with a warning).

## File Structure

After running the workflow, the output directory contains:

```
<output-dir>/
├── local/<type>/<ref_name>.yaml           # Config files
├── local/<type>/<ref_name>.context.yaml   # Structure + dependency context
├── local/<type>/<ref_name>.analysis.yaml  # AI analysis (created by store)
├── <Library>/<BranchId>/<type>/           # Library configs (same structure)
├── libraries.yaml                          # Library index
├── info.yaml                               # Application info
└── graph/
    ├── dependency-graph.yaml               # Dependency graph (if built)
    └── progress.yaml                       # Analysis progress tracking
```

## Progress Tracking

The `graph/progress.yaml` file uses **file paths as keys** to uniquely identify configs:

```yaml
processing_order:
  - local/datasource/customers_ds.yaml      # Leaves first (no dependencies)
  - local/grid/customers_grid.yaml          # Depends on customers_ds
  - local/hub/orders_hub.yaml               # Depends on customers_grid
config_status:
  local/datasource/customers_ds.yaml:
    status: completed
    analysis: completed
    reference_name: customers_ds
    config_type: datasource
    library: null
    analysis_file: local/datasource/customers_ds.analysis.yaml
  local/grid/customers_grid.yaml:
    status: completed
    analysis: pending
    reference_name: customers_grid
    config_type: grid
    library: null
```

## Implementation Details

- Commands are implemented in `src/dxs/commands/document.py`
- Progress tracking uses the `DocumentProgress` class from `src/dxs/core/graph.py`
- Topological sorting uses `topological_sort()` from `src/dxs/core/graph.py`
- Context generation uses `_generate_context_data()` from `src/dxs/commands/explore.py`
- Analysis files are YAML with automatic `_metadata` injection
