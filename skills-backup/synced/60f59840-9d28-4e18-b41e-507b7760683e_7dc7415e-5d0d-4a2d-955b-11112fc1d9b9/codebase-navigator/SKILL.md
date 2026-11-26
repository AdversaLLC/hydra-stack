---
name: codebase-navigator
description: Read, map, and understand any uploaded codebase before making changes or recommendations. Triggers when a zip/repo is uploaded and the user says "read this codebase", "understand this repo", "what is this project", "give me the lay of the land", "where does X live", or any time chatdev-vm needs codebase context before designing. Extracts file tree, language breakdown, entry points, framework/architecture indicators, key dependencies, README and docs, existing tests, build/CI configuration. Outputs a single CODEBASE.md briefing the next phase of work can build on. Single-instance, claude.ai-only — runs in the bash sandbox, writes outputs to /mnt/user-data/outputs/.
---

# Codebase Navigator — claude.ai

Take an uploaded codebase, produce a structured briefing of what it is, how it's laid out, and where the load-bearing pieces live. Nothing fancier than that. The briefing is what `chatdev-vm`, `redteam`, or just a code-review request can build on.

The Claude Code original integrated with TreeSitter MPP CodeGraph, BM25 + PageRank, Nexus emit, momentum KG handoff. Here we use the bash sandbox and read carefully.

---

## When to invoke

- A zip/folder of source code was uploaded
- "What's in this repo" / "what is this project" / "read this codebase"
- About to do anything — refactor, review, add feature — to an unfamiliar codebase
- Before chatdev-vm Phase 3 (CTO / Architecture) when the build is against existing code

Skip if the upload is a single file the user wants reviewed — just review it directly.

---

## Workflow

### Step 0 — veritas

Run veritas first on the upload. Confirm what's there, assemble any split archives, log binary skips. Don't start mapping until the audit is done.

### Step 1 — Extract and orient

```bash
mkdir -p /home/claude/repo
cd /home/claude/repo
unzip -q /mnt/user-data/uploads/<archive>.zip
# or copy unzipped contents if the user uploaded a folder structure
```

Then a fast orient pass:

```bash
# File tree, top 3 levels
find . -maxdepth 3 -not -path '*/node_modules/*' -not -path '*/.git/*' | head -100

# File counts by extension
find . -type f -not -path '*/node_modules/*' -not -path '*/.git/*' \
  | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -20

# Total size
du -sh .
```

### Step 2 — Identify entry points

Look for:
- `package.json` / `pyproject.toml` / `Cargo.toml` / `go.mod` / `pom.xml` / `Gemfile` / `mix.exs` — what is this project ecosystem-wise
- `main.{py,go,rs,c,cpp}` / `index.{ts,js}` / `app.{py,rb,ex}` / `cmd/` directories — where does execution start
- `Dockerfile` / `docker-compose.yml` / `Makefile` / `justfile` — how does it build and run
- `.github/workflows/` / `.gitlab-ci.yml` / `.circleci/` — CI configuration
- `README*` / `CONTRIBUTING*` / `docs/` — what does the project say about itself

For each entry point file found: read it. Don't guess what it does from the filename.

### Step 3 — Architecture indicators

Common signals to surface in the briefing:

- **Frameworks**: Next.js (look for `next.config.*`), Django (`manage.py`, `settings.py`), Rails (`config/application.rb`), Flask (`app.py` + Flask import), Spring (`application.yml`), Express (Express in package.json), Actix (Cargo deps), gin/echo/fiber (Go imports), etc.
- **Database**: schema files, migrations directory, ORM config
- **API style**: REST controllers, GraphQL schemas, gRPC `.proto` files, OpenAPI specs
- **Auth**: passport / NextAuth / Devise / Firebase / Auth0 / custom
- **State management** (frontend): Redux store, Zustand, Pinia, Context patterns
- **Testing**: pytest / vitest / jest / cargo test / go test — what's in the repo
- **Infrastructure as code**: Terraform, Pulumi, Helm charts, Ansible
- **Patterns**: monorepo (Nx, Turborepo, pnpm workspaces, Lerna) vs single-package, clean architecture vs MVC vs flat

Don't list every observation. Pick the 5–10 that matter most for the project's identity.

### Step 4 — Read the load-bearing files

The README, the entry-point files, the central config, the most-imported module, the longest test file. These tell you the project's actual character. Read them, not just glance.

If the project has a `docs/` directory: read the table of contents, then the architecture-style docs (anything called `architecture.md`, `design.md`, `overview.md`, `ADR/`).

### Step 5 — Write CODEBASE.md

Produce a single briefing file at `/mnt/user-data/outputs/codebase-briefing/CODEBASE.md` with this structure:

```
# <Project name>

**One-line description**: <what this project IS, in plain English>

## Stack
- Language(s): ...
- Framework: ...
- Database: ...
- Key dependencies: ...
- Build/run: ...
- Tests: ...

## Layout
<top-level directory tree, annotated with what each top-level dir contains>

## Entry points
- <file>: <what runs when this is invoked>
- <file>: <...>

## Load-bearing files (the ones to read first when changing anything)
- <path>: <why this matters>
- <path>: <...>

## What surprised me
<2–4 observations that aren't obvious from the file tree — e.g., "auth is hand-rolled, not using a library", "tests are skipped in CI", "uses an undocumented internal package called X">

## Open questions
<things I couldn't determine from reading — e.g., "where the deployment target is", "whether this fork has diverged from upstream">

## Suggested entry point for further work
<if the user said what they want to do, point them to where to start>
```

### Step 6 — Present

`present_files` on `CODEBASE.md`. That's the deliverable.

---

## What got stripped from v2

- **TreeSitter / MPP CodeGraph** — bash sandbox can install tree-sitter Python bindings, but the value-add over careful reading isn't worth the install time for typical codebase sizes here. Skip unless a specific tree-walk is needed.
- **BM25 + PageRank ranking of files** — replaced by "read the README, entry points, load-bearing files" judgment. PageRank is for when you can't read; we can read.
- **Nexus COMPLETE emit** — no bus.
- **Gleaner handoff** — Gleaner is a separate skill; if applicable, the user invokes it separately. No automatic handoff.
- **Page-by-page chunking for huge codebases** — for codebases that genuinely are too large to read in one session (>10K files, multi-million LOC), say so plainly and walk a subset. Don't pretend to have read what you haven't.
- **chatdev-vm CTO auto-feed** — if `chatdev-vm` is invoked next, that workflow reads `CODEBASE.md` itself; no auto-pipe needed.

---

## Anti-patterns

- **Filename-based architecture claims**: don't say "looks like Clean Architecture" because there's a `domain/` folder. Read what's in it.
- **Dependency-list-as-summary**: pasting the package.json content isn't a briefing.
- **Skipping the README**: even bad READMEs disclose the project's intent.
- **Overlong CODEBASE.md**: aim for 1 page (~80 lines). If you need more, break out a separate `LAYOUT.md` and link from CODEBASE.md.

---

## Tool reference

| Need | Tool |
|---|---|
| Audit upload | `veritas` skill |
| Extract archive | `bash_tool` `unzip -q` to `/home/claude/repo` |
| Walk file tree | `bash_tool` find/ls/du, or `view` on directories |
| Read individual files | `view`, with `view_range` for long files |
| Detect language counts | `bash_tool` find + sed + sort + uniq |
| Visualize architecture | `visualize:show_widget` (diagram module) — only if the layout genuinely benefits from a diagram |
| Persist project context across sessions | `memory_user_edits` to add a one-liner if Joshua's going to keep working on this repo |
| Present briefing | `present_files` on `CODEBASE.md` |
