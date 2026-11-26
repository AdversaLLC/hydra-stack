# D3: Claude Code configuration and workflow (20%)

Unless marked otherwise, everything here comes from the Claude Code docs checked 2026-10-22 [S]. Confirm the syntax there before you ship.

## Pick the channel

| Need | Channel | Loads |
|---|---|---|
| your standing context, every repo | `~/.claude/CLAUDE.md` | session start |
| team conventions, one repo | `./CLAUDE.md` or `./.claude/CLAUDE.md`, committed, split by owner with `@path` imports | start |
| personal, this repo | `CLAUDE.local.md` | start |
| one subtree | `sub/CLAUDE.md` | lazily, when Claude reads or edits a file there |
| per file type or area | `.claude/rules/*.md` with `paths:` | when a matching file is touched |
| know-how for a task category | skill: `.claude/skills/<name>/SKILL.md` | description always; body on match or invoke |
| exact repeatable prompt by name, with args | command or skill: `/name args` | when invoked |
| must never happen, or must be proven | hooks, permission rules | enforced |

## CLAUDE.md

- **Locations:** managed (`/etc/claude-code/CLAUDE.md` on Linux), user, project, local.
- **Concatenated, never overriding.** Order: managed → user → project; ancestors from the root down to the cwd; `CLAUDE.local.md` after `CLAUDE.md` in each directory.
- **`@path` imports** resolve relative to the importing file, up to depth 4. They expand at load, so they save no context.
- **Delivered as a user message:** guidance, not enforcement. The system-prompt lever is `--append-system-prompt`.
- **Fallbacks and exclusions:** AGENTS.md is read only where no CLAUDE.md exists; `claudeMdExcludes` skips files.
- **Mid-session edits:** the course says they apply from the next session [U]. Lazy subfolder loads do add instructions mid-session.

## Rules

- **Loading:** `.claude/rules/**/*.md` without `paths:` loads at launch. With `paths:` (a YAML list of globs relative to the directory holding `.claude`), a rule loads when a matching file is read, written or edited. User rules (`~/.claude/rules/`) load first.
- **Matching rules stack;** the specific one never replaces the broad one.
- **No `grep:` content trigger exists.** Content checks belong in a hook or a linter.

## Commands and skills

- **Files:**
  - Command: `.claude/commands/<name>.md`, a prompt template with `$ARGUMENTS`.
  - Skill: `.claude/skills/<name>/SKILL.md` plus reference files.
  - A same-name skill overrides a command; command files still work.
- **Roles:** a command is "do this now", by name; a skill is know-how chosen by its description. They compose.
- **Frontmatter:**
  - `description` routes (name plus description are always in context, cut at 1,536 chars);
  - `argument-hint`;
  - `allowed-tools` **pre-approves** and does not restrict; `disallowed-tools` restricts;
  - `context: fork` runs the body as an isolated subagent with no history, and `agent:` picks its type;
  - `disable-model-invocation: true` makes it user-only;
  - also `paths`, `model`, `effort`, `hooks`.
- **Body:** loads on invocation and stays. Keep it under 500 lines; compaction re-attaches up to 5k tokens per skill.
- **When to fork:** standardized jobs that should ignore prior chatter (a security review), never work that builds on the discussion.

## Subagents

- **Files:** `.claude/agents/*.md` or `~/.claude/agents/*.md`. Precedence: managed > `--agents` JSON > project > user > plugin.
- **Fields:** `name` and `description` are required (the description routes). Optional: `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory`, `isolation: worktree`.
- **Explore** is read-only and skips CLAUDE.md, so seed its brief.
- **Defaults:** nesting 3 levels, 20 concurrent. In bypassPermissions, acceptEdits or auto mode, subagents inherit that mode over their own `permissionMode`.

```markdown
---
name: security-reviewer
description: Independent read-only security review of a finished change. Brief = artifact paths + flag list, never the author's summary.
tools: Read, Grep, Glob
maxTurns: 20
---
Check only the brief's flag list. Per finding: file:line, severity critical|minor, evidence.
```

## Hooks

- **Events** include PreToolUse, PermissionRequest, PostToolUse, PostToolUseFailure, UserPromptSubmit, Stop, SubagentStart, SubagentStop, SessionStart, SessionEnd, PreCompact, PostCompact and InstructionsLoaded.
- **stdin JSON:** `session_id`, `cwd`, `hook_event_name`, plus `tool_name` and `tool_input` for tool events.
- **Exit codes:**
  - 0 = ok (stdout JSON is parsed);
  - 2 = block (stderr becomes the reason);
  - anything else = a non-blocking error.
- **JSON output:**
  - `decision: "block"` with a `reason`;
  - PreToolUse: `hookSpecificOutput.permissionDecision` allow|deny|ask|defer, `updatedInput`, `additionalContext`;
  - PostToolUse: `updatedToolOutput`.
- **Stop hooks** block to keep Claude working. Check `stop_hook_active`; Claude Code overrides the block after 8 in a row.
- **Settings shape:** event → list of `{matcher, hooks: [{type, command}]}`.
- **Prevent in PreToolUse** on `tool_input`: Write and Edit content is known before execution. A path-only ban can be a deny rule instead.

```json
{"hooks": {"PreToolUse": [{"matcher": "Write|Edit",
  "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/guard.py"}]}]}}
```

```python
#!/usr/bin/env python3
import json, os, re, sys
ti = json.load(sys.stdin).get("tool_input", {})
name = os.path.basename(ti.get("file_path", ""))          # paths arrive absolute
text = ti.get("content", "") + ti.get("new_string", "")
if name.startswith(".env") or re.search(r"AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY", text):
    print(f"Blocked: {name} is a secrets file or holds a credential", file=sys.stderr)
    sys.exit(2)                                            # block; stderr goes to Claude
```

## Permissions and settings

- **Rules:** `permissions.allow|ask|deny`, e.g. `Bash(npm run *)`, `Read(./.env)`, `mcp__server__*`. Order is deny → ask → allow; an allow can't carve an exception out of a deny.
- **Modes:** default, acceptEdits, plan, auto, dontAsk, bypassPermissions.
- **Precedence:** managed > `--settings` > `.claude/settings.local.json` > `.claude/settings.json` > `~/.claude/settings.json`. Permission lists merge.

## Plan mode, Explore, refinement

- **Plan mode** is a permission mode within one session (Shift+Tab, `/plan`, `--permission-mode plan`): read and explore, no edits until a human approves.
  - Use it for multi-file, directory-wide or hard-to-reverse changes.
  - Act directly on small reversible ones.
  - Never in CI: there is no approver.
- **Explore** only unfamiliar areas, and return a curated summary.
- **Refinement:** define pass/fail first; "mostly fine" is a fail; fix interacting issues together.

## Headless and CI

- **`claude -p`** runs once and exits.
- **Output:** `--output-format json` returns an envelope (`result`, `session_id`, `total_cost_usd`). `--json-schema` puts the checked object in `structured_output`.
- **Bound every run:** `--max-turns`, `--max-budget-usd`, `--allowedTools` / `--disallowedTools`, `--permission-mode`.
- **`--bare`** skips hooks, skills, MCP, memory and CLAUDE.md, and authenticates only with an API key.
- **Packaged:** `anthropics/claude-code-action@v1`. Pipe untrusted diffs via stdin, not argv [U].
- **Branch in code on a field;** never grep prose.

```bash
git diff origin/main... | claude -p "Review this diff against the security flag list in CLAUDE.md" \
  --output-format json --json-schema "$(cat review.schema.json)" \
  --allowedTools "Read,Grep,Glob" --max-budget-usd 2 > out.json
jq -e '[.structured_output.findings[] | select(.severity == "critical")] | length == 0' out.json
```

## Memory

Auto memory (`~/.claude/projects/<project>/memory/`): MEMORY.md's first 200 lines / 25 KB load at start, topic files on demand; subagents don't get it, except forks.

## Exam traps

- One giant CLAUDE.md, or a copy per folder, for team-owned rules (→ `@import`).
- "All skills load every session"; a command for know-how (→ skill).
- A specific rule "replacing" the broad one.
- Plan mode for a typo, or in CI. Explore "always".
- Forking a command that must continue current work; leaving a standardized review unforked.
- Keyword-grepping prose to fail a build.
- Course-only answers the docs contradict (`grep:`, `/load-skills`, restrictive `allowed-tools`): see `traps.md`.
