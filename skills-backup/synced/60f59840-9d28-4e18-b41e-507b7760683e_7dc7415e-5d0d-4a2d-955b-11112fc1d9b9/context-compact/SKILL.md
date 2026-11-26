---
name: context-compact
description: Harvest a live session's findings into a research-base graph so the transcript becomes disposable. Reads the current frame transcript and any folded spans, extracts candidate claims, measurements, corrections and open questions, dedupes them against nodes already in graph.db, writes the survivors as typed nodes and edges, and returns a receipt of what was added versus merged. Triggers on "compact the context", "graph what we found", "save this before it folds", "free up context", "add this to the vault", "the session is getting long", or at any natural checkpoint in a long session. Companion to research-base, which reads the same graph. Does NOT shrink the live context window - no tool can - it makes folding lossless and the next session cheap.
---

# Context Compact — make the fold lossless

A long session's findings live in the transcript until the transcript folds, and then they live in a
summary that was written to be short rather than to be queried. This harvests them into the graph
first, so what survives is structured and searchable instead of narrated.

## Honest scope

- **Does not** free the live context window. Folding is the harness's, not yours.
- **Does** make the fold lossless: findings are in `graph.db` before compression.
- **Does** make the next session start at roughly 1,400 words instead of a transcript.
- Run it at checkpoints, not once at the end. A finding harvested before a fold is verbatim; one
  harvested after is second-hand through a summary.

## Workflow

```python
# In the `repl` tool - host.frames lives there, not in python/r:
cc_fetch_transcript(frame_id)          # -> handoff/transcript.json

# In the `python` tool:
base = rb_load()                       # research-base skill
cand = cc_harvest_file("handoff/transcript.json", base)   # extract candidates
cc_review(cand)                        # PRINT and read them - never merge unread
receipt = cc_merge(base, cand)         # dedupe, write typed nodes and edges
cc_verify(base)                        # every new claim grounded or marked UNGROUNDED
rb_rebuild(base)                       # re-zip; save as a new artifact version
```

## What is worth harvesting

| Harvest | Skip |
|---|---|
| A number with a source and a basis label | A number restated from an earlier message |
| A claim that survived a challenge | A claim asserted once and never tested |
| A correction and what changed | Narration of the process |
| An open question with what it gates | A task that was completed |
| A rule the user endorsed as their standard | A one-off preference |
| Evidence that CUTS AGAINST the thesis | Confirmation of what was already believed |

The last row matters most. A base that harvests only supporting evidence becomes an echo of the
first session's assumptions.

## Rules

1. **Read candidates before merging.** `cc_harvest` proposes; you decide. Automated merge of
   unreviewed extractions is how a graph fills with confident nonsense.
2. **Every new claim needs a grounding edge or an `UNGROUNDED` source string** stating why not.
   `cc_verify` fails the merge otherwise.
3. **Dedupe by normalised title, then check the body.** A "new" node that restates an existing one
   with different wording is a merge, not an insert.
4. **Numbers keep their basis label** (peak / measured / bound) into the node body.
5. **Corrections get a `corrects` edge to the node they fix**, and the original node is edited
   rather than deleted — provenance is the point.
6. **Never harvest a value from a folded summary without checking it.** Use
   `host.archive.search('"exact phrase"')` to recover the verbatim bytes first; if the search comes
   back empty, the value is not recoverable and must not be written.

## Keeping bearings before the fold

`cc_recite(base)` returns three lines - thesis, current blocker, last correction - meant for the
turns BEFORE compaction, not only after. Orientation degrades while the window fills, not just when
it empties. `cc_should_checkin(...)` gives a threshold instead of relying on noticing.

Both adapted from the compact-plus plugin's recitation and usage-threshold patterns.

## Anti-patterns

- Harvesting at the end of a session only — the early findings are already second-hand by then.
- Writing one node per message. Nodes are findings, not events.
- Letting the graph grow monotonically. Merge duplicates; retire superseded nodes with a
  `corrects` edge rather than leaving both.
- Recording what you did. The graph is what is true, not what happened.
