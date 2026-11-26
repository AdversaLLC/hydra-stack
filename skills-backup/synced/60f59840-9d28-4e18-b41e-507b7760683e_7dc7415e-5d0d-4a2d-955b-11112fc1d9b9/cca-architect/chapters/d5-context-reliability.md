# D5: Context management and reliability (15%)

## Preserve on purpose

- **Nothing crosses a boundary unless you put it there:** not a call, an agent, a compaction or a human handoff. Context is what the model holds now; memory is stored outside (database, CLAUDE.md, memory files) and retrieved later. [S]
- **Triage each item** [S]:
  - **Pin verbatim** anything a paraphrase would change downstream: IDs, amounts, dates, and user constraints written as prohibitions.
  - **Summarize faithfully** where only the conclusion matters.
  - **Drop** the rest, but keep "ruled out X because Y".
  - A wrong ID is worse than none.
- **Compress with headroom** (course: start at 70-80% full [U]), not at exhaustion and not every turn. One generic pass that also paraphrases IDs is the trap. [S]
- **One handoff shape everywhere** (fork, fresh start, subagent, human) [S principle; U names]:
  - scope, including what is out of scope;
  - entityIds;
  - keyFindings;
  - constraints;
  - openQuestions.
  - For a human, add what was tried and what is uncertain, and why.
- **Claude Code compaction** (automatic or `/compact`) re-attaches skill bodies, not your facts; pin those yourself. [S]

## Exploration budget [S]

- **CLAUDE.md seeds structure;** it doesn't replace search.
- **Glob → Grep → Read:** Glob finds candidates, Grep the pattern, Read only the excerpt.
- **Spend context in proportion to the task,** not the repo.

## Escalation

- **Ambiguity signals:** conflicting instructions, two reasonable readings, missing decision-critical information, a case the policy doesn't cover. [S]
- **Ambiguity is not escalation.** A one-line stated default or one clarifying question usually settles it; over-escalation defeats automation. [S]
- **Routing** [S]:
  - **Escalate:** policy gap (refund over the limit), an explicit request for a human, no progress, permission or business-rule errors.
  - **Retry:** transient retryable errors.
  - **Review queue:** low confidence on a business-impacting decision.
  - Reject (discard or redo, no human) is different from escalate.
- **Category beats confidence.** The course's function, with its fail-open gaps closed (thresholds [U]):

```python
def route(o):
    if o.error:
        if o.error == "transient" and o.retryable and o.attempt < 2: return "retry"
        if o.error == "validation" and o.attempt < 2:               return "fix_input_retry"
        if o.error in ("permission", "business_rule", "policy_gap"): return "escalate"
        return "human_review"                     # unknown or exhausted: fail closed
    if o.confidence is None: return "human_review"   # course defaulted to 1.0: fails open
    if o.confidence < 0.4:   return "reject"
    if o.confidence < 0.8:   return "human_review"
    return "auto_approve"
```

- **A human handoff carries** IDs verbatim, confirmed findings, the limit breached, what was tried and the exact ask. "Customer wants a refund, please help" is context-free failure. [S]
- **Graceful degradation:** finish the safe part and flag the rest with reasons ("10 SKUs updated, 2 flagged and unchanged"). Avoid both false confidence and total refusal. [S]

## Error propagation [S]

- **Blast radius** is what depends on the failed output, not system size or agent count.
- **The owning level decides.** A subagent reports accurately and stops; it never aborts the job. The coordinator, or the sub-coordinator that owns the unit, chooses retry, partial, abort or escalate.
- **Contain to the smallest scope:** retry the smallest unit, abort only the dependent chain, keep independent branches, and name what was lost.
- **Agent error report:** agent, errorCategory, isRetryable, attempt, message. The coordinator fills `dependents` from its own plan. [U schema]
- **Pass up outcomes,** never raw exceptions.
- **Silent failure:** `isError: false`, well-formed, wrong job (a security reviewer returning style notes). Check findings against the mandate and flag off-mandate items individually. Empty is not off-mandate.

## Confidence routing [S]

- **Route per field:** approve vendor and total; review only `due_date` at 54%. Never reject a whole record for one field.
- **Measure calibration before trusting a threshold:** 0.9-scored fields should be right about 90% of the time. ECE is the bin-weighted gap |accuracy − confidence|.
- **Re-measure after any change** to the model, prompt or inputs (drift). Audit with stratified samples across bands and field types, not just the approved pile.
- **Self-reported LLM confidence runs high.** [U]

## Provenance [S]

- **Every final claim traces to a source.** Each hop (research → summary → integration) can drop the reference while the claim survives.
  - Carry source, retrievedAt, confidence and agent with each claim [U field set].
  - Return a `summary` plus a claim-to-source map, because prose integration strips attribution.
- **Untraceable claims** are flagged, dropped or marked unverified, never shown like sourced ones.
- **Conflicts:** write "A reports X (source, date); B reports Y". Never take the first, the louder, the average or the story-fitting one; investigate why they differ.
- **Re-summaries lose precision** ("skips JWT expiry on refresh" becomes "possible security concerns"). Track hops and re-verify at the source before auto-approval or citation (course: at 3+ hops [U]).

## Exam traps

- Summarizing only when full; paraphrased IDs; constraints softened into preferences.
- Escalating a retryable error or every doubt; a bare "please help"; refusing all when part is uncertain.
- A subagent aborting the job; identical retries of a validation error; aborting everything on one failure.
- Trusting `isError: false` without a mandate check; empty treated as failure.
- A whole record rejected for one field; fixed-forever thresholds; auditing only approved items.
- Silently resolving or averaging a conflict; "stop summarizing" as the fix for degradation.
- "CLAUDE.md replaces glob and grep."
