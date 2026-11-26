---
name: "tsk-fsstat"
description: "Displays filesystem-level statistics and structural details (type, layout, allocation state, journal info) from a partition inside a disk image using The Sleuth Kit's fsstat command-line tool. Trigger phrases include \"fsstat this partition\", \"show me filesystem details\", \"what filesystem is this\", \"get the volume statistics\", \"check the journal state\", \"how many blocks/inodes does this filesystem have\", or \"confirm the filesystem type and layout\". Not for GUI Autopsy workflows (see autopsy-analysis), not for per-file metadata (see tsk-file-content's istat), and not for partition table layout across the whole disk (see tsk-mmls)."
---

---
name: tsk-fsstat
description: Displays filesystem-level statistics and structural details (type, layout, allocation state, journal info) from a partition inside a disk image using The Sleuth Kit's fsstat command-line tool. Trigger phrases include "fsstat this partition", "show me filesystem details", "what filesystem is this", "get the volume statistics", "check the journal state", "how many blocks/inodes does this filesystem have", or "confirm the filesystem type and layout". Not for GUI Autopsy workflows (see autopsy-analysis), not for per-file metadata (see tsk-file-content's istat), and not for partition table layout across the whole disk (see tsk-mmls).
---

# TSK fsstat — Filesystem Statistics and Details

## Purpose

`fsstat` prints general information about a filesystem's structure: type and version, volume/label info, layout of key metadata structures (e.g., MFT location for NTFS, superblock/group info for ext, catalog file info for HFS+), block/cluster size, total block and inode counts, and allocation state summaries. It operates at the whole-filesystem level, complementing `istat` (single inode) and `mmls` (whole-disk partition layout).

Always run against a verified forensic image or read-only mounted copy — never the original device.

## Command Syntax

```
fsstat [options] image
```

| Flag | Purpose |
|---|---|
| `-o offset` | Sector offset to the filesystem within the image (from `mmls`) |
| `-i imgtype` | Image format if not auto-detected |
| `-f fstype` | Force filesystem type instead of autodetection |
| `-b size` | Set sector size in bytes if non-standard |
| `-z zone` | Timezone for any timestamps shown in output |

Confirm exact flags for the installed TSK version with `fsstat -h` before quoting them in a report; output content also varies significantly by filesystem type (NTFS output differs substantially from ext4 or HFS+ output).

## What the Output Typically Contains

Output is organized in sections; specifics vary by filesystem type, but generally include:

| Section | Example Content |
|---|---|
| File System Type | e.g., "NTFS", "Ext4", "HFS+", "FAT32" |
| Volume Info | Volume serial number/label, OEM name, version |
| Metadata layout | MFT start cluster and size (NTFS); superblock/inode table locations (ext); catalog/extents files (HFS+) |
| Content/block layout | Cluster/block size, total block count, allocation bitmap location |
| Journal info | Presence and state of a filesystem journal (ext3/4, NTFS $LogFile, HFS+ journal), if applicable |

This makes `fsstat` valuable early in an examination to confirm assumptions before running more targeted tools (e.g., confirming cluster size before doing block math for `blkls`/`blkcat`).

## Typical Workflow

1. Confirm you are working from a verified forensic image.
2. Run `mmls` first if the image is a full disk, to get the partition's starting sector (see `tsk-mmls`).
3. Run `fsstat` against that offset:
   ```
   fsstat -o 2048 image.E01
   ```
4. Record filesystem type, cluster/block size, and total block/inode counts in case notes — these values are prerequisites for accurately interpreting `fls`, `icat`, `istat`, and `blk*` tool output.
5. If a journal is present, note its state; journal contents themselves require separate parsing (outside TSK's scope here) but their presence/absence is itself a forensically relevant fact.

## Troubleshooting

| Symptom | Likely Cause | Action |
|---|---|---|
| "Cannot determine file system type" | Wrong `-o` offset, or unsupported/corrupt filesystem | Re-check `mmls` output for correct offset; try `-f` to force a type if you have independent confirmation of what it should be |
| Output seems generic / missing filesystem-specific sections | Older TSK version or partially supported filesystem variant | Check TSK version and known filesystem support matrix on sleuthkit.org before assuming corruption |
| Runs very slowly on large volumes | Full allocation bitmap / structure walk on a large filesystem | This is expected for some filesystem types; allow it to complete rather than interrupting mid-scan |
| Sector-size-related math looks wrong downstream | Non-512-byte sector size not accounted for | Use `-b` if needed and re-verify calculations |

## What This Skill Must Never Do Automatically

- Never run `fsstat` against the original source device — only a verified forensic image or read-only mounted copy.
- Never write to or modify the image or filesystem being examined.
- Never fabricate or estimate filesystem parameters (cluster size, inode count, MFT location) when `fsstat` fails to report them — state clearly that the value is unknown/unavailable and needs further investigation.
- Never assume a filesystem type without evidence (from `fsstat` autodetection or independent confirmation) before forcing one with `-f`.
- Never invent flag syntax not confirmed via `-h`/man page; call out uncertainty explicitly.

