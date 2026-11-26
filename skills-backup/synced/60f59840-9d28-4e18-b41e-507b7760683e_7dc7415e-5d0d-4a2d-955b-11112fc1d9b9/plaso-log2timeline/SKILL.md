---
name: "plaso-log2timeline"
description: "Builds a multi-source \"super timeline\" from a disk image or exported artifacts using Plaso (log2timeline.py to parse, psort.py/psteal.py to filter and output). Triggers on \"super timeline\", \"plaso\", \"log2timeline\", \"psort\", \"psteal\", \"correlate all the artifacts by time\", \"build a timeline from this image\", or combining filesystem, registry, browser, event log, and application timestamps into one sorted view. Broader than tsk-mactime, which only produces MACB timelines from filesystem metadata (no registry/logs/apps) — use tsk-mactime for a fast filesystem-only pass, this skill when multiple artifact types must be fused. Only covers running the Plaso tools; cross-tool correlation across plaso/chainsaw/registry-analysis outputs belongs to the planned forensic-timeline skill. Not for EVTX-only triage (chainsaw/evtx-dump) or registry-only extraction (windows-registry-analysis)."
---

---
name: plaso-log2timeline
description: Builds a multi-source "super timeline" from a disk image or exported artifacts using Plaso (log2timeline.py to parse, psort.py/psteal.py to filter and output). Triggers on "super timeline", "plaso", "log2timeline", "psort", "psteal", "correlate all the artifacts by time", "build a timeline from this image", or combining filesystem, registry, browser, event log, and application timestamps into one sorted view. Broader than tsk-mactime, which only produces MACB timelines from filesystem metadata (no registry/logs/apps) — use tsk-mactime for a fast filesystem-only pass, this skill when multiple artifact types must be fused. Only covers running the Plaso tools; cross-tool correlation across plaso/chainsaw/registry-analysis outputs belongs to the planned forensic-timeline skill. Not for EVTX-only triage (chainsaw/evtx-dump) or registry-only extraction (windows-registry-analysis).
---

# Plaso / log2timeline — Super Timeline Generation

Plaso ("Plaso Langar Að Safna Öllu" — Icelandic for "Plaso wants to gather everything") is a Python framework that parses dozens of artifact types — filesystem metadata, Windows Registry, Windows Event Logs, browser history, email, application logs, and more — and merges every timestamped event into one unified, sortable timeline. It ships as two primary CLI tools: `log2timeline.py` (parses sources into a Plaso storage file) and `psort.py` (filters, sorts, and exports events from that storage file to a readable format). A combined tool, `psteal.py`, runs both stages in one invocation.

This is the flagship, broadest timeline tool in this skill library. It is not a replacement for targeted single-artifact tools — it is what you reach for when you need everything correlated by time in one place.

## Relationship to other skills in this library

- **tsk-mactime (Sleuth Kit)**: narrower and faster. Produces MACB (Modified/Accessed/Changed/Born) timelines from filesystem metadata only (via `fls`/`mactime`). No registry, no event logs, no browser artifacts, no application parsing. Use it for a quick filesystem-only timeline or when Plaso is overkill for the question being asked.
- **chainsaw / evtx-dump**: focused on Windows Event Logs specifically — faster and more targeted for EVTX triage/hunting than running the full Plaso EVTX parsers.
- **windows-registry-analysis (regripper/reglookup)**: extracts and interprets specific registry hive contents in depth; Plaso's registry parsers pull registry-derived events into the timeline but do not replace a full RegRipper pass.
- **unified-log-reader**: macOS-specific `.tracev3` parsing; Plaso has some macOS support but this dedicated tool is deeper for that artifact type.
- **forensic-timeline (planned)**: this skill's job ends at producing parsed, sorted timeline output. Correlating that output against chainsaw hits, registry findings, and other tool outputs — building the cross-tool narrative — is the job of the (not yet built) forensic-timeline skill. Do not attempt that broader correlation here; flag to the user that it belongs to that future skill if asked for it.

## When to use this skill

- "Build a super timeline from this image"
- "Run log2timeline / plaso on this evidence"
- "I need every artifact type correlated by time, not just filesystem MACB"
- Investigating activity that spans multiple artifact types (e.g., a file was downloaded, registry shows execution, event log shows logon) where cross-referencing by timestamp matters

## When NOT to use this skill

- Filesystem-only MACB timeline needed quickly → tsk-mactime
- Only Windows Event Logs, want fast Sigma-rule hunting → chainsaw
- Only need to read/convert EVTX to JSON/XML → evtx-dump
- Only need registry key extraction/interpretation → windows-registry-analysis
- Only macOS Unified Logs → unified-log-reader
- Need narrative correlation across already-produced tool outputs → forensic-timeline (not yet built; tell the user)

## Prerequisites and scope

- Plaso operates on a **disk image, mounted read-only forensic copy, or exported artifact set** — never a live/original evidence device directly.
- Presence of Plaso (`log2timeline.py`, `psort.py`, `psteal.py`) on the PALADIN system is based on the user's own system inventory as reported to Claude, not independently verified by Claude in this session. Confirm with `log2timeline.py --version` before relying on it.
- Processing a large image can take hours and consume significant disk space and RAM (the storage file can be gigabytes). Warn the user before kicking off a full-image run.

## Core workflow

### 1. Verify the tool and inspect options

```bash
log2timeline.py --version
log2timeline.py --info          # lists available parsers, parser presets, hashers, output modules
```

Review `--info` output rather than assuming a parser exists — parser names and presets change between Plaso releases.

### 2. Parse the source into a Plaso storage file

```bash
log2timeline.py [OPTIONS] OUTPUT.plaso SOURCE
```

Where `SOURCE` is a raw/E01/mounted image path or a directory of exported artifacts, and `OUTPUT.plaso` is the storage file that will be created.

Commonly used options (verify current names/behavior with `log2timeline.py --help` on the installed version before use, as flags have changed across Plaso releases):

| Purpose | Flag (verify against `--help`) |
|---|---|
| Restrict to a parser preset or list | `--parsers PRESET` or `--parsers "parser1,parser2"` |
| Single-process mode (debugging) | `--single-process` |
| Set number of worker processes | `--workers N` |
| VSS (Volume Shadow Copy) processing | `--vss-stores ALL` (or specific store numbers) |
| Hash extracted files | `--hashers "md5,sha256"` |
| Log to a file | `--logfile FILE` |
| Status/progress view | `--status_view` (window/linear, varies by version) |

If unsure of an exact flag spelling or default, run `log2timeline.py --help` and quote the actual output back to the user rather than guessing.

### 3. Inspect the storage file (optional but recommended)

```bash
pinfo.py OUTPUT.plaso
```

`pinfo.py` reports what was processed, parser counts, warnings/errors, and processing metadata — useful for sanity-checking a long-running parse before committing to the full sort/export step.

### 4. Filter, sort, and export with psort.py

```bash
psort.py -o OUTPUT_FORMAT -w OUTPUT_FILE OUTPUT.plaso [FILTER]
```

Verified output modules (per current Plaso documentation):

| Output module | Description |
|---|---|
| `dynamic` | Selectable-field delimited output (default-ish, flexible column set) |
| `l2tcsv` | Legacy log2timeline CSV, 17 fixed fields |
| `l2ttln` | Extended TLN, 7 fields, pipe-delimited |
| `tln` | TLN, 5 fields, pipe-delimited |
| `json` | Full JSON |
| `json_line` | JSON Lines (one event per line — good for downstream tooling) |
| `xlsx` | Excel spreadsheet |
| `kml` | Geographic events as KML |
| `rawpy` | Native/raw Python object dump (debugging) |

Example:

```bash
psort.py -o dynamic -w case_timeline.csv case_output.plaso
```

Time-bounded and artifact-filtered runs use a filter expression or a date filter; the exact filter syntax (Plaso's own filter language) varies by version — confirm current syntax with `psort.py --help` and the "Filtering Events" section of current Plaso docs rather than assuming legacy syntax still applies.

### 5. One-step alternative: psteal.py

```bash
psteal.py --source SOURCE -o OUTPUT_FORMAT -w OUTPUT_FILE
```

`psteal.py` runs extraction and output in a single pass — convenient for smaller sources or a first-pass look, but for large images running the two stages separately (so `pinfo.py` can be checked between them) is generally the safer workflow.

## Typical examiner workflow

1. Mount/attach the read-only forensic image or export the target artifact set.
2. `log2timeline.py --version` and `--info` to confirm tool state and available parsers on this system.
3. Run `log2timeline.py` against the source, using a parser preset appropriate to the OS (e.g., a Windows preset vs. a generic preset) if the installed version supports presets — check `--info` for the current preset names.
4. Run `pinfo.py` on the resulting storage file to confirm parsers actually ran and check for warnings/errors before investing time in export.
5. Run `psort.py` to produce a sorted, filtered export in the format needed (CSV/dynamic for spreadsheet review, JSON/JSONL for scripted analysis).
6. Review the exported timeline for the artifact types and time window relevant to the case question — do not treat the full unfiltered export as "the findings."
7. Hand off specific findings (with source artifact and parser attribution preserved) to forensic-reporting for writeup, or to the future forensic-timeline skill for cross-tool correlation.

## Troubleshooting

| Symptom | Likely cause / next step |
|---|---|
| `log2timeline.py: command not found` | Plaso not installed or not on PATH on this system — verify with the user; do not assume it's present just because this skill exists |
| Parsing extremely slow / appears hung | Large image, single-process mode, or VSS processing enabled — check `--status_view`/progress output; large images can legitimately take hours |
| `pinfo.py` shows many parser errors/warnings | Source may be corrupted, partially acquired, or an unsupported filesystem/artifact variant — review the specific warnings rather than discarding the whole run |
| Storage file is huge / disk fills up | Expected for full-image super timelines; ensure adequate free space before starting, consider `--parsers` restriction to reduce scope |
| Output missing an expected artifact type | Confirm the relevant parser is enabled and supported in this Plaso version via `--info`; not all artifact types have a parser in every release |
| Timestamps look wrong / offset | Check source and display timezone handling — Plaso normalizes to UTC internally; confirm `psort.py` timezone options for display rather than assuming local time |

## What this skill must never do automatically

- Never run `log2timeline.py` directly against a live/original evidence device — only against images, forensic copies, or already-exported artifacts.
- Never invent or guess at flag names, filter syntax, or parser preset names not confirmed via `--help`/`--info`/current documentation — state uncertainty and tell the user to verify against the installed version's help output.
- Never silently discard parser warnings/errors from `pinfo.py` — surface them to the user.
- Never present a raw timeline export as a finished finding — a timestamped event indicates that an artifact/event exists or occurred, not that a specific person performed the associated action. Frame conclusions accordingly (e.g., "this key was modified at this time" not "the user changed this at this time") unless corroborating evidence (login session, process ownership, etc.) supports attribution, and even then attribute with appropriate confidence qualifiers.
- Never delete, overwrite, or modify the source image/artifacts — all Plaso operations here are read-only against the source; only the `.plaso` storage file and exports are written, and those should go to a working/output directory, never back onto evidence.
- Never claim a parser or output format exists in the installed Plaso version without checking `--info`/`--help` first — Plaso's parser and output module list changes across releases.

