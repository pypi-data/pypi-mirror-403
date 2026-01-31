# Getting Started

Setup and prerequisites for using `dxs`.

## In This Section

| Document | Description |
|----------|-------------|
| [Authentication](./authentication.md) | Login, logout, status |
| [Configuration](./configuration.md) | Config files, env vars |

## Quick Start

```bash
# 1. Authenticate
uv run dxs auth login

# 2. Verify authentication
uv run dxs auth status

# 3. Start exploring
uv run dxs source repo list --org-name "Datex"
```

## Prerequisites

- Python 3.10+
- `uv` package manager
- Azure Entra credentials (for your organization)

## Installation

The `dxs` CLI is part of the `datex-studio-cli` package:

```bash
# Clone the repo
git clone <repo-url>
cd datex-studio-cli

# Install with uv
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Or run directly
uv run dxs --help
```

## Running Commands

All commands use this pattern:

```bash
uv run dxs <command-group> <command> [options]
```

Examples:
```bash
uv run dxs auth status
uv run dxs source branch list --repo 10
uv run dxs source changes -b 12345 --with-diffs
```

## Next Steps

1. [Authenticate](./authentication.md) with Azure Entra
2. [Configure](./configuration.md) defaults (optional)
3. Start [exploring branches](../branches/)

## See Also

- [Command Cheatsheet](../reference/command-cheatsheet.md) - All commands
- [Output Formats](../reference/output-formats.md) - Format options
