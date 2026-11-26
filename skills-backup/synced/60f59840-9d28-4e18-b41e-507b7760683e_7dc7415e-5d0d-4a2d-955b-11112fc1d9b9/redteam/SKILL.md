---
name: redteam
description: Adversarial critique skill for claude.ai. Triggers on red team, attack, critique, stress test, devil's advocate, find weaknesses, break this, find flaws, find fatal flaws, what's wrong with X, or any request to validate a plan/design/argument by trying to destroy it. Runs Phase 0 (audit the evaluation criteria itself), then 5–8 sequential adversarial passes from distinct perspectives chosen to match the target, then synthesizes findings by severity. Single Claude doing sequential perspective-shifts — not a fake 32-agent swarm. The original required subagents, sentence-transformer embeddings for ROSE diversity, and Nexus broadcast — none of which work in claude.ai.
---

# RedTeam — claude.ai Adversarial Critique

The job: take a target (plan, design, argument, code, claim) and seriously try to break it. Find the load-bearing assumptions and stress them. Surface the failure modes the target's author didn't consider.

This is the claude.ai version. The Claude Code v3 with 32-agent swarms, ROSE semantic-diversity embedding filters, and GroundedPRM step-level verification needs subagents and ML libraries we don't reliably have here. What survives is the **methodology**: Phase 0 is non-negotiable, perspective diversity matters more than perspective count, and synthesis is where most of the value lives.

---

## Phase 0 — Audit the evaluation criteria FIRST

Before attacking the target, attack the *frame*.

If the user asks "find weaknesses in plan X", check:
- Is "weakness" defined? Compared to what alternative?
- Is the goal of the plan stated? Without a goal, "weakness" is undefined.
- Are there hidden constraints (budget, time, regulatory) that make some "weaknesses" actually unfixable trade-offs?
- Is the user looking for *fatal* flaws, *cosmetic* flaws, or both?

If Phase 0 surfaces a malformed evaluation, **stop and surface that to the user before attacking**. A redteam pass on a malformed target produces noise.

This is the one phase from the original v3 that's both essential and fully implementable in claude.ai. Don't skip it.

---

## Phase 1 — Pick the attack roster

Choose 5–8 distinct adversarial perspectives that fit the target. Don't pick generically — pick perspectives that would actually *find different things*.

For a software design, useful perspectives might be:
- Security engineer (attack surface, auth, data leaks)
- SRE (failure modes under load, what happens at 3am)
- Junior dev (where will someone misuse this API?)
- Adversarial user (how do I cheat this system?)
- Maintainer 6 months later (what's the worst part to come back to?)
- Compliance / legal (regulatory exposure, audit trail)
- Cost engineer (where does this become expensive at scale?)

For an argument or claim, useful perspectives might be:
- Empiricist (what evidence supports the load-bearing claims?)
- Counter-example hunter (when does this fail?)
- Steelmanned opponent (best version of the opposite view)
- Expert in the specific domain
- Person harmed by the conclusion (incentive analysis)
- Future you in 5 years (what aged poorly?)

For a plan, useful perspectives might be:
- Person who will execute it (where does this break in week 2?)
- Person who has to fund it (why isn't this a worse use of capital than alternative X?)
- Person it affects (consent, agency, second-order effects)
- Pessimist (what does the failure-mode timeline look like?)
- Time auditor (where is the schedule fictional?)

State your roster explicitly before attacking. The user gets to disagree with the choice before you waste tokens on the wrong angles.

---

## Phase 2 — Run each perspective

For each perspective in the roster, do a sequential pass. **One paragraph per perspective**, capturing:
- The single strongest finding from that lens
- Severity: BLOCKER / SERIOUS / MINOR
- Whether the finding is *fixable* or *fundamental*

Discipline: each perspective must produce a finding that no other perspective in this run already produced. If you catch yourself repeating, switch perspectives or end early.

This replaces v3's "ROSE semantic diversity threshold" — instead of computing cosine similarity between agent findings, you (one Claude) just notice when you're saying the same thing twice and stop yourself. It's less rigorous than ROSE but it's what's actually possible here.

---

## Phase 3 — Synthesis

After all perspectives have run, produce a synthesis with three buckets:

**BLOCKERS** — issues that, if not addressed, mean the target should not ship as-is. Usually 1–3 items. Each blocker gets a one-sentence statement, the perspective(s) that found it, and the smallest fix that would address it.

**SERIOUS** — issues that don't block but should be addressed before counting the target as "done". Usually 3–8 items. State each, attribute to perspective, and note priority.

**MINOR** — issues worth noting but not solving in this round. Usually 2–10 items. Brief.

Discipline: don't pad. If there are no real blockers, say "no blockers found" — that's a result. The temptation is to manufacture severity to feel productive. Resist it.

---

## Phase 4 — The honest summary line

End with one sentence: would a competent professional in the target's domain ship this as-is, fix the blockers and ship, or rethink from scratch?

Three options, no fudging.

---

## What got stripped from v3

- **32 parallel agents** — no subagents in claude.ai. 5–8 sequential perspectives, well-chosen, beat 32 noisy parallel ones anyway.
- **Occupation-matched roster from 867 occupations** — overkill for most targets. Pick perspectives by what would actually *find different failure modes*, not by occupation cardinality.
- **ABP scoring on each finding** — kept implicitly (don't be cruel, don't be dishonest, don't be performative). Not as a numeric gate.
- **Entropy-injected diversity** — replaced by "notice when you're repeating, switch or stop".
- **ROSE semantic diversity via sentence-transformers** — same. Cognitive discipline > ML filter, when you only have one Claude.
- **GroundedPRM step-level verification** — replaced by Phase 4's honest summary line. The synthesis is the verification.
- **Gossip-weighted synthesis with reputation_ema** — there's no agent reputation here. Just synthesize honestly.
- **PoABP Consensus** — same.
- **Nexus CRITICAL emit** — no bus.
- **Kaizen log auto-write** — no persistent log.
- **Gleaner blueprint pre-load** — no Gleaner skill in claude.ai.

---

## When NOT to use this skill

- The user asked for **feedback**, not **attack**. Feedback is generative ("here's what would help"); redteam is destructive ("here's what's broken"). Misapplied redteam feels mean.
- The target is the user themselves (their writing, their work, their plan for their own life). Default to feedback, ask before attacking.
- The target is a person or organization the user is in conflict with. Redteaming someone Joshua is mad at is mostly a vehicle for confirmation bias — surface that and offer to do something more useful.
- The user has already decided. Redteaming a decision the user has irrevocably made just makes them feel bad without changing outcomes.

---

## Severity calibration cheat-sheet

| Label | Threshold |
|---|---|
| BLOCKER | A reasonable person, after seeing this, would not ship the target as-is |
| SERIOUS | The target has a meaningful flaw, but a reasonable person might still ship and address later |
| MINOR | Worth noting, but the target is mostly fine on this dimension |

If you find yourself wanting to mark something BLOCKER for emphasis, but it's actually SERIOUS — don't. Severity inflation kills the signal value of the labels.

---

## Tool reference

| Need | Tool |
|---|---|
| Read the target if it's a file | `view` |
| Look up real-world failure cases for a domain | `web_search` |
| Visualize an attack tree | `visualize:show_widget` (diagram module) |
| Run static analysis on code | `bash_tool` (semgrep, etc., if installable) |
