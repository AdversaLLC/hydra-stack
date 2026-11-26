# Claudeception

Every time you use an AI coding agent, it starts from zero. You spend an hour debugging some obscure error, the agent figures it out, session ends. Next time you hit the same issue? Another hour.

This skill fixes that. When a session discovers something non-obvious (a debugging technique, a workaround, some project-specific pattern) and you ask for it, Claude saves that knowledge as a new skill (after showing you the draft). Next time a similar problem comes up, the skill's description lets it load automatically.

## Installation

### Step 1: Clone the skill

**User-level (recommended)**

```bash
git clone https://github.com/blader/Claudeception.git ~/.claude/skills/claudeception
```

**Project-level**

```bash
git clone https://github.com/blader/Claudeception.git .claude/skills/claudeception
```

### Step 2: No activation hook

Upstream ships `scripts/claudeception-activator.sh`, a `UserPromptSubmit` hook that injects a ~1.4 KB "MANDATORY SKILL EVALUATION" block on every prompt (and on scheduled-task, background-subagent and cross-session messages, which also fire `UserPromptSubmit`). This setup already runs hydra-mem and the vault classifier on that event, and hydra-mem already captures INSIGHT/FAILED PATH lines, so the hook is retired here. Run `/claudeception` (or say "save this as a skill") when a session produced something worth keeping.

## Usage

### Running it

Trigger a learning retrospective:

```
/claudeception
```

Or explicitly request skill extraction:

```
Save what we just learned as a skill
```

### What Gets Extracted

Not every task produces a skill. It only extracts knowledge that required actual discovery (not just reading docs), will help with future tasks, has clear trigger conditions, and has been verified to work.

## Research

The idea comes from academic work on skill libraries for AI agents.

[Voyager](https://arxiv.org/abs/2305.16291) (Wang et al., 2023) showed that game-playing agents can build up libraries of reusable skills over time, and that this helps them avoid re-learning things they already figured out. [CASCADE](https://arxiv.org/abs/2512.23880) (2025) introduced "meta-skills" (skills for acquiring skills), which is what this is. [SEAgent](https://arxiv.org/abs/2508.04700) (2025) showed agents can learn new software environments through trial and error, which inspired the retrospective feature. [Reflexion](https://arxiv.org/abs/2303.11366) (Shinn et al., 2023) showed that self-reflection helps.

Agents that persist what they learn do better than agents that start fresh.

## How It Works

Claude Code has a native skills system. Skill names and descriptions sit in the skill listing on every turn; the full body loads only when a skill is invoked. Every new skill therefore costs context on every turn, so this skill prefers updating existing skills and asks before writing.

But this retrieval system can be written to, not just read from. So when this skill notices extractable knowledge, it writes a new skill with a description optimized for future retrieval.

The description matters a lot. "Helps with database problems" won't match anything useful. "Fix for PrismaClientKnownRequestError in serverless" will match when someone hits that error.

More on the skills architecture [here](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills).

## Skill Format

Extracted skills are markdown files with YAML frontmatter:

```yaml
---
name: prisma-connection-pool-exhaustion
description: |
  Fix for PrismaClientKnownRequestError: Too many database connections 
  in serverless environments (Vercel, AWS Lambda). Use when connection 
  count errors appear after ~5 concurrent requests.
metadata:
  version: 1.0.0
  date: 2024-01-15
---

# Prisma Connection Pool Exhaustion

## Problem
[What this skill solves]

## Context / Trigger Conditions
[Exact error messages, symptoms, scenarios]

## Solution
[Step-by-step fix]

## Verification
[How to confirm it worked]
```

See `resources/skill-template.md` for the full template.

## Quality Gates

The skill is picky about what it extracts. If something is just a documentation lookup, or only useful for this one case, or hasn't actually been tested, it won't create a skill. Would this actually help someone who hits this problem in six months? If not, no skill.

## Examples

See `examples/` for sample skills. They are reference material only: Claude Code discovers personal skills at `~/.claude/skills/<name>/SKILL.md`, so these nested files are not listed or loaded. Copy one into its own `~/.claude/skills/<name>/` folder only if you actually want it active.

- `nextjs-server-side-error-debugging/`: errors that don't show in browser console
- `prisma-connection-pool-exhaustion/`: the "too many connections" serverless problem
- `typescript-circular-dependency/`: detecting and fixing import cycles

## Contributing

Contributions welcome. Fork, make changes, submit a PR.

## License

MIT
