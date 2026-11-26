---
name: gsd-hydra
description: The fusion flagship - GSD Core's disciplined delivery spine (the Discuss, Plan, Execute, Verify, Ship phase loop from open-gsd/gsd-core, successor to the archived gsd-build/get-shit-done) fused with the hydra suite's organs at every station - wisdom/theory/baton memory at session start, orchestrator fan-out with kill-conditions inside Discuss, schematic and meta-params inside Plan, swarm Hubs as execute waves with razor scope discipline and taskmaster completion tokens, ledger-scored Verify escalating to the adversarial-execution independent done-gate, and a post-Ship learning tail (RETRO, theory_check, Claudeception gate, vault sync, baton drop). In Claude Code with GSD installed, defers to real /gsd-new-project, /gsd-onboard and fresh-context subagents and augments them; in Cowork or claude.ai it runs the same loop natively and sequentially. Triggers on "gsd", "get shit done", "ship it", "run the loop on this project", "new project", "onboard this codebase", "full delivery loop", or any multi-phase build.
metadata:
  authored_via: "claude-science"
  published_by: "agent"
  published_at: "2026-10-22T18:09:47.927Z"
  authored_by: "unknown"
  last_modified_by: "agent"
  last_modified_at: "2026-10-22T18:09:46.562Z"
---

# GSD-Hydra — Git. Ship. Done. Wiser every phase.

GSD Core (verified 2026-08-12; re-verified 2026-10-21 against gsd-core 1.18.0 @199ef8a — its `.planning/` tree now also holds `ROADMAP.md`, per-phase `NN-LEARNINGS.md` from `gsd:extract-learnings`, and `graphs/graph.json` from `gsd:graphify`; hydra-graph reads all three via `gsd-import`, GSD stays their owner) supplies what the hydra suite never had: a **delivery spine** — the five-step phase loop, fresh-context executors that beat context rot, and artifacts (`STATE.md`, `CONTEXT.md`, `.plans/`) that survive sessions. The suite supplies what GSD doesn't claim to have: **verified reasoning** ([V]/[S]/[U] ledger, fan-out, baseline), a **memory ladder** (wisdom records → theory → batons), **independent verification** (two-reviewer done-gate), and a **learning tail** (RETRO → meta-params → skill extraction). Fused, each phase both ships and learns.

## Runtime routing (first thing, every project)

- **Claude Code + GSD installed** (check for `/gsd-new-project` availability or `~/.claude/commands/gsd/`): GSD's commands and fresh-context subagents are the engine — never reimplement them, never copy GSD's files by hand (its installer is required for cross-runtime compatibility: `npx @opengsd/gsd-core@latest`). This skill *augments* each phase as below.
- **Claude Code without GSD**: offer hydra-setup to install it; until then run the loop natively via the suite.
- **Cowork / claude.ai**: run the loop natively — same five stations, sequential, honestly labeled (no fresh-context subagents exist here; the swarm's tagged passes substitute).

## Spine choice: one methodology owns the loop

obra/superpowers (verified, 267k stars, MIT, official Claude plugin marketplace) is a COMPLETE alternative delivery spine — brainstorming, worktrees, plans, subagent-driven execution, TDD, review, branch-finishing — with auto-triggering "mandatory workflows, not suggestions." GSD and superpowers both want to own Plan/Execute: pick ONE spine per project and attach the hydra organs to it; running both auto-triggering methodologies simultaneously is an untested conflict [U]. The organs are spine-agnostic — wisdom/theory/baton at session start, ledger tags on decisions, RETRO tail after ship — and the superpowers deltas below are adopted into this loop regardless of spine.

## Belt: load organs per station, not per session

Every skill in the stack has a loop slot (`belt-rules.json`, rendered in `BELT.md`). At each station run `hydra_graph.py belt --phase <start|discuss|plan|execute|verify|ship|learn>` and load only what that step needs — the 71 shipped SKILL.md files total ~108k tokens if loaded together; a station list is ~1k. A newly installed skill is slotted by rule or keyword on the next `hydra-setup doctor` (absorb), and shows as `unplaced` until hydra-evolve places it. Alternate spines in the belt — superpowers (`using-superpowers`), GRACE 4 (`grace-init`) — stay organs unless a project chooses one of them instead of GSD; never two auto-triggering spines in one repo.

## Domain routing: code ships via GSD, papers ship via ARS, screens ship via GSD + the Design organs

For academic/research deliverables, the delivery spine is not GSD but **Academic Research Skills** (Imbad0202/academic-research-skills, verified v3.19.0, CC-BY-NC 4.0): its 10-stage pipeline with MANDATORY Stage 2.5/4.5 integrity gates, deterministic 4-index citation-existence verification, and 0-100 rubric peer review is the paper-world equivalent of Discuss→Plan→Execute→Verify→Ship. The hydra organs attach the same way: wisdom/theory at session start, fan-out inside its Socratic/plan stages, RETRO + theory_check + vault sync after its Stage 6. Where both are installed, route by deliverable: repo → GSD; paper/lit-review/systematic-review → ARS pipeline; a project producing both uses both, sharing one wisdom store.

For UI/UX deliverables the spine is still GSD and the Design plugin's seven skills attach one per station: **Discuss** — design-critique on the mockup or screen the user shared, user-research (plan/interview guide) and research-synthesis (transcripts, tickets, NPS → themes) produce the decision record; **Plan** — design-system checks tokens, naming and hardcoded values before anything is built; **Execute** — ux-copy writes the microcopy, errors, empty states and CTAs as screens are built; **Verify** — accessibility-review (WCAG 2.1 AA) runs beside the done-gate, with opera-browser-cli screenshots as its evidence; **Ship** — design-handoff's spec sheet (layout, tokens, props, states, breakpoints, edge cases, motion) is the phase's ship artifact. Operational health of the stack itself is setup-audit's station (after install, when sessions get expensive, on `/gsd-onboard` as the agent-readiness check); its repeated-mistake findings feed the RETRO.

## The fused loop

**Session start (before any phase)** — grab-check `.baton/` (newest baton wins), read the operating theory (theory-keeper), pull wisdom for this project. In an obsidian-mind vault, its SessionStart hook already injects North Star, active work, and tasks (personal memory) — /om-standup complements, never replaces, the work-memory grab-check. Both obsidian-mind and GSD register Claude Code hooks; they are designed as additive lists but running them stacked is [U] untested — if session start misbehaves, check `.claude/settings.json` hook ordering first (failed_paths pre-seed; meta-params seed ceremony). GSD's `STATE.md`/`CONTEXT.md` remain the *phase* state; the suite's ladder holds what GSD's artifacts don't: cross-project lessons and the durable why. Never duplicate content across them — link.

1. **Discuss** — GSD captures implementation decisions before planning. Fusion: run orchestrator Phase 0 + fan-out here — K angle sketches with kill-conditions become the *decision record*, killed angles go straight to FAILED PATHS, and every captured decision carries a ledger tag ([V]/[S]/[U]) so the plan inherits calibrated inputs, not vibes.
2. **Plan** — GSD researches, decomposes, and verifies plans fit a fresh context window (keep all of that). Fusion: brownfield → run schematic first so the spec starts from branch reality; seed plan parameters from nested-learning's meta-params; check FAILED PATHS so no plan re-walks a dead end. Spec gate criteria (testable success conditions, Always/Ask/Never boundaries) apply to every plan.
3. **Execute** — GSD runs plans in parallel waves of fresh 200k-context executors (Claude Code). Fusion: waves map to swarm Hubs; each executor gets hydra-swarm's brief (source, absolute-path inputs, role, owned and off-limits files, return shape) and its summary must end with a `STATUS: done | partial | empty | failed` block plus evidence, then a WISDOM block that flows up; a missing block counts as failed, the coordinator checks every result against the brief, and waves run in parallel only on independent work with disjoint files; razor scope discipline and taskmaster's completion contract govern cutting and stopping — the full rules live in ONE home, the orchestrator's Implement step; this station inherits them by reference. Superpowers deltas (adapted from obra/superpowers): establish a CLEAN TEST BASELINE before wave 1 so every failure is attributable to the delta; plan tasks at 2-5 minute granularity with exact file paths and verification steps, written for "a junior with no project context and no judgement" — if a task needs taste to execute, it isn't decomposed yet; and for production-intent code, RED-GREEN TDD with teeth — write the failing test, WATCH it fail, write minimal code, watch it pass, commit. A test that was never seen red proves nothing: red-first evidence makes a passing test [V]; a never-failed test stays [U]. Spikes are exempt but must be labeled spike.
4. **Verify** — GSD walks through what was built and generates fix plans before declaring done (keep). Fusion: the walk-through's claims get ledger tags and the phase confidence is ledger-derived; for user-facing or high-stakes phases, escalate to the adversarial-execution independent done-gate (two fresh reviewers, both pass with evidence) — where unavailable, the phase report says "verified by self-review only." Superpowers deltas: review in TWO STAGES — spec compliance first, code quality second, as separate passes (quality-reviewing code that misses spec wastes the pass, and conflating them lets beautiful-wrong-code through); and when verification FAILS, run systematic debugging (superpowers' 4-phase root-cause process) before writing any fix plan — fix causes, not symptoms.
5. **Ship** — GSD creates the PR and archives the phase (keep). Fusion adds the **learning tail**, in order: RETRO (params, outcome, one change) → theory_check (understanding changed? holistic rewrite now) → Claudeception gate (rare [V] lesson with crisp trigger → extract skill) → vault sync (wisdom-memory Tier 1.5 mirrors new records to Obsidian) → if the next phase won't start this session, drop a baton.

**Entropy gate wraps the whole loop**: a phase may not re-plan on pure self-critique — fresh external signal (verify evidence, user feedback, new research) is required, hard cap 2 self-directed iterations.

## Artifact map (who owns what — no duplication)

| Content | Home |
|---|---|
| Phase decisions, current phase state | GSD `CONTEXT.md` / `STATE.md` / `.plans/` |
| In-progress handoff mid-phase | `.baton/` (baton format, verified state of play) |
| Atomic cross-project lessons + failed paths | wisdom store (+ Obsidian mirror) |
| The durable why for THIS project | `THEORY.MD` or vault `Theory/project.md` |
| Tuned loop parameters per problem type | nested-learning meta-params |

## Anti-patterns

- Reimplementing GSD's subagent machinery instead of deferring to it where installed; hand-copying GSD files against its installer requirement
- Declaring a phase done from a convincing summary (taskmaster's exact failure mode)
- Letting Discuss decisions enter Plan untagged, or Plans re-walk logged failed paths
- Skipping the learning tail because the phase shipped — shipping without learning is the old loop
- Claiming fresh-context executors outside Claude Code

## Tool reference

| Need | Tool |
|---|---|
| GSD engine (Claude Code) | installed /gsd-new-project, /gsd-onboard + its subagents |
| Native loop elsewhere | modulated-loop-orchestrator + hydra-swarm |
| Memory ladder | wisdom-memory (+ vault_sync.py), theory-keeper, baton format |
| Learning tail | nested-learning (+ Claudeception gate) |
| Install/repair everything | hydra-setup (doctor absorbs new skills into the belt) |
| Which organs this station may load | `hydra_graph.py belt --phase <station>` |
| Cross-runtime memory | hydra-mem (capture) + hydra-graph (graph, RAG, vault); GSD's mempalace is Claude-Code-only and optional |
| Stack health, cost, readiness | setup-audit |
| Study a book, paper, spec or docs folder (Discuss/Plan research input) | book-to-skill (`/book-to-skill <file\|folder\|glob>` → on-demand skill in `~/.claude/skills/<slug>/`); then `hydra_graph.py absorb` + `graphify-import` to put it in the graph and vault |
