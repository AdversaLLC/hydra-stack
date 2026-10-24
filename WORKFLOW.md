# WORKFLOW — the GSD-Hydra loop with every skill in its place

This is the fused loop from `gsd-hydra` with the whole belt placed station by station. Counts and
slots come from `BELT.md` (generated); if the two disagree, `BELT.md` wins and this file is stale.

## The three loops (Bruniaux's split, mapped onto what you own)

| Loop | What runs it | Artifacts |
|---|---|---|
| **Execution** — Discuss → Plan → Execute → Verify → Ship | GSD Core (spine) + the organs below | `.planning/STATE.md`, `ROADMAP.md`, `phases/NN-*.md`, `graphs/graph.json` (GSD owns these) |
| **Governance** — what may be accepted and by whom | Immutable Baseline + [V]/[S]/[U] ledger (orchestrator), gates (veritas, research-verification), adversarial-execution done-gate, remote_guard hook, CLAUDE.md's ask-before-irreversible rule, hydra-graph quarantine + integrity chain | `graph.db` audit log, quarantine list |
| **Improvement** — the stack gets better at the loop | nested-learning RETRO → meta-params, hydra-evolve ABSORB/CONDENSE/EVOLVE, grow-as-we-go defect nodes, setup-audit repeated-mistake findings, absorb/drift on every doctor | `graph.db` (`retro`, `meta_param`, `variant`, `defect`, `skill` nodes), `BELT.md` |

Only a deterministic validator or a named human accepts an irreversible outcome: tests, `verify-integrity`,
`validate`, the counts script, and you. No agent node accepts its own output inside a closed loop.

## Session start (every project, before any station)

`belt --phase start` → 13 skills; load at most: the baton (`ls -t .baton/`), the theory, the graph context.

| Skill | Tier | Does |
|---|---|---|
| hydra-belt | installed | the router: `belt --phase <station>`, `belt --load <name>` |
| hydra-graph | installed | `graph_context` is injected by hydra-mem's SessionStart hook: theory, open questions, conflicts, decisions, dead ends, quarantine count, belt line |
| hydra-mem | installed | raw capture (hooks); `search → timeline → get` for the timeline |
| baton | installed | grab-check `.baton/` first; newest wins |
| theory-keeper / theorist | installed | read `THEORY.MD` or `Theory/<project>.md`; theorist owns the repo home when installed |
| napkin | installed | `.claude/napkin.md` as an extra failed_path source |
| wisdom-memory | installed | states the active tier once (Tier 1 = hydra-mem + hydra-graph) |
| veritas | installed | every upload gets a status before work starts |
| research-base, grace-ask, grace-status | shelved | research projects / `.grace/` projects only |

Runtime routing stays as gsd-hydra says: Claude Code + GSD → GSD's commands are the engine; elsewhere the orchestrator + swarm run the same stations natively and say so.

## 1. Discuss — `belt --phase discuss` (9)

modulated-loop-orchestrator Phase 0 + fan-out (K angle sketches with kill-conditions become the decision record; killed angles → FAILED PATHS; every decision ledger-tagged). Loop contract written here (7 fields). hydra-consult pulls an outside opinion when the plan is non-trivial.
Domain organs (shelved, load when the deliverable needs them): **design-critique**, **user-research**, **research-synthesis** for UI/UX; **grace-ask**/**grace-spec** for GRACE projects; **brainstorming** when superpowers is the spine.

## 2. Plan — `belt --phase plan` (12)

GSD plans and verifies fit in a fresh context. Organs: **schematic** (brownfield: branch diff → spec first), **setup-audit** (agent-readiness of the repo: one-command setup, hidden env vars such as `.envrc`, test loop, guardrails — the `/gsd-onboard` gate), **karpathy-guidelines** (assumptions surfaced, plan with verify-per-step), **modulated-loop-orchestrator** Build Track Specify gate: constitution first, EARS acceptance criteria, out-of-scope, specs in the repo. nested-learning's meta-params seed K/depth/modes; FAILED PATHS are checked so no plan re-walks a dead end.
Shelved domain organs: **design-system** (tokens/components consistency), **ponytail-audit** (whole-repo audit before planning), **neo4j-modeling-skill** (only if the project itself uses Neo4j), **writing-plans** / **grace-plan** (alternate spines).

## 3. Execute — `belt --phase execute` (15)

GSD runs plans in waves of fresh executors (Claude Code). Organs: **hydra-swarm** (Prime/Hub/Leaf; graph contract in `swarm-map.md`; admission control: open Leaves ≤ verification capacity), **razor** (scope discipline), **karpathy-guidelines** (surgical changes, goal-driven loop), **napkin** (append gotchas as they bite). Red-first TDD for production code; clean test baseline before wave 1.
Shelved: **ux-copy** (screens), **ponytail** (lazy-senior-dev mode), **test-driven-development**, **using-git-worktrees**, **subagent-driven-development**, **dispatching-parallel-agents** (Claude Code only), **executing-plans** / **grace-execute** / **grace-refactor** (alternate spines), **neo4j-cypher-skill** (project code against Neo4j).

## 4. Verify — `belt --phase verify` (17)

Two stages, separate passes: spec compliance, then code quality. Ledger tags on every claim; phase confidence is ledger-derived. **adversarial-execution** is the independent done-gate for user-facing or high-stakes phases (Claude Code; elsewhere the report says "verified by self-review only"). **research-verification** before any number or count is written. **razor** re-measures the diff. **hydra-consult** at the verify point. When Verify fails: **systematic-debugging** (shelved) before any fix plan.
Shelved domain organs: **accessibility-review** (WCAG 2.1 AA, with opera-browser-cli screenshots as evidence), **ponytail-review** (second-stage quality review), **requesting-/receiving-code-review**, **verification-before-completion**, **grace-verification**/**grace-reviewer**/**grace-fix**, **neo4j-query-tuning-skill**/**neo4j-security-skill**.
Record `verdict_overturned` later if Verify's acceptance is overturned — the RETRO field that tests creator–verifier separation instead of assuming it.

## 5. Ship — `belt --phase ship` (5)

GSD creates the PR (your remote_guard and ask-rules still prompt: nothing is pushed without your say). Then the learning tail, in order: `graph ship-tail --retro "RETRO: …"` (retro node linked to the phase from `.planning/STATE.md`; auto-links; vault sync; cache refresh) → theory_check (holistic rewrite now if understanding changed) → Claudeception gate → **baton** if the next phase won't start this session. **research-verification** gates any figure in the PR body. Shelved: **design-handoff** (the spec sheet is the ship artifact for a design), **finishing-a-development-branch**.

## 6. Learn — `belt --phase learn` (16)

**nested-learning** RETRO (one param change, keep_or_revert, theory_check, verdict_overturned) → `meta_param` nodes. **hydra-evolve**: every new skill/repo/article goes through ABSORB (verify → REDUNDANT/DELTA/TENSION/NOVEL → assert-per-patch → wisdom record); every third absorb forces CONDENSE with measured word deltas; CREATE only through Claudeception's five gates; EVOLVE one mutation per round, human-gated. **claudeception** / **continuous-learning** (same upstream skill, two names — keep one) extract a skill when all five gates pass. **setup-audit**'s repeated-mistake findings and **grow-as-we-go** defect nodes feed the retro. GSD's own `gsd:extract-learnings` writes `NN-LEARNINGS.md`; hydra-graph's `gsd-import` reads it, so GSD stays the owner and the graph gets the lessons.
Shelved: **context-compact** / **research-harvest-verified** (harvest a long session into the graph), **ponytail-debt** (`shortcut:` ledger → defect nodes), **writing-skills**, **grace-refresh**, **neo4j-document-import-skill**.

## Ops — `belt --phase ops` (15)

**hydra-setup** (doctor / install / fix; absorb + drift + belt regeneration on every run), **setup-audit** (security / cost / readiness audit of the Claude Code config against the docs), **hydra-evolve** (CONDENSE), **hydra-belt**. Shelved: the methodology entry points of the alternate spines (**using-superpowers**, **grace-init**, **grace-explainer**, **grace-migrate**, **grace-setup-subagents**), **ponytail-help**, **neo4j-getting-started/mcp/migration**.

## Gates, consult, tools, memory

- **gate** (3): veritas (inputs), research-verification (outputs), verification-before-completion (shelved; superpowers' twin).
- **consult** (2): hydra-consult (automatic, at loop points), call-a-friend (manual; gpt / deepseek / local Ollama).
- **tool** (22): opera-browser-cli, ponytail-gain, grace-cli, and the 19 Neo4j driver/platform skills — all shelved, loaded only when writing code against that platform.
- **memory** (11): hydra-graph, hydra-mem, wisdom-memory (installed); research-base, context-compact, research-harvest-verified, grace-ask, neo4j-agent-memory / graphrag / vector-index / document-import (shelved).

## The stack's own pipeline (state machine; what the hooks do without you)

```
            SessionStart ─────────────────────────────────────────────────────────┐
  hydra-mem: inject ≤2.4k context ── + graph half (cache, ≤800 chars, belt line)   │
  obsidian-mind: vault index · remote_guard: armed                                 │
                 │                                                                 │
                 ▼                                                                 │
          UserPromptSubmit ──► PostToolUse ──► … (hydra-mem logs, async)           │
                 │                                                                 │
                 ▼  Stop / SessionEnd                                              │
  hydra-mem: extract tagged lines ──► spawn (detached, lock-serialized)            │
      hydra_graph.py promote --project-root R                                      │
         ├─ promote: mem.db rows → nodes   (dedupe by hash · screen → quarantine · burst cap)
         ├─ gsd-import: .planning/**/NN-LEARNINGS.md, graphs/graph.json (if .planning/ exists)
         ├─ link: mentions · supersedes · contradicts · part_of(phase) · tested_by
         ├─ embed: rag_worker (Ollama → ONNX) if configured, else skip
         ├─ vault-import (notes you edited) → vault-export (notes + MOCs)
         └─ context → graph-cache/<project>.txt  ─────────────────────────────────┘
  every mutation → audit row (HMAC chain)  ·  doctor: verify-integrity · validate · absorb/drift · belt
  terminals: done │ quarantined (you approve/reject) │ rolled_back (one command per session) │ escalated (irreversible → you)
```

Idempotency keys: node id (kind/date/slug) + content hash; edge (src,dst,kind); `sync_state` watermarks per importer (hydra-mem last id, vault mtimes, graphify hash, LEARNINGS mtime); `bridge-chain.lock` serializes chains; rework budgets persist as `meta_param` nodes. Re-running any step is a no-op.

## Asks → where they landed

| You asked for | Where it is |
|---|---|
| "Walk me through Setup Audit" / "the design plugin" | both in the belt with real stations (setup-audit installed: ops/plan/learn; Design shelved: one per station); `ABSORB-LOG.md` |
| System-agnostic skills | no path in any SKILL.md (`grep` in `README.md`); `~/.hydra/config.json` + `setup.py` runtime detection |
| Obsidian MIND + graphify + Chroma memory RAG | hydra-graph: vault export/import in obsidian-mind format, `graphify-import` (incl. GSD's `.planning/graphs/`), Chroma tier in its own venv |
| GSD as the standard | spine unchanged; `gsd-import` reads GSD 1.18 artifacts; gsd-hydra patched for 1.18 names |
| RSI (hydra-evolve) × ARS research overlap | shared node kinds in one `graph.db`; constitution rows protected; absorb seed records |
| Analyse new input on install, fold in updates | `absorb` (skill nodes + overlaps) and drift on every doctor; `belt` regenerated; keyword fallback + `unplaced` |
| Effective against poisoning without hindering | `POISONING.md`: trust lanes, screen, quarantine, envelope, burst cap, audit chain, rollback, protected rows |
| karpathy, ponytail, GRACE, Neo4j, SDD, loop/graph engineering, cookbook | cloned/fetched, triaged in `ABSORB-LOG.md`, placed in `belt-rules.json`, deltas patched into the suite (`CHANGES.md`) |
| Everything in one zip, git clone anything missing | `hydra-stack.zip`: 14 vendor clones at pinned commits, `vendor/` is the offline fallback for `setup.py` |
| Load as needed, aware of the belt | two tiers + `belt --phase`; measured: 24 installed ≈ 4.3k always-on tokens vs 237k if everything were loaded |
