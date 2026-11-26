---
name: gleaner
description: Extract valuable content from messy folders of mixed files — code snippets, blueprints, half-written specs, designs, scattered notes — sort into clean buckets, and name every output based on what it actually contains. Triggers on "gleaner", "extract", "pull out", "sort files", "find the code", "find the blueprints", "clean up this folder", "what's valuable in here", "rename these files", "name these properly". Works on uploaded zips, individual file dumps, or whatever's in /mnt/user-data/uploads/. Naming happens inline using Claude's reading of file contents — no Ollama, no local LLM, no sentence-transformer embeddings, no persistent pattern bank between sessions.
---

# Gleaner — claude.ai Extraction

Take a messy upload and produce a clean output: the actually-valuable content sorted into named buckets, with each output file named for what it contains, not for what its source file happened to be called.

The Claude Code v3 had a SemanticNamingEngine using local Ollama, learned naming patterns persisted to disk, ABP gates, shadow clones broadcasting to a Nexus bus, and KG node emission. None of that infrastructure exists here. What survives: the **two-pass extraction discipline** (read first, then sort/name), and the bias toward content-driven naming over filename-driven naming.

---

## When to invoke

- A folder/zip was uploaded and the user wants the substance pulled out
- "What's valuable in here" — the user knows there's signal in noise but doesn't want to dig
- "Rename these to make sense" — naming task on uploaded files
- A messy chat-archive / notes-dump / scratch-folder needs cleaning

If the upload is a clean codebase, that's `codebase-navigator`'s job, not this one.

---

## Workflow

### Step 0 — Run veritas first

Before extracting, audit. Use `veritas` to log every file's status. Don't start extracting if you haven't established what's there.

### Step 1 — First pass: read everything

For every file flagged READABLE by veritas:
- Skim the content
- Tag it with a one-sentence "what this is" note
- Tag it with a category: code / spec / note / blueprint / design / data / log / image / config / unknown
- Tag with a relevance: keep / borderline / drop

Don't start writing output yet. First-pass is read-only.

### Step 2 — Second pass: extract and name

For each "keep":
- If the file is already a clean unit (a script, a doc, a single concept): copy as-is to the output folder, but with a content-driven name.
- If the file is a mixed bag (multiple concepts in one document, code + commentary, half-formed ideas): split into separate output files, one per concept.

**Naming rules:**
- Filename describes content, not source: `vector-search-cosine-impl.py`, not `script_3_FINAL_v2.py`
- Use kebab-case for general files, snake_case for code that follows snake_case convention in its language
- Include a meaningful prefix only if needed for sort order (`01-spec.md`, `02-arch.md`)
- Date prefixes only if the date is content-relevant (e.g., daily logs)
- Extension matches actual content type, not the source extension

**Naming consistency within a batch:**
Look at what naming conventions you've already used in this output run. Stay consistent. If the first three outputs are `auth-flow.md`, `auth-tokens.md`, `auth-revocation.md`, the fourth shouldn't be `password_handling.md`. Pick a convention early and hold it.

This is what the v3 SemanticNamingEngine pattern-learning was supposed to automate — but a single attentive pass through the batch by Claude does the same job for the volumes typical here (dozens of files, not thousands).

### Step 3 — Bucket sort

Group outputs into clean folders by category:

```
/mnt/user-data/outputs/gleaned-<task-tag>/
├── code/
├── specs/
├── notes/
├── blueprints/
├── designs/
├── data/
├── logs/
└── _unsorted/   (only if there's genuine ambiguity — minimize this)
```

If a category has zero items, omit the folder. Don't create empty placeholders.

### Step 4 — Index file

Write `INDEX.md` at the root of the output folder containing:

- Source: where the upload came from (zip name, etc.)
- Total files in: from veritas audit
- Total files out: from gleaning
- Drop reasons: what was dropped and why (briefly)
- Per-bucket count: how many ended up in each category
- Highlights: 3–7 of the most valuable items, with one-sentence notes

The INDEX is the user's table of contents. They'll skim it first.

### Step 5 — Present

Use `present_files` on the INDEX.md and any single most-valuable output. Don't present every output file — that's a wall. The user can navigate from the INDEX.

---

## What got stripped from v3

- **Local Ollama / Llama3 for AI semantic naming** — replaced by Claude reading content and naming inline. For typical batch sizes (under a few hundred files), this is fine. For tens of thousands of files, it isn't — but that's not the workflow here.
- **SemanticNamingEngine class with persistent pattern learning** — replaced by Step 2's "look at what conventions you've used in this batch and stay consistent". Same effect at this scale.
- **ABP gate (score ≥ 0.65 to ship a glean output)** — replaced by Step 1's keep/borderline/drop tagging. Same intent, less ritual.
- **Shadow clone verification** — replaced by Step 0 (veritas audit) plus a quick self-check at the end that no input file went unaddressed.
- **Nexus CONTEXT and COMPLETE emit** — no bus.
- **KG node generation** — no persistent KG. If a pattern emerges that's worth carrying forward, surface it to the user and offer to add to memory via `memory_user_edits`.
- **Momentum checkpoint integration** — replaced by ending-state summary in INDEX.md.
- **Privacy-first local processing claim** — claude.ai's sandbox is also reasonably private (per-session, ephemeral), but be honest: data passing through Claude's API isn't "local". If the upload is sensitive (PII, internal docs), say so to the user before proceeding.

---

## Anti-patterns

- **Naming by source file**: `script_3_FINAL_v2_actually_final.py` becomes... what? Read the script. Name it for what it does.
- **One giant output file**: don't dump 40 concepts into one `extracted.md`. Split.
- **Zero drops**: if the input was messy, drops are expected. A clean glean has 30–70% drop rate. If you "kept" everything, you didn't actually filter.
- **Inventing structure**: if the source is a single brain-dump with no internal structure, don't fabricate folders to make it look organized. Let the structure emerge from content.
- **Reading every byte for huge files**: for files over a few hundred KB, sample (head, tail, middle) and decide if a full read is justified. If yes, do it; if no, document the partial read in the INDEX.

---

## Tool reference

| Need | Tool |
|---|---|
| List uploads | `view /mnt/user-data/uploads/` or `bash_tool` ls |
| Read text files | `view`, or `bash_tool` cat / head / tail |
| Sample binary files | `bash_tool` with `file`, `strings`, `xxd` |
| Extract zips | `bash_tool` `unzip -q` to `/home/claude/extracted/` |
| Write outputs | `create_file` to `/mnt/user-data/outputs/gleaned-<tag>/...` |
| Present results | `present_files` on the INDEX and most-valuable item |
| Persist a discovered pattern (rare) | `memory_user_edits` |
