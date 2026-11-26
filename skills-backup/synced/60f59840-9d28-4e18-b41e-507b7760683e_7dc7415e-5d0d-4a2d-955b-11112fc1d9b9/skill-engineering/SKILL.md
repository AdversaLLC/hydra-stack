---
name: skill-engineering
description: Design, evaluate, and improve Claude skills — SKILL.md structure, description tuning, content architecture, validation. Triggers whenever a task involves any interaction with skills: creating a new skill, reviewing an existing one, debugging why a skill isn't triggering, optimizing a description, validating frontmatter against the spec, packaging into a .skill file, or migrating a skill from one runtime to another (e.g., Claude Code → claude.ai). Anchored on the spec the validator actually enforces (name kebab-case, description ≤1024 chars, no angle brackets in description, allowed frontmatter keys: name, description, license, allowed-tools, metadata, compatibility).
---

# Skill Engineering — claude.ai

The job: make skills that actually work. Triggering reliably, doing what they say, fitting the runtime they're deployed in.

This is the working knowledge accumulated across the rewrites in this conversation: what claude.ai's validator enforces, what makes descriptions trigger, what fails silently, and how to migrate skills between runtimes.

---

## Spec (what the validator actually enforces)

Frontmatter is YAML between two `---` lines at the very top of `SKILL.md`. The validator allows exactly these keys:

```
name           required   string, kebab-case (lowercase + digits + hyphens), ≤64 chars
description    required   string, ≤1024 chars, NO angle brackets (< or >)
license        optional   string
allowed-tools  optional   string or list — names of tools the skill can use
metadata       optional   nested object — arbitrary structured metadata
compatibility  optional   string, ≤500 chars — runtime constraints
```

ANY other top-level key fails validation. Common offenders:

- ❌ `version` (e.g., `version: 2.3.2`) — strip
- ❌ `category`, `tags`, `author`, `authors` — strip
- ❌ `requires`, `dependencies`, `prerequisites`, `tools_required` — strip; if relevant, fold into `compatibility` or the body
- ❌ `progressive_disclosure`, `priority`, `difficulty`, `estimated_time` — strip
- ❌ `title` (separate from `name`) — strip; folder name is the canonical identifier

The `name` MUST equal the directory name. `name: "My Cool Skill"` fails because of the space and capitalization. Use `my-cool-skill`.

Description must not contain literal `<` or `>` — even in URL examples. If you need to show angle-bracket content, replace with `(` and `)` or describe in prose.

---

## Anatomy

```
skill-name/
├── SKILL.md            ← required, validator-checked
├── README.md           ← optional, human-facing
├── scripts/            ← executable code skill calls (bash or python typically)
│   └── helper.sh
├── references/         ← long-form docs claude reads only when needed
│   └── deep-dive.md
└── assets/             ← static files used in outputs (templates, fonts, icons)
```

Loading model:
1. Metadata (name + description) — always in context
2. SKILL.md body — in context when skill triggers
3. Bundled files — only when claude reads them via tools

Keep SKILL.md under ~500 lines. Beyond that, push detail to `references/` and have the SKILL.md point to specific reference files for specific situations.

---

## Description writing

The description is the trigger mechanism. claude.ai's model decides whether to consult a skill based on this text. Two failure modes:

**Under-triggering**: skill is relevant but doesn't fire. Usually because the description is too vague ("for content tasks") or describes outputs rather than triggers.

**Over-triggering**: skill fires when irrelevant. Usually because the description claims too broad a scope ("for any task involving text").

Good description structure:
1. One-line statement of WHAT the skill does
2. Concrete trigger phrases the user is likely to say (in quotes if helpful)
3. Concrete contexts/scenarios where the skill applies
4. Notable exclusions (when NOT to use it) — only if there's a likely confusion

Be specific. "Create new skills" is too vague; "Create new Claude skills with proper YAML frontmatter, validate against the spec, package into .skill files for claude.ai install, optimize descriptions for triggering reliability" tells the model when to fire and when not to.

Keep within 1024 chars. Most good descriptions land 300–800.

---

## Body writing

The body is what Claude reads when the skill triggers. It instructs Claude on the workflow.

**Structure that works:**
- Brief opening: one paragraph on what this skill is and isn't
- "When to invoke" / "When to skip" — explicit triggers
- The workflow itself, in numbered steps or named sections
- "Tool reference" table near the end, mapping needs to specific tools
- "Anti-patterns" section calling out failure modes

**Keep prose tight.** This is instructions to Claude, not marketing copy. Bullet lists and tables compress better than long paragraphs.

**Reference real tools.** If the skill says "use the bash sandbox", it should mean `bash_tool`. If it says "search past chats", it should mean `conversation_search`. Don't use generic phrasing for things that have specific tool names.

**Be honest about limits.** If the skill can't do X in claude.ai, say so. The original Claude Code skills failed in claude.ai partly because they didn't tell Claude what wouldn't work — Claude tried, hit a wall, and confabulated.

---

## Migration: Claude Code → claude.ai

Common things to strip:
- Subagent dispatch (`Task` tool spawning, swarm_init, agent_spawn)
- Local filesystem persistence between sessions (`.skill-state.json`)
- `claude-flow` / `agentic-flow` CLI invocations
- Local model dependencies (Ollama, llama.cpp pipelines)
- Persistent vector DBs (Milvus, Pinecone instances assumed available)
- Cross-instance bus reads/writes (Nova Nexus `~/.nova/nexus.jsonl`)
- Hardcoded MCP server URLs that aren't connected here

Common substitutions:
- Subagent parallel work → sequential one-Claude work with persona framing
- Local persistence → `memory_user_edits` for facts, `conversation_search` for history
- Local LLM call → claude.ai itself, or web_fetch on docs
- Vector DB → in-memory with chromadb / FAISS / NumPy in the bash sandbox
- Cross-instance handoff → human-readable resumption brief the user pastes into a new chat

When migrating, preserve the *concept* of the original skill (what it's for) but rewire the *implementation* to claude.ai's actual tools.

---

## Validation workflow

Before shipping a skill, validate manually:

```bash
# In bash sandbox or wherever you have python:
python3 << 'EOF'
import re, yaml
text = open('SKILL.md').read()
m = re.match(r'^---\n(.*?)\n---', text, re.DOTALL)
fm = yaml.safe_load(m.group(1))
allowed = {'name','description','license','allowed-tools','metadata','compatibility'}
extra = set(fm.keys()) - allowed
print('Extra keys:', extra or 'none')
print('Name format ok:', bool(re.match(r'^[a-z][a-z0-9-]*$', fm['name'])))
print('Desc length:', len(fm['description']), '/ 1024')
print('Angle brackets in desc:', '<' in fm['description'] or '>' in fm['description'])
EOF
```

Or run the official validator if `/mnt/skills/examples/skill-creator/scripts/quick_validate.py` is accessible.

---

## Packaging into .skill files

The skill-creator scripts include `package_skill.py` which validates and creates a `.skill` zip:

```bash
python3 -m scripts.package_skill /path/to/skill-folder /path/to/output/
```

The `.skill` file is what users upload via Settings → Capabilities → Skills → Create skill. It's a regular zip with the skill folder structure inside.

---

## Iteration loop

For non-trivial skills, iterate:

1. Draft SKILL.md
2. Define 5–10 representative test prompts
3. For each test prompt, walk through what Claude would do with the skill loaded
4. Note where the skill's instructions are ambiguous, missing, or wrong
5. Revise the SKILL.md
6. Repeat

This is what `skill-creator` does at full scale (with parallel test execution). In claude.ai you do it sequentially — slower but works.

For triggering specifically: once content is solid, test triggering with prompts the user is *likely to type*, not the trigger phrases verbatim. If the skill only fires on its exact trigger phrases and not on natural variations, the description is too narrow.

---

## Anti-patterns

- **Frontmatter cargo-culting**: `version`, `tags`, `author`, etc. The validator rejects them. Strip.
- **Description as marketing copy**: "powerful skill that elegantly handles..." — Claude doesn't care about adjectives. State triggers.
- **Body as essay**: walls of prose are skimmed-not-read. Use lists, tables, named steps.
- **Pretending to be a runtime**: a SKILL.md that says "spawn 32 agents" in claude.ai will fail. Don't ship instructions Claude can't follow in the target runtime.
- **Triggering on everything**: "Use this skill for any text-related task" → over-triggers, dilutes signal. Be specific.
- **Triggering on nothing**: "Use when explicitly invoked by the user" → never triggers proactively. State concrete trigger phrases.
- **Skipping validation**: a skill with a bad `name` field fails install silently in some clients. Always validate before shipping.

---

## Tool reference

| Need | Tool |
|---|---|
| Validate a SKILL.md | bash sandbox + the validate snippet above, or `quick_validate.py` |
| Package into .skill | `package_skill.py` from skill-creator's scripts |
| Read existing skills for reference | `view` on `/mnt/skills/...` paths |
| Edit a draft | `create_file` and `str_replace` |
| Test triggering qualitatively | Pose a representative user message in chat, see if Claude consults the skill |
