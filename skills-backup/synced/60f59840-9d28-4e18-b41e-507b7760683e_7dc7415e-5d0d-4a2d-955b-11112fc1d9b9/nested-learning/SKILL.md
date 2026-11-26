---
name: nested-learning
description: Meta-learning loops for orchestrated work - the system gets better at learning, not just at tasks. Level 0 is doing the job; Level 1 runs a structured RETRO after every orchestrated or swarm job (params used, outcome, one proposed change) and persists tuned meta-params per problem type via wisdom-memory; Level 2, every 5 or so retros, reviews the retro history and revises the heuristics. Includes the Claudeception post-trigger - when a job produced a hard-won, verified, recurring lesson with crisp trigger conditions, escalate it from a wisdom record into a new extracted skill (blader/Claudeception in Claude Code, or a drafted .skill in claude.ai); most lessons stay records. Triggers on "retro", "retrospective", "meta-learning", "nested learning", "claudeception", "save what we learned as a skill", "extract a skill", "what have we learned", "tune the orchestrator", or automatically after any swarm or full orchestrator run. Pairs with modulated-loop-orchestrator, hydra-swarm, and wisdom-memory.
metadata:
  authored_via: "claude-science"
  published_by: "agent"
  published_at: "2026-10-22T18:10:04.358Z"
  authored_by: "unknown"
  last_modified_by: "agent"
  last_modified_at: "2026-10-22T18:10:04.353Z"
---

# Nested Learning — Learning How to Learn (bounded, honest)

The Nested Learning doc translated to a loop Claude can actually close: no meta-gradients, no super-exponential curves — a disciplined retro cycle with persisted parameters and one-change-at-a-time hill climbing, which is exactly what the doc's own implementation sketch falls back to.

## The levels (translation)

| Doc level | Real form | Cadence |
|---|---|---|
| Level 0 — base learning | Doing the task; wisdom/failed-path capture (already handled by orchestrator + swarm) | every job |
| Level 1 — agent meta-learning | RETRO block after each orchestrated job; update meta-params for that problem type | every orchestrated/swarm job |
| Level 2 — meta-meta | Retro-of-retros: review the last ~5 RETROs, revise the retro questions and tuning heuristics themselves | every ~5 retros, or when Level 1 stalls |
| Level 3+ | **Not run.** No data exists to learn from at that height in a single user's workflow. State this if asked. |

## Meta-params (the θ vector, translated)

Stored per **problem type** (coding, research, architecture, writing, debugging, ...) in wisdom-memory as `meta_param` records, mirrored to `.hydra/meta-params.json` when a persistent disk exists:

```json
{
  "coding": {"fanout_K": 4, "promote": 2, "max_depth": 2, "default_modes": ["analytical","adversarial"], "ceremony": "standard"},
  "research": {"fanout_K": 6, "promote": 3, "max_depth": 3, "default_modes": ["analytical","creative","strategic"], "ceremony": "deep"}
}
```

At the start of any orchestrated job: **load meta-params for the problem type** (wisdom-memory search: `meta_param <type>`) and use them to seed Phase 0 instead of defaults. Absent params → orchestrator defaults, and this job seeds them.

## Level 1 — the RETRO block

Run at the end of every orchestrated or swarm job, before the resumption brief:

```
RETRO
- problem_type: coding
- params_used: K=4, promote=2, depth=2, modes=[analytical,adversarial]
- outcome: [success | partial | failed]  + one-line evidence (tests passed, user accepted, criteria met)
- efficiency: [insights or tasks completed] vs [passes spent] — where was effort wasted?
- one_change: raise/lower exactly ONE param, with reason
- keep_or_revert: (filled next comparable job) did the last change help?
- theory_check: did understanding of THIS project change enough that the operating theory needs a holistic rewrite? If yes → theory-keeper, now, in-session (sticky rule), not later.
- verdict_overturned: did anything Verify accepted get overturned later (by the user, a later test, production)? Creator–verifier separation is tested, not assumed (Bruniaux 2026); a rising overturn rate is a Level-2 trigger.
```

Rules: **one parameter change per retro** (the honest hill-climb — simultaneous changes make attribution impossible). If the next comparable job is worse, revert and log it. Persist the RETRO as a `meta` record and the updated params as `meta_param` records via wisdom-memory.

## Level 2 — retro-of-retros

Every ~5 retros (or when the same param oscillates twice):

1. Pull the last 5-10 RETRO records for the problem type (wisdom-memory search).
2. Ask the meta-questions: Are the retro questions measuring the right thing? Is "outcome" being judged consistently? Is one problem type actually two (split it)? Is a param that never moves worth tracking? Is there a recurring failure the params can't express (→ propose a new param or a new heuristic)?
3. Output: revised retro template and/or heuristic, logged as a `meta` record tagged `level2`.

This is where "self-discovered learning strategies" live honestly: new heuristics come from evidence in the retro history, and each carries the record IDs it was derived from.

## Adaptive specialization (translated)

The doc's explorer/exploiter split emerges naturally: problem types with high novelty drift toward high K + low promotion threshold; routine types drift toward K=0-2 and shallow ceremony. Let the per-type params diverge — do not average across types.


## Skill extraction post-trigger (Claudeception)

After the RETRO, run one extraction check. A lesson graduates from wisdom record to **extracted skill** only if it clears ALL five gates:

1. **Discovery** — it cost real investigation, debugging, or trial-and-error; a documentation lookup never qualifies
2. **Recurrence** — it will plausibly apply again (across projects, or as a project pattern that will repeat)
3. **Crisp trigger** — a specific error message, symptom, or scenario exists that a retrieval-optimized description can match (the difference between "helps with database problems" and "fix for PrismaClientKnownRequestError in serverless")
4. **[V] only** — the lesson is verified to work in the ledger; [S]/[U] lessons never become skills, because an extracted skill is a claim future sessions will trust
5. **Not already covered** — search existing skills and wisdom records first

Most jobs produce zero extractions. If a lesson clears fewer than five gates, it stays a wisdom record — that is the normal outcome, not a failure.

**Runtime routing when the bar is met:**

- **Claude Code + Claudeception installed** (check `~/.claude/skills/claudeception/` or project `.claude/skills/claudeception/`): hand off — follow its template (Problem / Context-Trigger Conditions / Solution / Verification) and quality gates. If the user runs its UserPromptSubmit hook, extraction evaluation happens automatically each prompt.
- **Claude Code without it**: draft the skill folder natively into `~/.claude/skills/NAME/` or `.claude/skills/NAME/` using the same four-section template, **with user approval before creating** (the suite's self-architecting rule); mention once that `git clone https://github.com/blader/Claudeception.git ~/.claude/skills/claudeception` automates this permanently.
- **claude.ai**: draft SKILL.md per skill-engineering conventions, validate, package as a `.skill` file for the user to upload — approval implicit in the upload.

**After extraction**: write a `decision` record to wisdom-memory linking lesson to skill name ("extracted skill semver-prerelease-comparison from job X retro"), so memory knows the lesson graduated and never re-proposes it. The extracted skill's description IS its retrieval key — spend effort there; a skill that never triggers is a dead record with extra steps.

## Guardrails

- Extraction is escalation, not default: record first, skill only past all five gates; never extract [S]/[U] lessons
- Meta-learning **never** overrides the orchestrator's Immutable Baseline, verification ledger, or entropy gate. Only budgets, mode defaults, and ceremony are tunable.
- A param change is an [U] hypothesis until a subsequent comparable job confirms it — track that in `keep_or_revert`.
- If retros show quality dropping across the board, freeze params at last-known-good and tell the user rather than continuing to climb.
- Performance framing: "insight per pass," never fabricated compute/energy numbers.

## Anti-patterns

- Changing several params at once; tuning on one noisy sample; letting Level 2 rewrite Level 1 records
- Running Level 2 with fewer than 5 retros of data
- Treating the doc's super-exponential growth math as an expectation to report
- Meta-learning theater: producing RETRO blocks that never actually change the next job's Phase 0

## Tool reference

| Need | Tool |
|---|---|
| Persist/retrieve RETROs and meta-params | hydra-graph (`graph add --kind retro|meta_param`, `graph recall "meta_param <type>"`); wisdom-memory Tier 3 in claude.ai |
| Seed job parameters | modulated-loop-orchestrator Phase 0 |
| Mirror params to disk (Claude Code) | `.hydra/meta-params.json` via file tools |
| Analyze retro history | `bash_tool` (counts, trends) |
