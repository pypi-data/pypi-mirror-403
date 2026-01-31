# Listing Configurations

List all configurations in a branch.

## Command

```bash
uv run dxs source explore configs -b <branch_id> [OPTIONS]
```

## Options

| Option | Description |
|--------|-------------|
| `-b, --branch <id>` | Branch ID (required) |
| `-t, --type <type>` | Filter by config type |
| `-s, --search <text>` | Search by name/label |
| `-n, --limit <num>` | Limit results |
| `--owned-only` | Only local configs |

## Examples

```bash
# All configs
uv run dxs source explore configs -b 12345

# Only grids
uv run dxs source explore configs -b 12345 --type grid

# Search by name
uv run dxs source explore configs -b 12345 --search "user"

# Only configs owned by this branch
uv run dxs source explore configs -b 12345 --owned-only
```

## Example Output

```yaml
configurations:
- referenceName: order_list_grid
  label: Orders
  configurationTypeId: grid
  accessModifier: public
  isOwned: true
- referenceName: order_editor
  label: Order Editor
  configurationTypeId: editor
  accessModifier: public
  isOwned: true
metadata:
  success: true
  count: 156
  by_type:
    grid: 45
    form: 23
    flow: 67
    editor: 12
    hub: 9
```

## Use Cases

### Find All Grids
```bash
uv run dxs source explore configs -b 12345 --type grid
```

### Find Changed Configs
```bash
# First get changes
uv run dxs source changes -b 12345

# Then explore specific ones
uv run dxs source explore config <config_name> -b 12345
```

## See Also

- [Viewing Configs](./viewing-configs.md) - View content
- [Config Types](./config-types.md) - Type reference
