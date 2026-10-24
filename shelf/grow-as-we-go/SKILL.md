---
name: grow-as-we-go
description: Runs at the END of a skill's use, not the start. Evaluates what the skill actually produced against what its own SKILL.md promised, grades any gap by research impact rather than by code severity, and writes a typed defect node into the research graph so the skill improves with every use instead of accumulating unrecorded rough edges. Triggers when a skill's work completes, when a helper returns a degraded or placeholder value, when output is right but required manual steps the skill claimed to handle, and on "did that skill work", "review that skill", "what did it miss", "log a defect", "grow as we go". A skill that fails loudly is less dangerous than one that quietly returns less than it promised, and the grading reflects that. Companion to research-base and context-compact, which own the graph it writes to.
---

# Grow As We Go — every use makes the skill better, or says why not

A skill is a promise written in its own description. The only moment you can check the promise is
after it has run. This runs then, and records what it finds where it will be acted on — so the
catalogue compounds instead of calcifying. Every use either confirms the promise or produces a
graded, fixable defect. Nothing stays merely annoying.

## The severity scale is about research impact, not code

This is the whole point, and it inverts ordinary bug triage.

| Grade | Meaning | Example from this project |
|---|---|---|
| **critical** | A wrong or unsupported claim reached a deliverable | A README stating counts that disagreed with its own contents, shipped twice |
| **high** | Silent degradation — ran without error, returned less than promised | `cc_recite` returned "(no theory loaded)" and looked like output |
| **medium** | Failed loudly — work blocked, but nothing wrong entered the record | `kernel_loader.py` raised NameError under the documented exec path |
| **low** | Caught by an external gate before any harm | A description over the registry's character limit, rejected at publish |
| **design-gap** | Worked as written, but the writing under-promises the need | Harvest reads the live transcript but not folded spans |

**A loud failure outranks a quiet one in desirability, not severity.** A NameError costs a turn.
A helper that returns a plausible placeholder costs a wrong claim in a paper, and you will not
know. Grade accordingly: `high` sits above `medium` because silence is worse than a stack trace.

## Procedure

```python
sp_promises(skill_name)              # parse SKILL.md into checkable promises
sp_grade(promise, observed)          # -> critical|high|medium|low|design-gap|met
sp_log(base, skill, grade, what,     # write a Defects/ node + `challenges` edge to the skill node
       evidence, fix)
sp_open(base, skill=None)            # open defects, worst first
sp_close(base, defect_id, how)       # close with a `corrects` edge - never delete
```

## Rules

1. **Run it on the way out, every time — including when the skill worked.** "Met" is a finding.
   A skill with no postmortems has no evidence of working, only an absence of complaints.
2. **Evidence is a value, not a description.** "returned `(no theory loaded)` while `graph.db`
   loaded 75 nodes" — not "the theory line was broken".
3. **Grade by what reached the record**, not by how alarming the traceback looked.
4. **A defect gets a `challenges` edge to the skill's node.** It is evidence against the skill, and
   the graph should hold it the same way it holds evidence against a thesis.
5. **Close with a `corrects` edge and keep the original.** A defect list that shrinks by deletion
   teaches nothing.
6. **A skill that produced a defect graded `critical` or `high` gets its description amended**, not
   just its code — the promise was wrong, not only the implementation.

## Anti-patterns

- Running it only when something broke. Then the record is a complaint log, not an evaluation.
- Grading by exception type. `NameError` is not worse than a placeholder string; it is better.
- Logging "should improve error handling". Name the value, the promise, and the fix.
- Fixing the code and leaving the description promising what it never delivered.
