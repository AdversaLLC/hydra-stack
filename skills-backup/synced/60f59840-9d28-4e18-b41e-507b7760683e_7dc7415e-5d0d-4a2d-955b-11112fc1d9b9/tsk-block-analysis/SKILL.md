---
name: "tsk-block-analysis"
description: "Performs block/sector-level analysis of a filesystem inside a disk image using The Sleuth Kit's blkls, blkcat, blkstat, and blkcalc command-line tools — extracting unallocated space, slack space, and individual blocks, and converting between block addresses. Trigger phrases include \"extract unallocated space\", \"pull slack space from this file\", \"blkls this partition\", \"cat this specific block\", \"blkstat this block\", \"convert this block address\", \"carve unallocated clusters\", or \"dump the unallocated space for keyword searching\". Not for GUI Autopsy workflows (see autopsy-analysis), not for inode-based file extraction (see tsk-file-content), and not for whole-partition layout (see tsk-mmls)."
---

---
name: tsk-block-analysis
description: Performs block/sector-level analysis of a filesystem inside a disk image using The Sleuth Kit's blkls, blkcat, blkstat, and blkcalc command-line tools — extracting unallocated space, slack space, and individual blocks, and converting between block addresses. Trigger phrases include "extract unallocated space", "pull slack space from this file", "blkls this partition", "cat this specific block", "blkstat this block", "convert this block address", "carve unallocated clusters", or "dump the unallocated space for keyword searching". Not for GUI Autopsy workflows (see autopsy-analysis), not for inode-based file extraction (see tsk-file-content), and not for whole-partition layout (see tsk-mmls).
---

# TSK blkls / blkcat / blkstat / blkcalc — Block-Layer Analysis Tools

## Purpose

These four tools operate on raw data units (blocks/clusters/sectors) of a filesystem rather than on named files or inodes. They are grouped together because they share the same addressing model and are commonly used in sequence: locate blocks of interest (via `istat`, `ifind -d`, or `blkstat`), extract or convert them (`blkcat`/`blkls`/`blkcalc`).

Common uses: extracting all unallocated space in a filesystem for keyword searching or carving, pulling file slack space (residual data past a file's logical end within its last allocated cluster), inspecting a single block's allocation status, and converting between filesystem-relative and image-relative block addresses when a filesystem sits inside a partition.

Always operate on a verified forensic image or read-only mounted copy — never the original device.

## blkls — Extract Unallocated Space / Slack, or List Blocks

```
blkls [options] image [start-stop]
```

| Flag | Purpose |
|---|---|
| `-o offset` | Sector offset to the filesystem within the image |
| `-A` | Display only allocated blocks |
| `-u` | Display only unallocated blocks (commonly the default behavior for extraction; verify against `-h`) |
| `-s` | Extract slack space instead of unallocated block content |
| `-e` | Output every block including metadata, in "raw" mode (verify exact meaning against `-h`) |
| `-i imgtype` / `-f fstype` | Image/filesystem type overrides |

Example — dump all unallocated space to a file for later carving/keyword searches:
```
blkls -o 2048 image.E01 > unallocated.dd
```

Example — extract slack space only:
```
blkls -o 2048 -s image.E01 > slack.dd
```

**Note:** exact default behavior (whether unallocated-only extraction requires an explicit flag or is the default mode) has varied across TSK versions. Confirm with `blkls -h` before writing this into a report as fact.

## blkcat — Extract Content of a Specific Block/Data Unit

```
blkcat [options] image addr [len]
```

| Flag | Purpose |
|---|---|
| `-o offset` | Sector offset to the filesystem |
| `-h` | (help) — do not confuse with a data-related flag |
| `-i imgtype` / `-f fstype` | Image/filesystem type overrides |

Example — dump block 45231 (and the following 3 blocks) to a file:
```
blkcat -o 2048 image.E01 45231 4 > block_dump.bin
```

Useful after `istat` reports the specific block addresses allocated to a file of interest, to inspect raw content directly rather than through the file-content abstraction.

## blkstat — Report Allocation Status of a Block

```
blkstat [options] image addr
```

Reports whether a given data unit/block is allocated or unallocated, and (filesystem-dependent) which group/cluster structure it belongs to.

```
blkstat -o 2048 image.E01 45231
```

## blkcalc — Convert Between Block Addressing Schemes

`blkcalc` converts a block address as reported by `blkls` (which operates on a compacted, unallocated-only address space in certain modes) back into the corresponding address in the full filesystem/image address space, or vice versa. This matters because when `blkls` extracts only unallocated blocks, the offsets *within that extracted output* do not directly correspond to filesystem block addresses — `blkcalc` bridges that gap so a hit found (e.g., via keyword search) inside `unallocated.dd` can be mapped back to its real location on the filesystem.

```
blkcalc [options] image -u unit_in_extracted_output
```

Exact option letters for direction of conversion vary — verify with `blkcalc -h` before use in casework.

## Typical Workflow

1. Confirm working from a verified forensic image.
2. Get the filesystem offset via `mmls` if needed (see `tsk-mmls`); confirm block/cluster size via `fsstat` (see `tsk-fsstat`).
3. Extract unallocated space for bulk keyword search or carving:
   ```
   blkls -o 2048 image.E01 > unallocated.dd
   ```
4. Run keyword search or a carver (e.g., `photorec` — see `testdisk-photorec` skill, or `scalpel`/`foremost` outside TSK) against `unallocated.dd`.
5. When a hit is found at a given offset inside `unallocated.dd`, use `blkcalc` to translate that offset back to the real filesystem block address.
6. Use `blkstat` to confirm that block's current allocation status, and `blkcat` to re-extract just that block directly from the original image for verification.
7. Cross-reference with `istat` (see `tsk-file-content`) if the block can be tied to a specific known inode.

## Troubleshooting

| Symptom | Likely Cause | Action |
|---|---|---|
| `blkls` output is enormous / fills disk | Extracting all unallocated space on a large volume | Expected — ensure sufficient destination storage before running; consider extracting a bounded range instead |
| Keyword hit offset in `unallocated.dd` doesn't match anything sensible in the raw image | Offset not translated from "unallocated-only" address space | Use `blkcalc` to convert before looking up the block directly in the image |
| "Cannot determine file system type" | Wrong offset or unsupported filesystem | Re-verify with `mmls`/`fsstat` |
| `blkcat` output is one block short/long | Off-by-one in `len` argument or misunderstanding of units (blocks vs. bytes) | Re-check `blkcat -h` for whether `len` is in blocks or bytes for the given filesystem |

## What This Skill Must Never Do Automatically

- Never run these tools against the original source device — only a verified forensic image or read-only mounted copy.
- Never write extraction output (`unallocated.dd`, slack dumps, block dumps) back onto the evidence image or original media.
- Never treat content recovered from unallocated/slack space as attributable to a specific file or user without corroborating metadata (timestamps, surrounding context, `istat`/`ifind` cross-reference).
- Never fabricate flag behavior (e.g., exact default of `blkls` with no flags) — confirm via `-h`/man page and flag any uncertainty explicitly.
- Never skip logging the exact command and offsets used to produce an extraction — reproducibility is required for evidentiary work.

