---
name: "ddrescue"
description: "Run GNU ddrescue for error-tolerant imaging of failing, degraded, or physically damaged storage media, using its mapfile to resume interrupted attempts and progressively fill in unreadable regions. Triggers on \"the drive has bad sectors\", \"ddrescue this disk\", \"recover a failing hard drive image\", \"resume a ddrescue job\", \"ddrescue mapfile\", \"drive keeps disconnecting during imaging\", or \"image a clicking/failing drive\". This is the tool to reach for specifically when source media is failing — for healthy media where hashing/logging is the priority, use dc3dd or dcfldd instead; for E01 output use ewf-tools; for the actual data-carving/partition-recovery step after imaging, see testdisk-photorec."
---

---
name: ddrescue
description: Run GNU ddrescue for error-tolerant imaging of failing, degraded, or physically damaged storage media, using its mapfile to resume interrupted attempts and progressively fill in unreadable regions. Triggers on "the drive has bad sectors", "ddrescue this disk", "recover a failing hard drive image", "resume a ddrescue job", "ddrescue mapfile", "drive keeps disconnecting during imaging", or "image a clicking/failing drive". This is the tool to reach for specifically when source media is failing — for healthy media where hashing/logging is the priority, use dc3dd or dcfldd instead; for E01 output use ewf-tools; for the actual data-carving/partition-recovery step after imaging, see testdisk-photorec.
---

# GNU ddrescue

`ddrescue` (GNU ddrescue, not the different and less capable `dd_rescue`) is purpose-built for copying data from a source that has read errors, physical damage, or is otherwise unreliable. Its core design idea is the **mapfile**: a record of which byte regions have been successfully copied, which failed, and which haven't been tried yet. This lets an imaging attempt be interrupted (drive disconnects, examiner needs to stop) and resumed later without re-reading already-good data, and lets ddrescue prioritize easy-to-read regions first before spending time retrying damaged areas.

Presence of `ddrescue` on this PALADIN system was reported by the user via their own system inventory, not independently verified by Claude.

## Why this tool specifically (vs dc3dd/dcfldd/Guymager)

| Situation | Better tool |
|---|---|
| Healthy source, need hash + log | dc3dd or dcfldd |
| Need E01 case file with GUI | Guymager |
| Source has bad sectors, is clicking, intermittently disconnects, or previous imaging attempts stalled/failed | **ddrescue** |
| Imaging was interrupted and needs to resume without restarting from zero | **ddrescue** (via its mapfile) |

ddrescue does not compute forensic hashes as part of its core operation the way dc3dd/dcfldd do — plan a separate hashing pass (e.g., `sha256sum`) on the completed image once ddrescue finishes, or use whatever hashing step the case workflow requires.

## Core syntax

```
ddrescue [options] <source> <destination> <mapfile>
```

The **mapfile** (sometimes called logfile) is not optional in practice — always supply one, even on a first attempt, so an interrupted run can be resumed. Verify exact flag spelling against `ddrescue --help` or `man ddrescue` on the installed system before relying on it in a report; the flags below reflect general knowledge of ddrescue's documented behavior, not a live version check.

| Flag | Purpose |
|---|---|
| `-f` / `--force` | Force overwrite of an existing destination file/device (required when destination already exists, e.g., resuming) |
| `-d` / `--idirect` | Use direct disk access on the input, bypassing some kernel caching — often recommended for damaged media |
| `-r <n>` / `--retry-passes=<n>` | Number of retry passes over failed/error regions after the initial pass |
| `-n` / `--no-scrape` | Skip the slower "scraping" phase (byte-by-byte retry of bad areas) — useful for a fast first-pass triage image before committing to a long scrape |
| `-R` / `--reverse` | Read the source backwards — sometimes recovers regions a forward pass could not |
| `--min-read-rate=<bytes>` | Skip regions where read speed drops below a threshold, to avoid getting stuck on a very slow section |
| `-A` / `--try-again` | Mark previously failed non-trimmed/non-scraped blocks for retry |
| `-v` / `--verbose` | Verbose status output |

## Typical workflow

1. **Declare source and destination explicitly**, same discipline as any imaging tool:
   ```
   SOURCE / EVIDENCE:     /dev/sdX (serial, WWN, model, exact byte size, noted health issues)
   DESTINATION / WORKING: /path/to/case001_drive1.img
   MAPFILE:               /path/to/case001_drive1.mapfile
   Write-blocked source:  YES / NO / UNKNOWN — resolve UNKNOWN before proceeding
   ```
2. **This is a write operation to the destination — get explicit confirmation before running**, stating source, destination, mapfile path, and the general strategy (e.g., "fast first pass with `-n`, then scrape remaining errors").
3. A common two-phase strategy on badly damaged media:
   - **Phase 1 — fast triage pass**, skipping slow/scraping work to grab everything easy first:
     ```
     ddrescue -n -d /dev/sdX /path/case001_drive1.img /path/case001_drive1.mapfile
     ```
   - **Phase 2 — scrape remaining bad regions**, now that easy data is already safe:
     ```
     ddrescue -d -r3 /dev/sdX /path/case001_drive1.img /path/case001_drive1.mapfile
     ```
   (Exact flag choice depends on drive condition — confirm current syntax against `--help` before executing; do not present this two-phase pattern as the only correct approach, it's a common convention, not a spec requirement.)
4. **If the process is interrupted** (drive disconnects, power issue, examiner stops it), re-running the same command with the same mapfile resumes from where it left off rather than restarting — this is the entire point of the mapfile, so never delete or overwrite it between attempts on the same source.
5. **After completion, read the mapfile** to determine actual coverage: how much was rescued, how much remains unreadable, and where. Report this honestly — a ddrescue image of severely damaged media may legitimately have gaps, and that must be stated, not hidden.
6. **Hash the resulting image** separately if the case requires a hash (ddrescue's own output is the image + mapfile, not a hash value).

## Troubleshooting

| Symptom | Likely cause | What to check |
|---|---|---|
| `ddrescue: command not found` | Not installed / not on PATH, or confused with `dd_rescue` (different tool) | `which ddrescue`; confirm it is GNU ddrescue, not `dd_rescue` |
| Run refuses to start, complains destination exists | Resuming into an existing partial image without `-f`, or accidentally targeting an existing unrelated file | Confirm this is actually a resume of the same job before forcing; never `-f` onto a destination that isn't the intended resume target |
| Very slow progress on one region | Physically damaged area causing many retries | Consider `--min-read-rate` to skip past it faster on a first pass, then return to it in a dedicated retry phase |
| Drive disconnects mid-run (USB dropout, power issue) | Failing drive electronics, power delivery issue, USB enclosure fault | Reconnect and re-run the identical command with the same mapfile to resume; check `dmesg` for the actual disconnect event before assuming device path is unchanged |
| Mapfile shows large unreadable regions after multiple passes | Physical damage beyond what retries can recover | Report actual coverage percentage from the mapfile; do not claim full imaging success when the mapfile shows otherwise |
| Device path changed after reconnect (e.g., `/dev/sdb` became `/dev/sdc`) | Kernel reassigns device nodes | Re-verify identity via serial/WWN before resuming — do not resume against a device path without confirming it's still the same physical unit |

## What this skill must never do automatically

- Run an acquisition/rescue command without explicit confirmation of source, destination, and mapfile path.
- Delete, overwrite, or ignore an existing mapfile for the same source without the user's awareness — that mapfile is the record of what's already been recovered.
- Claim complete imaging success when the mapfile indicates unrecovered regions remain.
- Fabricate a coverage percentage, error count, or read-rate figure not actually shown in ddrescue's output or mapfile.
- Force (`-f`) over a destination without confirming it is genuinely the intended resume target.

## Handoff

- Once imaging is as complete as the media allows, hash and verify → `dc3dd`/`dcfldd`-style hashing or a plain hashing utility, then `forensic-reporting` for documentation (including honestly stating any unrecovered regions from the mapfile).
- Source/destination identification and write-block discipline → `paladin-forensic-workflow`.
- Recovering files/partitions from within the resulting (possibly incomplete) image → `testdisk-photorec`.
- Mounting the resulting image read-only for review → `forensic-image-mounting`.

