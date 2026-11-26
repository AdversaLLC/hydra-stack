---
name: "chainsaw"
description: "Rapid triage and hunting through Windows Forensic Artefacts — primarily EVTX Event Logs, also registry hives, MFT, and other supported artefacts — using WithSecure Labs' Chainsaw, including Sigma rule execution via --sigma/--mapping. Triggers on \"chainsaw\", \"hunt these event logs\", \"run sigma rules against this\", \"triage these EVTX files fast\", \"search event logs for X\", or flagging suspicious Windows event log activity across many files fast. Narrower and faster than plaso-log2timeline (full multi-source super timeline) — use chainsaw for fast triage/hunting over Windows Event Logs specifically, not cross-artifact correlation. Complements evtx-dump (raw JSON/XML conversion, no rule engine) — use evtx-dump for complete raw record output, chainsaw for rule-driven or keyword hits across many logs. Correlating chainsaw hits against other artifact timelines belongs to the planned forensic-timeline skill, not here."
---

---
name: chainsaw
description: Rapid triage and hunting through Windows Forensic Artefacts — primarily EVTX Event Logs, also registry hives, MFT, and other supported artefacts — using WithSecure Labs' Chainsaw, including Sigma rule execution via --sigma/--mapping. Triggers on "chainsaw", "hunt these event logs", "run sigma rules against this", "triage these EVTX files fast", "search event logs for X", or flagging suspicious Windows event log activity across many files fast. Narrower and faster than plaso-log2timeline (full multi-source super timeline) — use chainsaw for fast triage/hunting over Windows Event Logs specifically, not cross-artifact correlation. Complements evtx-dump (raw JSON/XML conversion, no rule engine) — use evtx-dump for complete raw record output, chainsaw for rule-driven or keyword hits across many logs. Correlating chainsaw hits against other artifact timelines belongs to the planned forensic-timeline skill, not here.
---

# Chainsaw — Windows Event Log Hunting and Triage

Chainsaw (WithSecure Labs) is a Rust-based command-line tool for rapidly searching and hunting through Windows forensic artefacts — most commonly EVTX Windows Event Logs, but it also has support for other artefact types depending on version (check `chainsaw --help` for what the installed build supports). Its main strengths are speed over large volumes of logs and built-in Sigma rule execution, letting an examiner run community or custom detection rules against exported event logs without standing up a full SIEM.

Chainsaw does not build a unified timeline across artifact types — it is a fast triage/hunt layer over event log (and related) data. Treat its output as a starting point for investigation, not a final verdict.

## Relationship to other skills in this library

- **plaso-log2timeline**: the broad, multi-source super-timeline tool. Use Chainsaw first for fast triage/hunting over event logs; use Plaso when the question requires correlating event log activity against filesystem, registry, browser, and other artifact timestamps in one sorted view.
- **evtx-dump**: a raw EVTX-to-JSON/XML converter with no rule engine. Use evtx-dump when you need the complete, unfiltered contents of specific EVTX files (e.g., to inspect a record's full XML); use Chainsaw when you need to search/hunt across many logs quickly, especially with Sigma rules.
- **windows-registry-analysis**: separate artifact domain (registry hives) — Chainsaw's registry support (if present in the installed build) is not a substitute for a dedicated RegRipper/reglookup pass.
- **forensic-timeline (planned)**: correlating Chainsaw hunt results against other tools' output over time is out of scope here; that belongs to the future forensic-timeline skill.

## When to use this skill

- "Hunt through these event logs for suspicious activity"
- "Run Sigma rules against this EVTX export"
- "Search these logs for logon events / PowerShell execution / service creation"
- Fast triage of a large set of exported EVTX files before deciding what warrants deeper analysis

## When NOT to use this skill

- Need the complete raw contents of specific EVTX records → evtx-dump
- Need a full cross-artifact-type super timeline → plaso-log2timeline
- Need registry hive analysis → windows-registry-analysis
- Need macOS Unified Logs → unified-log-reader

## Prerequisites and scope

- Chainsaw operates on **exported/copied EVTX files (and other supported artefact exports)**, not a live evidence device.
- Presence of Chainsaw on the PALADIN system is based on the user's own system inventory as reported to Claude, not independently verified in this session. Confirm with `chainsaw --version` / `chainsaw --help` before relying on specific flags.
- Sigma rule hunting requires a local copy of Sigma rules and (depending on version) a mapping file that tells Chainsaw how to match Sigma's generic field names to specific EVTX log/event-ID structures. Verify the mapping file path and format against the installed version's documentation/`--help`, since mapping file formats have changed across Chainsaw releases.

## Core workflow

### 1. Verify the tool

```bash
chainsaw --version
chainsaw --help
chainsaw hunt --help
```

Confirm subcommands available in the installed build (commonly `hunt`, `search`, and others depending on version) before assuming a specific subcommand exists.

### 2. Basic hunt (built-in detection logic, no Sigma)

```bash
chainsaw hunt <path-to-evtx-directory-or-file>
```

This runs Chainsaw's bundled/built-in detection rules (mapping-driven) against the target logs.

### 3. Sigma-rule-driven hunt

```bash
chainsaw hunt <evtx-path> --sigma <sigma-rules-dir> --mapping <mapping-file.yml>
```

Example pattern (structure confirmed against WithSecure documentation; verify exact rule/mapping paths for your installed Sigma rule set and Chainsaw version):

```bash
chainsaw hunt /evidence/exported-evtx/ -s /opt/sigma/rules/ --mapping /opt/chainsaw/mappings/sigma-event-logs-all.yml
```

### 4. Common flags (verify current spelling/behavior with `chainsaw hunt --help` on the installed version)

| Purpose | Flag (verify) |
|---|---|
| Output as CSV | `--csv` |
| Output as JSON | `--json` |
| Full/untruncated field values | `--full` |
| Time-bound the search, start | `--from` |
| Time-bound the search, end | `--to` |
| Sigma rules directory | `--sigma` / `-s` |
| Field mapping file | `--mapping` |
| Load additional/custom detection rules | check `--rule` / `--rules` equivalent in `--help` |

Do not assume flags not confirmed via `--help` for the specific installed version — Chainsaw's flag set has evolved across major versions (v1 vs v2+).

### 5. Search subcommand (keyword/pattern search rather than rule-based hunting)

If the installed version includes a `search` subcommand for simple keyword/regex search across logs (separate from rule-based `hunt`), confirm its syntax with `chainsaw search --help` rather than assuming it mirrors `hunt`.

## Typical examiner workflow

1. Export/copy the relevant EVTX files from the image (never operate on a live/original device).
2. `chainsaw --version` and `--help` to confirm installed capabilities.
3. Run an initial `chainsaw hunt` with built-in rules for a fast first pass.
4. Run a Sigma-driven hunt with a current, relevant Sigma ruleset and correct mapping file for deeper, rule-based detection.
5. Export hits as CSV or JSON for review and for handoff to reporting.
6. Treat each hit as a lead: pivot into the specific EVTX records (via evtx-dump or a log viewer) to confirm context before drawing conclusions.
7. Document findings for forensic-reporting, being explicit that a rule match indicates a pattern was found in the log data, not a confirmed compromise or a confirmed human action.

## Troubleshooting

| Symptom | Likely cause / next step |
|---|---|
| `chainsaw: command not found` | Not installed or not on PATH — verify with the user before proceeding |
| Sigma hunt produces zero results unexpectedly | Wrong or outdated mapping file for the Sigma ruleset/Chainsaw version; confirm mapping file matches the Chainsaw version's expected schema |
| Errors parsing specific EVTX files | File may be corrupted/truncated (common with improperly acquired or carved logs); try evtx-dump on the same file to see if it parses independently |
| Extremely high hit volume / noisy output | Sigma ruleset too broad for this environment baseline; narrow with `--from`/`--to` time bounds or a curated rule subset rather than accepting the raw volume as findings |
| Output truncated in terminal | Use `--full` (if supported) or export to `--csv`/`--json` and review in a proper viewer instead of the terminal |

## What this skill must never do automatically

- Never run Chainsaw directly against a live/original evidence device — only against exported/copied EVTX and related artefacts.
- Never invent flag names, subcommands, or mapping file schemas not confirmed via `--help`/current WithSecure documentation — flag uncertainty and tell the user to verify against the installed version.
- Never present a Sigma/rule hit as a confirmed incident or confirmed user action — it indicates the described event pattern is present in the log; it does not by itself establish intent, attribution, or compromise. State findings with that qualification.
- Never delete or modify the source EVTX files being hunted; write all output (CSV/JSON) to a separate working/output location.
- Never silently drop parsing errors on individual files — surface which files failed and why so the examiner can decide whether to investigate further (e.g., with evtx-dump).

