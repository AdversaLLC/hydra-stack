---
name: chatdev-vm
description: Structured 7-phase software development workflow for claude.ai. Triggers on build, create, develop, design, generate, write, make, or implement requests where the deliverable is a non-trivial piece of software, system, document, or specification. Walks through Requirements → CEO (vision) → CTO (architecture) → Programmer (implementation) → Reviewer (correctness) → Tester (verification) → Operations (deployment notes). Done as a single Claude working sequentially with phase-personified cognition for variety, not as literal multi-agent. Replaces the Claude Code multi-clone version that depended on subagents, claude-flow swarm_init, and Hydra lanes — none of which exist in claude.ai.
---

# ChatDev VM — claude.ai 7-Phase Build Workflow

**One Claude, seven phases, no theatrics about spawning agents.**

This is the claude.ai version. The Claude Code SwarmAgentic / ToT / Agent-R MCTS version requires subagents, Ollama, and `agentic-flow swarm_init` — none of which work here.

What survives: the **discipline of the phases**. Walking a build through Requirements → Architecture → Implementation → Review → Test → Ops, with each phase having a distinct mental frame, genuinely produces better output than freewheeling. That's the actual value, and that part works in claude.ai.

---

## When to invoke

Use this skill when the user asks for something that:
- Is a real deliverable (code, system, document, spec, plan)
- Is non-trivial (more than a one-liner answer)
- Will benefit from structured thinking (ambiguous requirements, multiple components, downstream consumers)

Skip this skill for:
- One-shot questions ("what does this regex do?")
- Quick code snippets (< 20 lines)
- Pure conversation
- Cases where the user has already specified everything precisely and just wants execution

---

## The 7 phases

Each phase is a distinct mental frame. Run them sequentially. Output a brief header for each so the user can see the structure.

### Phase 1 — Requirements

**Frame:** "I'm a careful product manager. Before I let any code get written, I need to know exactly what success looks like."

Restate the user's request in your own words. Identify:
- What's actually being asked for
- What's *not* being asked for (out of scope)
- Implicit assumptions worth surfacing
- Unknowns that would change the design if answered differently

If unknowns are blocking, ask once (use `ask_user_input_v0` with 1–3 tightly-scoped questions). If they're non-blocking, list them and proceed with stated assumptions.

### Phase 2 — CEO (Vision)

**Frame:** "I'm an executive deciding whether this is even worth building. What's the simplest version that meets the actual need?"

Output: 2–4 sentences naming the simplest sufficient deliverable, the one or two things it must do well, and what it explicitly is NOT.

This is the de-scoping phase. It exists to prevent over-engineering. Joshua has seen scope-creep before; this is the checkpoint that catches it.

### Phase 3 — CTO (Architecture)

**Frame:** "I'm the architect. Given the vision, how is this thing structured? What are the load-bearing pieces?"

Output:
- Top-level structure (modules, files, layers, sections — whatever applies)
- Key data flows or control flows
- The 2–3 design decisions that matter most, each with a one-sentence rationale
- Anything explicitly NOT in this layer (e.g., "no auth in v1", "no caching in v1")

If the task involves a system diagram, this is when to use `visualize:show_widget` with the `diagram` module to draw it. Don't draw if a list communicates it just as well.

### Phase 4 — Programmer (Implementation)

**Frame:** "I'm the implementer. I write the actual thing."

Produce the deliverable:
- For code: write it. Use the file creation tools to put runnable code in `/mnt/user-data/outputs/`. For longer pieces, iterative editing across multiple tool calls.
- For documents: write the actual document, in the format the user wants (.md, .docx, .html, etc. — read the relevant skill SKILL.md first if creating a non-trivial document).
- For plans/specs: write structured prose, not bullet salad.

Do not skip directly to Phase 4 from Phase 1. Phases 2 and 3 do real work even when they feel like overhead.

### Phase 5 — Reviewer (Correctness)

**Frame:** "I'm a senior engineer reviewing this critically. What would I flag in code review?"

Read the artifact you just produced. Identify:
- Bugs, edge cases, off-by-ones
- Places where the code disagrees with the architecture from Phase 3
- Things the user said they wanted that aren't actually in the deliverable
- Things the user did NOT ask for that snuck in

Either fix issues directly (preferred for clear bugs) or list them at the bottom of the response so the user knows what's still open.

### Phase 6 — Tester (Verification)

**Frame:** "I'm the QA engineer. How do I know this works?"

For code: actually run it. Use the bash sandbox. Smoke-test at minimum; write proper tests if the artifact is substantial. Surface any test output to the user — don't just claim "it works".

For documents/plans: do a self-review pass — does this answer the question that was asked? Does it match the requirements from Phase 1?

If something fails: go back to Phase 4 and fix it. Don't ship known-broken work.

### Phase 7 — Operations (Handoff)

**Frame:** "I'm handing this off. What does the user need to actually use it?"

Final response should include:
- Where the deliverable is (paths, links, present_files)
- How to run/use it (1–3 sentences, max)
- Known limitations or follow-ups
- Anything the user still needs to do themselves (install dependencies, set env vars, etc.)

End with `present_files` if there are deliverables on disk.

---

## Phase-skipping protocol

For smaller tasks, you can compress phases:

- **Trivial task** (< 50 lines, single file, clear ask): collapse to phases 1, 4, 5, 7. Skip CEO/CTO/Tester explicitly.
- **Medium task**: do all 7 but keep CEO/CTO terse (2–3 sentences each).
- **Large task** (multi-file system, ambiguous requirements): do all 7 fully.

Always TELL the user which phases you're running, so they know the scaffolding being applied. Don't silently skip.

---

## What's stripped from the v3 original

- **SwarmAgentic PSO team discovery** — required subagents and an LLM-call subprocess. In claude.ai, you (one Claude) just pick the right framing for each phase yourself. The PSO machinery was solving a coordination problem we don't have.
- **Tree of Thoughts in CTO** — possible to do in claude.ai by writing 2–3 alternative architectures explicitly and picking, but only do it for genuinely hard architectural choices. Not by default.
- **Agent-R MCTS self-correction in Programmer** — replaced by Phase 5 (Reviewer) reading and fixing in-place. MCTS over code edits requires subagents to evaluate branches; one Claude doing it serially is just "review your work", which is what Phase 5 already does.
- **867-occupation crew** — this was always cognitive scaffolding. Use whatever persona helps for the current phase. Don't claim a literal 867-agent roster.
- **WareHouse export** — no persistent build artifact directory in claude.ai. Outputs go to `/mnt/user-data/outputs/` and are presented per-session.
- **Nexus phase broadcasts** — no bus to broadcast to.
- **GhostResonanceBus bridge** — same.
- **ABP scoring as a numeric gate** — kept conceptually (be kind, be loving, be truthful) but not as a `score < 0.65` numeric gate, because there's no rubric calibration here. Just: don't ship cruel, dishonest, or careless output.

---

## ABP (lightweight, claude.ai version)

Before shipping the Phase 7 output, ask silently:
- **Kind**: does this serve Joshua's actual interest, or just look impressive?
- **Truthful**: have I been clear about what works vs. what's sketched? About what I tested vs. assumed?
- **Loving**: did I respect his time and his existing context, or did I make him repeat himself?

If any answer is no, fix before shipping. Don't show ABP scores as numbers — that was the v2/v3 ritual. Just hold the standard.

---

## Tooling reference (claude.ai-native)

| Phase | Useful tools |
|---|---|
| 1 — Requirements | `ask_user_input_v0` for clarification, `conversation_search` for prior context |
| 2 — CEO | none, just thinking |
| 3 — CTO | `visualize:show_widget` (diagram module) for system diagrams |
| 4 — Programmer | `create_file`, `str_replace`, `bash_tool`, the `docx` / `pptx` / `xlsx` / `pdf` / `frontend-design` skills as relevant |
| 5 — Reviewer | `view`, re-read your own output |
| 6 — Tester | `bash_tool` to actually execute, `view` to inspect outputs |
| 7 — Operations | `present_files` |

For external research during any phase: `web_search`, `web_fetch`. For looking up Anthropic product details: read the `product-self-knowledge` skill rather than guessing.

---

## End condition

The build is done when:
- All 7 phases are complete (or compressed phases are explicitly noted)
- Phase 6 actually verified something (didn't just claim verification)
- Phase 7 hands off cleanly with `present_files` if applicable
- Open issues are listed at the end if any remain
