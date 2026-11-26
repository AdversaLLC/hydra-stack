---
name: "forensic-image-mounting"
description: "Mount an already-acquired forensic image (E01, AFF/AFF4, raw dd, VHD/VMDK) as a virtual read-only disk for examination, using xmount, ewfmount, affuse, or fvdemount depending on source format. Triggers on \"mount this image\", \"mount this E01 read-only\", \"I need to browse this image's filesystem\", \"xmount this to raw\", \"mount a VHD/VMDK image\", \"fvdemount\", or \"how do I access files inside this acquired image\". Focused on the mount-for-read-access use case across formats — for E01-specific acquisition, header inspection, and verification (ewfacquire/ewfinfo/ewfverify) see ewf-tools; for AFF/AFF4-specific conversion/verification see afflib-aff4; for the original acquisition step itself see guymager/dc3dd/dcfldd/ddrescue."
---

---
name: forensic-image-mounting
description: Mount an already-acquired forensic image (E01, AFF/AFF4, raw dd, VHD/VMDK) as a virtual read-only disk for examination, using xmount, ewfmount, affuse, or fvdemount depending on source format. Triggers on "mount this image", "mount this E01 read-only", "I need to browse this image's filesystem", "xmount this to raw", "mount a VHD/VMDK image", "fvdemount", or "how do I access files inside this acquired image". Focused on the mount-for-read-access use case across formats — for E01-specific acquisition, header inspection, and verification (ewfacquire/ewfinfo/ewfverify) see ewf-tools; for AFF/AFF4-specific conversion/verification see afflib-aff4; for the original acquisition step itself see guymager/dc3dd/dcfldd/ddrescue.
---

# Forensic Image Mounting (xmount / ewfmount / affuse / fvdemount)

Once an image is acquired and verified, examination almost always means mounting it as a virtual block device or filesystem rather than working with the raw container file directly. Several tools do this, each tied to specific source/output format combinations. This skill covers the **mount-for-read-access** use case across tools; format-specific acquisition and header/hash operations for E01 and AFF/AFF4 live in `ewf-tools` and `afflib-aff4` respectively.

Presence of these tools on this PALADIN system was reported by the user via their own system inventory, not independently verified by Claude.

## Tool-to-format map

| Tool | Mounts | Typical output |
|---|---|---|
| `xmount` | E01, AFF, raw dd, VDI, VHD, VMDK (broad input support; check installed build's actual compiled-in format support) | Presents as raw dd, and/or VDI/VHD/VMDK for use with a hypervisor, via FUSE |
| `ewfmount` | E01/Ex01 specifically (part of libewf, covered in depth in `ewf-tools`) | Raw device-like file via FUSE, for further mounting with `mount -o loop` or similar |
| `affuse` | AFF specifically (part of afflib, covered in depth in `afflib-aff4`) | Raw device-like file via FUSE |
| `fvdemount` | FileVault-encrypted (FVDE/CoreStorage) volumes, given the correct password/recovery key | Decrypted raw volume via FUSE, for further mounting |

All of these are **FUSE-based**: they expose the image as a raw-like file under a mountpoint, which then typically needs a *second* mount step (`mount -o ro,loop,noload <raw-file-under-fuse-mount> <second-mountpoint>`) to actually browse the filesystem inside. Two mount operations, not one, is the normal pattern — don't expect the filesystem tree to appear directly from the first FUSE mount step alone.

## General workflow (two-stage mount)

1. **Confirm you're mounting the image file, not the original source device.** The whole point of acquisition is to never touch the source again for routine examination — mount the verified image.
2. **Stage 1 — format-specific FUSE mount**, exposing the image as a raw-like device file:
   ```
   ewfmount case001_drive1.E01 /mnt/ewf1        # E01
   affuse case001_drive1.aff /mnt/aff1          # AFF
   xmount --in ewf case001_drive1.E01 /mnt/x1   # xmount, format flags vary — confirm against --help
   fvdemount -p <password_or_recovery_key> encrypted_volume.dmg /mnt/fvde1   # FileVault
   ```
   (Flag names/spelling illustrative — verify exact syntax against each tool's `--help`/man page on the installed system before relying on it in a report.)
3. **Identify the raw device-like file** created inside the FUSE mountpoint (commonly named `ewf1`, `aff1`, or similar depending on tool).
4. **Stage 2 — mount that raw file read-only** to actually browse the filesystem:
   ```
   mount -o ro,noload,loop /mnt/ewf1/ewf1 /mnt/case001_review
   ```
   Always include a read-only flag (`ro`) and, for journaled filesystems, an option to avoid journal replay (`noload` for ext3/ext4, or the equivalent for the filesystem in question) — mounting evidence read-write, even accidentally, can modify metadata (mount times, journal state) on what should be an immutable copy.
5. **If the image contains multiple partitions**, an offset may be needed for the second mount (`-o ro,noload,loop,offset=<bytes>`), determined from `fdisk -l` or `parted print` run against the stage-1 raw device file. State the exact offset used and how it was determined.
6. **When done reviewing**, unmount cleanly in reverse order: unmount the filesystem mount first, then the FUSE mount (`umount /mnt/case001_review`, then `fusermount -u /mnt/ewf1` or the equivalent for the tool used).

## Common flags

Verify all of the below against the live `--help`/man page before use — exact flags vary by tool and version, and this list reflects general documented behavior, not a live check on this system.

| Tool | Flag | Purpose |
|---|---|---|
| `xmount` | `--in <format>` | Specify input format (ewf, aff, dd, vdi, vmdk, etc.) |
| `xmount` | `--out <format>` | Specify output presentation format |
| `xmount` | `--cache <file>` | Redirect writes (e.g., from a hypervisor treating the mount as writable) to a cache file instead of the original image, preserving read-only integrity of the source image |
| `ewfmount` | `-X <options>` | Additional libewf-specific mount options (verify against man page) |
| `affuse` | (mountpoint as final arg) | Standard FUSE-style invocation |
| `fvdemount` | `-p <password>` | Supply password |
| `fvdemount` | `-r <recovery key>` | Supply recovery key instead of password |
| `fvdemount` | `-X <options>` | Additional libfvde-specific options |
| `mount` (stage 2) | `-o ro,noload` | Read-only, skip journal replay (ext3/ext4) |
| `mount` (stage 2) | `-o ro,loop,offset=<n>` | Mount a partition at a byte offset within a raw device file |

## Troubleshooting

| Symptom | Likely cause | What to check |
|---|---|---|
| FUSE mount command hangs or fails immediately | FUSE not available/loaded, permissions, already mounted at that path | Check `fusermount -u` on the target path first in case of a stale mount; confirm FUSE kernel support |
| Stage-1 mount succeeds but stage-2 `mount` fails with "wrong fs type" | Wrong filesystem assumed, or an offset is needed because the image contains a partition table rather than a bare filesystem | Run `fdisk -l`/`parted print` against the stage-1 raw file to find actual partition layout and offsets |
| Filesystem mounts but appears empty or garbled | Wrong offset calculated, or filesystem needs journal recovery that wasn't permitted read-only | Recompute offset from partition table sector size × start sector; for journal-recovery-required filesystems, mount a working copy, never treat this as acceptable on the primary verified image |
| Accidentally mounted read-write | `ro` omitted or overridden by a default, or underlying storage mounted the FUSE layer writably | Immediately unmount; check whether mount time / metadata changed; note this explicitly in report as a documented anomaly, don't hide it |
| `fvdemount` fails to decrypt | Wrong password/recovery key, or volume isn't actually FileVault/CoreStorage | Reconfirm credential source; confirm volume type before assuming tool failure |
| Unmount fails, "target is busy" | A shell or file browser still has a working directory inside the mount | Close/cd out of anything referencing the mountpoint before retrying `umount`/`fusermount -u` |

## What this skill must never do automatically

- Mount the original evidence source device directly when a verified image is available — always mount the image.
- Mount anything read-write, or omit `ro`/`noload`-equivalent options, without explicit confirmation that read-write access is actually required and why.
- Guess at a partition offset without deriving it from an actual partition table inspection.
- Leave a mount in place unreported — always note current mounted state so it isn't forgotten and left attached indefinitely.
- Treat an accidental read-write mount as a non-event — it must be disclosed, not silently corrected and hidden.

## Handoff

- E01-specific header/hash inspection before or after mounting → `ewf-tools`.
- AFF/AFF4-specific conversion/verification before or after mounting → `afflib-aff4`.
- Original acquisition → `guymager` / `dc3dd` / `dcfldd` / `ddrescue`.
- Filesystem-level analysis of the mounted content → `autopsy-analysis` (when available) or manual review.
- Documenting the examination → `forensic-reporting`.

