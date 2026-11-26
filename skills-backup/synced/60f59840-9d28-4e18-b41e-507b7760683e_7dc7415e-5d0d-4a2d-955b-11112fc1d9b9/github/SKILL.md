---
name: github
description: GitHub workflows in claude.ai — PR creation and review, issue triage, multi-repo coordination, project board automation, release orchestration, and GitHub Actions CI/CD design. Triggers on "create PR", "review this PR", "label these issues", "set up CI", "release process", "GitHub Actions", "multi-repo", "project board", "PR template", "release notes". Produces gh CLI command sequences, Actions YAML, PR/issue/release templates, and review checklists the user runs in their actual GitHub environment. Single-instance, no claude-flow swarm; the bash sandbox can install the `gh` CLI for demos but auth-requiring operations are designed for the user to run on their own machine.
---

# GitHub — claude.ai

Six original `github-*` skills consolidated. The work splits cleanly into **design** (claude.ai produces YAML, scripts, templates, checklists) and **execute** (the user runs `gh` / `git` / clicks through GitHub UI on their own auth). claude.ai does design competently; execute happens on the user's machine because that's where the GitHub auth and the repo live.

The Claude Code originals routed everything through `npx claude-flow github ...` with swarm-coordinated agents. claude.ai has no swarm. What survives is the *patterns* — PR review checklists, multi-repo strategies, release orchestration logic — produced as artifacts the user deploys.

---

## Routing by request type

| Request | Output |
|---|---|
| Create a PR | `gh pr create` command + body markdown ready to paste |
| Review a PR | review checklist + (if URL given) fetched diff with annotated findings |
| Triage / label issues | labeling rules + `gh issue` script that applies them |
| Set up CI | `.github/workflows/*.yml` files |
| Release process | release notes draft + `gh release create` command + Actions release workflow |
| Multi-repo coordination | shared workflow file for `.github/workflows/` + dispatch action |
| Project board automation | Projects v2 GraphQL queries + automation rules |
| PR template / issue template | `.github/PULL_REQUEST_TEMPLATE.md` / `.github/ISSUE_TEMPLATE/*.yml` |
| Branch protection / repo settings | `gh api` calls or Terraform config |

---

## Tools claude.ai actually has

- **`gh` CLI** — installable in bash sandbox: `sudo apt-get install -y gh` (or download binary). Auth requires `gh auth login` with a token; the sandbox has none, so live `gh` calls only work for *unauthenticated* read operations on public repos. For auth'd operations: produce the command, user runs locally.
- **`web_fetch`** — fetches public GitHub pages: PR diffs (`/pulls/N.diff`), file content (`raw.githubusercontent.com`), issue text, release pages, Actions run logs (if public).
- **`bash_tool`** — produce and validate Actions YAML, lint with `actionlint` if installed.
- **No GitHub MCP connector** in your current setup. If one gets added later, route through it instead of asking the user to paste.

---

## Design workflows

### Creating a PR

When the user says "create a PR for this":

1. Determine: branch name, target branch, title, body content
2. Produce a paste-ready block:

```
**Run this in your repo:**
```bash
git checkout -b <branch-name>
git add .
git commit -m "<conventional commit message>"
git push -u origin <branch-name>
gh pr create \
  --title "<title>" \
  --body-file - <<'EOF'
## Summary
<what changed and why>

## Changes
- <bullet>
- <bullet>

## Testing
<how it was verified>

## Related
- Closes #<issue>
EOF
```

3. If the user gives the PR URL after pushing, `web_fetch` it to confirm and offer follow-up (request reviewers, link issues, set merge method).

### Reviewing a PR

When given a PR URL:

1. `web_fetch` the `.diff` URL (e.g., `https://github.com/owner/repo/pull/N.diff`)
2. Read the diff carefully — files changed, lines added/removed, semantic intent
3. Apply review checklist:
   - **Correctness**: does it do what the title claims? Edge cases?
   - **Security**: input validation, auth checks, secret handling, SQL/cmd injection
   - **Performance**: obvious O(n²)/N+1, memory leaks, blocking I/O on hot paths
   - **Tests**: are there tests? Do they actually exercise the change? Skipped/flaky?
   - **API stability**: breaking changes for consumers? Deprecation path?
   - **Code style**: matches repo conventions (read a few neighboring files to check)
   - **Docs**: changelog, README, inline docs updated where they should be
4. Produce a structured review:

```
## PR Review: <title>

### Blockers
- [file:line] <issue>

### Suggestions
- [file:line] <suggestion>

### Nits
- [file:line] <nit>

### Questions
- <question for the author>

### Overall
<1-2 sentence summary: approve / request changes / comment>
```

5. Optionally produce the `gh pr review` command:
```bash
gh pr review <num> --request-changes -b "<body>"   # or --approve / --comment
```

### Triaging issues

Given a list of issues (paste or `gh issue list` output):

1. Group by topic (bug / feature / question / docs / discussion)
2. For each, propose: label, milestone, assignee, priority
3. Produce a `gh issue edit` script:
```bash
gh issue edit 123 --add-label "bug,priority:high"
gh issue edit 124 --add-label "enhancement" --milestone "v2.0"
# ...
```

---

## CI / GitHub Actions design

When the user wants a workflow set up, produce the actual `.github/workflows/<name>.yml` file as an artifact.

### Patterns

**On-PR test/lint:**
```yaml
name: CI
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-<lang>@v5
        with:
          <lang>-version: '<version>'
      - run: <install>
      - run: <test>
```

**Scheduled job:**
```yaml
on:
  schedule:
    - cron: '0 9 * * 1'  # Monday 9am UTC
  workflow_dispatch:    # also allow manual trigger
```

**Multi-OS / multi-version matrix:**
```yaml
strategy:
  fail-fast: false
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
    version: ['18', '20', '22']
```

**Reusable workflow** (for multi-repo consistency):
```yaml
# .github/workflows/reusable-ci.yml
on:
  workflow_call:
    inputs:
      lang-version: { type: string, required: true }
# ... jobs
```

Caller in another repo:
```yaml
jobs:
  test:
    uses: org/shared-workflows/.github/workflows/reusable-ci.yml@main
    with:
      lang-version: '20'
```

### Validation

Before shipping the YAML, check it:
- Indentation (Actions YAML is whitespace-sensitive)
- Action versions pinned (avoid `@main`/`@latest` for security)
- Secrets referenced exist (`${{ secrets.X }}` — note in the deliverable which secrets the user needs to set)
- `permissions:` scoped narrowly (default to `contents: read` and add as needed)

If `actionlint` is installed in the sandbox, run it against the YAML before delivering:
```bash
actionlint .github/workflows/ci.yml
```

---

## Multi-repo coordination

Patterns for working across N repos:

- **Shared workflows**: one `org/shared-workflows` repo with reusable `.yml`; all other repos call them via `uses: org/shared-workflows/.github/workflows/X.yml@main`
- **Dependabot config sharing**: `.github/dependabot.yml` template stored centrally, copied per repo (or generated by a sync action)
- **Release coordination**: a coordinator workflow that triggers downstream releases via `gh workflow run` or `repository_dispatch`
- **Issue triage across repos**: a project (Projects v2) that pulls issues from multiple repos; queries via `gh project item-list`

For "do thing X across all my repos": produce a bash script using `gh repo list` + a per-repo loop:
```bash
gh repo list <org> --limit 100 --json name -q '.[].name' | while read repo; do
  echo "=== $repo ==="
  gh api repos/<org>/$repo/branches/main/protection --method PUT --input protection.json
done
```

---

## Release orchestration

A typical release flow:

1. **Bump version** — update package manifest, CHANGELOG, commit
2. **Tag** — `git tag vX.Y.Z && git push origin vX.Y.Z`
3. **Release workflow fires** — Actions builds artifacts, runs smoke tests
4. **Create release** — `gh release create vX.Y.Z --notes-file notes.md` or via Action
5. **Notify** — Slack/Discord webhook, mailing list, etc.

Produce the release Actions workflow that does steps 3–5 automatically on tag push:

```yaml
name: Release
on:
  push:
    tags: ['v*']

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - run: <build artifacts>
      - uses: softprops/action-gh-release@v2
        with:
          files: dist/*
          generate_release_notes: true
```

For changelog generation, options include `conventional-changelog`, `git-cliff`, or hand-curated. For semver bumping, `release-please` or `semantic-release` if the user wants automation.

---

## Project boards (Projects v2)

Projects v2 is GraphQL-only. Produce queries the user runs:

```bash
# List items in a project
gh api graphql -f query='
  query($org: String!, $number: Int!) {
    organization(login: $org) {
      projectV2(number: $number) {
        items(first: 50) {
          nodes { id content { ... on Issue { title number } } }
        }
      }
    }
  }
' -f org="<org>" -F number=<num>
```

For automation rules within a project, use the Projects UI workflow rules (auto-add issues from repo, auto-archive when closed, etc.). Most workflows fit those built-ins; only drop to GraphQL when they don't.

---

## What got stripped from the originals

- **`npx claude-flow github ...` commands** — claude-flow is dead; replaced by `gh` CLI + Actions YAML
- **AI swarm coordination** for review/triage/release — replaced by sequential structured work in claude.ai
- **MCP `github_*` tool calls** — no GitHub MCP connected in this setup; produce paste-ready commands instead
- **6 separate skills** — consolidated to 1 because claude.ai's router benefits from broader skills
- **`agentic-flow` integration** — dead

---

## Anti-patterns

- **Live auth'd `gh` calls in the sandbox**: the sandbox has no GitHub auth. Don't try `gh pr create` in bash and pretend it worked. Produce the command for the user to run.
- **Pinning Actions to `@main` or `@v1`**: `@main` is unauditable; `@v1` is a moving major-version tag. Pin to a specific SHA or full version (`@v4.2.2`) for security.
- **Over-broad `permissions:`**: many examples in the wild use full-write defaults. Scope to minimum required.
- **Reviewing the diff without reading neighbors**: a change might match its file's local style but break a convention used elsewhere. Spot-check.
- **Generated release notes verbatim**: `generate_release_notes: true` produces serviceable but generic text. For a public release, hand-curate the highlights.

---

## Tool reference

| Need | Tool |
|---|---|
| Public PR diff / file / issue | `web_fetch` on github.com URL |
| `gh` CLI demo (no auth) | `bash_tool`: `sudo apt-get install -y gh; gh ...` |
| YAML lint | `bash_tool`: install `actionlint` |
| Produce workflow file | `create_file` to `/mnt/user-data/outputs/` |
| Visualize release pipeline | `visualize:show_widget` (diagram) |
| Save patterns persistently | `memory_user_edits` for "user uses X repo, Y release cadence" facts |
| Hand off paste-ready commands | format as code blocks in chat; if multi-step, save script to outputs and `present_files` |
