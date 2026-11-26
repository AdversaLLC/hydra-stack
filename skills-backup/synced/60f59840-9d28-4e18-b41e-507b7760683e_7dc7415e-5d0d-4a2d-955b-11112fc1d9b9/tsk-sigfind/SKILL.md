---
name: "tsk-sigfind"
description: "Searches a raw disk or image for a binary signature/pattern at a given block-boundary alignment using The Sleuth Kit's sigfind command-line tool, to locate lost or damaged partition boundaries and filesystem structures when the partition table itself is unreadable. Trigger phrases include \"find lost partitions\", \"sigfind this image\", \"search for filesystem signatures\", \"find the boot sector by hex signature\", \"recover a deleted partition boundary\", or \"locate NTFS/FAT/ext superblocks in raw data\". Not for GUI Autopsy workflows (see autopsy-analysis), not for general partition listing when the table is intact (see tsk-mmls, which should be tried first)."
---

---
name: tsk-sigfind
description: Searches a raw disk or image for a binary signature/pattern at a given block-boundary alignment using The Sleuth Kit's sigfind command-line tool, to locate lost or damaged partition boundaries and filesystem structures when the partition table itself is unreadable. Trigger phrases include "find lost partitions", "sigfind this image", "search for filesystem signatures", "find the boot sector by hex signature", "recover a deleted partition boundary", or "locate NTFS/FAT/ext superblocks in raw data". Not for GUI Autopsy workflows (see autopsy-analysis), not for general partition listing when the table is intact (see tsk-mmls, which should be tried first).
---

# TSK sigfind — Binary Signature Search for Lost Partitions/Filesystems

## Purpose

`sigfind` scans raw image data for a specific byte signature at a defined offset within each sector/block, aligned to a chosen block size. Its primary forensic use is finding filesystem or partition boundary signatures (e.g., the `0x55AA` boot sector signature, or filesystem-specific superblock magic values) when the partition table has been deleted, corrupted, or intentionally wiped, and `mmls` cannot identify the volume layout normally.

This is a **last-resort / damaged-media tool** — always try `mmls` first (see `tsk-mmls`); reach for `sigfind` only when `mmls` cannot identify the volume system or when you have independent reason to believe partitions exist that the table doesn't reflect.

Run only against a verified forensic image — never the original source device.

## Command Syntax

```
sigfind [options] [signature_hex] image
```

| Flag | Purpose |
|---|---|
| `-o offset` | Byte/sector offset within the signature check location (position within each block where the signature is expected) — verify exact semantics against `sigfind -h` |
| `-b size` | Block size to align the search to (e.g., 512 for typical sector-aligned boot sector signatures) |
| `-l` | List built-in known signatures (e.g., commonly-supported ones like the boot sector `0x55AA`) rather than searching for a custom one |
| `-t template` | Use a named built-in template signature instead of specifying raw hex |

If no signature is given, `sigfind` commonly defaults to searching for the standard partition boot sector signature (`0x55AA` at the end of a 512-byte sector) — but confirm this default against the installed version's `-h`/man page rather than asserting it as universal.

Example — search for boot-sector signatures at default alignment:
```
sigfind -o 510 -b 512 55AA image.dd
```

(The signature bytes, offset, and block size shown above reflect the well-documented standard MBR/boot-sector signature location; still confirm current flag names/order against `sigfind -h` before use, since exact positional argument order has been documented differently across versions.)

## Typical Workflow

1. Confirm you're working from a verified forensic image, and that `mmls` has already been tried and failed to produce a usable volume layout (see `tsk-mmls`).
2. Determine what signature to search for:
   - Standard boot sector: `0x55AA` at offset 510 within a 512-byte sector.
   - Filesystem-specific superblock magic values (e.g., ext2/3/4 superblock magic `0xEF53`) if you suspect a specific filesystem type based on other case context.
3. Run `sigfind` with the appropriate signature, offset, and block size.
4. For each hit reported (a sector/byte offset in the image), treat it as a **candidate** partition/filesystem start — not a confirmed one.
5. Validate each candidate by attempting to run `fsstat` or `fls` against that offset:
   ```
   fsstat -o <candidate_sector> image.dd
   ```
   A clean, sensible `fsstat` result strongly supports the candidate; an error suggests a false-positive signature match (byte patterns can coincidentally match without being a real structure).
6. Document every candidate tried, including ones that turned out to be false positives, for reproducibility.

## Troubleshooting

| Symptom | Likely Cause | Action |
|---|---|---|
| No hits found | Signature, offset, or block size assumption wrong; media may use non-standard sector size | Verify signature/offset against documented values for the target filesystem/boot sector; try `-b` with 4096 for 4Kn media |
| Many hits, most look like false positives | Signature is short/common (higher chance of coincidental matches) | Validate every candidate with `fsstat`/`fls` before treating as real; prioritize hits at sensible alignment/spacing |
| Tool reports unknown template with `-t` | Template name not supported in installed TSK version | Use `-l` to list available built-in signatures, or supply raw hex directly |
| Recovered offset doesn't yield a working filesystem in `fsstat` | False positive, or filesystem is present but corrupted beyond simple offset recovery | Note as inconclusive; consider deeper carving tools (e.g., `testdisk`) as a complementary approach |

## What This Skill Must Never Do Automatically

- Never run `sigfind` against the original source device — only a verified forensic image.
- Never treat a raw signature hit as a confirmed partition/filesystem boundary — always require validation via `fsstat`/`fls` before reporting it as a finding.
- Never write to, repair, or reconstruct a partition table on the image itself; `sigfind` is read-only reconnaissance, and any reconstruction should happen in a working copy explicitly created for that purpose, with the user's awareness.
- Never fabricate signature hex values or offsets for filesystem types not independently verified — state clearly when a signature/offset is a well-known documented constant versus a guess.
- Never invent flag syntax not confirmed via `-h`/man page; flag uncertainty explicitly, especially since `sigfind`'s flags are less consistently documented across TSK versions than more commonly used tools.

