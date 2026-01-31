# Dependencies

Commands for viewing and comparing dependencies.

## Commands

| Command | Description |
|---------|-------------|
| `dxs source deps -b <id>` | List dependencies |
| `dxs source deps -b <id> --tree` | Show dependency tree |
| `dxs source deps-diff --from <id> --to <id>` | Compare dependencies |
| `dxs source graph -b <id>` | Generate dependency graph |

## List Dependencies

```bash
uv run dxs source deps -b 12345
```

Shows component packages referenced by a branch.

## Dependency Tree

```bash
uv run dxs source deps -b 12345 --tree
```

Shows full transitive dependency tree (what your dependencies depend on).

## Compare Dependencies

```bash
uv run dxs source deps-diff --from 63367 --to 63379
```

Shows:
- Added dependencies
- Removed dependencies
- Updated dependencies (version changes)

Useful for release notes.

## Dependency Graph

```bash
uv run dxs source graph -b 12345
```

### Options

| Option | Description |
|--------|-------------|
| `--max-depth, -d <n>` | Max recursion depth (default: 10) |
| `--save-to, -s <path>` | Save to file |
| `--flat` | Flat list instead of tree |

### Example

```bash
# Save graph to file
uv run dxs source graph -b 63588 --save-to deps.yaml

# Flat list
uv run dxs source graph -b 100 --flat
```

## Use Cases

### Release Notes
```bash
# Find what changed between versions
uv run dxs source deps-diff --from <old_release> --to <new_release>
```

### Understanding Impact
```bash
# See what this branch depends on
uv run dxs source deps -b 12345 --tree
```

### Documentation
```bash
# Generate dependency diagram
uv run dxs source graph -b 12345 --save-to architecture.yaml
```

## See Also

- [Commit History](./commit-history.md) - Finding versions to compare
- [Exploring Configs](../exploring-configs/) - Deeper config analysis
