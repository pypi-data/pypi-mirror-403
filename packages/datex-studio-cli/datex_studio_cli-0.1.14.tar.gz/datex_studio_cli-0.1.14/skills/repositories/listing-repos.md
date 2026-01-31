# Listing Repositories

Find and list repositories in Datex Studio.

## Command

```bash
uv run dxs source repo list [OPTIONS]
```

## Options

| Option | Description |
|--------|-------------|
| `--org <id>` | Filter by organization ID |
| `--org-name <name>` | Filter by organization name |
| `--type <type>` | Filter by application type |
| `--with-branches` | Include branch metadata |
| `--published-after <date>` | Published after date |
| `--published-before <date>` | Published before date |

## Examples

```bash
# All repositories
uv run dxs source repo list

# By organization
uv run dxs source repo list --org-name "Datex"

# Component modules only
uv run dxs source repo list --type componentmodule

# With branch info
uv run dxs source repo list --org-name "Datex" --with-branches

# Recently published
uv run dxs source repo list --published-after 2026-01-01
```

## Example Output

```yaml
repositories:
- id: 87
  name: FootprintManager
  description: Main warehouse management application
  applicationDefinitionTypeId: 1
  organizationId: 1
  organizationName: Datex
- id: 45
  name: SalesOrders
  description: Sales order management library
  applicationDefinitionTypeId: 3
  organizationId: 1
  organizationName: Datex
metadata:
  success: true
  count: 132
  organization_filter: Datex
```

## With Branches Option

```bash
uv run dxs source repo list --org-name "Datex" --with-branches --limit 2
```

Adds:
```yaml
- id: 87
  name: FootprintManager
  branches:
    total: 2106
    active: 754
    feature: 41
    lastCommit: '2026-01-14T10:22:02Z'
```

## Search

```bash
uv run dxs source repo search "Footprint"
```

Case-insensitive search across name and description.

## Large Output Handling

When listing all repositories for a large organization, the output can exceed 50KB. This may cause truncation in terminal displays.

### Strategies for Large Outputs

```bash
# 1. Check count first before full iteration
uv run dxs source repo list --org-name "Datex" --limit 1
# Look at metadata.count to see total

# 2. Save to file for processing
uv run dxs source repo list --org-name "Datex" > /tmp/repos.yaml

# 3. Use pagination for iteration
uv run dxs source repo list --org-name "Datex" --limit 50 --offset 0
uv run dxs source repo list --org-name "Datex" --limit 50 --offset 50
```

### Extracting Repository Names

When iterating through repos programmatically, extract just the names:

```yaml
# Output structure
repositories:
- id: 32
  name: Addresses      # <-- Extract this
  organization:
    name: Datex
metadata:
  count: 132           # <-- Use this to know total
```

## See Also

- [Repositories Index](./index.md) - Overview
- [Branches](../branches/) - Working with repo branches
- [Multi-Repo Review](../code-review/multi-repo-review-guide.md) - Reviewing across all repos
