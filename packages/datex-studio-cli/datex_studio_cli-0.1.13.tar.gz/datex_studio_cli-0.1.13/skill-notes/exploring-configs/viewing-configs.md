# Viewing Configurations

View configuration content and structure.

## Commands

| Command | Description |
|---------|-------------|
| `explore config <name>` | Full JSON content |
| `explore summary <name>` | Structural summary |
| `explore trace <name>` | Dependencies |

## View Full Config

```bash
uv run dxs source explore config order_list_grid -b 12345
```

Returns the complete JSON configuration.

### Options

| Option | Description |
|--------|-------------|
| `-b, --branch <id>` | Branch ID |
| `-t, --type <type>` | Config type (speeds lookup) |
| `--raw` | Only JSON, no metadata |

### Example

```bash
# With type hint (faster)
uv run dxs source explore config userGrid -b 12345 --type grid

# Raw JSON only
uv run dxs source explore config userGrid -b 12345 --raw
```

## View Summary

```bash
uv run dxs source explore summary order_list_grid -b 12345
```

Extracts key structural elements based on type:
- **grid**: datasource, columns, toolbar, row actions
- **form**: fields, submit/cancel flows
- **flow**: parameters, called flows/datasources
- **hub**: linked pages

## Trace Dependencies

```bash
uv run dxs source explore trace order_list_grid -b 12345
```

Shows what this config references:
- Datasources
- Flows
- Other configs

## When to Use What

| Need | Command |
|------|---------|
| Quick overview | `summary` |
| Full details | `config` |
| What it calls | `trace` |
| For code review | `config` with diff |

## See Also

- [Config Types](./config-types.md) - Type reference
- [Viewing Changes](../source-control/viewing-changes.md) - Compare versions
