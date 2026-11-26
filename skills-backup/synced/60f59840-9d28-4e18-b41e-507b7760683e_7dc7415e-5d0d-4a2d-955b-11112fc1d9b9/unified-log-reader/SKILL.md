---
name: "unified-log-reader"
description: "Parses macOS Unified Logging .tracev3 binary files (from the diagnostics/ and uuidtext/ folders) into readable log entries using UnifiedLogReader (ydkhatri) or equivalent tracev3 parsers. Triggers on \"unified log\", \"tracev3\", \"parse macOS logs\", \"UnifiedLogReader\", \"macOS unified logging\", \"what does the log utility output show from this image\", or requests to extract/read Apple's unified log data from a mounted macOS image or exported diagnostics/uuidtext export. This is the macOS-specific counterpart to the Windows-focused tools in this library (chainsaw/evtx-dump for EVTX, windows-registry-analysis for hives) — there is no macOS coverage in plaso-log2timeline as deep as this dedicated tool for tracev3 specifically, though Plaso may pull in other macOS artifacts. Cross-referencing unified log findings against other artifact timelines belongs to the planned forensic-timeline skill, not here."
---

---
name: unified-log-reader
description: Parses macOS Unified Logging .tracev3 binary files (from the diagnostics/ and uuidtext/ folders) into readable log entries using UnifiedLogReader (ydkhatri) or equivalent tracev3 parsers. Triggers on "unified log", "tracev3", "parse macOS logs", "UnifiedLogReader", "macOS unified logging", "what does the log utility output show from this image", or requests to extract/read Apple's unified log data from a mounted macOS image or exported diagnostics/uuidtext export. This is the macOS-specific counterpart to the Windows-focused tools in this library (chainsaw/evtx-dump for EVTX, windows-registry-analysis for hives) — there is no macOS coverage in plaso-log2timeline as deep as this dedicated tool for tracev3 specifically, though Plaso may pull in other macOS artifacts. Cross-referencing unified log findings against other artifact timelines belongs to the planned forensic-timeline skill, not here.
---

# UnifiedLogReader — macOS Unified Logging (.tracev3) Parsing

macOS (10.12+) replaced traditional syslog with **Unified Logging**, which stores log data in binary `.tracev3` files under `/private/var/db/diagnostics/` (plus supporting `Persist`, `Special`, `Signpost`, `HighVolume` subfolders depending on OS version) with symbol/format-string data referenced from `/private/var/db/uuidtext/` and timestamp-sync data from a `timesync` folder. These binary files are not human-readable without a parser — Apple's own `log` command reads them live on a running macOS system, but on an image or export you need a dedicated offline parser.

**UnifiedLogReader** (ydkhatri) is a Python-based parser for these files that runs on any platform with Python, producing readable log output in multiple formats. Other tracev3 parsers exist (e.g., Mandiant's Rust-based `macos-UnifiedLogs` project); if the PALADIN system has a different specific tool installed under this name, confirm its actual CLI syntax with `--help` before following the command examples below, since exact flags can differ between implementations.

## Relationship to other skills in this library

- **chainsaw / evtx-dump**: the Windows Event Log equivalents. Unified Logging is macOS's closest analog to the Windows Event Log, and this tool is the corresponding parser.
- **windows-registry-analysis**: Windows-only, not applicable to macOS unified logs.
- **plaso-log2timeline**: Plaso has some macOS artifact support, but deep, dedicated `.tracev3` parsing is better served by this specialized tool; treat Plaso as complementary for other macOS artifact types (filesystem, browser, etc.), not as a substitute for this tool's log depth.
- **forensic-timeline (planned)**: correlating unified log findings against other tools' timelines is out of scope here.

## When to use this skill

- "Parse the unified logs from this Mac image"
- "What's in this diagnostics/tracev3 export?"
- "Convert these .tracev3 files to something readable"
- Investigating macOS system/application activity where unified logging is the relevant artifact

## When NOT to use this skill

- Windows Event Logs → chainsaw / evtx-dump
- Windows Registry → windows-registry-analysis
- Cross-artifact-type super timeline → plaso-log2timeline

## Prerequisites and scope

- Operates on **exported/copied unified logging data** pulled from a mounted read-only macOS image — specifically the `diagnostics` folder (containing `.tracev3` files) and the `uuidtext` folder (containing symbol/format-string data), plus timesync data — never a live/original evidence device.
- Presence of UnifiedLogReader (or an equivalent tracev3 parser) on the PALADIN system is based on the user's own system inventory as reported to Claude, not independently verified in this session. Confirm with `python3 UnifiedLogReader.py -h` (or the installed tool's own help) before relying on specific flags.
- Requires all three input pieces (tracev3, uuidtext, timesync) to render meaningful output — records reference external UUID files for format strings, and missing pieces will show unresolved/garbled entries rather than errors.

## Core workflow

### 1. Verify the tool

```bash
python3 UnifiedLogReader.py -h
```

(Exact invocation depends on how it's installed/packaged on this system — it may be a standalone script, a `pip`-installed console entry point, or bundled differently. Confirm the actual command with the user/system before running.)

### 2. Gather required inputs from the mounted image

You need, from the mounted read-only macOS image (paths reflect standard macOS locations; confirm against the actual mount):

- `private/var/db/diagnostics/` — contains the `.tracev3` files
- `private/var/db/uuidtext/` — contains UUID-keyed format-string data
- The timesync folder (location varies by version, typically under `diagnostics/timesync/`)

### 3. Run the parser

Documented invocation pattern (verify current positional argument order and flags with `-h` on the installed version before running, since this has been reported to vary by release):

```bash
python3 UnifiedLogReader.py [-h] [-f OUTPUT_FORMAT] [-l LOG_LEVEL] uuidtext_path timesync_path tracev3_path output_path
```

Example:

```bash
python3 UnifiedLogReader.py -f sqlite /evidence/uuidtext /evidence/diagnostics/timesync /evidence/diagnostics /evidence/output/
```

### 4. Output formats (per project documentation — verify against installed version)

| Format | Description |
|---|---|
| Default (`LOG_DEFAULT`) | Only the fields the native `log` utility would show |
| `TSV_ALL` | All available fields, tab-separated |
| `SQLITE` | All available fields written to a SQLite database |

### 5. Filtering

If the installed version supports filtering by process, subsystem, predicate, or time range, confirm the exact flag names/syntax with `-h` rather than assuming — this functionality and its syntax have varied across parser versions and forks.

## Typical examiner workflow

1. Mount the macOS image read-only and locate/export the `diagnostics`, `uuidtext`, and timesync data.
2. Confirm the installed parser and its exact invocation syntax with `-h`.
3. Run the parser against the full set of exported inputs, choosing an output format appropriate to the next step (SQLite for querying, TSV for spreadsheet review).
4. Review output for the process/subsystem/time window relevant to the case question — unified logs are extremely high-volume; do not attempt to review the full unfiltered output as "the findings."
5. Cross-check specific log entries' timestamps against other artifacts (filesystem, other macOS logs) manually, or via plaso-log2timeline if broader correlation is needed, keeping in mind the future forensic-timeline skill is the intended home for that correlation work.
6. Hand off relevant findings to forensic-reporting.

## Troubleshooting

| Symptom | Likely cause / next step |
|---|---|
| Script/tool not found | Not installed, not on PATH, or dependencies (e.g., `lz4`, `biplist`) missing — verify with the user rather than assuming a fix |
| Entries show unresolved format strings / garbled text | Missing or mismatched `uuidtext` data for that log's UUID — confirm the full `uuidtext` folder was exported, not a partial copy |
| Timestamps look wrong or missing | timesync data missing or mismatched with the tracev3 files being parsed — confirm all three inputs came from the same system/export and are complete |
| Extremely large output / tool very slow | Unified logs are high-volume by design; consider filtering (if supported) or narrowing which `.tracev3` files are processed rather than parsing the entire diagnostics folder unfiltered |
| Output format doesn't match what was expected | Confirm the `-f`/format flag and accepted values with `-h` on the installed version — format option names have varied across releases |

## What this skill must never do automatically

- Never run the parser directly against a live/original evidence device — only against exported/copied diagnostics, uuidtext, and timesync data from a read-only mounted image.
- Never invent flag names, positional argument order, or output format names not confirmed via `-h`/current project documentation for the installed tool — flag uncertainty and tell the user to verify.
- Never present a unified log entry as proof a specific person performed an action — it indicates a process/subsystem logged an event at that time, not who initiated it, absent further corroboration.
- Never modify the source diagnostics/uuidtext/timesync files; write all parsed output to a separate working/output location.
- Never claim complete coverage of the logs if only a filtered subset or partial export was actually processed — state explicitly what was and wasn't reviewed.

