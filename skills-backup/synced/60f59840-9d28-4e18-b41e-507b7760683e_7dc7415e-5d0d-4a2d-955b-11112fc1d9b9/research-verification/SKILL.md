---
name: research-verification
description: A gate that runs before any claim, number, count, or ranking is written into a document, artifact, graph node, or message. Maps each kind of research assertion to the evidence that actually establishes it and to the evidence that only looks like it does. Triggers before saving an artifact, before quoting a figure or ranking, before marking a claim verified, before writing a count into a README or caption, and on the words "should", "probably", "seems to", or any expression of satisfaction that precedes a check. Complements veritas rather than duplicating it, since veritas audits INPUTS for coverage and this audits OUTPUTS for evidential standard. Adapted from the verification-before-completion pattern, translated from software testing into research terms.
metadata:
  authored_via: "claude-science"
  published_by: "agent"
  published_at: "2026-10-22T18:10:06.476Z"
  authored_by: "unknown"
  last_modified_by: "agent"
  last_modified_at: "2026-10-22T18:10:06.313Z"
---

# Research Verification — claiming is not establishing

Software testing has a discipline research prose lacks: you do not say the tests pass, you run them
and read the output. The same gap exists between knowing a number and having read it.

## The table

| Claim | Requires | NOT sufficient |
|---|---|---|
| "X GB/s measured" | A source stating it was measured, plus the exact SKU | A vendor peak; a figure recalled as "about right" |
| "verified from primary source" | The text retrieved and quoted, with identifier and page | Locating the document; reading its table of contents |
| A count in a README, caption, or manifest | Computed from the object being described, in the same cell | Typed; carried over from a previous version |
| "most cited" / "top ranked" | A topic-filtered corpus with the rejects saved | A raw keyword search result order |
| A claim in a knowledge graph | A `supported-by` or `documented-in` edge to evidence | An edge to another claim |
| "the file exists" / "the fetch worked" | Reading it back and checking size or checksum | The command exited 0 |
| A version, rank, parameter count, or date | Read from the source in this session | Recalled; inferred from a filename or title |
| "this endpoint works" | Two DIFFERENT inputs returning DIFFERENT outputs | HTTP 200 with well-formed output |
| A derived figure quoted in prose | Recomputed, or read back from the saved table | Read off a figure; remembered from an earlier cell |
| "the output looks right" (PDF, page, UI, build artifact) | A fresh regeneration, opened and looked at in full | The generator exited clean; last run's output |
| "independently checked" | A record of who produced and who checked the evidence, the checker differing in method or model | The producer rereading its own work; two copies of one model told to agree |

The last-but-one row is not hypothetical. An archive.org scrape endpoint returns HTTP 200 and
valid JSON with an identical body for every query. Status codes verify transport, not semantics.

## Red flags — stop and check

- The words **should**, **probably**, **seems to**, **looks right**, **as expected**
- Any expression of satisfaction written *before* the check ("Clean." "That works.")
- Writing a number that appears elsewhere in the same document
- A status field asserting more than the evidence in hand
- "Just this once" / "I'm confident" — confidence is not evidence
- Reporting a subagent's result without reading its declared deviations

## Procedure

```python
rv_check(claims)          # list of (claim, evidence_kind) -> flags the unsupported ones
rv_counts(path)           # every integer in a document vs the object it describes
rv_readback(path, values) # confirm quoted values appear verbatim in the saved artifact
rv_endpoint(fn, a, b)     # two different inputs must give different outputs
```

`rv_counts` exists because this failure recurs: a README claimed 132 files describing 129, and
"ten errors" describing six notes. Both numbers were typed rather than computed, both survived a
read-through, and both were caught only by an external audit.

## The honest exemption

Some things cannot be verified here — a document behind a lending restriction, a measurement
needing hardware, a rate limit not yet hit. Those get an explicit `UNGROUNDED: reason` marker.
An unverifiable claim that says so is fine. An unverifiable claim that does not is the failure.
A tooling gap (cannot render, cannot open, cannot run) is `INCONCLUSIVE`, never a pass.
