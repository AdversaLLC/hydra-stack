# Cheatsheet

| Situation | Answer |
|---|---|
| Model "forgot" a fact | the app didn't resend it (the API is stateless) |
| `stop_reason` | `end_turn` → exit · `tool_use` → run all, one result turn · `max_tokens` → don't parse · `pause_turn` → resend · `refusal` → fall back or escalate |
| Several `tool_use` blocks | append content whole; all results in one turn |
| Delegating | full brief: source, sourceData, role, constraints, return shape |
| Independent subtasks | parallel spawn; time = slowest; name failures, report empties |
| Must never happen | PreToolUse hook or deny rule; stage gate in code |
| Exact JSON shape | schema + enums (exam: forced tool; build: `auto` + `strict`, or `output_config.format`) |
| Validation failed | append the attempt + specific error; 2-3 tries; then a human |
| Consistent reviews | flag/skip lists + severity; 2-3 blind reviewers |
| Bulk, nobody waiting | Message Batches (~50%) |
| Tool misrouted | boundary descriptions; fewer tools |
| External system | MCP server; secrets as `${VAR}` |
| Tool error | transient → retry · validation → fix input · permission/business → escalate · empty = success |
| Team conventions | project CLAUDE.md + `@import` per owner |
| Per-language rules | `.claude/rules` with `paths:` |
| Task-type know-how | skill |
| Repeatable prompt with arguments | `/name $ARGUMENTS` |
| CI review | `claude -p --json-schema` + a field check in code |
| Risky multi-file change | plan mode (never in CI) |
| Ambiguity | a default or one question; escalate policy gaps |
| One uncertain field | per-field routing; calibrate; watch for drift |
| Conflicting sources | surface both, with sources |
