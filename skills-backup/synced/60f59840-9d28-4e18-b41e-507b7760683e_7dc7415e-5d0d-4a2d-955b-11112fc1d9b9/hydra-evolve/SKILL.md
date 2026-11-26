---
name: hydra-evolve
description: Self-evolution protocol for the hydra suite - how skills absorb new frameworks they encounter, condense against bloat, create new skills only through gates, and iteratively improve themselves. Formalizes the absorption loop proven in three live runs and adapts GAIR-NLP ASI-Evolve's LEARN-DESIGN-EXPERIMENT-ANALYZE cycle with its experiment-database and parent-selection ideas to skill improvement. One small candidate mutation per round, run through a fitness gauntlet (validator, packaged-byte assertions, regression tests, eval scores when available), recorded as a variant record, human-approved before shipping - no fitness function means no autonomous evolution, only proposals. A constitution clause protects the ledger, red-first rule, concession threshold, and verify-before-fusing from being evolved away. Triggers on "absorb this", "evolve the skills", "condense", "improve the suite", "asi evolve", or whenever a new skill, repo, or methodology is encountered.
metadata:
  authored_via: "claude-science"
  published_by: "agent"
  published_at: "2026-10-22T18:09:55.486Z"
  authored_by: "unknown"
  last_modified_by: "agent"
  last_modified_at: "2026-10-22T18:09:49.933Z"
---

# Hydra-Evolve — the suite improves itself, with receipts

Adapted from GAIR-NLP/ASI-Evolve (Apache-2.0): a closed loop of LEARN → DESIGN → EXPERIMENT → ANALYZE, repeated. Their hard-won requirement transfers whole: **no evaluation, no evolution** — a change you can't score is a drift, not an improvement. Where automated skill-fitness doesn't exist yet, selection is **human-gated**: Claude proposes with evidence, the user approves. Never mutate a shipped skill silently.

## The four operations

**ABSORB** (a new skill/repo/framework is encountered) — the protocol proven live three times:
1. Verify the target before fusing (fetch, check archived/successor status, license, maturity; for anything that runs code or carries instructions, also run `references/vetting-checklist.md`)
2. Triage every element into: **REDUNDANT** (we have it — cite where, adopt nothing), **DELTA** (strictly stronger — adopt with attribution + per-patch assertion), **TENSION** (conflicts with an existing organ — document the choice, never stack two auto-triggering spines), **NOVEL** (nothing covers it — route to CREATE)
3. Frame check before patching: is this an accessory or a rival spine? Popularity is not fit (a 268k-star rebuttal scores 2)
4. Land deltas under assert-per-patch; anchor-miss = stop, find the real anchor, retry
5. RETRO + wisdom records; deferred candidates go to FAILED PATHS as deferred-not-dead

**CONDENSE** (anti-bloat — skills must not grow monotonically):
- Same guidance living in 2+ skills → ONE home + a pointer from the others
- Every 3rd absorption run REQUIRES a condensation pass; measure words before/after and report the delta
- A skill whose body doubles since last condensation is a smell; split or trim
- Never condense away attribution, [U] flags, or constitution items

**CREATE** (new skill) — only through Claudeception's five gates (discovery cost, recurrence, crisp trigger, [V]-only content, not-covered-elsewhere). Most lessons stay wisdom records; graduation is rare by design.

**EVOLVE** (iterative self-improvement, the ASI-Evolve adaptation):
- **LEARN**: sample the archive — wisdom store + variant records are the experiment database; meta-params seed the round; parent selection is greedy on scored variants, exploration-biased toward never-tested skills (UCB1's spirit, honestly sequential)
- **DESIGN**: ONE small candidate mutation per round per skill — a description tweak, a section rewrite, one new rule. Big-bang rewrites are not evolution
- **EXPERIMENT**: the fitness gauntlet — quick_validate pass, package + shipped-byte assertions, script regression tests (setup.sh corruption/idempotency style), hydra-eval or drill-style behavior scores when they exist. What can't be scored is labeled [U] and needs the human gate
- **ANALYZE**: write a **variant record** (motivation / diff summary / gauntlet result / lesson) to the wisdom store; failed variants become failed_paths so they are never re-proposed
- **Entropy gate**: max 2 evolution rounds on one skill without fresh external signal or new eval data; self-critique alone cannot fuel round 3

## Constitution (evolution may strengthen these, never weaken or delete without explicit user override)
The [V]/[S]/[U] ledger and locator rule · red-first test evidence · Concession Threshold + frame check · verify-before-fusing · assert-per-patch · human gate on skill mutations · attribution and license notes

## Runtime honesty
In claude.ai/Cowork rounds are sequential and the "population" is an archive, not parallel workers. For code-evolution problems with a real scoring script (better code = better outcome), the heavy tool is the actual ASI-Evolve pipeline (clone + pip, Apache-2.0, needs an OpenAI-compatible endpoint) — hydra-setup checks for it; this skill is the lightweight loop, and like ASI-Evolve's own skill-vs-pipeline note, expect the full pipeline to search better.

## Anti-patterns
Evolving without a fitness signal (drift) · silent mutation of shipped skills · monotonic growth (absorb-absorb-absorb, never condense) · re-proposing archived failed variants · deleting constitution items because a round scored well · adopting by star count
