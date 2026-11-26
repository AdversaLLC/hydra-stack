---
name: paladin-forensic-workflow
description: Guides forensic acquisition and evidence-handling workflows in the Paladin Forensic Suite (SUMURI) live-boot environment — device identification, write-blocking, imaging with dd/dc3dd/Guymager, hash verification, read-only mounting, and acquisition troubleshooting. Triggers on "image this drive", "acquire this evidence", "identify the disks", "verify this image/hash", "mount this evidence read-only", "check drive health", "troubleshoot this Paladin system", "what disks are connected", or any request to inventory, acquire, or verify storage evidence in a forensic boot environment. Read/inventory operations may proceed automatically; anything that writes to a device, formats, repartitions, or could alter evidence requires explicit user confirmation with a clear statement of what will happen first. Not for post-acquisition artifact analysis inside Autopsy (see autopsy-analysis) or for producing the final written report (see forensic-reporting).
---

# Paladin Forensic Workflow

Operational guidance for forensic acquisition inside the Paladin Forensic Suite (SUMURI) live-boot environment. This skill covers getting from "drive connected" to "verified, hashed, working image" — safely, and with a clear audit trail. It does not cover artifact analysis (Autopsy) or writing the final report (`forensic-reporting`, which this skill should hand off to).

## Non-negotiable rules

1. **Never treat `/dev/sdX`, `/dev/nvmeXnY`, or similar kernel-assigned names as stable identifiers.** They can and do change across boots or when drives are added/removed. Before any operation that writes to or reads from a specific device, re-resolve identity using persistent identifiers: serial number, WWN, model, capacity (exact byte count, not rounded), and partition/filesystem signature. State the device path used in a command alongside these identifiers, not instead of them.
2. **Source and destination are never ambiguous.** Every acquisition step must explicitly label which device is SOURCE/EVIDENCE (read-only, never written to) and which is DESTINATION/WORKING COPY (the image file or clone target). If this isn't 100% clear from context, ask before proceeding.
3. **Read-only by default.** Inventory, identification, health checks, hash verification, and mounting evidence for review are read-only and may proceed without asking. Anything that writes — imaging to a destination disk (not a file), formatting, repartitioning, wiping, flashing firmware, or mounting evidence read-write — requires stopping and getting explicit confirmation, with the exact command and its effect stated plainly first.
4. **No invented output.** Never fabricate a hash value, SMART status, device serial, capacity, or command result. If a command wasn't actually run or its output wasn't actually seen, say so — mark it `NOT VERIFIED` rather than presenting a plausible-looking value.
5. **Everything is logged as it happens**, in a form `forensic-reporting` can consume later: timestamp (UTC), exact command, exit status, and result. Don't reconstruct this after the fact from memory.

## Workflow

### 1. Environment and hardware identification
Before touching any drive, establish what you're working with. Read-only:

- Confirm Paladin Forensic Suite is the running environment (check for its known live-boot markers rather than assuming); note the version if visible, since acquisition tool versions/behavior can differ across releases.
- Enumerate connected block devices and their persistent identifiers: `lsblk -o NAME,SERIAL,WWN,MODEL,SIZE,FSTYPE,MOUNTPOINT` and cross-check with `udevadm info --query=all --name=/dev/sdX` for serial/WWN, and `smartctl -i /dev/sdX` for model/serial confirmation.
- Identify which device is genuinely write-blocked (hardware write-blocker in use, or Paladin's software write-block toggle state) versus which is not. State this explicitly for every device before recommending any operation.

### 2. Source vs. destination declaration
Before any acquisition command, produce an explicit statement in this form and get it confirmed if there's any ambiguity:

```
SOURCE / EVIDENCE:      /dev/sdX  (serial: ____, WWN: ____, model: ____, size: ____ bytes)
DESTINATION / WORKING:  /dev/sdY or /path/to/image.dd  (serial/path: ____, size: ____ bytes, must be >= source size)
Write-blocked source:   YES / NO / UNKNOWN — verify before proceeding if UNKNOWN
```

If write-block status is UNKNOWN, that is a stop condition — resolve it before imaging.

### 3. Pre-acquisition health check
Read-only:
- `smartctl -a /dev/sdX` for SMART health, reallocated sectors, pending sectors.
- `fdisk -l /dev/sdX` or `parted /dev/sdX print` for partition table type (MBR/GPT) and layout.
- `blkid /dev/sdX*` for filesystem types and existing UUIDs/labels.
- Note any read errors, reported bad sectors, or SMART failures — these affect which imaging tool/strategy to recommend (e.g., dc3dd/ddrescue-style error handling for a failing drive rather than plain dd).

### 4. Imaging
Recommend the tool based on the situation, and state why:
- **dc3dd** — general acquisition with built-in hashing and logging; good default.
- **dd** — available everywhere, but no built-in verification/error-recovery; pair manually with a separate hash step.
- **Guymager** — GUI acquisition with E01/AFF support and built-in verification; useful when a case format (E01) is required, or the examiner prefers a GUI-driven log.

For any of these, before executing:
- State the exact command.
- State expected duration is unknown/estimate only if given, never a fabricated ETA.
- State the hash algorithm(s) to be computed (MD5 and/or SHA-256 — note MD5 alone is not collision-resistant but remains an industry-standard pairing for legacy compatibility; recommend SHA-256 as primary when the case allows).
- This is a write operation to the destination — get explicit confirmation before running it, even though the source stays untouched.

Log: full command, start/end timestamp (UTC), exit code, tool version if obtainable.

### 5. Verification
- Compute and record source and destination hashes independently (don't just trust the imaging tool's self-reported hash if independent verification is feasible — note when it isn't).
- Compare and state PASS/FAIL/NOT VERIFIED explicitly. Never state a match without having actually seen both values.
- If verification fails, stop, report the mismatch, and do not proceed to analysis on that image.

### 6. Mounting for review
- Mount the **image**, not the source device, whenever possible.
- Mount read-only (`-o ro,noload` for filesystems that support it) and note the exact mount options used.
- If a write-blocker is in use and mounting the physical source directly is unavoidable, confirm write-block status again immediately before mounting.

### 7. Handoff
Once acquisition and verification are complete, the acquisition log (commands, timestamps, hashes, device identifiers, verification result) is exactly the input `forensic-reporting` needs — pass it along rather than re-deriving it from memory.

## Troubleshooting

| Symptom | Likely causes | Diagnostic steps |
|---|---|---|
| Device not detected | Cable/port fault, unsupported controller, drive failure | Check `dmesg` tail after connect; try different port; check `lsblk` vs `dmesg` for partial detection |
| Imaging tool reports I/O errors mid-acquisition | Failing sectors, cable issue, power issue on drive | Check `smartctl` for reallocated/pending sector counts; consider error-tolerant re-acquisition rather than restarting from scratch; document exact byte offset of errors |
| Hash mismatch between source and image | Read errors during imaging, destination write error, bit rot on destination media | Re-verify destination media health; re-image if source is still readable; do not silently re-hash and report a "corrected" match without noting the discrepancy |
| Write-blocker status unclear | Hardware write-blocker not properly seated, software write-block toggle in unknown state | Physically reseat/reconfirm hardware blocker; check Paladin's write-block indicator directly rather than assuming from a previous session |
| Destination disk smaller than source | Sector math error (512 vs 4096 sector size), miscounted capacity | Compare exact byte counts (not "GB" rounding) from both devices before starting |
| Mount fails or mounts read-write unexpectedly | Missing `ro` flag, filesystem needing journal replay | Explicitly pass `-o ro`; for journaled filesystems needing recovery, mount a copy, never the original, if replay is required |

## What this skill must never do automatically

- Write to, format, partition, or wipe any physical device without explicit per-action confirmation.
- Flash or modify firmware.
- Assume a `/dev/sdX` path from an earlier step is still valid without re-verifying identifiers.
- Report a hash, SMART value, or command result that wasn't actually observed.
- Skip stating source/destination roles explicitly, even when "obvious."

## Handoff to other skills

- Artifact-level analysis of a verified image → `autopsy-analysis` (when available).
- Writing the acquisition up as a formal report → `forensic-reporting`.
- Network capture found on the evidence → `wireshark-pcap-analysis` (when available).
