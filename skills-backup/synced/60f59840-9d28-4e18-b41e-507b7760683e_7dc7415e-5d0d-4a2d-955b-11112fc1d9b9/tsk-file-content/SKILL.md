---
name: "tsk-file-content"
description: "Extracts file content by inode and looks up inode/metadata information from a filesystem inside a disk image using The Sleuth Kit's icat, ifind, and istat command-line tools. Trigger phrases include \"extract this file by inode\", \"cat this inode to a file\", \"find which inode owns this file\", \"find the parent directory of this inode\", \"show me inode metadata\", \"istat this file\", \"recover file content from an inode\", or \"what filesystem structures point to this data\". Covers icat (content extraction), ifind (inode/metadata lookups), and istat (inode statistics). Not for GUI Autopsy workflows (see autopsy-analysis), not for directory listings (see tsk-fls), and not for raw sector/block-level carving (see tsk-block-analysis)."
---

---
name: tsk-file-content
description: Extracts file content by inode and looks up inode/metadata information from a filesystem inside a disk image using The Sleuth Kit's icat, ifind, and istat command-line tools. Trigger phrases include "extract this file by inode", "cat this inode to a file", "find which inode owns this file", "find the parent directory of this inode", "show me inode metadata", "istat this file", "recover file content from an inode", or "what filesystem structures point to this data". Covers icat (content extraction), ifind (inode/metadata lookups), and istat (inode statistics). Not for GUI Autopsy workflows (see autopsy-analysis), not for directory listings (see tsk-fls), and not for raw sector/block-level carving (see tsk-block-analysis).
---

# TSK icat / ifind / istat — Inode-Based Content and Metadata Tools

## Purpose

These three tools work at the **inode / metadata-address** level of a filesystem, which is why they are grouped as one skill — they are typically used together in a single investigative sequence: find an inode (`ifind`), inspect its metadata (`istat`), then extract its content (`icat`).

All three read from a forensic image (or a partition inside one) and never write to the source. Always operate on a verified image copy, never the original device.

## icat — Extract File Content by Inode

Outputs the raw content of a file, given its metadata/inode address, to stdout.

```
icat [options] image inode
```

| Flag | Purpose |
|---|---|
| `-o offset` | Sector offset to the filesystem within the image |
| `-i imgtype` | Image format if not auto-detected |
| `-f fstype` | Force filesystem type |
| `-r` | Recover deleted file content, attempting to use resident/recovered data even for unallocated inodes |
| `-s` | Display slack space content appended after the file's logical content (verify exact behavior against `icat -h`; slack extraction specifics vary by filesystem support) |

Example — extract inode 128 to a local file for hashing/analysis:
```
icat -o 2048 image.E01 128-128-3 > recovered_file.docx
```

Redirect stdout to a file rather than printing binary content to the terminal.

## ifind — Find Inode/Metadata Address

Locates the metadata address (inode) associated with a filename, or finds the parent directory of a given inode.

```
ifind [options] image
```

| Flag | Purpose |
|---|---|
| `-o offset` | Sector offset to the filesystem |
| `-n filename` | Find the inode for a given filename/path |
| `-p inode` | Find the parent directory inode of the given inode (useful for orphaned/deleted files) |
| `-d dataunit` | Find which inode a given data unit/block address belongs to |
| `-i imgtype` / `-f fstype` | Image/filesystem type overrides |

Examples:
```
ifind -o 2048 -n /Users/josh/report.docx image.E01
ifind -o 2048 -p 128 image.E01
ifind -o 2048 -d 45231 image.E01
```

Verify exact option letters against `ifind -h` for the installed TSK version — some flag mappings (particularly `-d` for data unit lookups) have varied slightly across releases.

## istat — Display Inode/Metadata Statistics

Prints detailed metadata for a given inode: allocation status, size, MAC(B) timestamps, permissions, and the data unit (block) addresses allocated to the file.

```
istat [options] image inode
```

| Flag | Purpose |
|---|---|
| `-o offset` | Sector offset to the filesystem |
| `-z zone` | Timezone for displayed timestamps |
| `-i imgtype` / `-f fstype` | Image/filesystem type overrides |

Example:
```
istat -o 2048 -z UTC image.E01 128-128-3
```

Typical output includes allocation status (allocated/unallocated), owner/group, link count, size, Modified/Accessed/Changed/Created (Born) times, and a list of block/cluster addresses — the latter is useful input to `blkcat`/`blkstat` (see `tsk-block-analysis`) for direct block-level review.

## Typical Combined Workflow

1. Confirm you're working from a verified forensic image.
2. Use `fls` (see `tsk-fls`) or `ifind -n` to locate the inode of interest:
   ```
   ifind -o 2048 -n /Users/josh/Documents/budget.xlsx image.E01
   ```
3. Inspect metadata before extracting, to confirm allocation status and timestamps:
   ```
   istat -o 2048 image.E01 4112-128-1
   ```
4. Extract content:
   ```
   icat -o 2048 image.E01 4112-128-1 > /case/output/budget_recovered.xlsx
   ```
5. Hash the extracted file immediately and log the hash in case notes — extraction of evidence artifacts should always be paired with hashing per chain-of-custody practice (see `forensic-reporting`).
6. If the inode is orphaned (no name via `fls`), use `ifind -p` to find its parent directory to help contextualize the recovered file's original location.

## Troubleshooting

| Symptom | Likely Cause | Action |
|---|---|---|
| `icat` outputs nothing / binary garbage to terminal | Content sent to terminal instead of redirected | Always redirect: `icat ... > outfile` |
| "Metadata not found" / invalid inode error | Wrong inode format or offset | Re-verify inode string format (`inode-type-id`) from `fls` output; confirm `-o` offset |
| Recovered file is corrupt or incomplete | Blocks overwritten (common for deleted files) | Note as partial recovery; check `istat` for allocation status and compare file size to blocks actually resident |
| `ifind -n` returns nothing for a known filename | Path typo, or file was deleted and unlinked from directory tree | Try `fls -r -d` to search deleted entries by name pattern instead |
| Timestamps in `istat` look wrong | No/incorrect timezone applied | Use `-z` with correct zone; document the zone used in reporting |

## What This Skill Must Never Do Automatically

- Never run these tools against a live/original device — only against a verified image or read-only mounted copy.
- Never present recovered content from an unallocated inode as complete/authentic without checking `istat` allocation status and noting possible overwrite/partial recovery.
- Never skip hashing of extracted (`icat`) output before it is treated as an evidence artifact.
- Never guess or fabricate an inode number or offset; require it to come from `fls`, `mmls`, or `ifind` output, or explicit user-supplied case data.
- Never invent flag syntax not confirmed via `-h`/man page; explicitly flag uncertainty (e.g., exact `-s` slack behavior) rather than asserting it as fact.

