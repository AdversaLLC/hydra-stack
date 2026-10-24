#!/usr/bin/env python3
"""hydra-setup: doctor | install | fix for the GSD-Hydra stack, system-agnostic.

Stdlib only. Reads and writes one config file (~/.hydra/config.json, override HYDRA_HOME)
so no path lives in any SKILL.md. Detects the runtime (Claude Code, Codex, Cowork sandbox,
claude.ai, generic MCP client). Never runs an upstream installer (GSD Core, graphify,
Ollama pulls, chromadb venv) without its explicit --with-* flag; prints the command instead.
Every file it changes is backed up first to ~/.hydra/backups/<timestamp>/. Idempotent.

    python setup.py doctor
    python setup.py install --vault <path> [--with-rag] [--with-gsd] [--with-graphify]
    python setup.py fix
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def stack_root() -> Path | None:
    """The unzipped hydra-stack folder: the nearest ancestor holding belt-rules.json (or STACK env / config)."""
    env = os.environ.get("HYDRA_STACK")
    if env and (Path(env) / "belt-rules.json").is_file():
        return Path(env)
    for d in (HERE, *HERE.parents):
        if (d / "belt-rules.json").is_file():
            return d
    cfg = load_config().get("stack_root")
    return Path(os.path.expanduser(cfg)) if cfg and (Path(os.path.expanduser(cfg)) / "belt-rules.json").is_file() else None


BELT = ["baton", "Claudeception", "adversarial-execution", "theorist", "napkin", "razor", "schematic"]
BELT_URL = "https://github.com/blader/{name}.git"
# the installed tier = every folder under <stack>/skills; shelf = <stack>/shelf (loaded on demand by `belt --load`)
UPSTREAM_HINTS = {  # printed, never run: these are interactive or plugin-marketplace installs
    "gsd-core": "npx @opengsd/gsd-core@latest            # GSD Core 1.18+, pick runtime + scope when it asks",
    "superpowers": "/plugin marketplace add obra/superpowers-marketplace && /plugin install superpowers@superpowers-marketplace   # or keep using the shelved copies",
    "grace": "/plugin marketplace add osovv/grace-marketplace && /plugin install grace@grace-marketplace   # only if GRACE is the project's spine",
    "ponytail": "/plugin marketplace add DietrichGebert/ponytail && /plugin install ponytail@ponytail   # adds 3 hooks (+~3.5 KB per session); the shelved skills work without them",
    "neo4j": "npx skills add neo4j-contrib/neo4j-skills   # shelved copies already placed; Neo4j itself: docker run neo4j:2026 (self-hosted) - Aura is paid, off by default",
    "graphify": "uv tool install graphifyy && graphify install",
    "karpathy": "/plugin marketplace add multica-ai/andrej-karpathy-skills   # installed-tier copy already present",
}
ENV_KEYS = {  # written into settings.json "env" (applied to every session, hooks and the Bash tool inherit it, like the
    # user's existing BASH_DEFAULT_TIMEOUT_MS). hydra_mem.py spawns the graph where it spawned the bridge; the skills'
    # bash snippets use HYDRA_PY / HYDRA_GRAPH / HYDRA_MEM_PY so no SKILL.md needs `python` on PATH or a machine path.
    "HYDRA_BRIDGE": "{graph_py}", "HYDRA_BRIDGE_PYTHON": "{python}", "HYDRA_GRAPH_PREFER_BRIDGE": "1",
    "HYDRA_PY": "{python}", "HYDRA_GRAPH": "{graph_py}", "HYDRA_MEM_PY": "{mem_py}", "HYDRA_HOME": "{hydra_home}",
}


def hydra_home() -> Path:
    return Path(os.environ.get("HYDRA_HOME") or (Path.home() / ".hydra"))


def which(*names: str) -> str | None:
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None


def run(cmd: list[str], timeout=20, cwd=None) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=timeout, cwd=cwd, stdin=subprocess.DEVNULL)
        return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace").strip()
    except Exception as e:
        return 1, str(e)


# --------------------------------------------------------------------------- runtime + config

def detect_runtime() -> str:
    h = Path.home()
    if os.environ.get("CLAUDE_CODE_SSE_PORT") or os.environ.get("CLAUDECODE") or (h / ".claude" / "settings.json").is_file():
        return "claude-code"
    if (h / ".codex").is_dir():
        return "codex"
    if Path("/mnt/user-data").exists() or Path("/home/claude").exists():
        return "cowork-or-claude-ai-sandbox"
    return "generic-mcp-client"


def default_config() -> dict:
    h = Path.home()
    rt = detect_runtime()
    skills = {"claude-code": ["~/.claude/skills", "~/.claude/plugins"], "codex": ["~/.codex/skills"]}.get(rt, ["~/.claude/skills"])
    st = str(hydra_home() / "stack")  # install copies memory/, shelf/, belt-rules.json, absorb-seed.jsonl here
    return {
        "version": 2, "runtime": rt, "python": sys.executable, "os": platform.system(),
        "skills_dirs": skills, "stack_root": st, "shelf_dirs": [st + "/shelf"], "belt_rules": st + "/belt-rules.json",
        "mem_db": "~/.claude/hydra-mem/mem.db", "mem_py": "~/.claude/hydra-mem/hydra_mem.py",
        "graph_db": "~/.hydra/graph.db", "graph_py": st + "/memory/hydra_graph.py",
        "vault": None, "vault_layout": "obsidian-mind",
        "rag": {"backend": "auto", "model": "nomic-embed-text", "python": None, "worker": st + "/memory/rag_worker.py",
                "chroma_path": "~/.hydra/chroma", "venv": "~/.hydra/venv-rag"},
        "gsd": {"installer": "npx @opengsd/gsd-core@latest"},
        "graphify": {"enabled": False, "out": "graphify-out", "installer": "uv tool install graphifyy && graphify install"},
        "legacy": {"kuzu": "retired; see MIGRATION-kuzu.md"},
    }


def load_config() -> dict:
    p = hydra_home() / "config.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def expand(p) -> Path | None:
    return Path(os.path.expandvars(os.path.expanduser(str(p)))) if p else None


def backup(path: Path, stamp: str) -> None:
    if path.exists():
        dst = hydra_home() / "backups" / stamp / path.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dst)


# --------------------------------------------------------------------------- checks (each returns status, detail, fix-hint)

OK, WARN, FAIL, INFO = "OK", "WARN", "FAIL", "INFO"


def check_belt(cfg) -> list[tuple]:
    rows = []
    for base in [expand(d) for d in cfg.get("skills_dirs", [])][:1]:
        for name in BELT:
            d = base / name
            if (d / "SKILL.md").is_file() and (d / "SKILL.md").stat().st_size > 0:
                rc, _ = run(["git", "-C", str(d), "rev-parse", "--is-inside-work-tree"], 5)
                rows.append((f"belt/{name}", OK if rc == 0 else WARN, "git clone" if rc == 0 else "present, not a git repo", ""))
            else:
                rows.append((f"belt/{name}", FAIL, "missing", f"git clone {BELT_URL.format(name=name)} {d}"))
    return rows


def installed_tier(suite_src: Path | None) -> list[Path]:
    src = suite_src or ((stack_root() / "skills") if stack_root() else None)
    return sorted(d for d in src.iterdir() if (d / "SKILL.md").is_file()) if src and src.is_dir() else []


def check_suite(cfg, suite_src: Path | None) -> list[tuple]:
    rows = []
    base = expand(cfg.get("skills_dirs", ["~/.claude/skills"])[0])
    srcs = installed_tier(suite_src)
    if not srcs:
        return [("suite", FAIL, "no stack skills/ folder found", "run from the unzipped hydra-stack or pass --suite-src")]
    missing, stale, ok = [], [], 0
    for sd in srcs:
        d = base / sd.name
        if not (d / "SKILL.md").is_file():
            missing.append(sd.name)
        elif (d / "SKILL.md").read_bytes() != (sd / "SKILL.md").read_bytes():
            stale.append(sd.name)
        else:
            ok += 1
    rows.append(("suite/installed-tier", OK if not missing and not stale else FAIL,
                 f"{ok}/{len(srcs)} present and identical" + (f"; missing {missing}" if missing else "") + (f"; differ from stack {stale}" if stale else ""),
                 "" if not missing and not stale else "setup.py install (copies from the stack's skills/; your edits are backed up)"))
    return rows


def check_gsd(cfg) -> list[tuple]:
    npx = which("npx", "npx.cmd")
    h = Path.home()
    present = any((h / p).exists() for p in (".claude/commands/gsd-new-project.md", ".claude/commands/gsd", ".claude/commands/gsd-onboard.md", ".claude/gsd-core"))
    cmds = list((h / ".claude" / "commands" / "gsd").glob("*.md")) if (h / ".claude" / "commands" / "gsd").is_dir() else list((h / ".claude" / "commands").glob("gsd*")) if (h / ".claude" / "commands").is_dir() else []
    ver = ""
    for pj in (h / ".claude" / "gsd-core" / "package.json", h / ".claude" / "gsd-core" / "VERSION"):
        try:
            ver = json.loads(pj.read_text(encoding="utf-8")).get("version", "") if pj.suffix == ".json" else pj.read_text().strip()
            break
        except Exception:
            pass
    if present or cmds:
        return [("gsd-core", OK, f"{len(cmds)} gsd command(s)" + (f", runtime {ver}" if ver else "") + " (1.18.0 is current as of 2026-10-21)", "")]
    return [("gsd-core", FAIL, "not installed (archived gsd-build/get-shit-done does not count)",
             (cfg.get("gsd", {}).get("installer", "npx @opengsd/gsd-core@latest")) + ("" if npx else "  (install Node 20+ first)"))]


def check_hydra_mem(cfg) -> list[tuple]:
    rows = []
    py = expand(cfg.get("mem_py"))
    db = expand(cfg.get("mem_db"))
    if not py or not py.is_file():
        return [("hydra-mem", FAIL, f"hydra_mem.py not at {py}", "point config.mem_py at your hydra_mem.py")]
    rows.append(("hydra-mem/code", OK, str(py), ""))
    rows.append(("hydra-mem/db", OK if db and db.is_file() else WARN, str(db) if db and db.is_file() else "mem.db not created yet (first hook creates it)", ""))
    s = Path.home() / ".claude" / "settings.json"
    try:
        st = json.loads(s.read_text(encoding="utf-8"))
        hooks = st.get("hooks", {})
        have = {ev for ev, lst in hooks.items() for h in lst for hh in h.get("hooks", []) if "hydra-mem" in hh.get("command", "") or "hydra_mem" in hh.get("command", "")}
        need = {"SessionStart", "UserPromptSubmit", "PostToolUse", "Stop", "SessionEnd"}
        miss = need - have
        rows.append(("hydra-mem/hooks", OK if not miss else FAIL, "all five registered" if not miss else f"missing {sorted(miss)}", "" if not miss else "python hydra-mem/install.py (then re-check async flags)"))
        async_ok = all(hh.get("async") for ev in ("UserPromptSubmit", "PostToolUse") for h in hooks.get(ev, []) for hh in h.get("hooks", []) if "hydra_mem" in hh.get("command", ""))
        rows.append(("hydra-mem/async", OK if async_ok else WARN, "UserPromptSubmit/PostToolUse async" if async_ok else "async: true missing on UserPromptSubmit/PostToolUse", ""))
        env = st.get("env", {})
        want = env_want(cfg)
        wired = all(env.get(k) == v for k, v in want.items())
        bad = [k for k in ("HYDRA_BRIDGE", "HYDRA_BRIDGE_PYTHON") if "kuzu" in str(env.get(k, "")).lower()]
        rows.append(("hydra-mem/graph-wiring", OK if wired else FAIL,
                     "settings.env points hydra-mem at hydra_graph.py" if wired else ("still points at kuzu bridge" if bad else "HYDRA_BRIDGE / HYDRA_BRIDGE_PYTHON not set"),
                     "" if wired else "setup.py install (writes the three env keys, with backup)"))
        kuzu_hooks = [hh.get("command") for ev, lst in hooks.items() for h in lst for hh in h.get("hooks", []) if "kuzu" in hh.get("command", "").lower()]
        if kuzu_hooks:
            rows.append(("hydra-mem/hook-safety", FAIL, "a hook command contains 'kuzu' (kuzu-memory's installer deletes such hooks)", "rename/move the command"))
    except Exception as e:
        rows.append(("hydra-mem/hooks", FAIL, f"cannot read settings.json: {e}", ""))
    return rows


def check_graph(cfg) -> list[tuple]:
    gp = expand(cfg.get("graph_py"))
    if not gp or not gp.is_file():
        return [("hydra-graph", FAIL, "hydra_graph.py missing", "setup.py install")]
    gdb = expand(cfg.get("graph_db"))
    if not gdb or not gdb.is_file():
        return [("hydra-graph/db", WARN, "graph.db not initialized", "setup.py install")]
    rc, out = run([sys.executable, "-I", str(gp), "--json", "stats"], 20)
    if rc != 0:
        return [("hydra-graph", FAIL, out[-200:], "")]
    try:
        s = json.loads(out)
    except Exception:
        return [("hydra-graph", FAIL, "stats not json", "")]
    rows = [("hydra-graph/db", OK, f"{sum(s.get('nodes', {}).values())} nodes, {sum(s.get('edges', {}).values())} edges, {s.get('audit_rows')} audit rows", "")]
    integ = s.get("integrity", "")
    rows.append(("hydra-graph/integrity", OK if integ.startswith("ok") else FAIL, integ, "" if integ.startswith("ok") else "graph.db was changed outside hydra-graph: review `hydra_graph.py rollback` / restore a backup"))
    q = s.get("nodes", {}).get("quarantined", 0)
    rows.append(("hydra-graph/quarantine", INFO if q else OK, f"{q} item(s) awaiting review" if q else "empty", "hydra_graph.py quarantine list" if q else ""))
    lp = s.get("sync", {}).get("hydra-mem.last_promote")
    rows.append(("hydra-graph/promote", OK if lp else WARN, f"last {lp}" if lp else "never promoted", "" if lp else "hydra_graph.py promote"))
    return rows


def check_vault(cfg) -> list[tuple]:
    v = expand(cfg.get("vault"))
    if not v:
        return [("vault", WARN, "no vault configured", "setup.py install --vault <path>")]
    if not v.is_dir():
        return [("vault", FAIL, f"{v} not found", "")]
    layout = "obsidian-mind" if (v / "brain").is_dir() and (v / ".claude" / "scripts").is_dir() else "plain"
    rows = [("vault", OK, f"{v} ({layout})", "")]
    for f in ("Hydra Wisdom", "Hydra Graph", "Theory"):
        rows.append((f"vault/{f}", OK if (v / f).is_dir() else WARN, "present" if (v / f).is_dir() else "will be created on first export", ""))
    return rows


def check_rag(cfg) -> list[tuple]:
    r = cfg.get("rag", {})
    py = expand(r.get("python"))
    worker = expand(r.get("worker"))
    if not py or not py.is_file():
        return [("rag", INFO, "tier 1 (vectors) not set up; FTS-only recall works",
                 "setup.py install --with-rag   (creates the isolated venv and pip-installs chromadb)")]
    req = json.dumps({"op": "probe", "path": str(expand(r.get("chroma_path"))), "backend": r.get("backend", "auto"), "model": r.get("model", "")})
    try:
        p = subprocess.run([str(py), "-I", str(worker)], input=(req + "\n").encode(), capture_output=True, timeout=60,
                           env={**os.environ, "HYDRA_RAG_NO_DOWNLOAD": "1"})
        resp = json.loads(p.stdout.decode("utf-8", "replace").strip().splitlines()[-1])
    except Exception as e:
        return [("rag", FAIL, f"worker probe failed: {e}", "")]
    if resp.get("ok"):
        return [("rag", OK, f"backend {resp.get('backend')}", "")]
    return [("rag", WARN, resp.get("error", "probe failed"), "start Ollama (`ollama pull nomic-embed-text`) or allow the one-time ONNX model download")]


def check_graphify(cfg) -> list[tuple]:
    g = cfg.get("graphify", {})
    exe = which("graphify")
    if not g.get("enabled"):
        return [("graphify", INFO, "optional, disabled" + (" (binary found)" if exe else ""), "setup.py install --with-graphify")]
    return [("graphify", OK if exe else FAIL, exe or "not on PATH", "" if exe else g.get("installer", ""))]


def check_belt(cfg) -> list[tuple]:
    gp = expand(cfg.get("graph_py"))
    if not gp or not gp.is_file():
        return [("belt", WARN, "hydra_graph.py missing", "setup.py install")]
    cmd = [sys.executable, "-I", str(gp), "--json", "belt", "--no-db"] + sum((["--skills-dir", str(expand(d))] for d in cfg.get("skills_dirs", [])), []) \
        + sum((["--shelf", str(expand(d))] for d in cfg.get("shelf_dirs", [])), [])
    rc, out = run(cmd, 60, cwd=str(hydra_home()))
    try:
        ents = json.loads(out)["skills"]
    except Exception:
        return [("belt", WARN, f"belt scan failed: {out[-120:]}", "")]
    inst = [e for e in ents if e["tier"] == "installed"]
    un = [e["name"] for e in ents if "unplaced" in e["slots"]]
    rows = [("belt/tiers", OK, f"{len(inst)} installed, {len(ents) - len(inst)} shelved; always-on descriptions ~{sum(e['desc_tokens'] for e in inst)} tokens/session", ""),
            ("belt/unplaced", INFO if un else OK, (", ".join(un[:6]) + (" …" if len(un) > 6 else "")) if un else "every skill has a slot",
             "add rules to belt-rules.json or let hydra-evolve ABSORB place them" if un else "")]
    big = sorted(inst, key=lambda e: -e["desc_tokens"])[:3]
    if inst and sum(e["desc_tokens"] for e in inst) > 6000:
        rows.append(("belt/cost", WARN, "installed descriptions exceed ~6k tokens/session; shelve what you rarely use: " + ", ".join(e["name"] for e in big), "hydra_graph.py belt --unload <name>"))
    return rows


def check_hooks(cfg) -> list[tuple]:
    """Census of every hook command in settings.json, by owner, so stacked spines are visible."""
    s = Path.home() / ".claude" / "settings.json"
    try:
        hooks = json.loads(s.read_text(encoding="utf-8")).get("hooks", {})
    except Exception:
        return []
    owners: dict[str, list[str]] = {}
    total = 0
    for ev, lst in hooks.items():
        for h in lst:
            for hh in h.get("hooks", []):
                c = hh.get("command", "")
                total += 1
                own = ("hydra-mem" if "hydra_mem" in c or "hydra-mem" in c else "vault/obsidian-mind" if "/.claude/scripts/" in c or "vault" in c
                       else "gsd" if "gsd" in c.lower() else "ponytail" if "ponytail" in c.lower() else "remote_guard" if "remote_guard" in c
                       else "kuzu" if "kuzu" in c.lower() else "other")
                owners.setdefault(own, []).append(f"{ev}{'(async)' if hh.get('async') else ''}")
    rows = [("hooks/census", INFO, f"{total} hook commands: " + "; ".join(f"{k}: {len(v)}" for k, v in sorted(owners.items())), "")]
    spines = [k for k in owners if k in ("gsd", "ponytail", "vault/obsidian-mind")]
    if len(spines) >= 2:
        rows.append(("hooks/stacked", WARN, f"{len(spines) + 1} hook owners share SessionStart/Stop ({', '.join(['hydra-mem'] + spines)}); stacking is [U] untested upstream - check order if session start misbehaves", ""))
    if "other" in owners:
        rows.append(("hooks/unknown-owner", WARN, f"{len(owners['other'])} hook(s) with no known owner: review them", ""))
    return rows


def check_absorb(cfg) -> list[tuple]:
    gp = expand(cfg.get("graph_py"))
    rc, out = run([sys.executable, "-I", str(gp), "--json", "overlaps"], 20)
    try:
        ov = json.loads(out)
    except Exception:
        ov = None
    if ov is None:
        return [("absorb", WARN, "graph not reachable", "")]
    return [("absorb/overlaps", INFO if ov else OK, f"{len(ov)} trigger/description overlap(s)" + (": " + "; ".join(ov[:3]) if ov else ""), "hydra_graph.py overlaps" if ov else "")]


def check_kuzu(cfg) -> list[tuple]:
    rows = []
    h = Path.home()
    found = []
    for p in (h / ".claude.json", h / ".mcp_servers.json"):
        try:
            if "kuzu" in p.read_text(encoding="utf-8", errors="replace").lower():
                found.append(p.name)
        except Exception:
            pass
    uv = which("kuzu-memory", "kuzu-memory.exe")
    if found or uv:
        rows.append(("legacy/kuzu-memory", WARN, "still registered: " + ", ".join(found + ([uv] if uv else [])), "see MIGRATION-kuzu.md (export, verify, then remove on your go-ahead)"))
    else:
        rows.append(("legacy/kuzu-memory", OK, "not present", ""))
    if which("claude-mem"):
        rows.append(("legacy/claude-mem", WARN, "installed but intentionally unused here", ""))
    return rows


def check_tools() -> list[tuple]:
    rows = []
    for name, alts, why in (("git", ("git",), "belt clones, project roots"), ("node", ("node",), "GSD Core, obsidian-mind hooks"),
                            ("npx", ("npx", "npx.cmd"), "GSD installer"), ("ollama", ("ollama",), "local embeddings (optional)"),
                            ("uv", ("uv",), "graphify (optional)")):
        p = which(*alts)
        rows.append((f"tool/{name}", OK if p else (INFO if name in ("ollama", "uv") else WARN), p or f"not found ({why})", ""))
    rows.append(("tool/python", OK, f"{platform.python_version()} at {sys.executable}", ""))
    return rows


def doctor(cfg, suite_src=None) -> list[tuple]:
    rows: list[tuple] = []
    rows += [("runtime", INFO, cfg.get("runtime", detect_runtime()), ""), ("config", OK if (hydra_home() / "config.json").is_file() else WARN,
             str(hydra_home() / "config.json"), "" if (hydra_home() / "config.json").is_file() else "setup.py install"),
             ("stack", OK if stack_root() else WARN, str(stack_root() or "not found (run from the unzipped hydra-stack or set HYDRA_STACK)"), "")]
    rows += check_tools()
    rows += check_belt(cfg) + check_suite(cfg, suite_src) + check_gsd(cfg) + check_hydra_mem(cfg) + check_graph(cfg)
    rows += check_vault(cfg) + check_rag(cfg) + check_graphify(cfg) + check_belt(cfg) + check_hooks(cfg) + check_absorb(cfg) + check_kuzu(cfg)
    return rows


def print_table(rows) -> None:
    w = max(len(r[0]) for r in rows)
    print(f"{'component'.ljust(w)}  status  detail")
    for name, st, detail, hint in rows:
        print(f"{name.ljust(w)}  {st.ljust(6)}  {detail}" + (f"\n{' ' * (w + 10)}-> {hint}" if hint else ""))
    counts = {s: sum(1 for r in rows if r[1] == s) for s in (OK, WARN, FAIL, INFO)}
    print(f"\n{counts[OK]} ok, {counts[WARN]} warn, {counts[FAIL]} fail, {counts[INFO]} info")


# --------------------------------------------------------------------------- install / fix

def env_want(cfg) -> dict:
    return {k: v.format(graph_py=cfg.get("graph_py"), python=cfg.get("python"), mem_py=str(expand(cfg.get("mem_py")) or ""),
                        hydra_home=str(hydra_home())) for k, v in ENV_KEYS.items()}


def write_settings_env(cfg, stamp: str, dry: bool) -> str:
    s = Path.home() / ".claude" / "settings.json"
    if not s.is_file():
        return "settings.json not found; skipped (not Claude Code?)"
    st = json.loads(s.read_text(encoding="utf-8"))
    env = st.setdefault("env", {})
    want = env_want(cfg)
    if all(env.get(k) == v for k, v in want.items()):
        return "settings.env already wired"
    if dry:
        return f"would set settings.env {want}"
    backup(s, stamp)
    env.update(want)
    s.write_text(json.dumps(st, indent=2) + "\n", encoding="utf-8")
    return f"settings.env set: {', '.join(want)} (backup in {hydra_home() / 'backups' / stamp})"


def register_mcp(cfg, stamp: str, dry: bool) -> str:
    """Add mcpServers.hydra-graph to ~/.claude.json (user scope) so any MCP client can use the graph."""
    cj = Path.home() / ".claude.json"
    if not cj.is_file():
        return ".claude.json not found; register `python hydra_graph.py mcp` as a stdio server in your client"
    data = json.loads(cj.read_text(encoding="utf-8"))
    entry = {"type": "stdio", "command": cfg["python"], "args": ["-I", cfg["graph_py"], "mcp"], "env": {"PYTHONUTF8": "1"}}
    if data.get("mcpServers", {}).get("hydra-graph") == entry:
        return "mcp hydra-graph already registered"
    if dry:
        return "would add mcpServers.hydra-graph to ~/.claude.json"
    backup(cj, stamp)
    data.setdefault("mcpServers", {})["hydra-graph"] = entry
    cj.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return "mcp hydra-graph registered in ~/.claude.json"


def setup_rag_venv(cfg, dry: bool) -> str:
    venv = expand(cfg["rag"]["venv"])
    # Checked on PyPI 2026-10-21: chromadb 1.5.9 ships a cp39-abi3 wheel, onnxruntime 1.31.0 and tokenizers 0.23.3 ship
    # cp314 wheels, so the user's 3.14 works. Base = the configured interpreter; 3.13/3.12 only as fallbacks.
    cand = [cfg.get("python")] + [which(f"python3.{m}", f"python3.{m}.exe") for m in (13, 12)] + [sys.executable]
    base = next((c for c in cand if c and Path(c).is_file()), sys.executable)
    pyv = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if pyv.is_file():
        rc, out = run([str(pyv), "-c", "import chromadb; print(chromadb.__version__)"], 60)
        if rc == 0:
            cfg["rag"]["python"] = str(pyv)
            return f"rag venv ok (chromadb {out})"
    if dry:
        return f"would create {venv} with {base} and pip install chromadb"
    rc, out = run([base, "-m", "venv", str(venv)], 120)
    if rc != 0:
        return f"venv failed: {out[-200:]}"
    rc, out = run([str(pyv), "-m", "pip", "install", "--disable-pip-version-check", "-q", "chromadb"], 600)
    if rc != 0:
        return f"pip install chromadb failed under {base}: {out[-300:]}\n  (try --rag-python <3.12 or 3.13 interpreter>)"
    cfg["rag"]["python"] = str(pyv)
    return f"rag venv created at {venv} (base {base})"


def install(a) -> int:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    cfg = {**default_config(), **load_config()}
    if a.vault:
        cfg["vault"] = str(Path(a.vault).resolve())
    if a.python:
        cfg["python"] = a.python
    if a.skills_dir:
        cfg["skills_dirs"] = a.skills_dir
    if a.rag_python:
        cfg["rag"]["python"] = a.rag_python
    if a.with_graphify:
        cfg["graphify"]["enabled"] = True
    # code runs from the copied payload under ~/.hydra/stack so the unzipped folder can be deleted afterwards
    cfg["graph_py"] = str(Path(cfg["stack_root"]) / "memory" / "hydra_graph.py")
    cfg["rag"]["worker"] = str(Path(cfg["stack_root"]) / "memory" / "rag_worker.py")
    cfg["belt_rules"] = str(Path(cfg["stack_root"]) / "belt-rules.json")
    cfg["shelf_dirs"] = [str(Path(cfg["stack_root"]) / "shelf")]
    say = (lambda m: print(("[dry-run] " if a.dry_run else "") + m))
    hh = hydra_home()
    if not a.dry_run:
        hh.mkdir(parents=True, exist_ok=True)
        (hh / "backups" / stamp).mkdir(parents=True, exist_ok=True)
    # stack payload -> ~/.hydra/stack (memory code, shelf, rules, seed) so the zip folder can go away afterwards
    st = stack_root()
    if not st:
        print("Refusing: run setup.py from inside the unzipped hydra-stack (belt-rules.json not found above this file).", file=sys.stderr)
        return 2
    target = Path(cfg["stack_root"])
    for item in ("memory", "shelf", "belt-rules.json", "absorb-seed.jsonl", "BELT.md", "WORKFLOW.md"):
        src_i, dst_i = st / item, target / item
        if not src_i.exists():
            continue
        say(f"stack: {item} -> {dst_i}")
        if not a.dry_run:
            if dst_i.is_dir():
                shutil.rmtree(dst_i)
            dst_i.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src_i, dst_i, ignore=shutil.ignore_patterns("__pycache__", "*.pyc")) if src_i.is_dir() else shutil.copy2(src_i, dst_i)
    # installed tier: every folder under <stack>/skills
    base = expand(cfg["skills_dirs"][0])
    src = Path(a.suite_src).resolve() if a.suite_src else None
    for sdir in installed_tier(src):
        name = sdir.name
        d = base / name
        if d.is_dir() and (d / "SKILL.md").is_file() and (d / "SKILL.md").read_bytes() == (sdir / "SKILL.md").read_bytes():
            continue
        say(f"skill/{name}: copy -> {d}" + (" (yours backed up)" if d.exists() else ""))
        if not a.dry_run:
            if d.exists():
                shutil.copytree(d, hh / "backups" / stamp / "skills" / name, dirs_exist_ok=True)
                shutil.rmtree(d)
            shutil.copytree(sdir, d, ignore=shutil.ignore_patterns("__pycache__", ".git"))
    # belt clones (git first; the zip's vendor copy when offline)
    for name in BELT:
        d = base / name
        if (d / "SKILL.md").is_file():
            continue
        vend = st / "vendor" / name
        say(f"belt/{name}: git clone {BELT_URL.format(name=name)}" + (f" (fallback: {vend})" if vend.is_dir() else ""))
        if not a.dry_run:
            rc, out = run(["git", "clone", "--depth", "1", BELT_URL.format(name=name), str(d)], 120)
            if rc != 0 and vend.is_dir():
                shutil.copytree(vend, d)
                rc, out = 0, "copied from vendor"
            say(f"  -> {'ok' if rc == 0 else out[-120:]}")
    # graph db + vault folders
    say("graph: init " + cfg["graph_db"])
    if not a.dry_run:
        run([cfg["python"], "-I", cfg["graph_py"], "init"], 30)
    v = expand(cfg.get("vault"))
    if v and v.is_dir():
        for f in ("Hydra Wisdom", "Hydra Graph", "Theory"):
            if not (v / f).is_dir():
                say(f"vault: mkdir {v / f}")
                if not a.dry_run:
                    (v / f).mkdir(parents=True)
    # wiring
    say(write_settings_env(cfg, stamp, a.dry_run))
    say(register_mcp(cfg, stamp, a.dry_run))
    if a.with_rag:
        say(setup_rag_venv(cfg, a.dry_run))
    else:
        say("rag: tier 1 not set up (pass --with-rag); FTS recall works now")
    say("upstream installers are never run by this script; when you want one, run it yourself:")
    for key, cmd in UPSTREAM_HINTS.items():
        say(f"  {key:12s} {cmd}")
    # config
    cp = hh / "config.json"
    say(f"config: write {cp}")
    if not a.dry_run:
        backup(cp, stamp)
        cp.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
        # absorb on install: record every installed skill, flag overlaps, detect drift
        rc, out = run([cfg["python"], "-I", cfg["graph_py"], "--json", "absorb", *sum((["--skills-dir", str(expand(d))] for d in cfg["skills_dirs"]), [])], 120)
        say("absorb: " + (out[:300] if rc == 0 else f"failed: {out[-200:]}"))
        rc, out = run([cfg["python"], "-I", cfg["graph_py"], "--json", "promote", "--no-embed"], 300)
        say("promote: " + (out[:200] if rc == 0 else f"failed: {out[-200:]}"))
        seed = target / "absorb-seed.jsonl"
        if seed.is_file():
            rc, out = run([cfg["python"], "-I", cfg["graph_py"], "--json", "seed-import", str(seed)], 60)
            say("seed (absorbed decisions + constitution): " + (out[:160] if rc == 0 else f"failed: {out[-160:]}"))
        rc, out = run([cfg["python"], "-I", cfg["graph_py"], "belt", "--write", str(target / "BELT.md")]
                      + sum((["--skills-dir", str(expand(d))] for d in cfg["skills_dirs"]), []) + sum((["--shelf", str(expand(d))] for d in cfg["shelf_dirs"]), []), 120)
        say("belt: " + (out.splitlines()[0][:200] if rc == 0 and out else f"failed: {out[-160:]}"))
    print()
    print_table(doctor(cfg, src))
    return 0


def fix(a) -> int:
    cfg = {**default_config(), **load_config()}
    rows = doctor(cfg, Path(a.suite_src) if a.suite_src else None)
    failed = [r for r in rows if r[1] == FAIL]
    if not failed:
        print("nothing to fix")
        print_table(rows)
        return 0
    strikes = json.loads((hydra_home() / "fix-strikes.json").read_text()) if (hydra_home() / "fix-strikes.json").is_file() else {}
    for name, _, detail, hint in failed:
        strikes[name] = strikes.get(name, 0) + 1
        if strikes[name] > 3:
            print(f"{name}: failed 3 times, not retrying ({detail}). Fix by hand: {hint}")
            continue
        if name.startswith("belt/"):
            n = name.split("/", 1)[1]
            d = expand(cfg["skills_dirs"][0]) / n
            if d.exists():
                shutil.rmtree(d)
            rc, out = run(["git", "clone", "--depth", "1", BELT_URL.format(name=n), str(d)], 120)
            print(f"{name}: re-cloned ({'ok' if rc == 0 else out[-100:]})")
        elif name in ("hydra-mem/graph-wiring", "hydra-graph", "config"):
            a.dry_run = False
            return install(a)
        else:
            print(f"{name}: {detail} -> {hint}")
    (hydra_home() / "fix-strikes.json").write_text(json.dumps(strikes))
    print()
    print_table(doctor(cfg))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="mode", required=True)
    for m in ("doctor", "install", "fix"):
        p = sp.add_parser(m)
        p.add_argument("--suite-src")
        p.add_argument("--vault")
        p.add_argument("--python")
        p.add_argument("--skills-dir", action="append")
        p.add_argument("--rag-python")
        p.add_argument("--with-rag", action="store_true")
        p.add_argument("--with-gsd", action="store_true")
        p.add_argument("--with-graphify", action="store_true")
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.mode == "doctor":
        cfg = {**default_config(), **load_config()}
        if a.vault:
            cfg["vault"] = a.vault
        rows = doctor(cfg, Path(a.suite_src) if a.suite_src else None)
        if a.json:
            print(json.dumps([dict(zip(("component", "status", "detail", "fix"), r)) for r in rows], indent=1))
        else:
            print_table(rows)
        return 1 if any(r[1] == FAIL for r in rows) else 0
    return install(a) if a.mode == "install" else fix(a)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass
    sys.exit(main())
