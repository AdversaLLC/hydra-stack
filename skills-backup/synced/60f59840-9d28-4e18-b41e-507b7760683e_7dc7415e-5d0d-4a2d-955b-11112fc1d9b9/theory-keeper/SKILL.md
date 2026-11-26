---
name: theory-keeper
description: Maintains a per-project operating theory - the durable why behind ongoing work - completing the suite memory ladder (baton carries in-progress state, wisdom-memory carries lessons, theory-keeper carries the current mental model). Adapted from blader/theorist verified mechanics - one theory doc per project, HOLISTIC REWRITES never appended logs, sections for problem thesis, current system model, strategy rationale, key discoveries and pivots, and open questions, updated when understanding changes rather than when code churns, sticky once active. Two homes - THEORY.MD at repo root (defer to blader/theorist if installed) or an Obsidian vault note at Theory/project-name.md with wikilinks into Hydra Wisdom notes. Triggers on "operating theory", "update the theory", "why is the system shaped this way", "what changed in our understanding", after debugging pivots, and at Phase 0 of orchestrated jobs on ongoing projects. Not a task plan, changelog, status report, or baton.
---

# Theory Keeper — the durable why

The suite remembers three ways: batons carry *in-progress state*, wisdom records carry *atomic lessons*, and the theory doc carries the *current mental model* — the thing that makes future decisions coherent. This skill keeps that third layer alive. Mechanics adapted from blader/theorist (verified 2026-08-12); Obsidian home added for vault users.

## The one rule that matters

**Holistic rewrite, never append.** A theory doc that accretes entries becomes a changelog and stops being a theory. When understanding changes, rewrite the affected sections so the document always reads as the *current* best model — the old model survives only as an entry under Key Discoveries & Pivots, with why it fell.

## When to update

- A debugging or investigation pivot changed what you believe about the system
- A verify/implement loop's outcome contradicted the model
- An orchestrator job's Synthesis produced a resolved conflict or unique insight about *this project's nature*
- A wisdom-memory `decision` record was written that reshapes strategy

**Not** on code churn, task completion, or routine progress — those belong in commits, task lists, and batons respectively. Update when *understanding* changes.

## Document homes (pick one per project)

1. **Repo**: `THEORY.MD` at repo root — exact theorist convention; if blader/theorist is installed (`~/.claude/skills/theorist/` or `~/.codex/skills/theorist/`), defer to it entirely and just feed it (this skill then only routes suite events to theory updates).
2. **Obsidian vault**: `Theory/<project>.md` with frontmatter (`type: theory`, `project`, `updated`, `tags: [theory, hydra-wisdom]`). Wikilink pivotal wisdom notes inline — `[[20260812085549-correction-...]]` — so the theory cites its evidence. Filenames avoid `# | ^ : % [ ]`.

3. **obsidian-mind vault** (verified template, preferred when present): the theory lives at `reference/Theory - PROJECT.md` — obsidian-mind's reference/ folder is exactly "codebase knowledge, architecture maps" — wikilinking `[[Key Decisions]]`, relevant `[[Gotchas]]` entries, and Hydra Wisdom evidence notes. Its PostToolUse hook validates the frontmatter; the template already complies. brain/Patterns.md holds cross-project patterns; the theory doc holds THIS project's model — don't blur them.

Never more than one home; a split theory is two stale theories.

## Structure (from assets/theory-template.md)

1. **Problem thesis** — what problem this project actually exists to solve, in current words
2. **Current system model** — how you believe the system works, including load-bearing assumptions tagged [V]/[S]/[U] per the suite ledger
3. **Strategy & shape rationale** — why the approach is shaped the way it is; what alternatives were rejected and why (pull from FAILED PATHS)
4. **Key discoveries & pivots** — dated list of understanding-changes; the only append-ish section, and each entry names what prior belief it replaced
5. **Open questions** — what the model can't yet explain

## Suite integration

- **Phase 0 (orchestrator)**: on ongoing projects, read the theory before framing — the theory is the highest-density context that exists. Contradiction between the job's findings and the theory is a first-class signal, not noise.
- **RETRO (nested-learning)**: the retro asks "did understanding change enough to rewrite the theory?" If yes, do it now, in-session — theorist's sticky rule — not "later."
- **wisdom-memory**: `decision` records that reshape strategy trigger a theory pass; the theory wikilinks (vault home) or references (repo home) the records it rests on.
- **Runtime**: Claude Code and Cowork/Desktop Commander have real filesystems — full function. claude.ai: draft the rewritten theory in-chat for the user to paste into their vault/repo, and say plainly that persistence is on them.

## Anti-patterns

- Appending dated entries to Current System Model instead of rewriting it
- Recording task progress or code churn in the theory
- A theory with no [U] assumptions and no open questions — that's marketing, not a model
- Splitting the theory across repo and vault
- Skipping the rewrite because the pivot was "small" — small pivots compound into a stale doc

## Tool reference

| Need | Tool |
|---|---|
| Read/rewrite THEORY.MD or vault note | `view`, `create_file`, `str_replace` / Desktop Commander file tools |
| Wikilink evidence notes | wisdom-memory vault (vault_sync.py output) |
| Detect theorist installed | `bash_tool` path check |
| Route understanding-changes here | orchestrator Phase 0 + nested-learning RETRO |
