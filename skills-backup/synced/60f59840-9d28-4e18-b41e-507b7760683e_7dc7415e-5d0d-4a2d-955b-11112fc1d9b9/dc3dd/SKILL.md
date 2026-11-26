---
name: "dc3dd"
description: "Run dc3dd, the DoD Cyber Crime Center's patched dd variant with built-in hashing, logging, split output, and error handling, for command-line raw (dd-format) forensic acquisition. Triggers on \"image with dc3dd\", \"acquire this drive with dc3dd\", \"dc3dd command syntax\", \"hash while imaging\", \"dc3dd log file\", or \"verify a dc3dd image\". Use this for raw/dd-format imaging with inline hashing from the command line — not for E01/AFF output (see ewf-tools or afflib-aff4), not for a GUI workflow (see guymager), and not for imaging a drive with failing sectors where read-error tolerance is the priority (see ddrescue, which is purpose-built for that)."
---

---
name: dc3dd
description: Run dc3dd, the DoD Cyber Crime Center's patched dd variant with built-in hashing, logging, split output, and error handling, for command-line raw (dd-format) forensic acquisition. Triggers on "image with dc3dd", "acquire this drive with dc3dd", "dc3dd command syntax", "hash while imaging", "dc3dd log file", or "verify a dc3dd image". Use this for raw/dd-format imaging with inline hashing from the command line — not for E01/AFF output (see ewf-tools or afflib-aff4), not for a GUI workflow (see guymager), and not for imaging a drive with failing sectors where read-error tolerance is the priority (see ddrescue, which is purpose-built for that).
---

# dc3dd

`dc3dd` is a patched version of GNU `dd` produced by the DoD Cyber Crime Center (DC3), built specifically for forensic acquisition. It behaves like `dd` (same basic block-copy model) but adds on-the-fly hashing of input/output, split output files, progress reporting, verification against a known hash, and a dedicated log file — the features examiners normally have to bolt onto plain `dd` by hand.

Presence of `dc3dd` on this PALADIN system was reported by the user via their own system inventory, not independently verified by Claude.

## What it actually does differently from plain dd

| Capability | Plain dd | dc3dd |
|---|---|---|
| Block copy | Yes | Yes |
| Built-in hashing during copy | No (separate pass needed) | Yes (`hash=`) |
| Progress display | No (needs `status=progress` on modern GNU dd) | Yes, built in |
| Split output into segments | No | Yes (`ofsz=`/`ofile=` split pattern) |
| Dedicated log file | No | Yes (`log=`) |
| Pattern/wipe fill support | Limited | Yes (`pat=`, `wipe`) |
| Verify written data against a hash | No | Yes (`vf=`) |

## Core syntax

```
dc3dd if=<source> of=<destination> hash=<algorithm> log=<logfile>
```

Common options (verify exact spelling/behavior against `dc3dd --help` or `man dc3dd` on the installed system before relying on it in a report — flags below reflect general knowledge of dc3dd's documented feature set, not a live version check on this system):

| Flag | Purpose |
|---|---|
| `if=` | Input (source) device or file |
| `of=` | Output (destination) file or device |
| `hash=md5,sha256` | Compute one or more hashes of the input as it's read (comma-separated list) |
| `log=<file>` | Write a run log (command, timing, hash results, errors) to this file |
| `bs=512` / `bs=64k` | Block size — larger blocks generally speed up imaging on healthy media |
| `conv=noerror,sync` | Continue past read errors, padding unreadable blocks so output stays aligned with source offsets |
| `ofsz=650m` | Split output into fixed-size segments (used with an output pattern) |
| `ofile=image.001` | Output file segment naming pattern used with `ofsz` |
| `progress=on` | Explicit progress reporting (behavior/default varies by version — confirm on system) |
| `vf=<file>` | Verify an existing output file against the source or against a supplied hash |
| `errlog=<file>` | Separate log of read errors and their byte offsets |

## Typical acquisition workflow

1. **Declare source and destination explicitly** before running anything:
   ```
   SOURCE / EVIDENCE:     /dev/sdX (serial, WWN, model, exact byte size)
   DESTINATION / WORKING: /path/to/case001_drive1.dd (or split segments)
   Write-blocked source:  YES / NO / UNKNOWN — resolve UNKNOWN before proceeding
   ```
2. **Confirm destination has enough free space** for the full source size (check exact byte count, not rounded GB, on both ends) plus room for the log.
3. **This is a write operation to the destination — get explicit user confirmation before running**, stating the exact command, source, destination, and hash algorithm(s) planned.
4. Example command shape (illustrative — confirm flag names against the live `--help` before use):
   ```
   dc3dd if=/dev/sdX hash=sha256 hash=md5 log=/path/case001_drive1.log of=/path/case001_drive1.dd
   ```
5. **Let it run to completion** — do not interrupt a running acquisition of evidence media without a clear reason and without noting the interruption in the log/report.
6. **Read the log file** for the actual computed hash(es), byte counts, and any reported errors — do not retype a hash from memory or infer one from a prior run.
7. **Independently verify** where feasible: compute a hash of the resulting image file with a separate tool (e.g., `sha256sum`) and compare against dc3dd's own reported hash, rather than trusting only the self-reported value, when the case requires independent verification.

## Troubleshooting

| Symptom | Likely cause | What to check |
|---|---|---|
| `dc3dd: command not found` | Not installed, or not on PATH in this shell | Confirm with `which dc3dd`; do not assume it's present system-wide just because it's on PALADIN generally |
| Acquisition much slower than expected | Small block size, failing source media causing retries, destination write bottleneck | Try a larger `bs=`; check `smartctl` on source for reallocated/pending sectors; check destination write speed independently |
| Read errors reported mid-run | Bad sectors on source | Check `errlog=` output for exact offsets; consider whether `ddrescue` is more appropriate for continued imaging of a degrading source rather than repeated dc3dd passes |
| Hash in log doesn't match a later independent hash of the image file | Output was modified/truncated after acquisition, split segments not concatenated correctly before independent hashing, read error during acquisition silently padded | Re-verify against the log's own error report first; do not assume tampering before ruling out a segment-concatenation or padding explanation |
| Output split into unexpected segment boundaries | `ofsz=`/output pattern set unintentionally or defaulted | Check the exact split settings used; confirm total reassembled size matches source before treating the image as complete |
| Destination fills up mid-acquisition | Insufficient free space was not checked before starting | Verify exact byte-for-byte source size vs. destination free space beforehand next time; do not resume onto a corrupted partial without noting it |

## What this skill must never do automatically

- Run an acquisition command (anything with `of=` pointing at a device or writing image data) without explicit confirmation of source, destination, and the exact command.
- Fabricate or "helpfully fill in" a hash, byte count, or error offset that wasn't actually in the log output.
- Treat a source with reported read errors as fully and cleanly imaged without surfacing the error log contents.
- Overwrite an existing image file at the destination path without flagging that it would be overwritten.
- Recommend skipping hashing to save time on an evidentiary acquisition.

## Handoff

- Acquisition log and hash results → `forensic-reporting`.
- Source/destination identification discipline and hardware write-block confirmation → `paladin-forensic-workflow`.
- If the source turns out to have significant bad-sector issues once acquisition starts → reconsider `ddrescue` for that media instead of continuing with dc3dd.
- Mounting the resulting raw image read-only for review → `forensic-image-mounting`.

