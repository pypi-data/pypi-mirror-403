# Multi-Repository Code Review (Guide)

Step-by-step guide for reviewing commits across all repositories in an organization.

## When to Use

- Periodic code audits (weekly/monthly)
- Organization-wide compliance reviews
- Pre-release quality checks across the platform
- Identifying patterns across multiple repos

## Prerequisites

- Authenticated with `dxs auth login`
- Know the organization name (e.g., "Datex")
- Sufficient time - large orgs may have 100+ repos

## Overview

1. List all repositories for the organization
2. Batch repositories into manageable groups
3. Query each repo for recent commits
4. Skip repos with no recent activity
5. Review commits and generate per-repo reports
6. Consolidate into organization-wide report

## Step 1: List All Repositories

```bash
uv run dxs source repo list --org-name "Datex"
```

**Important:** Large organizations can return 50KB+ of output. The response includes:
- Repository ID, name, description
- Organization info
- `metadata.count` showing total repositories

### Handling Large Output

For organizations with many repos, the output may be truncated in display. Options:

```bash
# Save to file for processing
uv run dxs source repo list --org-name "Datex" > /tmp/repos.yaml

# Get just the count first
uv run dxs source repo list --org-name "Datex" --limit 1
# Check metadata.count in output
```

### Example Output (truncated)

```yaml
repositories:
- id: 32
  name: Addresses
  organization:
    name: Datex
- id: 418
  name: Allocations
  organization:
    name: Datex
# ... many more ...
metadata:
  count: 132
  organization_filter: Datex
```

## Step 2: Batch Repositories

For efficient processing, divide repos into batches of 40-50. This allows parallel processing without overwhelming API rate limits.

**Example batching for 132 repos:**
- Batch 1: Repos 1-44
- Batch 2: Repos 45-88
- Batch 3: Repos 89-132

## Step 3: Query Each Repo for Recent Commits

For each repository, check for commits in your target date range:

```bash
uv run dxs source branch list \
  --repo-name "FootprintManager" \
  --status history \
  --sort commit-date \
  --desc \
  --created-after 2026-01-11 \
  --limit 20
```

**Key options:**
- `--status history` - Only committed branches (not WIP)
- `--sort commit-date --desc` - Most recent first
- `--created-after YYYY-MM-DD` - Filter by when commit was made
- `--limit 20` - Reasonable limit per repo

### Date Filter Behavior

The `--created-after` filter uses the branch's `createdDate` field, which for history branches corresponds to when the commit snapshot was created. This effectively gives you "commits made after this date."

## Step 4: Skip Repos with No Activity

If a repo returns `count: 0` in the metadata, skip it. Don't create empty report files.

```yaml
# This repo has no recent commits - skip it
metadata:
  count: 0
  filtered_count: 0
```

## Step 5: Review Commits with Diffs

For repos with commits, fetch the full changes:

```bash
uv run dxs source changes -b <branch_id> --with-diffs
```

Analyze for:
- **Bugs**: Logic errors, missing null checks
- **Incomplete work**: Missing features mentioned in title
- **Code quality**: Duplication, inconsistent patterns
- **Risk**: Scope of changes, core functionality affected

## Step 6: Generate Reports

### Per-Repository Reports

Create one file per repo with commits: `./reviews/<repo-name>.md`

Use the standard [Review Report Template](./review-report-template.md).

### Consolidated Organization Report

After all repos are reviewed, consolidate into a single report:

`./reviews/org_code_review_YYYYMMDD_YYYYMMDD.md`

See [Consolidated Report Template](#consolidated-report-template) below.

---

## Parallelization Strategy

For large organizations, use parallel subagents to speed up the review:

### Recommended Approach

1. **Main agent** lists all repos and divides into batches
2. **Launch 3 subagents in parallel**, each handling one batch
3. Each subagent:
   - Iterates through its assigned repos
   - Queries for recent commits
   - Fetches diffs for commits found
   - Creates per-repo markdown reports
4. **Main agent** collates results into consolidated report

### Batch Size Guidelines

| Total Repos | Batches | Repos per Batch |
|-------------|---------|-----------------|
| < 30 | 1 | All |
| 30-90 | 2 | 15-45 |
| 90-150 | 3 | 30-50 |
| 150+ | 3-4 | 40-50 |

### Example Subagent Prompt

```
Review committed branches from the last 3 days for these repositories:
[List of repo names]

For each repo:
1. Run: uv run dxs source branch list --repo-name "<repo>" --status history --sort commit-date --desc --created-after YYYY-MM-DD --limit 20
2. For repos with commits, run: uv run dxs source changes -b <id> --with-diffs
3. Create ./reviews/<repo-name>.md with the review
4. Skip repos with no commits in range

Return a summary of which repos had commits.
```

---

## Consolidated Report Template

For organization-wide reports, use this structure:

```markdown
# Organization Code Review Report

**Review Period:** YYYY-MM-DD to YYYY-MM-DD
**Review Date:** YYYY-MM-DD
**Organization:** [Name]
**Reviewer:** Claude Code (AI-assisted)

---

## Executive Summary

Of N total repositories scanned, X had commits in the review period,
resulting in Y total commits reviewed.

### Overall Health: :green_circle: Good / :yellow_circle: Needs Attention / :red_circle: Critical

[1-2 sentence summary of findings]

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Repositories Scanned | N |
| Repositories with Activity | X (%) |
| Total Commits Reviewed | Y |
| Low Risk Commits | A (%) |
| Medium Risk Commits | B (%) |
| High Risk Commits | C (%) |

---

## Highlights & Positive Notes

[Balance the report with positive observations]

1. **[Category]**: [Description]
2. **[Category]**: [Description]

### Most Active Contributors

| Author | Commits | Focus Areas |
|--------|---------|-------------|
| Name | N | Areas |

---

## Items Requiring Attention

### High Priority

| Repository | Commit | Issue |
|------------|--------|-------|
| Repo | #ID | Description |

### Medium Priority

| Repository | Commit | Reason |
|------------|--------|--------|
| Repo | #ID | Reason |

---

## Immediate Action Items

1. **[P1]** [Action]
2. **[P2]** [Action]

---

# Individual Repository Reviews

[Include all per-repo reviews below, or reference separate files]
```

---

## Common Issues to Watch For

### Repos with Many Sync Commits

If a repo has mostly "Component Package Sync" commits, these are typically low-risk library updates. Note them but don't over-analyze.

### Cross-Repo Features

Watch for features that span multiple repos (e.g., "Divert Billing" touching AsnOrders, Invoices, and Owners). Verify consistency across all related repos.

### Navigation/UI Changes

Changes to shell configurations (removing menus, changing navigation) affect user experience. Flag for senior review.

---

## Example Workflow

```bash
# 1. Get repo count
uv run dxs source repo list --org-name "Datex" --limit 1
# Note: metadata shows 132 repos

# 2. Create output directory
mkdir -p ./reviews

# 3. Launch parallel review (conceptual - done via subagents)
# Batch 1: Addresses through Footprint Driver Checkout
# Batch 2: Footprint Ecom Api through MovuRobotics
# Batch 3: Notifications through WorkOrders

# 4. After subagents complete, consolidate
# Create ./reviews/datex_code_review_YYYYMMDD_YYYYMMDD.md
```

---

## See Also

- [Reviewing Commits Guide](./reviewing-commits-guide.md) - Single-repo workflow
- [Review Report Template](./review-report-template.md) - Per-repo format
- [Listing Repositories](../repositories/listing-repos.md) - Repo commands
