---
name: "dcfldd"
description: "Run dcfldd, the Department of Defense Computer Forensics Lab's enhanced dd variant with on-the-fly hashing, progress display, and split output, for command-line raw (dd-format) forensic acquisition. Triggers on \"image with dcfldd\", \"dcfldd command syntax\", \"hash on the fly with dcfldd\", \"dcfldd status output\", or \"compare dcfldd vs dc3dd\". Use for raw/dd-format imaging with inline hashing from the command line — not for E01/AFF output (see ewf-tools or afflib-aff4), not a GUI workflow (see guymager), and not for a drive with significant read errors where error-tolerant re-reading is the priority (see ddrescue)."
---

---
name: dcfldd
description: Run dcfldd, the Department of Defense Computer Forensics Lab's enhanced dd variant with on-the-fly hashing, progress display, and split output, for command-line raw (dd-format) forensic acquisition. Triggers on "image with dcfldd", "dcfldd command syntax", "hash on the fly with dcfldd", "dcfldd status output", or "compare dcfldd vs dc3dd". Use for raw/dd-format imaging with inline hashing from the command line — not for E01/AFF output (see ewf-tools or afflib-aff4), not a GUI workflow (see guymager), and not for a drive with significant read errors where error-tolerant re-reading is the priority (see ddrescue).
---

# dcfldd

`dcfldd` is an enhanced version of GNU `dd` originally developed at the DoD Computer Forensics Lab. Like `dc3dd`, it adds forensic conveniences on top of the standard `dd` block-copy model: on-the-fly hashing, a running status display, split output files, and the ability to hash and write to multiple outputs simultaneously. It predates `dc3dd` and the two are frequently confused; they are separate codebases with different flag sets, not interchangeable syntax.

Presence of `dcfldd` on this PALADIN system was reported by the user via their own system inventory, not independently verified by Claude.

## dcfldd vs dc3dd — do not mix up syntax

Both tools solve the same problem (hash-while-imaging) but use different flags. If a command was written for one and run against the other, expect errors or silently ignored options. Confirm which tool is actually installed and being invoked (`which dcfldd`, `which dc3dd` — a system can have either, both, or neither) before pasting a command from memory.

## Core syntax

```
dcfldd if=<source> of=<destination> hash=<algorithm> hashlog=<logfile>
```

Common options (verify exact spelling/behavior against `dcfldd --help` or `man dcfldd` on the installed system before relying on it in a report — flags below reflect general knowledge of dcfldd's documented feature set, not a live version check on this system):

| Flag | Purpose |
|---|---|
| `if=` | Input (source) device or file |
| `of=` | Output (destination) file or device |
| `hash=md5,sha256` | Hash algorithm(s) to compute over the input while copying |
| `hashlog=<file>` | Write computed hash(es) to this log file |
| `hashwindow=<n>` | Compute a hash every n bytes instead of only a single hash for the whole transfer (piecewise hashing) — useful for later isolating where a discrepancy occurred |
| `bs=512` / `bs=64k` | Block size |
| `conv=noerror,sync` | Continue past read errors, padding to keep output aligned with source offsets |
| `of2=<file>` | Write a second copy of the output simultaneously (e.g., two destination images from one read pass) |
| `split=<size>` / `splitformat=` | Split output into fixed-size segments with a naming pattern |
| `statusinterval=<n>` | How often (in blocks) the status display updates |
| `sizeprobe=if` | Probe input size up front for a more accurate progress estimate (behavior/name may vary by version — confirm before use) |

## Typical acquisition workflow

1. **Declare source and destination explicitly**, same discipline as any other imaging tool:
   ```
   SOURCE / EVIDENCE:     /dev/sdX (serial, WWN, model, exact byte size)
   DESTINATION / WORKING: /path/to/case001_drive1.dd
   Write-blocked source:  YES / NO / UNKNOWN — resolve UNKNOWN before proceeding
   ```
2. **Confirm destination free space** against exact source byte count.
3. **This is a write operation — get explicit confirmation before running**, stating the exact command, hash algorithm(s), and destination.
4. Example command shape (illustrative — confirm flags against the live `--help` before use):
   ```
   dcfldd if=/dev/sdX hash=sha256,md5 hashlog=/path/case001_drive1.hashlog bs=64k of=/path/case001_drive1.dd
   ```
5. **Let it run to completion**; note the reported status/progress values as observed, not estimated.
6. **Read the hash log file** for actual computed values — never retype from memory.
7. **Independently verify** the destination image's hash with a separate tool where the case requires independent confirmation rather than relying solely on dcfldd's self-reported hash.

## Troubleshooting

| Symptom | Likely cause | What to check |
|---|---|---|
| `dcfldd: command not found` | Not installed / not on PATH | `which dcfldd`; confirm before assuming presence |
| Flags from a dc3dd example don't work | Syntax confused between the two tools | Re-check flags against `dcfldd --help` specifically, not dc3dd documentation |
| Progress/status display shows implausible ETA or size | Input size not probed correctly, piping from a device with unusual reported size | Cross-check actual device size independently (`blockdev --getsize64 /dev/sdX` or similar) rather than trusting a displayed ETA as fact |
| Read errors during acquisition | Bad sectors on source | Check for `conv=noerror,sync` usage; consider `ddrescue` instead if the source is degrading significantly |
| Hashlog missing or empty | Process killed before completion, hashlog path not writable | Confirm the run actually completed and the log path had write permission before treating the acquisition as done |
| Piecewise (`hashwindow`) hashes don't reassemble into a sensible full-image hash | Piecewise hashing produces segment hashes, not a single whole-image hash by design | Don't conflate a `hashwindow` segment hash with a full-image hash unless a full-image hash was also explicitly requested |

## What this skill must never do automatically

- Run an acquisition command without explicit confirmation of source, destination, and the exact command to be executed.
- Fabricate or infer a hash, byte count, or log entry that wasn't actually produced by the tool.
- Assume dcfldd and dc3dd flags are interchangeable.
- Treat a source with reported read errors as cleanly imaged without surfacing the actual error output.
- Overwrite an existing destination file without flagging it first.

## Handoff

- Acquisition log and hash results → `forensic-reporting`.
- Source/destination identification and write-block discipline → `paladin-forensic-workflow`.
- Source turns out to have significant bad sectors mid-acquisition → reconsider `ddrescue`.
- Mounting the resulting raw image read-only → `forensic-image-mounting`.

