# Output Formats

Control how `dxs` commands display their results.

## Format Options

| Option | Description | Best For |
|--------|-------------|----------|
| `--format yaml` | YAML output (default) | LLM consumption, readability |
| `--format json` | JSON output | Programmatic parsing |
| `--format csv` | CSV output | Spreadsheet export, lists |
| `--concise` | Strip null values | Reduce token usage |

## YAML Output (Default)

Best for LLM agents - readable and token-efficient.

```bash
uv run dxs source branch list --repo 10 --limit 2
```

```yaml
branches:
- id: 65327
  applicationStatusId: 4
  commitTitle: '[Bugfix] Auto email attachments'
  authorDisplayName: Evelin Velikov
  statusName: WorkspaceHistory
  isCommit: true
- id: 65320
  applicationStatusId: 4
  commitTitle: 'Add owner lookup to grids'
  authorDisplayName: Derek Armanious
  statusName: WorkspaceHistory
  isCommit: true
metadata:
  timestamp: '2026-01-14T19:21:32.362734Z'
  cli_version: 0.1.0
  success: true
  count: 2
```

## JSON Output

For programmatic parsing or piping to tools like `jq`.

```bash
uv run dxs source branch list --repo 10 --limit 1 --format json
```

```json
{
  "branches": [
    {
      "id": 65327,
      "applicationStatusId": 4,
      "commitTitle": "[Bugfix] Auto email attachments",
      "authorDisplayName": "Evelin Velikov"
    }
  ],
  "metadata": {
    "timestamp": "2026-01-14T19:21:32.362734Z",
    "success": true,
    "count": 1
  }
}
```

## CSV Output

For list commands when you need spreadsheet-compatible output.

```bash
uv run dxs source branch list --repo 10 --limit 2 --format csv
```

```csv
id,applicationStatusId,commitTitle,authorDisplayName
65327,4,"[Bugfix] Auto email attachments",Evelin Velikov
65320,4,"Add owner lookup to grids",Derek Armanious
```

## Concise Mode

Strips null values and verbose author fields to reduce token usage.

```bash
uv run dxs source branch list --repo 10 --limit 1 --concise
```

**Before (without --concise):**
```yaml
branches:
- id: 65327
  applicationStatusId: 4
  commitTitle: '[Bugfix] Auto email attachments'
  commitDescription: null
  authorDisplayName: Evelin Velikov
  authorExternalId: ba0d1eb4-7628-4b62-a3f0-2a724db9f0e2
  buildStatus: none
  someOtherField: null
```

**After (with --concise):**
```yaml
branches:
- id: 65327
  applicationStatusId: 4
  commitTitle: '[Bugfix] Auto email attachments'
  authorDisplayName: Evelin Velikov
  buildStatus: none
```

## Response Envelope

All commands return a standardized envelope:

```yaml
<data_key>:          # Command-specific data (branches, configurations, etc.)
  - ...
metadata:
  timestamp: ISO-8601 datetime
  cli_version: version string
  success: true/false
  count: number of items
  # Additional command-specific metadata
```

### Error Response

```yaml
success: false
code: "DXS-API-001"
message: "Human-readable error message"
suggestions:
  - "Try this instead"
  - "Check that X is configured"
```

## Tips for LLM Agents

1. **Use default YAML** - Most readable, best token efficiency
2. **Add `--concise`** - When you only need key fields
3. **Use `--format json`** - When you need to parse with code
4. **Check `metadata.success`** - Always verify command succeeded

## See Also

- [Command Cheatsheet](./command-cheatsheet.md)
