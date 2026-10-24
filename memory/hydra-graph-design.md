# hydra-graph — a simple RAG + knowledge-graph memory for the Hydra stack

Design for what `hydra-setup` should build. Written 2026-10-21 against your `claude-tuned` config, your skills export, and the current upstream docs (sources at the end). Nothing here is installed yet; this is the plan to approve or change.

## 0. Veritas audit of this turn's uploads

| File | Size | Status | Note |
|---|---|---|---|
| `42d2b9e0-skills-export-all.zip` | 8.2 MB | ✅ READ | 721 files. Four trees: `examples/` (34 Anthropic sample skills, each also as `.skill`), `organization/` (21 org skills), `plugins/` (56 plugin skills incl. qt-*, forensics, research-*, grow-as-we-go, context-compact), `public/` (docx/pdf/pptx/xlsx/file-reading/frontend-design), `user/` (the 8 Hydra suite skills + wisdom.py/vault_sync.py). Fully walked for the Hydra, research and graph pieces; the forensics and Qt skills were listed, not read, because they do not bear on this design. |
| `2921fbbf-claude-tuned-full.zip` | 375 KB | ✅ READ | 46 files. `settings.json`, `CLAUDE.md`, `apply_tuning.py`, `hooks/remote_guard.py`, `hydra-mem/` (hydra_mem.py 0.2.0 + 58 tests + README + HANDOVER + diff), 11 belt skills, 3 project memory notes, 6 review logs, 2 CSVs (1,606-row disposition and audit tables of your whole `~/.claude`). Every file opened; `hydra_mem.py` read by structure (function and DDL map) rather than line by line. |

Hashes: `70873ee1…` (claude-tuned), `0b511d30…` (skills-export). Not duplicates of each other; no split archives; nothing blocked.

What the uploads actually say, in one paragraph: you already own a working, tested, stdlib-only memory layer (hydra-mem: SQLite + FTS5, five Claude Code hooks, CLI and MCP server, secret redaction, 58 tests). On top of it sits a second store, kuzu-memory, fed by a detached bridge, and a human-readable mirror in an Obsidian vault that obsidian-mind manages with five TypeScript hooks. Your rules are explicit: model-agnostic, self-owned, plain files/SQLite/CLI/MCP, no paid services, no claude-mem, verify before done, never push without being asked, ask before anything hard to undo. The review logs document that the kuzu side is the weak link: 5–6 s import, single-writer locks, an installer that deletes any hook whose command contains "kuzu", an `mcp` version pin that crashed the server, and a bridge that promotes every project into every graph so 6 of 7 context caches were near-identical and clipped mid-item.

## 1. What the design has to satisfy

From your files, not from me:

| Constraint | Source |
|---|---|
| Model-agnostic, self-owned: plain files, SQLite, CLI, MCP any client can use | CLAUDE.md, `local-model-goal.md` |
| No paid third-party services; no claude-mem | CLAUDE.md, `no-claude-mem.md` |
| Windows host, Git Bash, Python 3.14 at a fixed path | CLAUDE.md |
| hydra-mem's five hooks and its DB stay the capture layer | README, HANDOVER, settings.json |
| obsidian-mind owns the vault's five hooks and validates frontmatter/wikilinks on every `.md` write | settings.json, obsidian-mind docs |
| GSD Core is the delivery spine; its artifacts (`STATE.md`, `CONTEXT.md`) are the source of phase truth | gsd-hydra SKILL.md, your message |
| RSI (hydra-evolve) and ARS (Academic Research Skills + research-base/context-compact/grow-as-we-go) must share one graph, not two | your message; the research kernels already use a typed-edge SQLite `graph.db` |
| New inputs (a skill library like superpowers, a new plugin, a graphify run) get analysed on install and folded in on update | your message |
| Verify before done; ask before irreversible changes | CLAUDE.md |

## 2. Architecture

```
                    capture (already yours)                 knowledge (new)                    humans + agents
  Claude Code ──hooks──▶ hydra-mem  mem.db ──promote──▶ hydra-graph  graph.db ◀──sync──▶ Obsidian vault (obsidian-mind)
  Codex/local ──CLI/MCP─▶ (SQLite+FTS5)                 (SQLite: nodes, edges, FTS,          brain/, Hydra Wisdom/, Theory/
                                                         optional vectors)                     wikilinks = edges
                                                            ▲        ▲
                                              graphify-out/ │        │ GSD .planning/ STATE.md, CONTEXT.md, RETRO
                                              graph.json    │        │ research-base / context-compact / grow-as-we-go
                                              (code graph)  │        │ hydra-evolve variant records
                                                            │        │
                                                   Chroma collection (optional tier: semantic search)
```

Three rules make it "simple":

1. **One graph file.** `graph.db` is a stdlib SQLite file with the same `nodes`/`edges` shape your research kernels already write. hydra-mem, ARS, RSI, graphify and GSD all land in it. kuzu-memory is retired (migration in §8) — every defect in your logs traces to it, and nothing it provides survives the "any client, no vendor" test better than SQLite.
2. **The vault is a view, and also an input.** Nodes are rendered as notes (frontmatter + wikilinks) so Obsidian's own graph view *is* the graph view; notes you write by hand are parsed back in (wikilinks become edges). obsidian-mind's validate-write hook sees every note we write, so our notes must pass its frontmatter rules — we write them in its format.
3. **Vectors are a tier, not a dependency.** FTS5 (already in hydra-mem) is tier 0 and always works. Chroma is tier 1 for semantic recall and sits beside, never inside, the graph: ids in Chroma are graph node ids. If Chroma is absent, everything still runs.

## 3. Schema (`graph.db`)

```sql
CREATE TABLE nodes(
  id        TEXT PRIMARY KEY,   -- slug: "insight/2026-10-21/kuzu-import-slow"
  kind      TEXT NOT NULL,      -- insight|decision|failed_path|correction|retro|meta_param|note
                                -- |theory|phase|task|claim|measurement|question|skill|capability|file|symbol|variant
  title     TEXT NOT NULL,
  body      TEXT NOT NULL,
  project   TEXT,               -- git toplevel name; NULL = global
  conf      TEXT CHECK(conf IN ('V','S','U')),
  source    TEXT NOT NULL,      -- hydra-mem:<id> | vault:<path> | graphify | gsd:<phase> | ars | evolve | manual
  tags      TEXT,               -- comma list
  ts        TEXT NOT NULL,      -- ISO
  updated   TEXT NOT NULL,
  hash      TEXT NOT NULL       -- normalized-token hash, same rule as hydra-mem near-dup
);
CREATE TABLE edges(
  src TEXT NOT NULL REFERENCES nodes(id),
  dst TEXT NOT NULL REFERENCES nodes(id),
  kind TEXT NOT NULL,           -- supports|contradicts|depends_on|caused|fixed_by|part_of|mentions|supersedes|tested_by|calls|imports
  weight REAL DEFAULT 1.0,
  source TEXT NOT NULL,
  ts TEXT NOT NULL,
  PRIMARY KEY(src,dst,kind)
);
CREATE VIRTUAL TABLE node_fts USING fts5(title, body, tags, content='nodes', content_rowid='rowid');
CREATE TABLE sync_state(key TEXT PRIMARY KEY, value TEXT);   -- watermarks: hydra-mem last id, vault mtimes, graphify hash
CREATE TABLE vectors(node_id TEXT PRIMARY KEY, backend TEXT, dim INT, ts TEXT); -- which nodes are embedded where
```

Why these node kinds: the seven wisdom types are hydra-mem's; `theory` is theory-keeper's; `phase`/`task` are GSD's; `claim`/`measurement`/`question` are ARS/research-base's; `skill`/`capability` are what the absorb-on-install pass writes; `file`/`symbol` are graphify's; `variant` is hydra-evolve's experiment record. One table, one query surface.

## 4. Data flow per event (what changes vs today)

| Event | hydra-mem (unchanged) | hydra-graph (new) | obsidian-mind (unchanged) |
|---|---|---|---|
| SessionStart | injects ≤2.4k context | replaces the kuzu bridge half: `graph context --project X` from a cache file written at Stop; ≤800 chars: top theory node, open questions, 3 contradictions, 3 recent decisions | injects vault index |
| UserPromptSubmit | stores prompt (async) | nothing | classifies |
| PostToolUse | stores tool key (async) | nothing | validates `.md` writes |
| Stop | extracts tagged lines | detached: `promote` (new hydra rows → nodes), `link` (auto-edges §5), `vault-sync` (changed nodes → notes), `context` (rewrite cache) | stop checklist |
| SessionEnd | same + catch-up | same, always | — |
| PreCompact | — | `harvest` hook point for context-compact (optional) | backs up transcript |

Hook commands never contain the string "kuzu" (that rule stays until kuzu is fully removed), never exit 2, and the Stop chain takes the same `bridge-chain.lock` so chains never overlap — the behaviours your review already fixed carry over because `hydra_graph.py` is spawned by `hydra_mem.py` exactly where `hydra_bridge.py` is today. **Zero changes to `settings.json`.**

## 5. Edges without an LLM (so the graph is useful offline and under a local model)

- **mentions**: a node body that contains another node's title or `[[wikilink]]`.
- **supersedes**: a `correction` whose normalized text overlaps ≥60 % with an earlier `insight`/`decision` of the same project.
- **contradicts**: a `failed_path` and a `decision` sharing ≥3 content tokens in the same project (flagged, conf `U`; a human or the Verify phase promotes to `V`).
- **part_of**: every wisdom node created during a GSD phase → that phase node (the phase is read from `.planning/STATE.md` at Stop time).
- **calls / imports**: copied verbatim from `graphify-out/graph.json` when present, tagged with graphify's own `EXTRACTED|INFERRED|AMBIGUOUS` label in `weight` (1.0 / 0.6 / 0.3).
- **tested_by**: an `insight`/`decision` whose body names a test file that exists in the repo.

Anything smarter (LLM-extracted claims) comes from research-harvest-verified, which already does structured extraction with a grounding gate; it writes the same tables, so it slots in without a second format.

## 6. Obsidian MIND interop contract

obsidian-mind expects `brain/` (North Star, Memories, Key Decisions, Patterns, Gotchas), `work/`, `thinking/`, `templates/`, and validates frontmatter and wikilinks on every markdown write.

What hydra-graph writes (and only this):

```
vault/
  Hydra Wisdom/<project>/<kind>/<slug>.md     one note per node (existing folder, kept)
  Theory/<project>.md                          theory-keeper's note (existing, unchanged)
  Hydra Graph/
    Index.md                                   MOC: one line per project → per kind → note links
    Contradictions.md                           every contradicts edge, newest first
    Open Questions.md                           question nodes with no fixed_by/supersedes edge
```

Note format (passes obsidian-mind validation; fields map 1:1 to columns):

```markdown
---
type: insight
project: lan-llm-proxy
conf: V
source: hydra-mem:412
tags: [kuzu, perf]
created: 2026-10-17T19:47:00Z
updated: 2026-10-20T08:00:00Z
hydra_id: insight/2026-10-17/kuzu-import-slow
---
# kuzu import takes ~2.5 s; keep graph timeout ≥ 15 s

(body)

## Links
- supports [[decision/2026-10-17/graph-timeout-15s]]
- part_of [[phase/lan-llm-proxy/02-execute]]
```

Reverse direction: `graph vault-import` parses every note under those three folders plus `brain/Key Decisions.md`, `brain/Patterns.md`, `brain/Gotchas.md`. A note with a `hydra_id` updates its node (vault wins on `body`, graph wins on edges it generated); a note without one becomes a `manual`-sourced node, and each `[[wikilink]]` becomes a `mentions` edge. mtimes are watermarked in `sync_state` so this is incremental. Nothing outside the listed folders/files is ever read or written, matching hydra-setup's "never touch user vault notes" rule.

Obsidian's built-in graph view therefore shows the knowledge graph with no plugin; obsidian-mind's QMD search (optional in its docs) searches the same notes.

## 7. RAG tier: Chroma

- **Store**: `chromadb.PersistentClient(path=<hydra_home>/chroma)`, one collection per project plus `global`. Document id = node id, metadata = `{kind, project, conf, ts}`. Only `title + body` are embedded; bodies are redacted upstream by hydra-mem already.
- **Embeddings, in order of preference** (chosen by `hydra-setup doctor`, overridable in config):
  1. **Ollama** `nomic-embed-text` or `bge-m3` at `http://127.0.0.1:11434` — local, no download at query time, works for your local-model goal, and is the same endpoint call-a-friend's `local` friend already uses.
  2. **Chroma's default** (`all-MiniLM-L6-v2` via ONNX) — fully local after a one-time model download on first use. Acceptable under "no paid services"; it is a download, not an account.
  3. **None** — FTS5 only. `graph search` says which tier answered.
- **Query** = hybrid: FTS5 BM25 top-20 ∪ vector top-20 → reciprocal-rank fusion → expand 1 hop along `supports|supersedes|contradicts|part_of` → return ≤8 with the edges that pulled them in. That one-hop expansion is the whole reason to have a graph next to a vector store: a `decision` comes back with the `failed_path` that forced it.
- **Isolation**: Chroma and its deps (onnxruntime, hnswlib/rust bindings, numpy) do **not** go into your Python 3.14 interpreter. Doctor creates `<hydra_home>/venv-rag` with the newest Python it can find that has chromadb wheels (3.12 or 3.13 today; 3.14 wheel coverage for onnxruntime is not something I could confirm) and `hydra_graph.py` talks to it over a subprocess JSON line protocol, the same pattern as the current bridge. Core stays stdlib.
- **Not Chroma Cloud, not an HTTP server**: `PersistentClient` only. Nothing listens on a port.

## 8. Retiring kuzu-memory (reversible, your approval required)

1. `hydra_bridge.py export --project-root <p>` → JSONL of every memory with `source_type=hydra` (they are already in `mem.db`; this is a safety copy of anything kuzu added on its own).
2. `hydra_graph.py promote --all` rebuilds nodes from `mem.db` (the true source) — nothing depends on kuzu's copy.
3. `HYDRA_BRIDGE_DISABLE=1` for one session; run doctor; confirm SessionStart context is served from the graph cache.
4. Then, and only on your go-ahead: remove `<project>/.kuzu-memory/`, the `kuzu-memory` MCP entries in `~/.claude.json` and `~/.mcp_servers.json`, `uv tool uninstall kuzu-memory`. Backups as `apply_tuning.py` does them.

What you lose: kuzu's 11 MCP tools and its 30-day episodic memories. What you keep: all hydra-sourced wisdom (it never left `mem.db`), and the `graph_recall`/`graph_context` MCP tool names, which hydra-graph re-implements with the same signatures so `skills/hydra-mem/SKILL.md` and `executor.py` keep working.

## 9. GSD as the standard

- hydra-graph never creates phase state; it **reads** `.planning/STATE.md` and `CONTEXT.md` (GSD Core 1.18 is current; the installer stays `npx @opengsd/gsd-core@latest`, never hand-copied).
- Discuss: `graph context` is what gsd-hydra's Phase 0 loads (theory + open questions + contradictions).
- Verify: ledger scores (`[V]/[S]/[U]`) are written as `conf` on the nodes the phase produced.
- Ship: the post-ship tail (RETRO, theory_check, Claudeception gate, vault sync, baton drop) is one command, `graph ship-tail --phase N`, which writes the `retro` node, re-links, syncs the vault and refreshes the cache. Baton stays in `.baton/`; its handoff file gets a one-line pointer to the phase node.

## 10. RSI × ARS overlap, and absorb-on-install

The overlap you asked for is a shared vocabulary, not shared code:

| Concern | hydra-evolve (RSI) writes | ARS / research-* writes | Shared edge |
|---|---|---|---|
| A thing that worked | `variant` (mutation, fitness scores, approved?) | `claim` conf V + `measurement` | `variant --supports--> claim` |
| A thing that failed | `variant` fitness < parent | `failed_path` / `claim` conf U | `contradicts` |
| What to try next | parent-selection reads `question` nodes | `question` nodes from research-verification's gate | `depends_on` |
| Skill got better | `skill` node updated, `supersedes` old variant | grow-as-we-go defect node → `fixed_by` | `fixed_by` |

Constitution clause from hydra-evolve (ledger, red-first, concession threshold, verify-before-fusing) is stored as `meta_param` nodes with `conf V` and a `protected` tag; `graph` refuses to delete or supersede them without `--override`.

**Absorb on install** (`hydra-setup install` and `fix` run it; `doctor` reports what it would do):
1. Walk every skill/plugin directory the runtime knows (`~/.claude/skills`, `~/.claude/plugins/*/skills`, `~/.codex/skills`, marketplace installs such as superpowers).
2. For each `SKILL.md`: a `skill` node (name, description, trigger phrases parsed from the description, git rev or plugin version, path) and `capability` nodes for each distinct trigger phrase.
3. **Overlap report**: two skills sharing a trigger phrase or ≥70 % description tokens → a `contradicts` edge tagged `trigger-overlap` and one line in doctor's table. (Your export has several: "orchestrate" and "hydra" fire three suite skills; napkin/theorist vs hydra-mem was exactly the clash the review retired.)
4. **Drift**: on every doctor run the recorded rev/version is compared with what's on disk; changed → re-absorb that skill, `supersedes` edge from the new `skill` node to the old. That is the "dynamically fold in updates" part, and it is what makes a `/plugin update superpowers` visible to the suite instead of silent.
5. Proposals only. Absorb never edits a skill; hydra-evolve's gated loop does that, reading the same nodes.

## 11. hydra-setup, made system-agnostic

Today's `setup.sh` hardcodes `~/.claude/skills`, assumes bash, and still offers claude-mem and taskmaster, both of which your review retired. Changes:

- **One config file**, `~/.hydra/config.json` (override `HYDRA_HOME`), created by `install`, read by every suite script:
  ```json
  { "python": "C:/Users/Admin/AppData/Local/Programs/Python/Python314/python.exe",
    "runtime": "claude-code", "skills_dirs": ["~/.claude/skills"],
    "mem_db": "~/.claude/hydra-mem/mem.db", "graph_db": "~/.hydra/graph.db",
    "vault": "C:/Users/Admin/Desktop/USB/vault", "vault_layout": "obsidian-mind",
    "rag": {"backend": "ollama", "model": "nomic-embed-text", "venv": "~/.hydra/venv-rag"},
    "gsd": {"installer": "npx @opengsd/gsd-core@latest"},
    "graphify": {"enabled": false, "out": "graphify-out" } }
  ```
  No path appears in any SKILL.md anymore; `skills/hydra-mem/SKILL.md`'s hardcoded `C:/Users/Admin/...` lines become `hydra config get python`.
- **Installer in Python, not bash** (`setup.py`, stdlib), because every other piece of yours is Python and Git Bash CRLF has already bitten two hooks. Same three modes: `doctor | install | fix`, same idempotence and three-strikes rule.
- **Runtime detection**: Claude Code (`~/.claude`), Codex (`~/.codex`), Cowork/desktop sandbox, claude.ai (prints the one-liner), "other MCP client" (registers `hydra_graph.py mcp` and prints the stdio command).
- **Doctor table components**: belt skills (7 — taskmaster dropped), suite skills, GSD Core (version vs latest), hydra-mem (tests pass? hooks registered? async flags intact?), hydra-graph (schema version, node count, cache age), vault (layout detected: obsidian-mind / plain), RAG tier (which backend answered a probe), graphify (installed? `graphify-out/graph.json` age), absorb (skills recorded vs on disk, overlaps), kuzu (present → "legacy, run migration §8"). claude-mem row removed; a `--with-mem` flag now errors with "not used here, see no-claude-mem".
- **Never auto-runs** GSD's installer, `uv tool install graphifyy`, or Ollama pulls; prints the exact command, as today.

## 12. Verification plan (what "done" will mean)

- `test_hydra_graph.py`: schema create/migrate; promote from a hydra-mem DB fixture (idempotent on re-run); every auto-edge rule with positive and negative cases; vault export → obsidian-mind-style frontmatter validates with the same checks `validate-write.ts` performs (I will port its rules into the test); vault import round-trip (edit a note, re-import, node body updated, edges preserved); hybrid search with tier 0 only; tier 1 via a stub RAG subprocess (slow / failing / garbage output, like your bridge stub); context cache under 800 chars with the footer intact; absorb on a fixture skills tree with a planted trigger overlap; drift after bumping a fixture's git rev; MCP `graph_recall`/`graph_context` signature compatibility with `executor.py`.
- hydra-mem's 58 tests still pass unchanged (hydra-graph is spawned where the bridge was; the stub mechanism is reused).
- A dry run of `setup.py doctor` against a copy of your `claude-tuned` tree, output pasted into the handover.
- Everything runs under `python -I`, temp HOME, temp DBs. Nothing touches a real vault in tests.

## 13. Decisions taken (2026-10-21)

1. kuzu-memory retired, conditional on "genuinely better" — the evidence table is in `MIGRATION-kuzu.md`; removal still waits for your go-ahead.
2. Embeddings: Ollama → Chroma ONNX → FTS-only fallback chain, auto-detected by doctor (no preference stated).
3. Vault: `Hydra Wisdom/` + `Hydra Graph/` + `Theory/` (no preference stated).
4. Added requirement: **effective against poisoning without hindering** → trust lanes, insert screen, quarantine, sanitised envelope, burst cap, HMAC audit chain, rollback, protected nodes. Full write-up in `POISONING.md`.

## 14. Status

Built and verified in the sandbox: `hydra_graph.py`, `rag_worker.py`, `setup.py`, 41 tests, two rewritten SKILL.md files, end-to-end through hydra-mem's unmodified hooks. See `README.md` for the verification table and the five findings about your current tree.

## Sources

- graphify: [Augment Code overview](https://www.augmentcode.com/learn/graphify-knowledge-graph-codebase-skill) — `uv tool install graphifyy`, `graphify-out/graph.json`, tree-sitter extraction, EXTRACTED/INFERRED/AMBIGUOUS labels, MCP tools.
- obsidian-mind: [x-cmd package page](https://x-cmd.com/install/obsidian-mind) — `breferrari/obsidian-mind`, five hooks, `brain/` layout, frontmatter/wikilink validation on write, Node 22+.
- Chroma: [clients](https://docs.trychroma.com/docs/run-chroma/clients), [embedding functions](https://tessl.io/registry/tessl/pypi-chromadb/files/docs/embedding-functions.md) — `PersistentClient`, default all-MiniLM-L6-v2 ONNX, `OllamaEmbeddingFunction`.
- GSD Core: [@opengsd/gsd-core on Socket](https://socket.dev/npm/package/@opengsd/gsd-core/overview/1.8.0) — installer, runtimes, `STATE.md`/`CONTEXT.md`, latest 1.18.0.
- superpowers: [installation docs](https://mintlify.wiki/obra/superpowers/installation/claude-code) — marketplace install and `/plugin update superpowers`.
- Your files: `claude-tuned/CHANGES.md`, `hydra-mem/README.md`, `hydra-mem/HANDOVER.md`, `logs/hydra-mem.md`, `logs/verification.md`, `user/hydra-setup/SKILL.md`, `plugins/research-base/kernel.py`.
