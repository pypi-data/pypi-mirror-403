# Configuration

Configure defaults and preferences for `dxs`.

## Configuration Priority

Settings are resolved in this order:
1. CLI flags (highest priority)
2. Environment variables (`DXS_*`)
3. Config file (`~/.datex/config.yaml`)
4. Defaults (lowest priority)

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DXS_REPO` | Default repository ID |
| `DXS_BRANCH` | Default branch ID |
| `DXS_ORG` | Default organization |
| `DXS_FORMAT` | Output format (yaml/json/csv) |

### Example

```bash
export DXS_REPO=87
export DXS_ORG=datexCorporation

# Now these commands don't need --repo
uv run dxs source branch list --status feature
```

## Config File

Location: `~/.datex/config.yaml`

### Example Config

```yaml
# Default values
repo: 87
org: datexCorporation

# Output preferences
format: yaml
concise: false

# API settings
api_url: https://api.datexcorp.com
```

## File Locations

| File | Purpose |
|------|---------|
| `~/.datex/config.yaml` | Configuration |
| `~/.datex/credentials.yaml` | Auth tokens |
| `~/.datex/cache.sqlite` | API response cache |

## CLI Flags Override Everything

```bash
# Config says repo: 87, but flag overrides
uv run dxs source branch list --repo 100
```

## See Also

- [Authentication](./authentication.md) - Login setup
- [Output Formats](../reference/output-formats.md) - Format options
