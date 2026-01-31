# DXS Skill Notes

Documentation for using the `dxs` CLI tool to explore and manage Datex Studio applications.

## How to Use These Notes

These notes are organized for AI agents to explore on-demand. Start with the section relevant to your task:

| Task | Start Here |
|------|------------|
| List or filter branches | [branches/](./branches/) |
| Review code changes | [code-review/](./code-review/) |
| View commit history | [source-control/commit-history.md](./source-control/commit-history.md) |
| Explore configurations | [exploring-configs/](./exploring-configs/) |
| Look up a command | [reference/command-cheatsheet.md](./reference/command-cheatsheet.md) |

## Quick Start

```bash
# All commands use this pattern
uv run dxs <command-group> <command> [options]

# Check authentication
uv run dxs auth status

# List branches in a repo
uv run dxs source branch list --repo-name "FootprintManager" --status feature

# View changes in a branch
uv run dxs source changes -b 12345 --with-diffs
```

## Sections

### [Getting Started](./getting-started/)
Authentication, configuration, and prerequisites.

### [Repositories](./repositories/)
Understanding and listing repositories (ApplicationDefinitions).

### [Branches](./branches/)
Working with branches - listing, filtering, understanding statuses.
- [Branch Statuses Reference](./branches/branch-statuses.md) - What each status means

### [Source Control](./source-control/)
Viewing changes, commit history, dependencies, and locks.
- [Viewing Changes Guide](./source-control/viewing-changes-guide.md) - Deep dive with examples

### [Exploring Configs](./exploring-configs/)
Listing and viewing configuration content.
- [Config Types Reference](./exploring-configs/config-types.md) - All 28 types

### [Code Review](./code-review/)
Workflows for reviewing commits and feature branches.
- [Review Report Template](./code-review/review-report-template.md) - Markdown format

### [DevOps Integration](./devops-integration/)
Querying Azure DevOps work items.

### [Reference](./reference/)
Quick lookups and cheatsheets.
- [Command Cheatsheet](./reference/command-cheatsheet.md) - All commands in one page

## Data Model

Understanding the Datex Studio data model:

| Term | API Name | Description |
|------|----------|-------------|
| Repository | ApplicationDefinition | A project/app containing all branches |
| Branch | Application | A working copy (feature, release, main) |
| Branch Container | ApplicationGroup | Groups branches within a repo |
| Configuration | Various types | Grid, form, flow, etc. (28 types) |

## See Also

- [Branch Statuses](./branches/branch-statuses.md) - Status types and meanings
- [Output Formats](./reference/output-formats.md) - YAML/JSON/CSV options
