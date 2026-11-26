# Exam traps and course corrections

## Distractor patterns (any domain) [U]

These options are wrong in almost every question:
- a bigger or smarter model;
- more tools, examples, reviewers or retries;
- retrying harder or raising the temperature;
- a more forceful prompt;
- hard-coding;
- fine-tuning;
- "the platform decides";
- any option that justifies itself through ML internals.

## Traps by domain (wrong → right)

**D0 API**
- `role: "system"` or `role: "tool"` → top-level `system`; `tool_result` inside a user message.
- "It forgot" → the app didn't resend the turn, or trimmed it.
- Context counted in messages → counted in tokens, PDFs included.
- `end_turn` or `tool_use` read as "the tool ran" → done; or proposed, not executed.
- "Temperature 0 guarantees identical output" → it only reduces variation.
- Claude Code for an internal orchestration app → Agent SDK.
- Parsing every stream delta as JSON → buffer the deltas and parse at block stop.

**D1 Agentic**
- Iteration count as the exit → `end_turn`; the cap is a backstop.
- A subagent inherits history → it gets only its brief; a bare "review this code" is a context-free failure.
- Parallel time is the average or the fastest → it is the slowest branch.
- One failure, so abort or retry all → handle that branch and say so.
- An empty result treated as failure → it is a valid finding.
- A forceful prompt or "confirm before proceeding" as a gate → a code gate that blocks and escalates.
- A log-only hook → that is observability.
- PostToolUse for "never" → PreToolUse.
- "Targeted re-analysis of changed files" → resume plus a scoped re-check.
- Fork branches that see each other → a broken fork.
- Three `tool_use` blocks in one response → batch them in one turn; they are not subagents.
- Also wrong: "looping is always safer"; a long role prompt with no content; subagents messaging each other; retrying a gate check forever; a hook where a stage gate belongs.

**D2 Prompting**
- 24 broad criteria → 5-10 named items with a skip list.
- 12 examples → 2-4 contrasting pairs.
- CoT everywhere → only for multi-step deduction.
- `any` picks a specific tool → only a named `tool_choice` fixes which one.
- Prose "return JSON" → a schema.
- Fresh restart or "try again" → append the attempt plus the specific error.
- Unbounded retries → 2-3, then a human.
- Batch inside a loop → batch only what nobody waits on (about 50% saving; tools work).
- Reviewers see prior comments → each sees only the artifact.
- Also wrong: "temperature 0 fixes vague criteria"; "batches don't support tools"; 10% or 90% savings; integration fed full traces; unlimited reviewers; every field required.

**D3 Claude Code**
- Monolithic or per-folder CLAUDE.md → `@import` per owner.
- A specific rule replaces the broad one → they stack.
- All skills load every session → only descriptions do; bodies load on match.
- A command for know-how → skill.
- A skill for an exact prompt with arguments → command.
- Plan mode in CI → `-p`.
- Grepping prose for "critical" → a schema field checked in code.
- Explore always → only for unfamiliar code.
- Forking a command that must build on the conversation, or leaving a standardized review unforked.

**D4 Tools and MCP**
- Misrouting fixed by a bigger model → boundary descriptions and fewer tools.
- MCP for local search → Grep or Glob.
- MCP "made Claude smarter" → it added standardized access.
- A read-only snapshot as a tool → it is a resource.
- Retry every `isError` → only the retryable categories.
- Zero results treated as an error → it is success.
- A literal token in committed config → an env-var reference.
- Also wrong: the USB-C port is one server; built-ins chosen by a fixed priority; "user scope always wins"; branching on message prose.

**D5 Context and reliability**
- Summarize at exhaustion, paraphrasing IDs → pin IDs and keep headroom.
- Escalate a transient error or every doubt → retry it, or give a default or ask one question.
- A bare "please help" → a handoff payload.
- A subagent aborts the job → the owning level decides.
- Reject a whole record → route per field.
- Fixed thresholds → re-check for drift.
- Average or silently pick between conflicting figures → surface both with sources.
- Trust `isError: false` → check findings against the mandate.
- Also wrong: identical retries of a validation error; auditing only auto-approved items; "stop summarizing" as the fix for degradation; "CLAUDE.md replaces glob and grep"; refusing everything when only part is uncertain.

## Course vs current docs

Use the course column on the exam; build on the docs column. All rows are [S] unless marked.

| Topic | Course says | Current docs |
|---|---|---|
| Structured output | force `tool_choice` to the named tool | forced `any`/`tool` returns HTTP 400 on Opus 5.5, Sonnet 5.5 and Fable 5.1 (2026-10; older models accept it). Use `auto` + instruction + `strict: true` and check the call, or `output_config.format` |
| Temperature | near 0 for repeatable output | newest models reject non-default sampling; use schemas, examples, effort |
| stop_reason | end_turn, tool_use, max_tokens | also stop_sequence, pause_turn, refusal (`stop_details`), model_context_window_exceeded |
| Streaming | two delta types; JSON complete at block stop | also thinking, signature, citations deltas; eager streaming or `max_tokens` can truncate JSON, so validate |
| Retry feedback | plain-text user turn | after a `tool_use`: its `tool_result` with `is_error: true` |
| System role | top-level only | still true for the system prompt; newest models also accept mid-conversation `role: "system"` messages (never `messages[0]`) |
| Summarization | API never summarizes | core API doesn't; opt-in compaction and context-editing betas |
| Resume / fork | `messages.create(resume=…, fork=…)` | no such params; Claude Code `--resume`, `--continue`, `--fork-session`; SDK `resume`, `fork_session` |
| Rules | `paths:` plus `grep:` content match | only `paths:`; content checks go in hooks or linters |
| Skills | `/load-skills` | no such command; `/skill-name` or a description match |
| `allowed-tools` | restricts tools | pre-approves; restrict with `disallowed-tools` or subagent `tools` |
| Command options | `context`, `scope`, `skills` in the body | `context` is frontmatter; no `scope` field; `skills` is a subagent field; same-name skill beats command |
| CLAUDE.md delivery | merged into the system prompt | a user message (guidance); enforce with hooks; `--append-system-prompt` for the system prompt |
| Subfolder CLAUDE.md | loaded at startup (page) | loaded lazily when a file there is touched (narration right) |
| `@imports` | loaded "when needed" | expanded with the importer, depth ≤4; no context saved |
| CLAUDE.md levels | user, project, subfolder | plus managed, `.claude/CLAUDE.md`, `CLAUDE.local.md`, rules, AGENTS.md fallback; all concatenated |
| `claude mcp add` | writes `.mcp.json` | default scope local (`~/.claude.json`); `--scope project` writes `.mcp.json`; local > project > user |
| MCP secrets | `$(JIRA_API_TOKEN)` | `${JIRA_API_TOKEN}`, `${VAR:-default}`; `$(…)` is shell command substitution |
| MCP `tools` key | restricts exposed tools | undocumented [U]; use permission rules, subagent `tools`/`mcpServers`, `--allowedTools` |
| MCP error fields | `errorCategory`, `isRetryable` | only `isError` is protocol; the rest is convention |
| Hook config | `{matcher, command}` | `{matcher, hooks: [{type: "command", command}]}` per event |
| PostToolUse secret check | rejection prevents the write | file already on disk; prevent in PreToolUse |
| Hook verdicts | reject, normalize, enforce, pass | exit 2 / `deny`; `updatedInput` / `updatedToolOutput`; `ask`; exit 0 |
| Edit tool | replaces first exact match | fails unless `old_string` is unique, or `replace_all` |
| Spawn tool | "Task tool" | `Agent` (formerly `Task`) |
| Subagent context | never inherits | fresh ones don't; `fork` subagents do; CLAUDE.md loads except in Explore |
| `-p` JSON | bare object | envelope with text in `result`; `--json-schema` → `structured_output` |
| Plan mode | plan call, approval, execute call | one session's permission mode, harness-enforced |
| Escalation function | missing confidence = 1.0 | fails open; default to review [U, analysis] |
| Surfaces | API, SDK, Claude Code, Claude.ai | also Tool Runner and Managed Agents |
