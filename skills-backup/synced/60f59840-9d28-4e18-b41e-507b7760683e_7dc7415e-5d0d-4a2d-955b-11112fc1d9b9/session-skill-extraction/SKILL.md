---
name: session-skill-extraction
description: "Turn a hard-won, verified fix or workflow from this session into a reusable Claude Code skill (or update an existing one). Use when the user runs /claudeception, says \"save this as a skill\", \"extract a skill from this\", \"make this reusable\", or asks \"what did we learn?\" at the end of a session. Not for one-line facts or preferences: those belong in memory, not a new skill.\n"
allowed-tools:
- Read
- Grep
- Glob
- WebSearch
- WebFetch
metadata:
  author: "blader (upstream), tuned for this setup"
  version: "3.1.0"
  authored_via: "claude-science"
  published_by: "agent"
  published_at: "2026-10-22T18:10:43.483Z"
  authored_by: "agent"
  authored_at: "2026-10-22T18:10:43.442Z"
  authoring_session: "df249c20-fa50-4f4d-9ba4-14b516173576"
  last_modified_by: "agent"
  last_modified_at: "2026-10-22T18:10:43.473Z"
---

> Published as `session-skill-extraction` (registry names cannot contain "claude"); the owner knows it as `claudeception`.

# Claudeception

Codify knowledge that took real discovery into a skill that a future session will find through its description. Run only when the user asks; do not self-trigger after tasks.

Every new skill's description is added to the skill listing on every turn, so a new skill must earn that cost. Prefer updating an existing skill over creating one.

## Where knowledge belongs

| Kind of knowledge | Put it in |
|---|---|
| One fact, preference or project convention | Memory (hydra-mem tag, auto memory) or the project's CLAUDE.md |
| Always-on rule for every session | CLAUDE.md, not a skill |
| Multi-step procedure, non-obvious fix with exact error text, tool workaround | A skill (this workflow) |

If it is not a skill, say where it should go instead and stop.

## Quality bar (all must hold)

- **Reusable**: likely to recur beyond this task.
- **Non-trivial**: needed investigation, not a doc lookup.
- **Specific**: exact trigger (error text, symptom, tool, file type) and exact fix.
- **Verified**: it worked in this session; cite the evidence (command output, passing test).

## Workflow

1. **Pick candidates.** Review the session. List 1-3 candidates with one line each on why they pass the bar. Drop the rest.
2. **Check for existing skills.** Use Glob for `~/.claude/skills/*/SKILL.md` and `.claude/skills/*/SKILL.md`, then Grep those paths for the error text, tool names and key terms. Decide:

   | Found | Action |
   |---|---|
   | Nothing related | Create new |
   | Same trigger, same fix | Update existing; bump `metadata.version` |
   | Same trigger, different root cause | Create new; add "See also" both ways |
   | Same domain, different trigger | Add a "Variant" section to the existing skill |
   | Existing skill is stale or wrong | Fix it, or mark it deprecated with a pointer |

3. **Research only when it adds something.** For library or framework behaviour that may have changed, check the official docs (WebSearch/WebFetch) and cite them under References. Skip for project-internal patterns.
4. **Draft.** Use `resources/skill-template.md` (in this skill's folder). Keep the body short: problem, trigger conditions, solution, verification, notes. Never include credentials, tokens or internal URLs.
5. **Write the description well.** Key use first, then triggers: exact error messages, symptoms, technologies, and "Use when ..." phrases. Keep `description` plus `when_to_use` well under 1,536 characters (the listing truncates there).
6. **Confirm, then save.** Show the user the proposed name, location and description and ask before writing. Locations:
   - Project-specific: `.claude/skills/<name>/SKILL.md`
   - User-wide: `~/.claude/skills/<name>/SKILL.md`
   Put helper scripts in `<name>/scripts/`. For workflows with side effects, add `disable-model-invocation: true` so only `/name` runs them.
7. **Report** what was created or updated and why, and what was rejected.

## Frontmatter Claude Code acts on

`name`, `description`, `when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `disallowed-tools`, `model`, `effort`, `context`, `agent`, `background`, `hooks`, `paths`, `shell`. Keep author, version and date under `metadata:` (accepted but not acted on). Use `paths:` to load a skill only for matching files.

## Anti-patterns

- Over-extraction: mundane fixes do not need a skill.
- Vague descriptions ("helps with React problems") never match.
- Unverified solutions.
- Copying official docs instead of linking them and adding what is missing.
