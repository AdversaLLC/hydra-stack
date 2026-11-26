---
name: luna-stack
description: Master router for claude.ai. Always-on. Reads every user message and decides which other skill to defer to based on trigger words and context. Maps build/create/develop requests to chatdev-vm, attack/critique/red-team requests to redteam, research/paper/arxiv to science, pentest/forensics/CVE to security, file uploads to veritas, session-start/orient questions to focal, etc. Replaces the Claude Code Nova Nexus version with a single-instance, claude.ai-native routing table that only points to skills that actually function in this runtime. Use this whenever a request could plausibly invoke any other installed skill.
---

# Luna Stack — claude.ai Master Router

One install. Routes once. No theatrics about cross-instance handoff.

This is the claude.ai version. The Claude Code multi-instance Nova Nexus version is a different file and only works with `~/.nova/nexus.jsonl` + the four-Claude-team protocol.

---

## How routing actually works in claude.ai

There's no central router daemon. "Routing" here just means: when a user message arrives, Claude reads the descriptions of available skills and decides which one(s) apply. This skill exists to make that decision sharper and more consistent — by giving Claude a single source-of-truth trigger table that excludes skills that don't function in this runtime.

If a skill in the routing table below isn't installed in your claude.ai workspace, the route is a no-op — fall through to using built-in tools.

---

## Routing Table (claude.ai-only)

```
TRIGGER PATTERN                                    → SKILL
─────────────────────────────────────────────────────────────────
session start / "orient me" / "what do we have"    → focal
"have we read X" / "what's pending"                →
─────────────────────────────────────────────────────────────────
files uploaded / "verify everything" / "did you    → veritas
miss anything" / "audit uploads"                   →
─────────────────────────────────────────────────────────────────
build / create / develop / make / generate /       → chatdev-vm
implement / design a system / write the app       →
─────────────────────────────────────────────────────────────────
red team / attack / critique / stress test /       → redteam
"find weaknesses" / "break this" / devil's advocate→
─────────────────────────────────────────────────────────────────
research / paper / arxiv / theorem / biology /     → science
chemistry / LaTeX / literature review              →
─────────────────────────────────────────────────────────────────
pentest / forensics / malware / CVE / fuzzing /    → security
incident response / static analysis (defensive)    →
─────────────────────────────────────────────────────────────────
zip / archive / extract / split / .7z / .tar       → built-in bash + zip-files (if installed)
─────────────────────────────────────────────────────────────────
codebase uploaded / "read this repo" /             → veritas first → then bash sandbox
"what is this project"                             →   (codebase-navigator if installed)
─────────────────────────────────────────────────────────────────
brand / visual / poster / theme / design system    → studio (if installed) OR
                                                   →   visualize:show_widget for inline
─────────────────────────────────────────────────────────────────
HTML / CSS / JS / frontend / single-file web tool  → built-in: artifact + frontend-design skill
─────────────────────────────────────────────────────────────────
weather / map / restaurant / hike / commute        → weather_fetch / places_search
─────────────────────────────────────────────────────────────────
calendar / email / Slack / Notion / Jira / GitHub  → MCP connectors (search_mcp_registry first)
─────────────────────────────────────────────────────────────────
"who is X" / "what's the price of Y" / current     → web_search
news / present-day facts                           →
─────────────────────────────────────────────────────────────────
remember that... / forget about... / update memory → memory_user_edits
─────────────────────────────────────────────────────────────────
"what did we discuss about X yesterday"            → conversation_search / recent_chats
─────────────────────────────────────────────────────────────────
nothing matches above                              → just answer with built-in capabilities
```

---

## Skills that are RETIRED in claude.ai (do not invoke, do not route, do not install)

These were in the original luna-stack v3 routing table but their reason-for-existing was multi-instance coordination across Claude Code / Claude Desktop / Chrome extension — surfaces that are no longer in the user's setup. They have no useful claude.ai-only equivalent. Delete from skill list.

| Original skill | Why retired |
|---|---|
| nova-nexus | Coordinates four Claude surfaces; only claude.ai exists now |
| cowork-oracle | Dispatches to a Claude Code instance that no longer exists |
| dmux | tmux multi-pane on a host that's no longer in scope |
| nova-workspace | Browser IDE that ran on the retired surface |

If a request matches one of these triggers ("hand this off to Claude Code", "dispatch to Ryū", "what did Desktop Claude find"), tell the user plainly that those surfaces aren't in play anymore and either do the task here or — if it genuinely needs filesystem access claude.ai doesn't have — surface that limit so the user knows it's a real limit, not a Claude oversight.

---

## Skills that mostly DON'T have working claude.ai equivalents (but may have partial substitutes)
| momentum | claude.ai sessions don't persist; no checkpoint file to write | Use `memory_user_edits` for state that must survive |
| gleaner | Local Ollama dependency for AI semantic naming | Do the naming inline using built-in tools (web_search if needed for context) |
| toolchain (multi-clone) | No subagents, no Hydra lanes | Do the work sequentially as one Claude |
| ai-agents (PSO/MCTS/ToT/DeepSearcher) | Requires local LLM + Milvus + sentence-transformers | Reason through the framework conceptually; for actual ToT/MCTS, run via bash sandbox if libraries are installable, otherwise be explicit you're sketching not executing |
| ghidra-re | Ghidra is heavy; bash sandbox can install but disk-image work is unsafe | Static analysis only via `radare2` or `objdump` if appropriate |
| reviselyt (full app) | Production app, not a skill that runs here | Help write code FOR reviselyt; don't simulate running it |
| instinct (genome update) | Persistent learning loop requires storage | One-shot pattern extraction is fine; don't claim genome updates persist |
| luna-build-notes | Local file tracker | Use `memory_user_edits` to record blueprint state |

---

## Persistence model (claude.ai)

There are two persistence layers, and that's it:

1. **`memory_user_edits`** — facts about the user that should survive across sessions. Write sparingly. Don't overwrite.
2. **Conversation history** — searchable via `conversation_search` / `recent_chats`. Read-only from Claude's side; the user can delete chats and the memories drawn from them.

There is NO:
- Filesystem that persists between sessions
- Shared state with other Claude instances
- Background daemon writing checkpoints
- Vector database / embeddings store

If a workflow seems to need persistence, it actually needs (a) `memory_user_edits`, or (b) a file the user keeps locally that they re-upload next session.

---

## Anti-patterns to avoid

- **Theatrical multi-agent.** Don't say "spawning 32 agents" or "dispatching to Hydra lanes". One Claude here, doing one thing at a time. Personification of phases is fine for cognitive scaffolding (e.g., "as the reviewer, I'd flag..."), but don't claim parallelism that isn't happening.
- **Phantom infrastructure.** Don't reference `~/.nova/nexus.jsonl`, `claude-flow swarm init`, `agentic-flow agent_spawn`, Ollama subprocess calls. They will fail.
- **Pretend persistence.** Don't write to "checkpoint files" that won't exist next session. If state must persist, use `memory_user_edits`.
- **Tool fabrication.** Don't invoke MCP tools that aren't actually connected. Check the connected MCP list before assuming.

---

## When in doubt

If no skill clearly fits, just answer with built-in tools. Routing through this skill is overhead — the goal is to land on the RIGHT capability quickly, not to make every interaction feel like it traversed a 24-skill routing table.
