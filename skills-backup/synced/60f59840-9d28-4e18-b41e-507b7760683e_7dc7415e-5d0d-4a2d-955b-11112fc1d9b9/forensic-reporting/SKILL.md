---
name: forensic-reporting
description: Turns forensic examination or system-repair work actually performed in the session into a professional, defensible written report — evidence handling, acquisition/repair actions, findings graded by confidence (Confirmed/Strongly supported/Supported/Possible/Inconclusive/Unknown), and explicit limitations. Triggers on "document what we did", "make a report", "document this repair", "what did we change", "give me the investigation report", "create an investigation report", "write up this case", or any request to formalize completed forensic or repair work into documentation. Works standalone, independent of Paladin or Autopsy. Only documents actions and findings actually observed in this session or explicitly supplied by the user — never invents commands, hashes, timestamps, or findings; anything not directly verifiable is marked NOT VERIFIED or INFORMATION NOT AVAILABLE rather than inferred into fact.
---

# Forensic & Repair Reporting

Produces reproducible, defensible documentation of forensic or repair work that has already happened — not a template to fill with guesses. The report's credibility depends entirely on not overstating what's known.

## Core discipline

**Only document what actually happened.** Before writing anything, gather from the actual session: tool calls made, commands run, their real output, timestamps, and any facts the user has explicitly stated. If a detail (a hash, a timestamp, a command's exact output, an examiner name) isn't available from one of those two sources, write `NOT VERIFIED` or `INFORMATION NOT AVAILABLE` in that field — never fill it with a plausible-sounding placeholder.

**Grade every conclusion.** Every finding gets one of:
- **Confirmed** — directly observed, verifiable, no reasonable alternative explanation.
- **Strongly supported** — well-corroborated by multiple independent artifacts/sources.
- **Supported** — consistent with available evidence, limited corroboration.
- **Possible** — one plausible explanation among others.
- **Inconclusive** — evidence doesn't favor one explanation over alternatives.
- **Unknown** — not enough information to assess.

**Separate observation from attribution.** Write "the filesystem metadata indicates the file was deleted at [time]" — not "the user deleted the file." Attribution to a specific person or intent requires evidence that actually establishes it (e.g., authenticated session logs tying an account to the action); absent that, say the action-to-person link is not established by the available evidence.

**Use UTC timestamps** for all investigation/action records; note local time separately if relevant to the narrative.

## When to use which report shape

Ask (or infer from context) whether this is:
- **A forensic examination** — focus on evidence, acquisition, artifacts, findings with confidence grading.
- **A repair/recovery job** — focus on problem, diagnosis, changes made, before/after state, verification.
- Some jobs are both — use both sections.

## Forensic examination report structure

```
CASE INFORMATION
  Case ID:              [user-supplied or NOT VERIFIED]
  Examiner:             [user's name/email if given, else NOT VERIFIED]
  Date/time (UTC):      [actual]
  Environment/host/OS:  [as observed]
  Tool versions:        [as observed; NOT VERIFIED if not captured]

EVIDENCE
  Evidence identifier / Source device / Image name / Format
  Capacity / Serial number
  Hashes (source, destination, algorithm) — only if actually computed and seen

ACQUISITION / METHODOLOGY
  Tools used
  Commands/actions performed (verbatim, from actual session log)
  Read-only vs. write operations, explicitly labeled
  Verification procedure and result

FINDINGS
  Each finding: observation → supporting artifact(s) → confidence grade → alternative explanations considered
  Timeline information (if applicable)
  Network findings / filesystem findings / system findings (as applicable)
  Errors encountered during examination

CONCLUSIONS
  Stated at the same confidence level as their weakest supporting finding
  Explicit statement of what the evidence does NOT establish

LIMITATIONS
  What wasn't examined, what couldn't be verified, scope boundaries
```

## Repair/recovery report structure

```
ORIGINAL PROBLEM
  Reported symptoms
  Diagnostic evidence gathered (actual observations, not assumptions)

ROOT CAUSE
  Stated with confidence grade — repairs often proceed on "Supported" or "Possible" causes; say so

CHANGES MADE
  Commands/actions performed (verbatim)
  Files changed / packages changed / configuration changed
  Before/after state (only states actually observed, not assumed)

VERIFICATION
  What was checked after the change, and result

REMAINING ISSUES
  Anything unresolved or unverified

RECOMMENDED PREVENTATIVE ACTIONS
```

## Automatic reporting trigger

When asked to "document what we did" or equivalent, reconstruct the report from:
1. The actual sequence of tool calls and their real results in this session.
2. Facts the user has explicitly told you (case ID, examiner name, evidence descriptions) — attribute these as user-supplied, not independently verified, unless independently confirmed.

Do not backfill gaps with inference. If the session log doesn't show a hash being computed, the report says hashing was not performed or not verified — it does not show a hash value.

## Format

Default to a clean written report (Markdown or, if the user wants a formal deliverable, a `.docx`/`.pdf` via the appropriate skill) rather than a bare table dump. Use prose for narrative sections (methodology, findings discussion) and tables only where genuinely tabular (evidence list, hash comparison, timeline).

## What this skill must never do

- Invent a command, hash, timestamp, tool version, examiner action, or finding not actually observed or supplied.
- Upgrade a "Possible" finding to "Confirmed" because the user phrased their question confidently.
- Attribute an action to a specific person without evidence that actually establishes identity/attribution.
- Include secrets, passwords, API keys, or private keys in report output.
- Silently drop a limitation or gap to make the report look more complete than the underlying work.

## Handoff from other skills

Takes acquisition logs from `paladin-forensic-workflow`, artifact findings from `autopsy-analysis`, network findings from `wireshark-pcap-analysis`/`ip-intelligence`/`wireguard-analysis`, and timeline data from `forensic-timeline` (as these become available) and assembles them into the final document — it does not re-derive or re-verify their underlying technical claims, only faithfully represents what those skills actually reported.
