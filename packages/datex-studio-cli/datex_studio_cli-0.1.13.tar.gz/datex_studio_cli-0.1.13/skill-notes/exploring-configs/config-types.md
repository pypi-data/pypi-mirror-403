# Configuration Types

Reference for all 28 configuration types in Datex Studio.

## UI/Display Types

| Type | Description |
|------|-------------|
| `grid` | Data grid/table component |
| `hub` | Dashboard/navigation page |
| `form` | Input form |
| `editor` | Full-page editor |
| `shell` | Application shell/layout |
| `calendar` | Calendar view |
| `list` | List component |
| `widget` | Widget component |
| `selector` | Selection component |
| `card` | Card component |
| `report` | Report view |
| `embed` | Embedded content |
| `codeeditor` | Code editor component |
| `visualization` | Chart/visualization |

## Data & Logic Types

| Type | Description |
|------|-------------|
| `datasource` | Data query/provider |
| `flow` | Backend flow/logic |
| `frontendflow` | UI flow/logic |
| `wizard` | Multi-step wizard |

## Application Types

| Type | Description |
|------|-------------|
| `localization` | Translations |
| `storage` | Storage configuration |
| `customtype` | Custom type definition |

## Backend Types

| Type | Description |
|------|-------------|
| `endpoint` | API endpoint |
| `securitypolicy` | Security rules |
| `footprintflow` | Footprint-specific flow |
| `footprintdatasource` | Footprint-specific datasource |
| `footprintworkflow` | Footprint-specific workflow |
| `backendtest` | Backend test |

## Common Patterns

### Grids
```yaml
# Grid config structure
accessModifier: public
columns: [...]
datasource: {...}
toolbar: {...}
rowActions: [...]
```

### Flows
```yaml
# Flow config structure
inParameters: [...]
outParameters: [...]
steps: [...]
```

### Forms
```yaml
# Form config structure
fields: [...]
submitFlow: {...}
cancelFlow: {...}
```

## Filtering by Type

```bash
# List only grids
uv run dxs source explore configs -b 12345 --type grid

# List only flows
uv run dxs source explore configs -b 12345 --type flow
```

## See Also

- [Listing Configs](./listing-configs.md) - Filter by type
- [Viewing Configs](./viewing-configs.md) - View content
