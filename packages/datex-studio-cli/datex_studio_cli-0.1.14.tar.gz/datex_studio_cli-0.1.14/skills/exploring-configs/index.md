# Exploring Configurations

Commands for viewing and analyzing configuration content.

## In This Section

| Document | Description |
|----------|-------------|
| [Listing Configs](./listing-configs.md) | List configs in a branch |
| [Viewing Configs](./viewing-configs.md) | View config content |
| [Config Types](./config-types.md) | Reference for 28 types |

## Quick Start

```bash
# List all configs in a branch
uv run dxs source explore configs -b 12345

# Filter by type
uv run dxs source explore configs -b 12345 --type grid

# View specific config
uv run dxs source explore config userGrid -b 12345

# Get config summary
uv run dxs source explore summary userGrid -b 12345
```

## Commands Overview

| Command | Description |
|---------|-------------|
| `explore info` | Branch overview |
| `explore configs` | List all configurations |
| `explore config <name>` | View config content |
| `explore summary <name>` | Structural summary |
| `explore trace <name>` | Trace dependencies |
| `explore graph` | Generate dep graph |

## When to Use

| Goal | Command |
|------|---------|
| What configs exist? | `explore configs` |
| What does this do? | `explore summary` |
| Full config JSON | `explore config` |
| What does this depend on? | `explore trace` |

## See Also

- [Viewing Changes](../source-control/viewing-changes.md) - Compare versions
- [Code Review](../code-review/) - Review workflows
