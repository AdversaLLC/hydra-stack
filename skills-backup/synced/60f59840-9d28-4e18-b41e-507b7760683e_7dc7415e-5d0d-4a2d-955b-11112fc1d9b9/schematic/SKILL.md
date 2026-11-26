---
name: schematic
description: "Reverse engineer a detailed product and technical specification document from a git branch's\nimplementation. Use when: (1) a branch has shipped or is in-progress and needs documentation,\n(2) you need to understand what a branch does at product and architecture level, (3) onboarding\nto someone else's feature branch, (4) creating PR descriptions or design docs after the fact,\n(5) user asks to \"analyze this branch\", \"write a spec from the code\", or \"document what this\nbranch does\". Produces a structured markdown spec covering problem statement, product requirements,\narchitecture, technical design, file inventories, testing strategy, rollout plan, and risks.\n"
metadata:
  author: "Codex"
  version: "1.0.1"
  date: "2026-10-20"
  tags:
  - "documentation"
  - "git"
  - "branch-analysis"
  - "spec"
  - "reverse-engineering"
  authored_via: "claude-science"
  published_by: "agent"
  published_at: "2026-10-22T18:10:15.228Z"
  authored_by: "agent"
  authored_at: "2026-10-22T18:10:15.216Z"
  authoring_session: "df249c20-fa50-4f4d-9ba4-14b516173576"
  last_modified_by: "agent"
  last_modified_at: "2026-10-22T18:10:15.216Z"
---

# Reverse Engineer Spec from Branch Implementation

Systematically extract a complete spec from a branch's diff: what was built, how, and (inferred) why.

## Phase 1: Scope the Branch

Get the full picture of what changed before reading any files.

```bash
# 1. Identify the base branch (usually main), then list commits
git log --oneline <base>..HEAD | head -50

# 2. File-level diff stats and total scale
git diff --stat <base>...HEAD
```

**Hitchhiker commit detection (CRITICAL)**: check whether the branch contains commits from other PRs
that were separately merged to the target branch (common on un-rebased branches). Needs the GitHub
CLI (`gh`) and an open PR; skip if either is missing.

```bash
BRANCH_NAME=$(git branch --show-current)
ALL_COMMITS=$(git log --oneline <base>..HEAD | wc -l)
PR_SHAS=$(gh pr list --head "$BRANCH_NAME" --json commits --jq '.[0].commits[].oid' 2>/dev/null)
PR_COMMIT_COUNT=$(printf '%s\n' "$PR_SHAS" | grep -c . || true)

if [ -n "$PR_SHAS" ] && [ "$PR_COMMIT_COUNT" -lt "$ALL_COMMITS" ]; then
  echo "HITCHHIKER COMMITS: $ALL_COMMITS on branch, $PR_COMMIT_COUNT in PR"
  # Files touched ONLY by PR commits
  PR_FILES=$(for sha in $PR_SHAS; do git diff-tree --no-commit-id --name-only -r "$sha"; done | sort -u)
fi
```

When hitchhikers are detected, use `git diff <base>...HEAD -- $PR_FILES` (simulates the post-rebase
diff) for all subsequent analysis and state this scoping in the output. Otherwise use the full diff.

Categorize the (scoped) files into groups:
- **Core implementation** (new modules, business logic)
- **Integration points** (modified selectors, reducers, hooks, components)
- **Tests** (unit, integration, e2e)
- **Configuration** (feature flags, env vars, types, configs)
- **Incidental** (formatting, imports, minor refactors)

## Phase 2: Parallel Deep Exploration

Launch 2-4 parallel subagents (e.g. Explore), each on a different file group — reading 50+ files
sequentially is too slow.

- **Agent 1: Core Implementation** — all new files. Focus: purpose, key types, exported functions,
  data flow, inter-module connections.
- **Agent 2: Integration Points** — modified selectors, reducers, hooks, components. Focus: what
  changed, why (inferred), how it connects to the core.
- **Agent 3: Tests** — all test files. Focus: behaviors validated, key assertions, which product
  requirements they encode.
- **Agent 4 (if needed): Configuration & Infrastructure** — flags, env vars, build configs, type
  declarations. Focus: rollout strategy, gating, deployment concerns.

Each agent reports, per file: purpose, key exports and types, data flow and dependencies, and how it
connects to the others in its group.

## Phase 3: Cross-Check for Gaps

Agents inevitably miss files. After they return, compare analyzed files against the full list:

```bash
# Full changed-file list (--stat abbreviates long paths, so use --name-only)
git diff --name-only <base>...HEAD | sort

# Show small diffs for any files not yet analyzed
git diff <base>...HEAD -- <uncovered-files>
```

Read the remaining diffs directly. They often hold important details: type declarations (new model
fields), feature flag definitions, bug fixes found during development, proxy/compatibility shims.

## Phase 4: Write the Spec Document

Save it under `docs/` in the repo (unless the user says otherwise). Use these sections, skipping any
that don't apply:

```markdown
# [Feature Name]
## Reverse-Engineered Product & Technical Specification

## 1. Problem Statement
Why this feature exists. What user/business pain it addresses.
Infer from the nature of the changes and any comments in the code.

## 2. Solution Overview
High-level description of the approach. Key design properties
(transparent, lazy, bounded, etc.).

## 3. Product Requirements
### 3.1 User-Facing Behavior
Table of requirements inferred from tests and UI changes.

### 3.2 Supported Workflows
List of workflows validated by tests.

### 3.3 Scope Boundaries
What is and isn't included.

## 4. Architecture
### 4.1 System Diagram
ASCII diagram showing component relationships and data flow.

### 4.2 Data Lifecycle
Step-by-step flow from initial state through steady state.

## 5. Technical Design
Subsections for each major design decision:
- Feature flags and gating
- Data models / schema changes
- Key algorithms or patterns
- Integration patterns (how existing code was modified)
- Cache/performance design
- Error handling and fallbacks

## 6. New Files
Table: file path, purpose (one line each).

## 7. Modified Files (Key Changes)
Table: file path, what changed (one line each).
Include ALL files — even minor ones.

## 8. Testing Strategy
### Unit Tests
### Integration / E2E Tests
### Instrumentation / Observability

## 9. Rollout Strategy
How the feature is gated, incremental rollout steps, kill switches.

## 10. Risks and Mitigations
Table: risk, mitigation.

## 11. Summary
Key metrics: files added/modified, lines changed, scope of impact.
```

Writing guidance:
- **Infer the "why"** from test assertions, comments, commit messages, and the shape of changes.
- **Don't over-document incidentals**: formatting, import reordering, and trailing commas get one
  line, not a subsection.
- **Use tables liberally** for file inventories, feature flags, and risks.

## Phase 5: Verify Completeness

1. Every file from `git diff --name-only` (scoped if needed) appears in Section 6 or 7.
2. Every test file is referenced in Section 8.
3. Feature flags mentioned in code appear in Section 5/9.
4. The architecture diagram matches the actual data flow the agents found.
5. Product requirements match what the tests actually validate; no significant design decision is
   missing from Section 5.
