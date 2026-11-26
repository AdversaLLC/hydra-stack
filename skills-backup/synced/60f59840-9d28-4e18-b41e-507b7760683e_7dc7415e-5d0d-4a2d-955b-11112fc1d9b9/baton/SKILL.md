---
name: baton
description: Write or resume a session handoff file in `.baton/`. Use when handing in-progress work to another agent or a future session — ending a session with unfinished work, "hand this off", "pick up where I left off", passing a task to a fresh agent/another window/another model, running low on context, or persisting intent + learnings before context is lost. Covers both dropping a baton (writing the handoff) and grabbing one (resuming from it). Not for finished tasks.
metadata:
  authored_via: "claude-science"
  published_by: "agent"
  published_at: "2026-10-22T18:10:13.558Z"
  authored_by: "agent"
  authored_at: "2026-10-22T18:10:13.550Z"
  authoring_session: "df249c20-fa50-4f4d-9ba4-14b516173576"
  last_modified_by: "agent"
  last_modified_at: "2026-10-22T18:10:13.550Z"
---

# Baton

A relay only works if the baton is passed cleanly. The next runner — a fresh window, a future
session, a different model — starts with **zero of your context**. A baton is a single markdown
file that lets them grab the work and sprint instead of re-deriving what you already know.

**Core principle:** capture what the next runner can't reconstruct from the code or git history —
your *intent*, the *dead ends you already ruled out*, and the *exact next step* — grounded in
verified repo state, not your chat narrative.

**Drop a baton** when a session ends with unfinished work someone will continue, the user asks to
hand off, you're about to dispatch the rest to another agent, or you're low on context and want to
checkpoint. **Grab a baton** when starting work where a prior session may have left one (check
first). **Don't use** for a finished task, or for durable architecture rationale (that belongs in
a long-lived design doc).

## Where the Baton Lives

Always **`.baton/`** at the repo root (or the working directory when there is no repo), created if
missing — never elsewhere, or the next agent can't find it. It's local scratch: the first time,
make sure `.gitignore` covers it (add a `.baton/` line if not).

Filename: **`<YYYY-MM-DD>-<short-slug>.md`** (e.g. `.baton/2026-06-13-formula-eval-rounding.md`).
The next agent finds the latest with `ls -t .baton/`.

## The Iron Rule: Verify Before You Write

A baton built from the chat story instead of repo reality is worse than none — it sends the next
runner the wrong way with false confidence. Before writing, run `git status` and
`git branch --show-current` and confirm what is *actually* committed vs. uncommitted. If reality
contradicts the narrative, **the baton documents reality** and flags the gap.

**No git repo?** If `git rev-parse --is-inside-work-tree` fails, say so under State of Play ("not a
git repository; nothing is version-controlled"), verify against the filesystem and runtime instead
(file mtimes, running processes, service health), and skip the `.gitignore` step.

## Baton Format

Fill every section. If one is genuinely empty, write "none" — don't delete it (the next runner
relies on a consistent shape).

```markdown
# Baton: <one-line title of the work>

**TL;DR:** <1–3 sentences: what this is, where it stands, the single next action.>

## Intent & Goal
Why this work exists and the desired end state. Include the acceptance
criteria — ideally the exact command/test that must go green.

## State of Play (verified against git)
- Branch: <branch> — confirmed via `git branch --show-current`
- Committed: <what's landed>
- Uncommitted / in flight: <what's in the working tree, from `git status`>
- Verified working: <what you've actually run and confirmed>
- Assumed / unverified: <what you believe but haven't proven>

## Learnings & Landmines
The highest-value section — what the next runner can't get from the code:
- Non-obvious discoveries.
- **Dead ends already ruled out** (so they don't repeat them) and *why*.
- **Do NOT touch** zones and the reason.

## Pointers
- Key anchors: `path/to/file.ts:123` — what's there.
- Relevant docs / prior batons / PRs.
- Commands to get oriented or reproduce: `<cmd>`.

## Next Steps
Ordered, concrete, immediate action first. Not "finish the feature" — the
literal next move.

## Open Questions
Unresolved decisions + your current lean (so they can proceed if no one answers).
```

Don't restate the diff — it's already in git.

## Grabbing a Baton (resuming)

1. **Find it:** `ls -t .baton/` — read the newest.
2. **Trust but verify:** re-check State of Play against real `git status` before acting; the repo
   may have moved since the baton was dropped.
3. **Continue** from Next Steps.
4. **Retire it** when the work lands: delete it, after folding any durable learnings into a
   canonical doc. Don't let stale batons pile up.

## Response Behavior

After dropping a baton, state the exact path written and a one-line summary of what's in it.
