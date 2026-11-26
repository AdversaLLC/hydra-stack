---
name: "windows-registry-analysis"
description: "Analyzes and extracts data from Windows Registry hive files (NTUSER.DAT, SYSTEM, SOFTWARE, SAM, SECURITY, USRCLASS.DAT, amcache) using RegRipper (rip.pl, plugin-based key interpretation and reporting) and reglookup (raw key/value/type enumeration and CSV export, including reglookup-recover for deleted-cell carving). Triggers on \"regripper\", \"reglookup\", \"parse this registry hive\", \"pull run keys / USB history / user activity from the registry\", \"extract deleted registry data\", \"what plugins should I run on this hive\", or requests to interpret specific registry artifacts (autoruns, USB devices, user assist, shellbags, recently opened files, etc). This skill covers registry hive analysis in isolation — registry-derived events folded into a full multi-source super timeline are covered by plaso-log2timeline instead, and cross-referencing registry findings against event logs or filesystem timelines belongs to the planned forensic-timeline skill, not here."
---

---
name: windows-registry-analysis
description: Analyzes and extracts data from Windows Registry hive files (NTUSER.DAT, SYSTEM, SOFTWARE, SAM, SECURITY, USRCLASS.DAT, amcache) using RegRipper (rip.pl, plugin-based key interpretation and reporting) and reglookup (raw key/value/type enumeration and CSV export, including reglookup-recover for deleted-cell carving). Triggers on "regripper", "reglookup", "parse this registry hive", "pull run keys / USB history / user activity from the registry", "extract deleted registry data", "what plugins should I run on this hive", or requests to interpret specific registry artifacts (autoruns, USB devices, user assist, shellbags, recently opened files, etc). This skill covers registry hive analysis in isolation — registry-derived events folded into a full multi-source super timeline are covered by plaso-log2timeline instead, and cross-referencing registry findings against event logs or filesystem timelines belongs to the planned forensic-timeline skill, not here.
---

# Windows Registry Analysis — RegRipper and reglookup

This skill covers two complementary command-line tools for analyzing Windows Registry hive files extracted from an image:

- **RegRipper** (`rip.pl`, Perl, plugin-based): applies purpose-built plugins to a hive to interpret specific known artifacts (run keys, USB device history, UserAssist, shellbags, recently-opened-file lists, network history, etc.) and produce human-readable reports.
- **reglookup**: a lower-level reader that enumerates raw keys/values/types from a hive as CSV, with filtering by path prefix or data type. Its companion `reglookup-recover` scours a hive for deleted/orphaned cell structures the normal registry tree no longer references.

Use RegRipper when you know (or want plugins to help identify) specific known artifact types to interpret. Use reglookup when you need raw, complete enumeration of a hive's contents, need to script against the data, or need to hunt for deleted registry data.

## Relationship to other skills in this library

- **plaso-log2timeline**: Plaso has its own registry parsers that pull registry-derived events into a full multi-source super timeline. Use this skill for a focused, in-depth registry pass (specific plugins, raw enumeration, deleted-data recovery); use Plaso when registry timestamps need correlating against filesystem, event log, and other artifact types in one sorted timeline.
- **chainsaw / evtx-dump**: separate artifact domain (Windows Event Logs), not registry.
- **forensic-timeline (planned)**: correlating registry findings against event log or filesystem timeline evidence is out of scope here.

## When to use this skill

- "Run RegRipper against this SYSTEM/SOFTWARE/NTUSER.DAT hive"
- "What USB devices were connected, per the registry?"
- "Pull autorun/run-key entries from this hive"
- "Enumerate every key/value in this hive as CSV"
- "Try to recover deleted registry keys from this hive"

## When NOT to use this skill

- Need registry data merged into a cross-artifact timeline → plaso-log2timeline
- Need Windows Event Log analysis → chainsaw / evtx-dump
- Need macOS Unified Logs → unified-log-reader

## Prerequisites and scope

- Both tools operate on **exported/copied registry hive files** (e.g., `SYSTEM`, `SOFTWARE`, `SAM`, `SECURITY`, `NTUSER.DAT`, `USRCLASS.DAT`, `Amcache.hve`) pulled from a mounted read-only image or forensic export — never a live/original evidence device or a live/mounted-in-place Windows registry.
- Presence of RegRipper and reglookup on the PALADIN system is based on the user's own system inventory as reported to Claude, not independently verified in this session. Confirm with `rip.pl -h` / `reglookup -h` before relying on specific flags.
- RegRipper plugins are version- and fork-specific (multiple forks/branches exist: e.g., keydet89/RegRipper3.0, and other community forks). Plugin names and available plugin profiles can differ between installs — always list available plugins on the installed copy rather than assuming a plugin exists.

## Core workflow: RegRipper

### 1. Verify the tool and list plugins

```bash
rip.pl -h
rip.pl -l          # list available plugins
```

### 2. Run a single plugin against a hive

```bash
rip.pl -r <hive_file> -p <plugin_name>
```

Example:

```bash
rip.pl -r /evidence/SYSTEM -p compname
```

### 3. Run all plugins applicable to a hive type

```bash
rip.pl -r <hive_file> -a
```

The `-a` (auto) switch runs all plugins RegRipper considers applicable to the detected hive type. A `-aT` variant runs all hive-specific TLN (timeline) plugins if present in the installed version — confirm with `-h` on the installed copy.

### 4. Common flags (verify exact set with `rip.pl -h` on the installed version — flag sets differ slightly between forks)

| Purpose | Flag (verify) |
|---|---|
| Registry hive file | `-r <file>` |
| Plugin to run | `-p <plugin>` |
| Run all applicable plugins | `-a` |
| Run all TLN plugins | `-aT` |
| CSV-style output | `-c` |
| List plugins | `-l` |
| Guess hive type | `-g` |
| User-hive-specific handling | `-u` |
| System-hive-specific handling | `-s` |
| Help | `-h` |

Output goes to STDOUT by default; redirect to a file (`rip.pl -r SYSTEM -a > system_report.txt`) to preserve it.

## Core workflow: reglookup

### 1. Verify the tool

```bash
reglookup -h
```

### 2. Basic enumeration (CSV to stdout)

```bash
reglookup <hive_file>
```

### 3. Filter to a specific key path prefix

```bash
reglookup -p '\Software\Microsoft\Windows\CurrentVersion\Run' <hive_file>
```

### 4. Filter by data type

```bash
reglookup -t SZ <hive_file>
```

Accepted type filters (per current documentation): `NONE`, `SZ`, `EXPAND_SZ`, `BINARY`, `DWORD`, `DWORD_BE`, `LINK`, `MULTI_SZ`, `RSRC_LIST`, `RSRC_DESC`, `RSRC_REQ_LIST`, `QWORD`, `KEY`.

### 5. Recover deleted/orphaned registry data

```bash
reglookup-recover <hive_file>
```

This scours the hive for deleted cell structures not referenced by the live registry tree and reports what it finds in CSV-like output. Treat recovered entries as forensically weaker evidence than live-tree entries — deleted-cell recovery can include partially overwritten or ambiguous structures. Verify current flag options (e.g., verbose, header row, raw cell display) with `reglookup-recover -h` on the installed version rather than assuming a fixed flag set.

## Typical examiner workflow

1. Export/copy the relevant hive(s) from the mounted read-only image (never operate on a live/original device or a mounted live OS registry).
2. Confirm tool availability and options: `rip.pl -h`, `rip.pl -l`, `reglookup -h`.
3. For known artifact questions (autoruns, USB history, UserAssist, shellbags, recent files), run the specific applicable RegRipper plugin(s), or `-a` for a broad first pass on that hive.
4. For raw/complete enumeration or scripting, run `reglookup` with appropriate path/type filters.
5. If deleted registry data is relevant to the case question, run `reglookup-recover` and clearly flag recovered entries as such in any findings.
6. Cross-check RegRipper plugin interpretations against reglookup's raw output when precision matters (plugins interpret/format data; raw enumeration shows what's actually stored).
7. Hand off findings to forensic-reporting, or to plaso-log2timeline's workflow if the registry timestamps need to be correlated with other artifact types in a timeline.

## Troubleshooting

| Symptom | Likely cause / next step |
|---|---|
| `rip.pl: command not found` / `reglookup: command not found` | Not installed or not on PATH — verify with the user |
| RegRipper plugin errors or produces no output | Wrong hive type for that plugin (e.g., running a SYSTEM plugin against NTUSER.DAT) — confirm hive/plugin match, or use `-g`/`-a` to let RegRipper apply only applicable plugins |
| Plugin doesn't exist on this install | Plugin sets differ between RegRipper forks/versions — check `rip.pl -l` on the installed copy rather than assuming a plugin from documentation exists here |
| reglookup errors on a hive | Hive may be corrupted, partially acquired, or a non-standard/dirty hive (unflushed transaction log not merged) — note this rather than treating a partial read as complete |
| reglookup-recover produces ambiguous/garbled entries | Expected for genuinely deleted/overwritten cell data — flag recovered results as lower-confidence rather than presenting them as confirmed live values |
| Timestamps from registry keys seem inconsistent with other evidence | Registry LastWrite timestamps reflect key modification time, not necessarily the timestamp of the interpreted artifact event (e.g., UserAssist run count entries encode their own timestamp separately from key LastWrite) — don't conflate the two without checking what the specific plugin/value actually represents |

## What this skill must never do automatically

- Never run RegRipper or reglookup directly against a live/original evidence device or a live/mounted-in-place Windows installation's registry — only against exported/copied hive files.
- Never invent plugin names, flags, or type-filter values not confirmed via `-h`/`-l`/current documentation for the installed version — flag uncertainty and tell the user to verify.
- Never present a registry key's existence or LastWrite time as proof a specific person performed the associated action — it indicates the key/value was written or the artifact exists, not who wrote it or why, absent further corroboration.
- Never treat `reglookup-recover` output with the same confidence as live-tree data — always label recovered/deleted-cell findings as such.
- Never modify or write back to the source hive file; all analysis here is read-only, and any output/reports go to a separate working directory.

