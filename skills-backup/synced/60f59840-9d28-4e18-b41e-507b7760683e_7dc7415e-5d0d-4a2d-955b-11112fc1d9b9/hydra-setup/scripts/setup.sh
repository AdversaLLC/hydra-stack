#!/usr/bin/env bash
# hydra-setup: install, verify, and self-repair the GSD-Hydra stack.
# Modes: doctor | install | fix. Idempotent. Never runs interactive upstream
# installers (GSD, claude-mem, taskmaster) without their explicit flag.
set -u

MODE="${1:-doctor}"; shift || true
HOME_DIR="$HOME"; SKILLS_DIR=""; TARGET="claude"; SUITE_SRC=""; VAULT=""; PROJECT=""
WITH_GSD=0; WITH_MEM=0; WITH_TM=0; ONLY=""; SKIP=""
while [ $# -gt 0 ]; do case "$1" in
  --home) HOME_DIR="$2"; shift 2;;
  --skills-dir) SKILLS_DIR="$2"; shift 2;;
  --codex) TARGET="codex"; shift;;
  --both) TARGET="both"; shift;;
  --suite-src) SUITE_SRC="$2"; shift 2;;
  --vault) VAULT="$2"; shift 2;;
  --project) PROJECT="$2"; shift 2;;
  --with-gsd) WITH_GSD=1; shift;;
  --with-mem) WITH_MEM=1; shift;;
  --with-taskmaster) WITH_TM=1; shift;;
  --only) ONLY="$2"; shift 2;;
  --skip) SKIP="$2"; shift 2;;
  *) echo "unknown flag: $1" >&2; exit 2;;
esac; done

GIT_BASE="${GIT_BASE:-https://github.com}"
BELT="baton Claudeception adversarial-execution theorist napkin taskmaster razor schematic"
SUITE="modulated-loop-orchestrator hydra-swarm nested-learning wisdom-memory theory-keeper gsd-hydra hydra-setup"
declare -A REPO=( [baton]=blader/baton [Claudeception]=blader/Claudeception \
  [adversarial-execution]=blader/adversarial-execution [theorist]=blader/theorist \
  [napkin]=blader/napkin [taskmaster]=blader/taskmaster [razor]=blader/razor \
  [schematic]=blader/schematic )

skilldirs() {
  if [ -n "$SKILLS_DIR" ]; then echo "$SKILLS_DIR"; return; fi
  case "$TARGET" in
    claude) echo "$HOME_DIR/.claude/skills";;
    codex)  echo "$HOME_DIR/.codex/skills";;
    both)   echo "$HOME_DIR/.claude/skills $HOME_DIR/.codex/skills";;
  esac
}

wanted() { # component filter via --only/--skip
  local n="$1"
  if [ -n "$ONLY" ]; then case ",$ONLY," in *",$n,"*) return 0;; *) return 1;; esac; fi
  case ",$SKIP," in *",$n,"*) return 1;; esac
  return 0
}

FAILED=""
ROWS=""
row() {
  ROWS="${ROWS}$(printf '%-24s | %-7s | %s' "$1" "$2" "$3")\n"
  if [ "$2" = "FAIL" ]; then FAILED="$FAILED $1"; fi
  return 0
}

check_belt() { # name dir -> OK/FAIL
  local d="$1"
  [ -d "$d" ] && [ -s "$d/SKILL.md" ] && git -C "$d" rev-parse --git-dir >/dev/null 2>&1
}
check_suite() { local d="$1" n="$2"; [ -s "$d/SKILL.md" ] && grep -q "^name: $n" "$d/SKILL.md"; }

install_belt() { # name dir
  local n="$1" d="$2" tries=0
  while [ $tries -lt 3 ]; do
    check_belt "$d" && return 0
    rm -rf "$d"
    if [ $tries -eq 2 ]; then git clone --depth 1 --quiet "$GIT_BASE/${REPO[$n]}.git" "$d"
    else git clone --depth 1 --quiet "$GIT_BASE/${REPO[$n]}.git" "$d" 2>/dev/null; fi
    tries=$((tries+1))
  done
  check_belt "$d"
}
install_suite() { # name dir
  local n="$1" d="$2"
  [ -n "$SUITE_SRC" ] && [ -d "$SUITE_SRC/$n" ] || return 1
  rm -rf "$d"; mkdir -p "$(dirname "$d")"; cp -r "$SUITE_SRC/$n" "$d"
  check_suite "$d" "$n"
}

for SD in $(skilldirs); do
  mkdir -p "$SD"
  for n in $BELT; do
    wanted "$n" || continue
    d="$SD/$(echo "$n" | tr 'A-Z' 'a-z')"; [ "$n" = "Claudeception" ] && d="$SD/claudeception"
    if [ "$MODE" = "doctor" ]; then
      if check_belt "$d"; then row "$n → $SD" OK "-"; else row "$n → $SD" FAIL "fix will re-clone ${REPO[$n]}"; fi
    else
      if ! check_belt "$d"; then install_belt "$n" "$d"; fi
      if check_belt "$d"; then row "$n → $SD" OK "cloned/verified"
      else row "$n → $SD" FAIL "clone failed 3x — check network/proxy (GIT_BASE=$GIT_BASE); org proxies may need github.com allowed"; fi
    fi
  done
  for n in $SUITE; do
    wanted "$n" || continue
    d="$SD/$n"
    if [ "$MODE" = "doctor" ]; then
      if check_suite "$d" "$n"; then row "$n → $SD" OK "-"; else row "$n → $SD" FAIL "provide --suite-src to (re)install"; fi
    else
      if ! check_suite "$d" "$n"; then install_suite "$n" "$d" || true; fi
      if check_suite "$d" "$n"; then row "$n → $SD" OK "copied/verified"
      else row "$n → $SD" FAIL "missing — pass --suite-src DIR containing $n/"; fi
    fi
  done
done

# Upstream installers: report, never auto-run without flag
if command -v npx >/dev/null 2>&1; then NPX=OK; else NPX=FAIL; fi
if [ "$NPX" = FAIL ]; then row "node/npx" FAIL "install Node 20+ for GSD/claude-mem"; else row "node/npx" OK "-"; fi
GSD_HINT="npx @opengsd/gsd-core@latest   # official installer, prompts for runtime"
if [ -d "$HOME_DIR/.claude/commands/gsd" ] || [ -d "$HOME_DIR/.codex/commands/gsd" ]; then
  row "GSD Core" OK "-"
else
  if [ $WITH_GSD -eq 1 ] && [ $NPX = OK ]; then npx @opengsd/gsd-core@latest || true; fi
  if [ -d "$HOME_DIR/.claude/commands/gsd" ]; then row "GSD Core" OK "installed"; else row "GSD Core" WARN "$GSD_HINT"; fi
fi
if [ -d "$HOME_DIR/.claude-mem" ]; then row "claude-mem" OK "-"; else
  [ $WITH_MEM -eq 1 ] && [ $NPX = OK ] && npx claude-mem install || true
  if [ -d "$HOME_DIR/.claude-mem" ]; then row "claude-mem" OK "installed"; else row "claude-mem" WARN "npx claude-mem install   # Tier 1 memory (Claude Code)"; fi
fi
if [ -d "$HOME_DIR/ASI-Evolve" ]; then row "ASI-Evolve (pipeline)" OK "-"
else row "ASI-Evolve (pipeline)" WARN "git clone https://github.com/GAIR-NLP/ASI-Evolve && pip install -r requirements.txt  # Apache-2.0; heavy evolution for scored problems; needs OpenAI-compatible endpoint"; fi
if [ -d "$HOME_DIR/.claude/plugins" ] && ls "$HOME_DIR/.claude/plugins" 2>/dev/null | grep -qi "superpowers"; then
  row "superpowers (alt spine)" OK "-"
else
  row "superpowers (alt spine)" WARN "/plugin install superpowers@claude-plugins-official  # full methodology - pick ONE spine (GSD or superpowers); telemetry opt-out: SUPERPOWERS_DISABLE_TELEMETRY=1"
fi
if [ -d "$HOME_DIR/.claude/plugins" ] && ls "$HOME_DIR/.claude/plugins" 2>/dev/null | grep -qi "academic-research"; then
  row "ARS (research)" OK "-"
else
  row "ARS (research)" WARN "in Claude Code: /plugin marketplace add Imbad0202/academic-research-skills then /plugin install academic-research-skills (CC-BY-NC 4.0 - noncommercial)"
fi
TM="$HOME_DIR/.claude/skills/taskmaster/install.sh"
if [ -f "$HOME_DIR/.claude/hooks/taskmaster-check-completion.sh" ]; then row "taskmaster hooks" OK "-"
elif [ $WITH_TM -eq 1 ] && [ -f "$TM" ]; then bash "$TM" || true; row "taskmaster hooks" WARN "ran installer — restart agent"
else row "taskmaster hooks" WARN "bash $TM   # registers Stop hook (needs jq)"; fi

# Vault + project scaffolding
if [ -n "$VAULT" ]; then
  TPL="$(dirname "$0")/../../theory-keeper/assets/theory-template.md"
  if [ -f "$VAULT/vault-manifest.json" ] || [ -f "$VAULT/brain/North Star.md" ]; then
    mkdir -p "$VAULT/Hydra Wisdom" "$VAULT/reference"
    if [ -f "$TPL" ] && [ ! -f "$VAULT/reference/theory-template.md" ]; then cp "$TPL" "$VAULT/reference/theory-template.md"; fi
    row "obsidian-mind vault" OK "Hydra Wisdom/ added inside it; theory template -> reference/"
  else
    mkdir -p "$VAULT/Hydra Wisdom" "$VAULT/Theory"
    if [ -f "$TPL" ] && [ ! -f "$VAULT/Theory/theory-template.md" ]; then cp "$TPL" "$VAULT/Theory/theory-template.md"; fi
    row "vault: $VAULT" OK "Hydra Wisdom/ + Theory/ ready (bare vault)"
    row "obsidian-mind" WARN "recommended vault template: npm i -g shardmind && shardmind install github:breferrari/obsidian-mind (interactive; or git clone it)"
  fi
  if command -v qmd >/dev/null 2>&1; then row "qmd semantic search" OK "-"
  else row "qmd semantic search" WARN "npm i -g @tobilu/qmd  # optional; first embed downloads ~328MB model"; fi
fi
if [ -n "$PROJECT" ]; then
  mkdir -p "$PROJECT/.hydra" "$PROJECT/.baton"
  touch "$PROJECT/.hydra/wisdom.jsonl"
  grep -qs '^\.baton/' "$PROJECT/.gitignore" 2>/dev/null || echo ".baton/" >> "$PROJECT/.gitignore"
  row "project: $PROJECT" OK ".hydra store + .baton/ (git-ignored)"
fi

printf '%-24s | %-7s | %s\n' "component" "status" "action"
printf '%s\n' "-------------------------------------------------------------------"
printf "$ROWS"
[ -n "$FAILED" ] && { echo; echo "FAILED:$FAILED  → run: setup.sh fix"; exit 1; }
exit 0
