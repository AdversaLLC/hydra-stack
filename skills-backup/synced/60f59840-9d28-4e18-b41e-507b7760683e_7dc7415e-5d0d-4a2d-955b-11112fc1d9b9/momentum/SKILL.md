---
name: momentum
description: Long-running session state management for claude.ai. Triggers on long task, multi-step build, "checkpoint", "save state", "resume where we left off", "what was I working on", or any task spanning multiple turns where context loss would hurt. Persists durable facts via memory_user_edits, recalls past threads via conversation_search, and produces explicit handoff text when approaching context-window limits. Single-instance — no Nexus bus, no checkpoint files written to disk between sessions, no Hydra cross-instance sharing. The Claude Code multi-instance version with state.json files and Wisdom Bank tiers is a different skill.
---

# Momentum — claude.ai Session State

The job: don't lose state across long sessions. Not by writing JSON files (claude.ai sessions are ephemeral) — by being deliberate about what gets persisted to `memory_user_edits` and what gets summarized for handoff.

The Claude Code original maintained `.momentum/state.json`, an SQLite Knowledge Graph, an HNSW vector store, and broadcast checkpoints to a Nexus bus. None of that infrastructure exists in claude.ai. What survives: the **discipline** of explicit checkpoints and explicit handoffs.

---

## Two persistence layers (and only two)

1. **`memory_user_edits`** — durable facts about Joshua: ongoing projects, preferences, technical context, standing decisions. Survives sessions. Editable.
2. **Conversation history** — searchable via `conversation_search` and `recent_chats`. Read-only from Claude's side.

If a piece of state matters, it goes in (1). If it's a transient working note, it lives in (2) and you retrieve it next session via search.

That's it. There is no third layer.

---

## Checkpoint protocol

A checkpoint happens when ANY of these triggers fire:

- The user explicitly says "checkpoint", "save state", "let's pause"
- A substantial deliverable was just shipped (file created, decision made, design finalized)
- About 75% of available context is consumed (rough estimate from response count + content size)
- The user says they're stopping for now

A checkpoint is one short message containing:

```
**Where we landed:** [1–2 sentences on what was done]
**Open threads:** [bullet list of what's pending, max 5]
**Next action:** [the very next concrete step]
**Persisted to memory:** [what, if anything, was added via memory_user_edits]
```

Then if the user IS leaving: stop. Don't try to keep going.

---

## What goes in `memory_user_edits`

Add only when the fact is durable AND useful for future sessions:

- ✅ "User is building X" (when the project is real and ongoing)
- ✅ "User uses [specific tool/version] as primary [thing]"
- ✅ "User prefers [communication style]"
- ✅ "User's [name] is [name], [name] is [name]" (relationships, pets, kids — when relevant)
- ❌ One-time facts ("user asked about Python today")
- ❌ Anything sensitive (passwords, addresses, financial details, health details unless the user asks for it persisted)
- ❌ Anything a senior Anthropic employee would cringe at being persisted

Use `memory_user_edits` with command="view" first to check for duplicates and conflicts. Then `add` or `replace` accordingly. Never silently overwrite.

---

## Handoff protocol — context-limit approach

When context is filling up but Joshua wants to keep working, produce a HANDOFF block that he can paste into a *fresh claude.ai conversation* to resume the work. (Same Joshua, same claude.ai, just a new conversation window once this one's stale.)

```
**Resumption brief**
Project: [what we're working on]
Goal: [the specific outcome targeted]
What's done: [bullet list, max 5]
What's left: [bullet list, ordered by priority]
Key decisions made: [bullet list of design choices that shouldn't be re-litigated]
Open questions: [things waiting on Joshua's input]
Next concrete step: [the single thing the next conversation should do first]
```

Write it self-contained — the new conversation won't see this one unless Joshua pastes the block in or says "search past chats for X".

If it's worth surfacing into memory: also call `memory_user_edits` to add a one-line note about the project being in-flight, so future Claude knows to `conversation_search` for context.

---

## What's stripped from v2

- **`.momentum/state.json` writes** — claude.ai's `/home/claude/` is ephemeral; writes don't persist between sessions
- **Knowledge Graph (BM25 + PageRank SQLite)** — no persistent DB
- **WisdomBank with HOT/WARM/COLD tiers** — replaced by `memory_user_edits` (one tier, deliberate adds)
- **EpisodicMemory** — replaced by `conversation_search`
- **TrainingDataBank** — not applicable; Claude isn't trained from these sessions
- **AgentDB HNSW** — no vector store
- **Nexus checkpoint broadcast** — no bus
- **Nexus insight at HOT promotion** — no bus
- **HANDOFF on context limit (multi-instance)** — replaced by the human-readable Resumption brief above
- **Auto-kaizen at every checkpoint** — kept as a one-line "what worked / what didn't" addition to the checkpoint when genuinely useful, not as a forced ritual
- **Gleaner KG auto-import** — Gleaner doesn't run automatically here

---

## Anti-patterns

- **Phantom persistence**: don't write to `.momentum/state.json` and pretend it'll be there next session. It won't.
- **Memory bloat**: don't add every detail of every conversation to `memory_user_edits`. Memories accumulate; bad memories crowd out good ones. Be picky.
- **Performative kaizen**: don't tag every checkpoint with a "lesson learned" if there isn't a real one. Empty rituals waste tokens.
- **Stale memory**: if a fact in memory is now wrong (Joshua moved jobs, deleted a project), use `replace` or `remove` to fix it — don't accumulate stale truth.

---

## Tool reference

| Need | Tool |
|---|---|
| Persist a durable fact | `memory_user_edits` (view first, then add/replace) |
| Recall past threads | `conversation_search` for topic, `recent_chats` for time-window |
| Examine current memory state | `memory_user_edits` command="view" |
| Generate handoff text | just write the block — it's a copy-paste artifact, not a tool call |

---

## End condition

A momentum-aware session ends well when:
- Any durable state was persisted via `memory_user_edits` (or explicitly noted as not-worth-persisting)
- Open threads are listed in the final message so Joshua can resume
- If the conversation is ending and work might be resumed in a fresh chat later, a Resumption brief was generated
- Nothing was silently dropped
