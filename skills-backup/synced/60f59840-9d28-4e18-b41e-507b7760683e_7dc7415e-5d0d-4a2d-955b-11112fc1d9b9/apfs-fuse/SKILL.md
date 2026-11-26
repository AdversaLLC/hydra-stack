---
name: "apfs-fuse"
description: "Read Apple APFS (Apple File System) volumes on Linux using apfs-fuse/apfsutil, including encrypted APFS containers when the password or key is available. Triggers on \"mount this APFS image\", \"read APFS on Linux\", \"apfs-fuse\", \"this is a Mac drive with APFS\", \"APFS container\", or \"decrypt encrypted APFS volume\". Read-only access to an already-acquired image or write-blocked source — not an acquisition tool (see paladin-forensic-workflow/dc3dd/ddrescue for imaging a Mac first) and not for HFS+ volumes (use standard Linux HFS+ read support instead, which is more mature)."
---

---
name: apfs-fuse
description: Read Apple APFS (Apple File System) volumes on Linux using apfs-fuse/apfsutil, including encrypted APFS containers when the password or key is available. Triggers on "mount this APFS image", "read APFS on Linux", "apfs-fuse", "this is a Mac drive with APFS", "APFS container", or "decrypt encrypted APFS volume". Read-only access to an already-acquired image or write-blocked source — not an acquisition tool (see paladin-forensic-workflow/dc3dd/ddrescue for imaging a Mac first) and not for HFS+ volumes (use standard Linux HFS+ read support instead, which is more mature).
---

# APFS-FUSE (Apple File System on Linux)

`apfs-fuse` (and the related `apfsutil`) provide read access to Apple's APFS format from Linux, which lacks first-party APFS support. This is commonly needed when examining Mac evidence imaged into a raw/E01/dd file, since Macs since ~2017 (macOS 10.13+) default to APFS.

## Scope

- **Read-only.** apfs-fuse is a read implementation; it does not support writing to or repairing APFS volumes. This aligns naturally with forensic best practice (never write to evidence), but note it also means this is not a repair tool if the APFS container is itself damaged — that's a different, harder problem outside this skill's scope.
- **Container-aware.** APFS uses a container/volume model — one physical partition (container) can hold multiple logical volumes (e.g., Macintosh HD, Macintosh HD - Data, Preboot, Recovery, VM). Identify which volume you actually need before mounting.

## Workflow

1. **Confirm the source is APFS.** `fsstat` or `blkid` may identify it, or the partition type GUID in `mmls` output (APFS container GUID is a known constant, but verify against current documentation rather than assuming a specific string from memory).
2. **Work from an image or write-blocked source**, never the original device directly, consistent with standard evidence handling.
3. **Mount the container via FUSE** (verify exact syntax against `apfs-fuse --help` or documentation — general pattern): `apfs-fuse [options] <source-image-or-device> <mountpoint>`. If the container has multiple volumes, apfs-fuse typically requires selecting which volume to expose, or exposes them as subdirectories — confirm current behavior rather than assuming.
4. **For encrypted APFS volumes** (FileVault), a password or recovery key is required. Do not attempt to guess or brute-force a FileVault password as part of this skill — that requires the same authorization gate as any other credential-based decryption (see `memory-key-recovery` for RAM-based key recovery as an alternative path, if legally authorized).
5. **Browse the mounted volume read-only** using standard file tools once mounted.
6. **Unmount cleanly** when done (`fusermount -u <mountpoint>` or equivalent).

## What this skill must never do automatically

- Mount read-write or attempt any write/repair operation against an APFS volume.
- Attempt to brute-force or guess a FileVault password.
- Assume a specific volume (e.g., "Data" vs. "System") is the right one without confirming the case's actual target — APFS's split system/data volume design (macOS Catalina+) means user data typically lives on the "Data" volume, not the one that looks like the main OS volume.
- Report a mount or decryption success that wasn't actually observed.

## Troubleshooting

| Symptom | Likely cause | Steps |
|---|---|---|
| apfs-fuse reports unrecognized format | Not actually APFS, or a snapshot/Fusion-drive layout not handled | Re-verify filesystem type; check for Core Storage (older Fusion Drive) instead of APFS |
| Container mounts but expected user files aren't visible | Mounted the System volume instead of the Data volume (post-Catalina split) | Check for and mount the "Data" volume specifically |
| Encrypted volume won't mount even with password | Wrong password, or volume uses a recovery key rather than a user password | Confirm which unlock method applies; check for `.plist`/keybag metadata about protection type |
| Mount succeeds but timestamps look wrong | APFS uses nanosecond timestamps and its own epoch handling that some tooling misparses | Cross-check timestamps against a tool known to correctly parse APFS metadata before relying on them in a report |

## Handoff

- Imaging the Mac before mounting → `paladin-forensic-workflow`, `dc3dd`, `ddrescue`.
- Partition/container layout identification → `tsk-mmls`.
- Recovering a FileVault key from a memory image (if legally authorized) → `memory-key-recovery`.
- Writing up findings → `forensic-reporting`.

