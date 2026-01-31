# Repositories

Working with repositories (ApplicationDefinitions) in Datex Studio.

## What is a Repository?

A **repository** (internally `ApplicationDefinition`) is a project or application that contains all branches and configurations. Think of it as a Git repository equivalent.

## Commands

| Command | Description |
|---------|-------------|
| `dxs source repo list` | List repositories |
| `dxs source repo show <id>` | Show repo details |
| `dxs source repo search "query"` | Search by name |

## Listing Repositories

```bash
# All repos
uv run dxs source repo list

# By organization
uv run dxs source repo list --org-name "Datex"

# By type
uv run dxs source repo list --type componentmodule

# With branch info
uv run dxs source repo list --with-branches
```

### Options

| Option | Description |
|--------|-------------|
| `--org <id>` | Filter by org ID |
| `--org-name <name>` | Filter by org name |
| `--type <type>` | Filter by app type |
| `--with-branches` | Include branch metadata |
| `--published-after` | Filter by publish date |

### Application Types

| Type | Description |
|------|-------------|
| `web` | Web applications |
| `mobile` | Mobile applications |
| `componentmodule` | Reusable components |
| `api` | Backend APIs |
| `portal` | Portal applications |

## Search Repositories

```bash
uv run dxs source repo search "FootPrint" --org-name "Datex"
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
metadata:
  success: true
  count: 1
```

## Data Model

```
Organization
    │
    └── Repository (ApplicationDefinition)
            │
            └── Branch Container (ApplicationGroup)
                    │
                    └── Branches (Applications)
```

## See Also

- [Branches](../branches/) - Working with branches
- [Listing Repos](./listing-repos.md) - More examples
