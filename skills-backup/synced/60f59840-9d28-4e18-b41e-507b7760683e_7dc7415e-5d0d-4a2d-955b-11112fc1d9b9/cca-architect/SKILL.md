---
name: cca-architect
description: "Designing a Claude agent or multi-agent pipeline, choosing between tools/MCP/subagents, structured output and retries, CLAUDE.md/rules/skills/hooks setup, escalation and confidence routing, CCA-F exam prep. Decision rules, scenario playbooks and exam traps from the Claude Certified Architect Foundations course, checked against docs. Not for API params, model IDs or prices (use claude-api)."
disable-model-invocation: true
metadata:
  authored_via: "claude-science"
  published_by: "agent"
  published_at: "2026-10-22T18:10:41.595Z"
  authored_by: "agent"
  authored_at: "2026-10-22T18:10:41.537Z"
  authoring_session: "df249c20-fa50-4f4d-9ba4-14b516173576"
  last_modified_by: "agent"
  last_modified_at: "2026-10-22T18:10:41.587Z"
---

> Published as `cca-architect` (registry names cannot contain "claude"); the owner knows it as `claude-architect`.

# Claude architecture decisions and CCA-F prep

Own-words condensation of notes on the course "Claude Certified Architect Foundations" (CCA-F, modules 0-7), corrected against the Claude Code docs (checked 2026-10-22) and the bundled API reference (cached 2026-10-06). Two uses:

1. **Building:** choosing a loop, agent topology, tool surface, output contract, Claude Code configuration or escalation policy.
2. **The exam:** recognising the scenario, applying its rule, avoiding the distractor.

**Markers:**
- [S]: the course and the docs agree, or the claim is docs-only.
- [U]: course-only or unverified. Most numbers, such as "2-3 retries" or "4-5 tools", are course heuristics.
- Where they disagree, the chapters give the docs answer, and `traps.md` → "Course vs current docs" gives both.

## The exam [U]

- **Format:** 60 questions, 120 minutes, scaled pass mark 720/1000 (not "72% correct").
- **Questions:** each is a scenario with four plausible designs. Six scenario types exist, and about four appear.
- **Out of scope, used as distractors:** fine-tuning, embeddings, model internals, sampling algorithms and pricing arithmetic (beyond "batches cost about half").

| Domain | Weight | Chapter |
|---|---|---|
| D1 Agentic architecture & orchestration | 27% | `chapters/d1-agentic-architecture.md` |
| D2 Prompt engineering & structured output | 20% | `chapters/d2-prompting-structured-output.md` |
| D3 Claude Code configuration & workflow | 20% | `chapters/d3-claude-code-config.md` |
| D4 Tools & MCP | 18% | `chapters/d4-tools-mcp.md` |
| D5 Context management & reliability | 15% | `chapters/d5-context-reliability.md` |
| Foundation for all: Claude API basics | n/a | `chapters/d0-api-foundations.md` |

## Route the question

| Question is about | Open |
|---|---|
| stop_reason, statelessness, "the model forgot", streaming, which surface (API, Agent SDK, Claude Code) | d0 |
| loops, decomposition, subagent briefs, parallel fan-out, gates, hooks as enforcement, resume/fork | d1 |
| review criteria, few-shot/CoT, schema output, retry loops, batches, multi-pass review | d2 |
| CLAUDE.md, rules, commands vs skills, subagent files, hook config, permissions, plan mode, `claude -p` | d3 |
| tool descriptions, misrouting, built-in vs custom vs MCP, MCP config and secrets, tool errors | d4 |
| handoffs, pinned facts, escalation, error propagation, confidence routing, provenance | d5 |
| a whole scenario stem (support, code review, research, dev productivity, CI/CD, extraction) | `scenarios.md` |
| "is the course answer still true?", distractor patterns | `traps.md` |
| quick lookup, a term | `cheatsheet.md`, `glossary.md` |

## Decision rules that matter most

1. **Name the scenario first.** It selects the domain's rules. [U]
2. **The caller owns memory.** Whatever the model needs must be in this call's `system` or `messages`. "It forgot" means the app dropped it. [S]
3. **Read `stop_reason` before `content`.** `end_turn` exits. `tool_use` means nothing ran yet. `max_tokens`, `refusal` and `pause_turn` each get their own branch. A cap is a backstop, not the exit. [S]
4. **Code enforces, prompts guide.** Whatever must never happen, or must be proven, goes in a gate, a PreToolUse hook, a permission rule or a schema check. [S]
5. **Pre prevents, Post detects.** PostToolUse runs after the write, so it can only flag, normalize or inform. [S]
6. **Every delegate starts blind.** A brief carries where the task sits, the actual inputs, role, constraints and return shape. [S]
7. **Fan out only independent work, and on disjoint files.** Time is the slowest branch. Name failures; report empties as findings. [S]
8. **Machines get schemas, not prose.** Use a tool schema, structured output or `--json-schema`, add enums, and branch in code on a field. Require only the fields the source always has. [S]
9. **Retry by appending the attempt and the specific error.** Cap at 2-3, then a human gets the last attempt. Repeated failure means the spec is ambiguous. [S; cap U]
10. **Reviewers see only the artifact.** No other reviewer's output, no author claims. Run 2-3 blind passes, then integrate. [S; count U]
11. **Fix misrouting with descriptions** that name the boundary and the confusable tool, then shrink the list. A bigger model is not the fix. [S]
12. **Classify the error before reading confidence.** Transient: retry. Validation: fix the input. Permission, business rule or policy gap: escalate with a handoff. Then route per field. [S; thresholds U]
13. **Use the narrowest channel that reliably loads.** CLAUDE.md (always) → `paths:` rule (by file) → skill (by task) → command (by name) → hook or permission (enforced). [S]
14. **Pin IDs and constraints verbatim, summarize findings, drop filler.** Keep a source on each claim; surface conflicts, never average them. [S]
15. **Continuing a session is a choice:** resume, fork, fresh + isolation, or fresh + summary. [S]

## Where specifics live

- **API parameters, model IDs, prices and current model behaviour** (thinking and effort, forced `tool_choice` support, structured outputs, caching, batch limits): the built-in `claude-api` skill.
- **Claude Code config facts** (settings keys, hook events and payloads, frontmatter fields, CLI flags): the docs at code.claude.com, or the claude-code-guide agent.

Both move faster than this course: decide here, confirm syntax there.
