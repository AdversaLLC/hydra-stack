# Retiring kuzu-memory (reversible; nothing removed without your go-ahead)

## Is it genuinely better? The evidence, not the pitch

| | kuzu-memory (today) | hydra-graph |
|---|---|---|
| Import/open time | 5–6 s measured on your machine (README) → required a cache layer and a 2 s SessionStart cap | 40–80 ms (`stats` on a 108-node graph in the sandbox); no cache needed, cache kept anyway |
| Writers | single-writer; `promote` rejected while the MCP server holds the DB (README "two rules") | SQLite WAL; hooks, CLI and MCP write concurrently (hydra-mem's own 40-parallel-hook test pattern) |
| Installer hazard | deletes any hook whose command contains "kuzu" (HANDOVER) | none; doctor still checks for the substring until kuzu is gone |
| Dependency surface | 93 MB uv tool env, Kuzu 0.11.3, `mcp` pin (2.3.0 crashed the server; pinned to 1.25.0 offline) | stdlib; Chroma optional in its own venv |
| Cross-project leakage | bridge promoted every project into every graph: 6 of 7 context caches near-identical, clipped mid-item (logs/hydra-mem.md) | `project` column; context and recall filter by it; global rows are explicit (`project IS NULL`) |
| Provenance / poisoning | episodic memories expire in 30 days; no trust lanes, no screen, no integrity check | trust lanes, screen, quarantine, HMAC audit chain, rollback (POISONING.md) |
| Interop | 11 MCP tools; CLI | 6 MCP tools (same `graph_recall`/`graph_context` names hydra-mem calls), CLI, Obsidian notes, `graph.db` readable by any SQLite client, same `nodes`/`edges` shape as research-base |
| What you lose | vector search inside kuzu | re-provided by Chroma tier (optional) |

Verdict: for *this* stack — stdlib rule, Windows, hooks on a 2 s budget, one owner — yes. If you ran
a multi-user server with Cypher queries, kuzu would be the right tool; you don't.

## Steps

1. **Safety copy of anything only kuzu has** (hydra-sourced rows are already in `mem.db`):
   ```
   <kuzu-python> C:/Users/Admin/Desktop/USB/hydra-mem/hydra_bridge.py recall "" --project-root <project> > kuzu-export-<project>.txt
   ```
   (or `kuzu-memory memory recall ""` in the project dir). Do this per project that has `.kuzu-memory/`.
2. **Install hydra-graph** — `python setup.py install --vault <vault> --suite-src <suite>` — it only
   adds three `env` keys to `settings.json` (backed up) and one MCP entry to `~/.claude.json`.
3. **Rebuild from the source of truth**: `python hydra_graph.py promote` pulls every wisdom row
   from `mem.db` (watermark starts at 0). Compare counts: `python hydra_mem.py stats` vs
   `python hydra_graph.py --json stats`.
4. **Run one real session.** Confirm SessionStart shows the `hydra-graph (...)` block, then
   `python hydra_graph.py verify-integrity` and `quarantine list`.
5. **Only then, on your explicit go-ahead** (CLAUDE.md: ask before anything hard to undo):
   - remove `projects[*].mcpServers["kuzu-memory"]` from `~/.claude.json` and the entry in `~/.mcp_servers.json`
     (`copy /Y` the `.bak-kuzu-memory` files back, as HANDOVER documents, or pop the keys)
   - `uv tool uninstall kuzu-memory`
   - delete `<project>/.kuzu-memory/` folders (each is one file + README)
   - delete `hydra_bridge.py` and `~/.claude/hydra-mem/bridge-cache/`
   `setup.py doctor` reports `legacy/kuzu-memory OK not present` when done.

## Undo

Set `HYDRA_BRIDGE_DISABLE=1` (hydra-mem then injects only its own half), or restore
`~/.hydra/backups/<stamp>/settings.json`. graph.db can be deleted at any time and rebuilt from
`mem.db` with `promote`.
