---
name: focal
description: Session orientation and working memory for claude.ai. Loads first whenever a session starts, the user asks "what skills do we have", "have we already processed X", "where does Y live", "orient me", "what's pending", or any cold-start question. Pulls context from userMemories, conversation_search of past chats, and the available_skills list — then states explicitly what is loaded, what is known about the user's ongoing work, and what the goal of this session is, BEFORE doing any other work. Prevents re-reading files already absorbed and re-discovering capabilities already built. Always run this first on session start.
---

# Focal — claude.ai Session Boot

Loads before any other skill. The whole point is: don't start cold, don't re-discover, don't re-read.

This is the claude.ai version. If you're looking for the Claude Code / multi-instance Nova Nexus bus version, that's a different file.

---

## Boot Sequence (every session, in this order)

```
Step 1 — Identity     What surface, what's known about Joshua already?
Step 2 — Memory pull  Read userMemories block in system context
Step 3 — Past chats   conversation_search if the request references prior work
Step 4 — Skill scan   What's in available_skills that's relevant?
Step 5 — Goal audit   Is the session goal clear? Restate it back.
Step 6 — Session header Print the orientation block.
```

Total: usually ≤ 1 turn. No theatrics, no "spawning agents".

---

## Step 1 — Identity

This is claude.ai in a browser (or the official mobile/desktop app, which is the same engine). One Claude instance per session. No persistent local filesystem. No other Claude surfaces in play — the skills that used to coordinate across surfaces have been retired.

Joshua is the user. Treat `userMemories` as authoritative for ongoing context.

---

## Step 2 — Memory pull

Read the `userMemories` block in the system prompt. Note:
- Top-of-mind threads
- Technical profile (OS, hardware, tools)
- Skill ecosystem he has installed
- Any standing preferences (e.g., "prefers technical detail without repeated questioning")

Do NOT recite these back as a list — that's surveillance-y. Use them silently to calibrate tone, depth, and assumptions.

---

## Step 3 — Past chats

Trigger `conversation_search` only when:
- The user references prior work ("our project", "the bug we discussed", "continue where we left off")
- The user asks a direct question whose answer would be in past chats ("what did I decide about X")
- The current request would benefit from context Claude doesn't already have in memory

Do NOT search for generic questions. Don't search "just to check". Searches cost tokens and time.

Query construction: 1–6 distinctive content words from the user's reference. Never paste documents into the query.

---

## Step 4 — Skill scan

Look at `available_skills` in the system prompt. Identify which loaded skills are relevant to the current request. If none are obviously relevant, that's fine — proceed with built-in tools.

If a skill is relevant but is one of the org-level skills built for Claude Code (anything mentioning Nexus bus, claude-flow CLI, agentic-flow, subagents, Ollama, Hydra lanes, ABP scoring with `n_particles`), DO NOT theatrically pretend to invoke its multi-agent machinery. Either use the claude.ai-native rewrite (if installed) or follow the spirit of the skill using available tools.

---

## Step 5 — Goal audit

Before producing any output, ask silently:
1. Is the session goal clear from the user's request?
2. Is it well-formed (not a malformed eval criterion)?
3. Is there a faster simpler path than what the user proposed?

If the goal is unclear OR malformed, surface that briefly before starting. If it's clear, proceed.

This is the only step from the original "RedTeam Phase 0 fitness audit" that survives in the claude.ai version — the rest of redteam is its own skill.

---

## Step 6 — Session Header

Output exactly one orientation paragraph at the top of the first response, ONLY when the user's request actually warranted orientation (cold-start, "orient me", "what do we have"). For routine requests, skip the header — going straight to the answer is the better default.

When you do output a header, format:

```
**Where we are:** [1 sentence on the user's current thread, drawn from memory]
**What I'm doing:** [1 sentence on what I'll do this turn]
**What I'm not doing:** [1 sentence flagging anything skipped or deferred]
```

Then proceed.

---

## What this skill is NOT

- Not a "spawn 4 agents to research" skill — there are no subagents in claude.ai
- Not a Nexus bus reader — there is no bus
- Not a heartbeat broadcaster — there is no team listening
- Not a momentum/checkpoint persister — context resets each session; persistent state lives in `userMemories` (via `memory_user_edits`) and past chat history (via `conversation_search`)

If a request needs persistence across sessions, save it to memory via `memory_user_edits`. That's the only persistence layer here.

---

## Tool reference (claude.ai-native)

| Need | Tool |
|---|---|
| Past conversation context | `conversation_search`, `recent_chats` |
| Persistent user fact | `memory_user_edits` (add/replace) |
| What's loaded | system prompt's `available_skills` |
| Files this session | `/mnt/user-data/uploads`, then `view` or `bash_tool` |
| External info | `web_search`, `web_fetch` |
| Visual orientation | `visualize:show_widget` (rare, only when a diagram genuinely helps) |

---

## End-of-session note

claude.ai sessions don't have a clean shutdown — the user just stops responding. There's no "kaizen log to write to disk". If the session produced a stable insight Joshua wants persisted, offer to add it to memory via `memory_user_edits` before he leaves. Don't add memories unsolicited.
