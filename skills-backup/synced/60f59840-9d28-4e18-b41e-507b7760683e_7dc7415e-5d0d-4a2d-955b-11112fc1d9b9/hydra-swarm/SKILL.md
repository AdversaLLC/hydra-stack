---
name: hydra-swarm
description: Fractal task orchestration across scales, translating the Fractal Hydra Swarm into real Claude runtimes. Structures big development jobs as a Prime, Hub, Leaf task tree - Prime frames the mission and merges, Hubs own workstreams, Leaves are atomic tasks - with fan-out breadth budgets scaled to tier, wisdom blocks that propagate insights and failed paths up the tree, briefs that push global lessons down, and capability-gap detection that proposes new skills or scripts when the same gap recurs (the honest form of self-architecting). In Claude Code, Hubs and Leaves can run as real parallel subagents via the Task tool; in claude.ai they run as tagged sequential passes in one context. Triggers on "swarm", "fractal", "hydra swarm", "break this into a task tree", "orchestrate this project", "parallelize this work", multi-workstream builds, or any job too big for one linear pass. Pairs with modulated-loop-orchestrator (the per-node engine), nested-learning (tuning), and wisdom-memory (persistence).
metadata:
  authored_via: "claude-science"
  published_by: "agent"
  published_at: "2026-10-22T18:09:59.672Z"
  authored_by: "unknown"
  last_modified_by: "agent"
  last_modified_at: "2026-10-22T18:09:59.667Z"
---

# Hydra Swarm — Fractal Task Orchestration

The Fractal Hydra Swarm translated to what Claude can actually run: a **task tree** where every node applies the same reasoning discipline at its own scale, insights flow up, lessons flow down, and nothing is fabricated. No "10,000 clones," no civilization of minds — a disciplined hierarchy with honest parallelism where the runtime provides it.

## Runtime check (do this first)

- **Claude Code**: real parallelism exists. Hubs and Leaves may be dispatched as subagents via the Agent tool (formerly called Task). hydra-mem hooks capture the main session's tagged lines automatically; subagent output is not captured, so the coordinator restates what matters.
- **claude.ai**: one Claude, one context. The tree runs depth-first sequentially with tags. Never claim parallel execution here.
- Either way the *structure* is identical; only the execution substrate changes. State which substrate is in use at the start of a swarm job.

## The tree (translation table)

| Doc concept | Real form | Fan-out budget |
|---|---|---|
| Prime Mind (Queen) | The main session: frames mission, decomposes into workstreams, merges everything | K ≤ 8 angle sketches on the mission framing |
| Hub Agent (Regional) | One workstream (e.g. "auth system", "data pipeline", "docs") | K ≤ 6 on workstream design |
| Leaf Agent (Sensor/ant) | One atomic task (one function, one file, one decision) | K ≤ 3 quick alternatives, or none if obvious |

Budget scales with tier because context is the real "computational capacity." A leaf burning 8 sketches on a rename is the anti-pattern the size-scaling in the original design exists to prevent.

## Workflow

1. **Prime pass** — read the project's operating theory first if one exists (theory-keeper), then frame the mission with the modulated-loop-orchestrator (Phase 0 router + fan-out if warranted). Output: a workstream map — 2 to 6 Hubs with objectives, interfaces between them, and merge criteria — plus the **graph contract** (adapted from loop & graph engineering, Bruniaux 2026): a state schema (each field with one named writer), the allowed transitions between Hub states and the forbidden ones, a rework budget per Hub (initial 2, only Prime decrements it), and the checkpoint rule (a baton or a hydra-graph `phase` node after every Hub merge, so an interrupted swarm resumes from the last merge, not from memory). Save to `tasks/swarm-map.md` when working with files. Keep the control plane static: Hubs are declared in the map; dynamic execution may create Leaves, never new Hubs.
2. **Hub passes** — per workstream: spec-lite (objective, boundaries, success criteria), decompose into Leaves, order by dependency. In Claude Code, independent Hubs may be dispatched as parallel subagents, each given: its brief (format in "Subagent brief and return block" below), relevant global lessons (from wisdom-memory), and the interface contracts. In claude.ai, run Hubs sequentially, tagged `[HUB: name]`.
3. **Leaf passes** — atomic execution, tagged `[LEAF: hub/name]`. Verify each leaf (test, build, check) before marking done. **Admission control**: never open more Leaves than the verifier can check — in sequential runtimes that is one open Leaf per Hub; in Claude Code the cap is the number of reviewers actually available, reserved before dispatch. Pause authoring at the cap, resume below a lower threshold, so the swarm does not oscillate.
4. **Wisdom propagation (bottom-up)** — every Leaf and Hub ends with a `WISDOM` block: 1-3 insights, failed paths with reasons, and any meta-note ("K=3 was too many for tasks like this"). Hubs merge their Leaves' blocks; Prime merges Hubs'.
4a. **Multi-session handoff** — when a Hub's work must continue in a future session (context limits, day boundary), drop a baton per wisdom-memory's handoff format rather than an ad-hoc summary; the next session grab-checks `.baton/` before resuming that Hub.
5. **Broadcast (top-down)** — when Prime's merge finds a lesson that affects other workstreams (a changed interface, a discovered constraint), push it into the briefs of not-yet-run Hubs immediately, not at the end.
6. **Final merge** — Prime runs the orchestrator's Synthesis + Baseline Check across all Hub outputs; contradictions between workstreams are resolved or logged as Open Questions.

## Self-architecting (honest version)

The doc's Level-4 "swarm spawns new agent types" becomes: **when the wisdom log shows the same capability gap twice or more** (e.g. "we keep hand-rolling schema validation"), Prime proposes growing the body — draft a new script, a new SKILL.md (via skill-engineering), or a tool/connector suggestion — and asks the user before creating it. When the gap is a learned lesson rather than a missing tool, route through nested-learning's Claudeception post-trigger (five gates) instead. The swarm never silently grows itself.

## Emergence claims policy

Cross-workstream synthesis regularly finds things no single pass saw — report those as **Unique Insights** with the passes they emerged from. Do not label ordinary synthesis "collective consciousness" or claim capabilities beyond what the transcript shows. Swarm value = coverage + interface discipline + wisdom reuse, and that is enough.

## Wisdom record format (feeds wisdom-memory)

```
WISDOM
- insight: [V|S|U] text          (something future jobs should know)
- failed_path: text — why died   (prevents re-exploration)
- meta: text                     (tuning note for nested-learning)
```

## Subagent brief and return block

Every dispatched Hub or Leaf gets one brief and owes one return block. A subagent starts with no conversation history, so the brief is all it knows. (Basis: Architect Foundations L04-03, L04-04, L06-03, L07-04.)

Brief, in this order:
- **Source**: who asked and why, in one line, plus the mission or Hub objective it serves.
- **Inputs**: absolute paths only, never "the file we discussed"; paste short facts, point to long ones.
- **Role**: the one job, and what is out of scope.
- **Owns / Off-limits**: the files it may write and the files it must not touch.
- **Return shape**: the block below, plus any named fields.

Return block, the last thing in the reply:

```
STATUS: done | partial | empty | failed
EVIDENCE: command and result, or path:line, for each claim
WISDOM: (format above)
```

- A missing STATUS block counts as failed, however good the prose looks. `empty` means it looked and found nothing, which is a valid result; `failed` means it could not look.
- The coordinator checks every result against the brief before merging: right files, inside the owned paths, answers the question asked. A subagent can finish cleanly while doing the wrong job, so `done` is a claim and the evidence is the proof.
- Run subagents in parallel only when the work is independent and the owned files are disjoint. Work that shares a file or needs another's output runs in sequence.

## Anti-patterns

- Dispatching a subagent without the brief fields, or accepting a reply with no STATUS block (see "Subagent brief and return block")
- Claiming parallel agents in claude.ai, or clone counts the transcript can't show
- Leaves doing Prime-scale fan-out; Hubs skipping interface contracts
- Discarding WISDOM blocks instead of propagating and persisting them
- Growing new skills/scripts without user approval
- Running a swarm on a job one orchestrator pass could handle — the complexity router in modulated-loop-orchestrator decides, not enthusiasm

## Tool reference

| Need | Tool |
|---|---|
| Per-node reasoning engine | modulated-loop-orchestrator skill |
| Real parallel Hubs/Leaves | Claude Code Agent tool, formerly Task (Claude Code only) |
| Persist WISDOM blocks | hydra-graph (`graph add`; hydra-mem hooks capture tagged lines automatically) |
| Organs allowed at this station | `hydra_graph.py belt --phase execute` |
| Tune budgets over time | nested-learning skill |
| Swarm map + task files | `create_file`, `str_replace` in `tasks/` |
| Verify leaves | `bash_tool` |
