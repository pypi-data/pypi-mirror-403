# Code Review Report Template

Markdown template for documenting code review findings.

## Template

```markdown
# Code Review Summary: [N] Most Recent Commits

**Review Date:** YYYY-MM-DD
**Repository:** [Repository Name]
**Reviewer:** [Name or AI-assisted]

---

## Commit 1: #[ID] - [Commit Title]

**Author:** [Name] | **Date:** [Date]

### Changes

- **N config changes** in [Repository]
- [List of changed configs with brief descriptions]

### Bugs Found

1. **[Bug Name]**: [Description of the issue]

### Assessment

| Category | Rating |
|----------|--------|
| Bug Risk | :green_circle: Low / :yellow_circle: Medium / :red_circle: High |
| Code Quality | :green_circle: Good / :yellow_circle: Medium / :red_circle: Poor |
| Senior Review | :white_check_mark: Yes / :x: No |

### Senior Review Guidance (if needed)

- [Priority area 1 to focus on]
- [Priority area 2 to focus on]

---

## Commit 2: #[ID] - [Commit Title]

[Repeat structure for each commit...]

---

## Summary Table

| Commit | Author | Risk | Quality | Senior Review? |
|--------|--------|------|---------|----------------|
| [ID] | [Name] | :green_circle: Low | :green_circle: Good | :x: No |
| [ID] | [Name] | :yellow_circle: Medium | :yellow_circle: Medium | :white_check_mark: Yes |

---

## Immediate Action Items

1. [Action item 1]
2. [Action item 2]
```

## Rating Guide

### Bug Risk

| Rating | Criteria |
|--------|----------|
| :green_circle: Low | No bugs found, minor changes, sync-only |
| :yellow_circle: Medium | Potential issues, incomplete implementation |
| :red_circle: High | Clear bugs, security concerns, data loss risk |

### Code Quality

| Rating | Criteria |
|--------|----------|
| :green_circle: Good | Clean code, follows patterns, complete |
| :yellow_circle: Medium | Some duplication, minor issues |
| :red_circle: Poor | Significant issues, needs refactoring |

### Senior Review Needed

| When | Reason |
|------|--------|
| :white_check_mark: Yes | Complex logic, architectural changes, unclear intent |
| :x: No | Simple changes, sync commits, straightforward fixes |

## Example Filled Template

```markdown
# Code Review Summary: 5 Most Recent Commits

**Review Date:** 2026-01-14
**Repository:** FootprintManager
**Reviewer:** Claude Code (AI-assisted)

---

## Commit 1: #65327 - Auto email attachments overwritten on save

**Author:** Evelin Velikov | **Date:** Today 10:22 AM

### Changes

- **0 config changes** in FootprintManager
- Updated reference to `Notifications` library (v20260105 → v20260114)

### Assessment

| Category | Rating |
|----------|--------|
| Bug Risk | :green_circle: Low |
| Code Quality | N/A (sync only) |
| Senior Review | :x: No |

### Notes

Sync commit - actual bug fix is in the Notifications component package.

---

## Commit 2: #65320 - Add owner lookup to inbound and outbound grids

**Author:** Derek Armanious | **Date:** Yesterday 11:59 PM

### Changes

- **1 config change**: `outbound_orders_grid`
  - Added new "Owner" column
  - Changed `agGrid: false` → `agGrid: true`
  - Removed project display formatting code

### Bugs Found

1. **Missing Inbound Grid**: Title says "inbound and outbound" but only outbound was changed
2. **Deleted Code**: Project formatting logic was removed - was this intentional?

### Assessment

| Category | Rating |
|----------|--------|
| Bug Risk | :yellow_circle: Medium |
| Code Quality | :yellow_circle: Incomplete |
| Senior Review | :white_check_mark: Yes |

### Senior Review Guidance

- Verify if inbound grid change was intentionally omitted
- Confirm project display removal was intentional
- Test `agGrid: true` doesn't break existing functionality

---

## Summary Table

| Commit | Author | Risk | Quality | Senior Review? |
|--------|--------|------|---------|----------------|
| 65327 | Evelin | :green_circle: Low | N/A | :x: No |
| 65320 | Derek | :yellow_circle: Medium | :yellow_circle: Incomplete | :white_check_mark: Yes |

---

## Immediate Action Items

1. Clarify with Derek if inbound grid was forgotten
2. Schedule senior review for commit 65320
```

## Usage Tips

1. **Be specific** - Include config names and exact issues
2. **Be actionable** - Senior review guidance should be prioritized
3. **Be fair** - Sync commits are low-effort, don't over-analyze
4. **Be consistent** - Use same format for all reviews

---

## Consolidated Report Template (Multi-Repo)

For organization-wide reviews covering multiple repositories, use this extended format:

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

### Overall Health: :green_circle: Good

[1-2 sentence summary]

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Repositories Scanned | 132 |
| Repositories with Activity | 19 (14%) |
| Total Commits Reviewed | 47 |
| Low Risk Commits | 39 (83%) |
| Medium Risk Commits | 8 (17%) |
| High Risk Commits | 0 (0%) |

### Commit Distribution by Type

| Type | Count | Percentage |
|------|-------|------------|
| Component Sync | 24 | 51% |
| Bug Fixes | 9 | 19% |
| New Features | 11 | 23% |
| Refactoring | 3 | 6% |

---

## Highlights & Positive Notes

[Balance the report - include positive observations]

1. **Strong Development Practices**: [Example]
2. **Active Maintenance**: [Example]

### Most Active Contributors

| Author | Commits | Focus Areas |
|--------|---------|-------------|
| Name | 9 | Entity Import, Bug Fixes |

---

## Items Requiring Attention

### High Priority (Potential Bugs)

| Repository | Commit | Issue | Assigned |
|------------|--------|-------|----------|
| **Waves** | #65092 | Config reference bug | Mitch |

### Medium Priority (Senior Review)

| Repository | Commit | Reason |
|------------|--------|--------|
| **FootprintManager** | #65118 | Navigation removal |

---

## Immediate Action Items

1. **[P1]** Fix Waves config reference
2. **[P2]** Verify navigation removal intentional

---

# Individual Repository Reviews

[Include all per-repo reviews below using the standard template]
```

### When to Use Consolidated Format

- Periodic org-wide audits (weekly/monthly)
- Pre-release quality gates
- Compliance reviews
- Management reporting

### Key Additions vs Single-Repo Template

| Section | Purpose |
|---------|---------|
| Executive Summary | High-level health assessment |
| Key Metrics | Quantitative overview |
| Highlights | Balance negative findings |
| Priority Tiers | Organize action items |

## See Also

- [Reviewing Commits Guide](./reviewing-commits-guide.md) - Full workflow
- [Multi-Repository Review](./multi-repo-review-guide.md) - Org-wide process
- [Viewing Changes Guide](../source-control/viewing-changes-guide.md) - Understanding diffs
