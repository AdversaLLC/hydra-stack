---
name: "evtx-dump"
description: "Converts Windows EVTX Event Log files into readable structured output (XML or JSON) using the Rust evtx_dump tool (omerbenamram/evtx). Triggers on \"evtx_dump\", \"convert this EVTX to JSON\", \"dump this event log\", \"show me the raw records in this .evtx file\", \"parse this Windows event log file\", or requests to view/export the complete contents of specific EVTX files. This is a raw format converter with no rule engine or detection logic — for fast rule-driven/Sigma-based hunting across many logs, use the chainsaw skill; for folding event-log-derived events into a larger multi-source timeline, use plaso-log2timeline. Use evtx-dump when the need is complete, faithful, per-record conversion of specific EVTX files (e.g., to inspect one record's full structure, or to feed JSON/JSONL into another tool or script)."
---

---
name: evtx-dump
description: Converts Windows EVTX Event Log files into readable structured output (XML or JSON) using the Rust evtx_dump tool (omerbenamram/evtx). Triggers on "evtx_dump", "convert this EVTX to JSON", "dump this event log", "show me the raw records in this .evtx file", "parse this Windows event log file", or requests to view/export the complete contents of specific EVTX files. This is a raw format converter with no rule engine or detection logic — for fast rule-driven/Sigma-based hunting across many logs, use the chainsaw skill; for folding event-log-derived events into a larger multi-source timeline, use plaso-log2timeline. Use evtx-dump when the need is complete, faithful, per-record conversion of specific EVTX files (e.g., to inspect one record's full structure, or to feed JSON/JSONL into another tool or script).
---

# evtx_dump — EVTX to JSON/XML Conversion

`evtx_dump` is the command-line binary from the `evtx` Rust crate (omerbenamram/evtx). It parses Windows XML Event Log (.evtx) files and converts every record to XML or JSON, without applying any detection rules or filtering logic. Both output formats are built directly from the binary's internal representation (JSON is not produced via an XML-to-JSON conversion step), and it is designed to be fast and memory-safe on large or malformed logs.

This tool answers "what does this EVTX file actually contain, completely and faithfully" — it does not tell you what's suspicious in it. For that, pair it with chainsaw (rule/Sigma-based hunting) or route the JSON output into your own analysis.

## Relationship to other skills in this library

- **chainsaw**: adds Sigma/rule-based hunting and fast multi-file searching on top of EVTX data. Use evtx-dump to inspect specific records or files in full; use chainsaw to search/hunt across a whole log set for known-bad patterns.
- **plaso-log2timeline**: pulls event-log-derived events into a full multi-source super timeline alongside filesystem, registry, and other artifacts. Use evtx-dump for standalone EVTX inspection/conversion; use Plaso when event log timestamps need to be correlated against other artifact types in one timeline.
- **forensic-timeline (planned)**: correlating evtx-dump output against other tools' findings is out of scope here.

## When to use this skill

- "Dump this EVTX file to JSON"
- "Show me the full XML of these event log records"
- "Convert this folder of EVTX files to JSONL for scripting"
- Need the complete, unmodified content of specific records (e.g., to verify a chainsaw hit's full context, or to extract a specific event for a report)

## When NOT to use this skill

- Need fast rule/Sigma-based hunting across many logs → chainsaw
- Need event log data merged into a cross-artifact timeline → plaso-log2timeline
- Need registry, not event log, data → windows-registry-analysis

## Prerequisites and scope

- Operates on **exported/copied .evtx files**, not a live evidence device.
- Presence of `evtx_dump` on the PALADIN system is based on the user's own system inventory as reported to Claude, not independently verified in this session. Confirm with `evtx_dump --help` before relying on specific flags, since flag names/defaults can vary by release.

## Core workflow

### 1. Verify the tool

```bash
evtx_dump --help
```

### 2. Default output (XML, to stdout)

```bash
evtx_dump path/to/file.evtx
```

### 3. JSON output

```bash
evtx_dump -o json path/to/file.evtx
```

### 4. Write output to a file instead of stdout

```bash
evtx_dump -f output.json -o json path/to/file.evtx
```

### 5. JSON Lines output (one JSON object per line — convenient for downstream scripting/ingestion)

```bash
evtx_dump -o jsonl path/to/file.evtx
```

### 6. Batch-processing multiple files

`evtx_dump` itself operates on one file per invocation; per the project's own documentation, batch processing across a directory is done by combining it with a file-finder such as `fd`:

```bash
fd -e evtx -x evtx_dump -o jsonl {} \; > all_logs.jsonl
```

(Verify the exact `fd`/shell quoting on your system — the pattern above reflects the documented approach of pairing `evtx_dump` with `fd` for batch conversion to a single JSONL stream; confirm current syntax with the tool's own `--help` and README if it does not match your installed version.)

### 7. Reading from stdin

```bash
cat file.evtx | evtx_dump -o jsonl -
```

Useful when the EVTX file is piped from another process (e.g., decompression) rather than sitting as a plain file.

### 8. WEVT template cache (advanced)

Some versions support supplying a `.wevtcache` template cache file so records can be rendered even when the embedded EVTX template expansion fails. Confirm the exact flag name and behavior with `--help` on the installed version before using it — do not assume the flag name without checking.

## Typical examiner workflow

1. Export/copy the target EVTX file(s) from the image (never operate on a live/original device).
2. `evtx_dump --help` to confirm available flags on the installed build.
3. Run a JSON or JSONL dump of the file(s) needed for review or for a chainsaw hit's full context.
4. Review or script against the JSON/JSONL output; for full-log hunting instead of single-record inspection, prefer chainsaw.
5. If feeding results into a broader timeline, hand the parsed data to plaso-log2timeline's workflow (or note that Plaso's own EVTX parser may be a more direct path for that purpose) rather than manually reconciling formats.

## Troubleshooting

| Symptom | Likely cause / next step |
|---|---|
| `evtx_dump: command not found` | Not installed or not on PATH — verify with the user |
| Records fail to render / show raw binary or template errors | Embedded template expansion failure — check whether the installed version supports a WEVT template cache option via `--help`; otherwise note the limitation rather than guessing at a workaround |
| Output is XML when JSON was expected | Default output format is XML — must explicitly pass `-o json` (or `-o jsonl`) |
| Huge output file / hard to review | Prefer `-o jsonl` for line-oriented review/scripting, or narrow to specific files rather than dumping an entire log set at once |
| File appears truncated or throws parse errors | Log may be corrupted or only partially recovered/carved — note this explicitly rather than treating partial output as complete |

## What this skill must never do automatically

- Never run `evtx_dump` directly against a live/original evidence device — only against exported/copied .evtx files.
- Never invent flag names or output-format options not confirmed via `--help`/current project README — flag uncertainty and tell the user to verify against the installed version.
- Never present the presence of a specific event record as proof of a specific person's action — a record indicates that event/artifact occurred or was logged, not who caused it, unless independently corroborated.
- Never overwrite or modify the source .evtx file; always write conversions to a separate output file/location.
- Never silently truncate or omit records when summarizing output for the user — if only a subset was reviewed, say so explicitly.

