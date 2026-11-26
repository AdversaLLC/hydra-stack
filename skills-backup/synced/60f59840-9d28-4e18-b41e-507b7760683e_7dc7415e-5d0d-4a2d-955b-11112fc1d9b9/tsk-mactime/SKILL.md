---
name: "tsk-mactime"
description: "Generates a MAC(B) (Modified/Accessed/Changed/Born) timeline from The Sleuth Kit body files produced by fls or fiwalk, using the mactime command-line tool. Trigger phrases include \"build a timeline\", \"mactime this body file\", \"generate a MAC timeline\", \"create a MACB timeline from fls output\", or \"sort file activity by time\". Covers only raw TSK-based timeline generation from body files, not multi-source timeline correlation (registry, logs, browser history, etc.) — that broader work belongs to the planned forensic-timeline skill once built. Not for GUI Autopsy workflows (see autopsy-analysis)."
---

---
name: tsk-mactime
description: Generates a MAC(B) (Modified/Accessed/Changed/Born) timeline from The Sleuth Kit body files produced by fls or fiwalk, using the mactime command-line tool. Trigger phrases include "build a timeline", "mactime this body file", "generate a MAC timeline", "create a MACB timeline from fls output", or "sort file activity by time". Covers only raw TSK-based timeline generation from body files, not multi-source timeline correlation (registry, logs, browser history, etc.) — that broader work belongs to the planned forensic-timeline skill once built. Not for GUI Autopsy workflows (see autopsy-analysis).
---

# TSK mactime — MAC(B) Timeline Generation

## Purpose

`mactime` takes a **body file** (a pipe-delimited intermediate format produced by `fls -m` or `fiwalk`, listing file metadata including MAC(B) timestamps) and renders it as a human-readable, chronologically sorted timeline. This is the classic TSK timeline workflow: filesystem metadata walk → body file → `mactime` → timeline.

## Boundary With `forensic-timeline`

This skill covers **only** the mechanical step of turning a TSK body file into a sorted MAC(B) timeline. A planned `forensic-timeline` skill (not yet built) is intended to cover broader, multi-source timeline correlation — combining this filesystem timeline with registry hive timestamps, event logs, browser history, application artifacts, and other non-TSK sources into a unified case timeline. Do not attempt that broader correlation here; if the user asks for cross-source correlation, note that it belongs to `forensic-timeline` once available.

## Command Syntax

```
mactime [options] -b bodyfile [start-date..end-date]
```

| Flag | Purpose |
|---|---|
| `-b bodyfile` | Path to the body file (from `fls -m` or `fiwalk`) |
| `-z zone` | Timezone to render timestamps in (should match the timezone used/intended in the source image analysis) |
| `-d` | Output in comma-separated (CSV) format instead of the default text format |
| `-y` | Display dates in ISO 8601 (YYYY-MM-DD) format |
| `-i hour\|day file` | Generate an index summarizing activity counts per hour/day, written to `file` (used for graphing/summary purposes) |
| `-g grpfile` / `-p passwordfile` | Map UIDs/GIDs to names using supplied group/password files (Unix/Linux images) |

Confirm exact flags for the installed TSK version with `mactime -h`/man page before quoting them in a report — CSV/date-format flags in particular have shifted between versions.

## Producing the Body File First

`mactime` does not read an image directly — it requires a body file as input:

```
fls -o 2048 -r -m / image.E01 > body.txt
mactime -b body.txt -z UTC > timeline.txt
```

Or from `fiwalk`'s DFXML output converted/exported to body-file format (see `tsk-fiwalk` for generating the DFXML; conversion tooling for DFXML-to-body format should be verified against current sleuthkit.org documentation, as it is not a core part of `fiwalk` itself).

## Typical Workflow

1. Confirm you are working from a verified forensic image.
2. Generate the body file with `fls -r -m` (see `tsk-fls`), using a consistent path prefix and covering the full filesystem.
3. Decide on and document the timezone to normalize all timestamps to (commonly UTC for cross-artifact consistency; note the original media's local timezone separately in case notes).
4. Run `mactime`:
   ```
   mactime -b body.txt -z UTC -d > timeline.csv
   ```
5. Review the timeline for clusters of activity, gaps, or anomalies (e.g., mass timestamp changes suggesting anti-forensic timestomping).
6. Hand off the resulting CSV/text timeline to `forensic-reporting` for narrative writeup, or to a future `forensic-timeline` skill if correlating with non-filesystem sources.

## Interpreting MACB Output

Each line typically represents one timestamp event tied to a file, annotated with which of M/A/C/B (Modified/Accessed/Changed/Born-Created) triggered that line — a single file can appear multiple times if its four timestamps differ. Pay attention to:

- Multiple files sharing the exact same timestamp down to the second, which can indicate bulk operations (e.g., mass copy, extraction of an archive, or installation).
- "Born" (creation) time earlier than "Modified" time is normal; the reverse relationship, or all four timestamps being identical, can sometimes be circumstantial evidence worth flagging for further investigation — but never state anti-forensic timestomping as a firm conclusion in a report without corroborating evidence.

## Troubleshooting

| Symptom | Likely Cause | Action |
|---|---|---|
| "Cannot open body file" | Wrong path or `fls -m` step failed silently | Confirm `body.txt` exists and is non-empty before running `mactime` |
| Timeline is empty despite valid body file | Date range filter (start-date..end-date argument) excludes all entries | Remove or widen the date range filter |
| Timestamps appear shifted by a fixed number of hours | Timezone mismatch between `-z` in `fls -m` (if applicable) and `mactime -z` | Use a single consistent timezone across the whole pipeline and document it |
| UID/GID shown instead of usernames | No `-p`/`-g` mapping file supplied | Supply the appropriate password/group file extracted from the image, or note UID/GID untranslated in the report |

## What This Skill Must Never Do Automatically

- Never fabricate or interpolate missing timestamp data — if `fls`/`fiwalk` did not capture a value, `mactime` will show it as missing; do not fill gaps with assumptions.
- Never assert timestamp manipulation ("timestomping") as confirmed fact from `mactime` output alone — flag as "possible" and note it requires additional corroboration.
- Never silently change or normalize the timezone used without explicitly documenting which zone was applied and why.
- Never run this against, or write output into, the original evidence image — inputs are body files, outputs go to case working directories.
- Never invent flag syntax not confirmed via `-h`/man page; state explicitly when unsure.

