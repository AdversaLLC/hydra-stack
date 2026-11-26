---
name: hydra-setup
description: Self-healing installer and doctor for the GSD-Hydra stack. Detects the runtime (Claude Code, Codex, Cowork sandbox, claude.ai, MCP client), writes one config file (~/.hydra/config.json) so no path lives in any skill, and installs or repairs the belt skills (baton, Claudeception, adversarial-execution, theorist, napkin, razor, schematic), the hydra suite and hydra-graph (stdlib RAG and knowledge-graph memory with quarantine and an integrity chain). Wires hydra-mem's hooks and MCP server, optionally sets up the isolated Chroma venv (--with-rag), points at GSD Core's and graphify's own installers (never hand-copied), records installed skills in the graph, and flags trigger overlaps and drift on each doctor run. Triggers on "set up hydra", "install the stack", "hydra doctor", "fix my skills", "something is broken in my setup", "install gsd", "retire kuzu", "which skills overlap", fresh-machine setup, or a suite skill reporting a missing dependency. Runs scripts/setup.py (doctor, install, fix).
metadata:
  authored_via: "claude-science"
  published_by: "agent"
  published_at: "2026-10-22T18:09:57.570Z"
  authored_by: "unknown"
  last_modified_by: "agent"
  last_modified_at: "2026-10-22T18:09:57.562Z"
---

# Hydra Setup — install, verify, self-repair (any runtime)

One stdlib script owns the stack's health: `scripts/setup.py`. Three modes — `doctor` (report only,
exit 1 if anything FAILs), `install` (idempotent, backs up every file it touches to
`~/.hydra/backups/<stamp>/`), `fix` (repairs only what doctor flagged; three strikes per component,
then it stops and tells you). Run it; don't hand-install.

```bash
python scripts/setup.py doctor
python scripts/setup.py install --vault <obsidian vault> --suite-src <folder with the suite skills> [--with-rag] [--with-gsd] [--with-graphify] [--dry-run]
python scripts/setup.py fix
```

Flags: `--python <interp>` (the interpreter hooks should use), `--skills-dir <dir>` (repeatable),
`--rag-python <3.12/3.13 interp>` (base for the Chroma venv), `--dry-run`, `--json` (doctor).
`HYDRA_HOME` moves the config, graph, backups and chroma store (default `~/.hydra`).

## What it manages (doctor's table, top to bottom)

| Row | Check | Fix |
|---|---|---|
| runtime, config | detected runtime; `config.json` present | install writes it |
| tool/* | git, node, npx, python; ollama and uv are optional | informational |
| belt/* | 7 blader skills: `SKILL.md` present, git repo | re-clone (taskmaster is retired: Codex-only, broken hook) |
| suite/* | the 8 suite skills + hydra-graph, `name:` matches folder | copy from `--suite-src` |
| gsd-core | `gsd-*` commands installed | prints `npx @opengsd/gsd-core@latest` (interactive, never auto-run) |
| hydra-mem/* | code, db, five hooks, async flags, **graph-wiring** (`settings.env` HYDRA_BRIDGE → hydra_graph.py), no hook command containing "kuzu" | install writes the three env keys with a backup |
| hydra-graph/* | db reachable, **integrity chain verifies**, quarantine count, last promote | `hydra_graph.py quarantine list` / `rollback` |
| vault/* | path, layout (obsidian-mind or plain), the three hydra folders | created on install or first export |
| rag | worker probe: which backend answered (ollama / onnx) | `--with-rag`; start Ollama or allow the one-time ONNX download |
| graphify | optional; binary on PATH when enabled | prints `uv tool install graphifyy && graphify install` |
| absorb/overlaps | skills sharing trigger phrases or ≥70 % description tokens | `hydra_graph.py overlaps`; hydra-evolve decides what to merge |
| legacy/* | kuzu-memory still registered; claude-mem present | `MIGRATION-kuzu.md`; claude-mem is intentionally unused |

## Absorb on install, drift on doctor

`install` and `fix` end with `hydra_graph.py absorb`: every `SKILL.md` under the skills dirs becomes a
`skill` node (reference status — its text is never injected into context) with its trigger phrases as
`capability` nodes. Two skills claiming the same phrase get a `contradicts` edge tagged
`trigger-overlap`; doctor prints the count. When a skill's git rev / plugin version / content hash
changes (a `/plugin update`, a new superpowers release, your own edit), the old node is superseded and
the new one linked — that is how updates fold in visibly instead of silently.

## Self-healing rules

- Every component has a machine check; `fix` acts only on FAIL rows.
- Interactive upstream installers (GSD Core, graphify, Ollama pulls) are never run without their
  flag; the exact command is printed. hydra-mem's own `install.py` is likewise pointed at, not re-done.
- claude-mem is not part of this stack; `--with-mem` does not exist.
- In claude.ai / Cowork the script runs for demonstration in the sandbox; persistent installs happen on
  your machine — it prints the one-liner to run there.

## Anti-patterns

- Hand-copying GSD Core files; putting a path in a SKILL.md instead of `config.json`
- Running fix before doctor; deleting healthy installs; touching vault notes outside the three hydra folders
- Approving a quarantined item without reading it
