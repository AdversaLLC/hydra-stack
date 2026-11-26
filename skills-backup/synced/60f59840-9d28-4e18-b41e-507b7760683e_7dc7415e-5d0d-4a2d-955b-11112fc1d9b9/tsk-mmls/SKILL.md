---
name: "tsk-mmls"
description: "Lists the partition/volume system layout of a disk image using The Sleuth Kit's mmls command-line tool, revealing partition boundaries, offsets, and unallocated gaps. Trigger phrases include \"show me the partition table\", \"mmls this image\", \"find partition offsets\", \"what volumes are on this disk\", \"check for hidden or unallocated partitions\", or \"list the volume layout\". Briefly mentions mmcat/mmstat for extracting/inspecting a specific partition. Not for GUI Autopsy workflows (see autopsy-analysis), not for filesystem-level listings inside a partition (see tsk-fls), and not for raw signature-based partition recovery when the table itself is damaged (see tsk-sigfind)."
---

---
name: tsk-mmls
description: Lists the partition/volume system layout of a disk image using The Sleuth Kit's mmls command-line tool, revealing partition boundaries, offsets, and unallocated gaps. Trigger phrases include "show me the partition table", "mmls this image", "find partition offsets", "what volumes are on this disk", "check for hidden or unallocated partitions", or "list the volume layout". Briefly mentions mmcat/mmstat for extracting/inspecting a specific partition. Not for GUI Autopsy workflows (see autopsy-analysis), not for filesystem-level listings inside a partition (see tsk-fls), and not for raw signature-based partition recovery when the table itself is damaged (see tsk-sigfind).
---

# TSK mmls — Volume/Partition System Layout Listing

## Purpose

`mmls` reads the partition table / volume system of a disk image (DOS/MBR, GPT, Mac, Sun, BSD) and lists each partition's starting sector, length, and description — including unallocated ("unpartitioned") space between or after partitions, which can conceal hidden data. It's normally the **first tool run** against a full-disk image, since most other TSK tools (`fls`, `icat`, `fsstat`, etc.) need a sector offset to locate the filesystem inside a specific partition.

`mmls` operates only on a forensic image or verified copy — never the original source device.

## Command Syntax

```
mmls [options] image
```

| Flag | Purpose |
|---|---|
| `-t vstype` | Force volume system type (`dos`, `gpt`, `mac`, `sun`, `bsd`) instead of autodetection |
| `-i imgtype` | Specify image format if not auto-detected (raw, ewf/E01, aff, vmdk, vhd) |
| `-o offset` | Sector offset if the volume system itself doesn't start at sector 0 (e.g., nested volume systems) |
| `-b size` | Set sector size in bytes if non-standard (default is usually 512) |
| `-a` / `-A` | Show only allocated / only unallocated partitions (verify exact letter case against `mmls -h`) |
| `-v` | Verbose diagnostic output |

Confirm exact flags for the installed TSK version with `mmls -h` before quoting them in a report.

## Reading Output

Typical `mmls` output columns: slot number, start sector, end sector, length (sectors), description. Example:

```
Slot    Start        End          Length       Description
000:    -----        0000000000   0000000000   Primary Table (#0)
001:    0000000000   0000002047   0000002048   Unallocated
002:    0000002048   0001050623   0001048576   NTFS (0x07)
003:    0001050624   0001953124   0000902501   Unallocated
```

- **Unallocated slots** deserve scrutiny — data can be hidden in gaps between partitions or after the last one.
- The **Start** sector for a partition of interest is the value to pass as `-o` to `fls`, `icat`, `fsstat`, `istat`, etc. Multiply by sector size (commonly 512 bytes) to get a byte offset if a tool requires bytes instead of sectors — confirm which unit each downstream tool expects.

## Typical Workflow

1. Confirm working from a verified, hash-matched image.
2. Run mmls to enumerate the volume layout:
   ```
   mmls image.E01
   ```
3. Note the start sector of each partition of interest, and flag any unusual unallocated regions for follow-up (e.g., with `blkls`/`sigfind`).
4. Feed the relevant start sector into filesystem-level tools:
   ```
   fsstat -o 2048 image.E01
   fls -o 2048 -r -p image.E01
   ```
5. If `mmls` fails to find a recognizable volume system at all (e.g., corrupted/wiped partition table), escalate to `sigfind` (see `tsk-sigfind`) to search for filesystem signatures directly, or `mmls -t` to try forcing an alternate volume system type.

## mmcat and mmstat (brief mention)

The `mm` family also includes:
- **mmstat** — prints the volume system type detected for the image (a quick complement to `mmls` when you just need to confirm the type).
- **mmcat** — extracts the raw content of a specific partition/volume to stdout, similar in spirit to `icat` but at the partition level, useful for carving out a single partition into its own image file for isolated analysis.

These are mentioned here for completeness; consult their respective `-h` output before use, as this skill focuses on `mmls`.

## Troubleshooting

| Symptom | Likely Cause | Action |
|---|---|---|
| "Cannot determine partition type" | Damaged/missing partition table, or unsupported volume system | Try `-t` to force a type; if still failing, consider `sigfind` to locate filesystem signatures manually |
| Partition list looks incomplete or wrong | Nested/nonstandard volume system (e.g., GPT protective MBR misread as plain MBR) | Try `-t gpt` explicitly; check image for a protective MBR structure |
| Sector numbers seem too large / image seems truncated | Wrong sector size assumption | Check `-b` if the media uses 4Kn (4096-byte) sectors instead of 512 |
| Offsets don't work in `fls`/`icat` | Unit mismatch (sectors vs. bytes) | Confirm what unit `-o` expects in the downstream tool's own `-h`; some tools want sector offset, others byte offset |

## What This Skill Must Never Do Automatically

- Never run `mmls` (or related `mm*` tools) against the original source device — only a verified forensic image or read-only mounted copy.
- Never write to, repartition, or otherwise modify the image being analyzed.
- Never assume a sector size or offset unit without checking — state assumptions explicitly and verify against tool `-h` output.
- Never present an "Unallocated" region as proof of hidden/wiped evidence without further analysis (e.g., `blkls`, `sigfind`) — flag it as an area warranting follow-up, not a conclusion.
- Never fabricate flag syntax not confirmed via `-h`/man page.

