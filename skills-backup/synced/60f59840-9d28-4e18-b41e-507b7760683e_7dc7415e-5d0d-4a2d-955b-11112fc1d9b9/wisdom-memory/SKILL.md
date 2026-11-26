---
name: wisdom-memory
description: Persistence layer for the hydra suite - the Wisdom Bank made real. Stores and retrieves insights, failed paths, decisions, RETROs, and meta-params across sessions using a tiered backend - Tier 1 claude-mem (github.com/thedotmack/claude-mem) when installed in Claude Code, using its automatic hooks and 3-layer mem-search workflow (search index, timeline, get_observations for filtered IDs only); Tier 2 a local RAG file at .hydra/wisdom.jsonl with the bundled stdlib-only scripts/wisdom.py (add, search with tf-idf scoring, stats) for any environment with a persistent disk; Tier 3 claude.ai memory plus resumption briefs when no disk persists. Triggers on "remember this", "save this insight", "what did we learn about X", "have we solved this before", "search memory", "wisdom bank", "recall", "load context", session starts on ongoing projects, and automatically when orchestrator or swarm jobs emit WISDOM or RETRO blocks. Pairs with modulated-loop-orchestrator, hydra-swarm, and nested-learning.
metadata:
  authored_via: "claude-science"
  published_by: "agent"
  published_at: "2026-10-22T18:10:08.702Z"
  authored_by: "unknown"
  last_modified_by: "agent"
  last_modified_at: "2026-10-22T18:10:08.695Z"
---

# Wisdom Memory — the persistence layer

Wisdom that isn't persisted is wisdom that dies at session end. This skill routes every WISDOM block, RETRO, failed path, and durable decision into whichever memory backend actually exists in the current runtime, and retrieves it at the start of related work.

## Backend detection (run once per session, in order)

1. **Tier 1 — hydra-mem + hydra-graph** (Claude Code, or any runtime with the hooks/MCP registered; self-owned, stdlib): hydra-mem captures sessions automatically via lifecycle hooks (SessionStart, UserPromptSubmit, PostToolUse, Stop, SessionEnd) into SQLite + FTS5; hydra-graph promotes the tagged wisdom into a typed graph (`graph.db`) with optional Chroma recall, screens it against poisoning, and mirrors it into the vault. Check `mcp__hydra-graph__*` / `mcp__hydra-mem__*` tools or `~/.hydra/config.json`. claude-mem is **not** used in this stack (paid third-party; see `no-claude-mem`).
1.5. **Tier 1.5 — Obsidian vault mirror** (any real filesystem: Claude Code, Cowork via Desktop Commander): the JSONL store stays the machine source of truth; the bundled `scripts/vault_sync.py` mirrors it into a human-browsable vault. `sync --vault DIR` writes one note per record under `Hydra Wisdom/TYPE/` with frontmatter Properties (wid, type, project, tags, conf, created) and rewrites a machine-owned `Hydra Wisdom MOC.md` (type: moc) with wikilinks grouped by type plus an optional Dataview block; idempotent via wid. `import --vault DIR` pulls human-written notes (valid type, no wid) back into the store and wid-stamps them. Filenames avoid the wikilink-breaking characters. Coexists with Tier 1: claude-mem is automatic capture, the vault is curated wisdom. Verified end-to-end 2026-08-12 (sync, MOC, idempotency, round-trip).

**obsidian-mind edition (preferred vault, verified)**: if the target vault is a breferrari/obsidian-mind vault (detect `vault-manifest.json` or `brain/North Star.md`), sync `Hydra Wisdom/` INSIDE it as a top-level folder — its PostToolUse hook validates our frontmatter (already compliant Properties) and its SessionStart QMD re-index picks up new wisdom notes automatically. Division of memory: obsidian-mind's `brain/` remembers the PERSON (North Star, Key Decisions, Patterns, Gotchas, people, perf); Hydra Wisdom remembers the WORK (lessons, failed paths, corrections). Read `brain/Gotchas.md` at session start as an additional failed_path source (sibling to napkin — mirror repo-agnostic gotchas there, don't migrate). **Retrieval upgrade**: when QMD is installed, prefer semantic search over wisdom.py's tf-idf — MCP tools `mcp__qmd__query`/`get` when registered, else `qmd --index NAME query "..."` (cheaper no-model-download fallbacks: `qmd search` BM25, `qmd vsearch`); note first `embed` downloads a ~328MB model and reranked `query` ~1.28GB.
2. **Tier 2 — local store**: persistent disk but hydra-graph not installed → `.hydra/wisdom.jsonl` with the bundled `scripts/wisdom.py` (pure stdlib). hydra-graph imports/exports this format, so Tier 2 stores migrate up without loss.
3. **Tier 3 — claude.ai**: no persistent disk → use Anthropic's memory feature when available; otherwise end jobs with a compact **resumption brief** the user can paste into the next chat or drop into Project knowledge.

**Handoff format = baton.** All resumption briefs and cross-session handoffs follow blader/baton's structure: Intent & Goal · State of Play (VERIFIED — in a repo, run `git status` and `git branch --show-current` first; state reflects runtime truth, never the chat narrative) · Learnings & Landmines · Pointers · Next Steps · Open Questions. The Learnings & Landmines section is populated from this store's `failed_path` records — dead ends already ruled out are the highest-value handoff content. In Claude Code with baton installed (`~/.claude/skills/baton/`), drop a real baton file in `.baton/` (git-ignored, `YYYY-MM-DD-slug.md`) instead of a chat brief; at session start in any repo, **grab-check first**: `ls -t .baton/ 2>/dev/null` and read the newest before doing anything else. A baton is for in-progress work only — finished tasks get wisdom records, durable rationale goes in design docs.

State the active tier once when the suite first needs memory. If Tier 1 is absent, `hydra-setup install` provides it — suggest once, never nag.

## Runtime matrix

| Runtime | Backends |
|---|---|
| Claude Code | Tier 1 hydra-mem + hydra-graph (auto, vault mirror built in) · Tier 2 JSONL only as fallback |
| Cowork / Claude Desktop + Desktop Commander | Tier 1.5 vault + Tier 2 JSONL (real filesystem via Desktop Commander file tools) |
| claude.ai (here) | Tier 3 baton-format briefs; can still EMIT vault-ready notes for the user to drop into their vault |

## Record schema (all tiers)

```json
{"ts":"2026-08-12T08:00:00Z","type":"insight|failed_path|decision|retro|meta_param|meta|correction",
 "project":"myapp","tags":["auth","jwt"],"conf":"V|U","text":"..."}
```

`conf` carries the orchestrator's three-tier ledger tag into storage (V = verified against reality, S = sourced to a document, U = unverified) — retrieved [S]/[U] records keep their tier until re-verified, and corrections are written as `correction` records rather than edits. When a lesson graduates into an extracted skill (nested-learning's Claudeception post-trigger), write a `decision` record naming the new skill so the lesson is never re-proposed. Never store secrets, credentials, or personal data; with claude-mem, wrap anything sensitive in its private tags so hooks exclude it.

## Writing (when WISDOM / RETRO blocks appear)

- **Tier 1**: write the block clearly in the session — hydra-mem's Stop hook stores every `INSIGHT:` / `DECISION:` / `FAILED PATH:` / `CORRECTION:` / `RETRO:` / `META_PARAM:` line (append `[V]/[S]/[U]`, `#tags`), and hydra-graph promotes, links and screens them. Lines that read like standing orders are quarantined until the user approves them.
- **Tier 2**: run the bundled script from wherever the skill is installed (the skill folder may be read-only — that's fine, only the store is written): `python3 SKILL_DIR/scripts/wisdom.py add --type insight --project myapp --tags "auth,jwt" --conf V "JWT refresh must rotate on every use — replay found in leaf auth/refresh"`. The store defaults to `./.hydra/wisdom.jsonl` in the current working directory; pin it explicitly with `--store /path/to/wisdom.jsonl` or env `HYDRA_WISDOM` so parallel subagents with different CWDs share one store. Appends are flock-protected on POSIX, so concurrent Hub/Leaf writers are safe.
- **Tier 3**: add to the session's resumption brief; if Anthropic memory is on, state the durable fact plainly so it can be captured.

Store distilled one-to-three-line records, not transcripts — the distillation threshold from the source docs, applied for real: an insight worth storing survives compression to three lines.

## Retrieval (progressive disclosure — cheap first)

At the start of any orchestrated/swarm job, or on "have we seen this before":

- **Tier 1**: `graph_recall` (hybrid FTS + vectors + one-hop edges, with provenance) for lessons and contradictions; hydra-mem `search` → `timeline` → `get_observations(ids=[...])` **only** for filtered IDs when the raw timeline matters. Never bulk-fetch full details first; the layered flow is roughly a 10x token saving.
- **Tier 2**: `python3 SKILL_DIR/scripts/wisdom.py search "jwt refresh" --project myapp --limit 5` (tf-idf keyword scoring; add `--type failed_path` to check dead ends before fanning out; same `--store`/`HYDRA_WISDOM` resolution as writes).
- **Tier 3**: check memory/user-provided briefs; if empty, proceed and say the job starts cold.

Retrieved failed paths pre-seed the orchestrator's FAILED PATHS log; retrieved meta-params seed Phase 0 (nested-learning).

## Wisdom propagation across the swarm

Hub/Leaf WISDOM blocks are written as they complete (bottom-up); Prime queries memory before briefing each new Hub (top-down). In Claude Code with parallel subagents, each subagent's session is captured by claude-mem independently — the Prime's merge query reunites them.

## Sibling stores (compatibility)

blader/napkin (verified) keeps a per-repo scratchpad at `.claude/napkin.md` — always-on every session, read at start, written continuously; the user chooses commit vs gitignore. Coexist: read it at session start as an additional `failed_path` source, and mirror repo-specific mistakes recorded here into it. Don't migrate between them — glanceable file vs searchable records are different retrieval styles.

## Local RAG upgrades (optional, Tier 2)

If keyword search proves too weak and the user wants semantic retrieval: chromadb or FAISS + sentence-transformers over the same JSONL (ask before installing — heavier deps). Note claude-mem already ships hybrid Chroma search, so upgrading Tier 2 rarely beats just installing Tier 1.

## Anti-patterns

- Storing raw transcripts or secrets; storing [U] speculation untagged
- Bulk-fetching full observations before filtering the index (Tier 1)
- Re-deriving a failed path that memory already holds — search before fan-out
- Claiming cross-session memory exists in Tier 3 when it doesn't; a resumption brief is the honest substitute
- Letting memory rot: on retrieval, if a record proves wrong, write a correction record rather than silently ignoring it

## Tool reference

| Need | Tool |
|---|---|
| Tier 1 search | hydra-graph MCP `graph_recall` / `graph_context`; hydra-mem MCP `search` → `timeline` → `get_observations` |
| Tier 2 store/search | `bash_tool` + `scripts/wisdom.py` |
| Tier 3 continuity | resumption brief text + Anthropic memory when present |
| Backend detection | `bash_tool` (check paths/tools) |
