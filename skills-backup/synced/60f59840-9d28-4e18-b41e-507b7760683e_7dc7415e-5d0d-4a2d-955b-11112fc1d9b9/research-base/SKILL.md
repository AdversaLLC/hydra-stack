---
name: research-base
description: Session-agnostic loader for a graphed research base (theory + curated runbook + typed-edge SQLite graph) built from a project's findings. Triggers on "load the research base", "what did we establish", "resume the knights corner project", "check the vault", "what gates progress", "what cuts against the thesis", or at the start of any session in a project that has a *-ResearchBase.zip artifact. Also documents how to REBUILD or EXTEND the base (build_vault.py / refine_vault.py pattern) so findings from a new session are graphed back in. Replaces re-reading a long transcript with ~1,400 words of loaded context.
---

# Research Base — load, query, extend

A research base is a folder with `THEORY.md` (operating theory, rewritten not appended),
`NAPKIN.md` (curated runbook, capped categories, every item has a "Do instead"),
`graph.db` (SQLite: `nodes`, typed `edges`, `fts`), and one markdown note per node so the
same folder opens as an Obsidian vault.

## Session start (do this first in a project that has one)

```python
base = rb_load()                 # finds newest *-ResearchBase.zip in the artifact store
print(base["theory"])            # ~750 words: the argument
base["blocking"]()               # what gates progress right now
base["ungrounded"]()             # claims resting on nothing measured — read before quoting
base["challenges"]()             # evidence that cuts AGAINST the thesis
base["search"]("ridge point")    # full-text over all notes
```

Apply THEORY silently. Curate NAPKIN on read: re-prioritise, merge, drop stale, cap 10/category.

## Edge types — the honesty machinery

`supported-by` · `documented-in` · `challenges` · `qualifies` · `corrects` · `gates` · `related`

A graph where everything merely "relates" hides which evidence cuts against the argument.
**Never quote a claim without calling `grounds(claim)` and `challenges()` first.**

## Status vocabulary (controlled, 14)

`verified` · `measured-elsewhere` · `derived` · `bound` · `unbuilt` · `stance` ·
`blocking-free` · `blocking-hardware` · `correction-applied` · `artifact` ·
`owned` · `owned-untested` · `in-transit` · `target`

Any new status must map onto one of these. If nothing in the base is `measured-here`,
say so — that absence is a finding.

## Extending after a session (nested-learning Level 1)

1. Write a `RETRO-<date>.md`: params used, outcome, what worked, what did not, **one** proposed change.
2. Add new nodes via `rb_note(folder, title, type, body, status, links)`; add typed edges via
   `rb_edge(src, dst, kind)`. Every new claim MUST get at least one `supported-by` or
   `documented-in` edge, or carry `source="UNGROUNDED: <why>"`.
3. Rewrite THEORY.md end-to-end if understanding changed. Do not append.
4. `rb_rebuild()` → regenerates `graph.db`, FTS, index, and a fresh `*-ResearchBase.zip`;
   save it as a new version of the existing artifact.

## Every 5 retros (Level 2)

Read all RETRO files. Revise NAPKIN heuristics. If a lesson is hard-won, verified, and has crisp
trigger conditions, propose extracting it as its own skill — propose, do not silently publish.

## Constitution (not evolvable)

- Labels peak / measured / bound stay at the point of use.
- Corrections are disclosed, never silently overwritten.
- No autonomous evolution without a fitness measure; human approves every published change.
