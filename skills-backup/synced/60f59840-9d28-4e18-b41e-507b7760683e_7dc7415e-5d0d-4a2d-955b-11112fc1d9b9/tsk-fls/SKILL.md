---
name: "tsk-fls"
description: "Lists file and directory entries (including deleted/orphan entries) from a filesystem inside a disk image or partition using The Sleuth Kit's fls command-line tool. Trigger phrases include \"list files in this image\", \"show deleted files\", \"fls this partition\", \"enumerate directory entries\", \"recover file names\", \"show me the MFT entries as a file list\", or \"what files existed on this volume\". Covers fls syntax, offsets, recursion, and body-file output for later mactime processing. Not for GUI Autopsy workflows (see autopsy-analysis), not for extracting file content (see tsk-file-content), and not for partition-table layout (see tsk-mmls)."
---

---
name: tsk-fls
description: Lists file and directory entries (including deleted/orphan entries) from a filesystem inside a disk image or partition using The Sleuth Kit's fls command-line tool. Trigger phrases include "list files in this image", "show deleted files", "fls this partition", "enumerate directory entries", "recover file names", "show me the MFT entries as a file list", or "what files existed on this volume". Covers fls syntax, offsets, recursion, and body-file output for later mactime processing. Not for GUI Autopsy workflows (see autopsy-analysis), not for extracting file content (see tsk-file-content), and not for partition-table layout (see tsk-mmls).
---

# TSK fls — Filesystem File/Directory Listing

## Purpose

`fls` walks a filesystem's directory structures (FAT, NTFS, ext2/3/4, HFS+, ISO9660, etc.) and lists file and directory names, including entries for deleted files whose metadata has not yet been overwritten. It reads the filesystem directly rather than relying on the OS's live view, so it can surface names the live filesystem hides.

`fls` operates on a **forensic image or a partition/volume within an image** — never on the original source device. Always work from a verified, hash-matched image copy, consistent with `paladin-forensic-workflow`.

## Command Syntax

```
fls [options] image [inode]
```

Where `image` is the path to the disk/partition image (or a segmented image set), and the optional `inode` restricts listing to a specific directory inode.

### Common Options (verify against `fls -h` before relying on any flag in a report)

| Flag | Purpose |
|---|---|
| `-r` | Recurse into subdirectories |
| `-p` | Show full path for each file (use with `-r`) |
| `-a` | Include `.` and `..` entries |
| `-d` | Display only deleted entries |
| `-u` | Display only undeleted (allocated) entries |
| `-l` | Long format (more metadata columns: size, timestamps) |
| `-m dir/` | Output in body-file format for `mactime`, with `dir/` prepended to paths |
| `-o offset` | Sector offset to the start of the filesystem/partition within the image (when the image contains a full volume system, not a single partition) |
| `-f fstype` | Force a specific filesystem type instead of autodetection |
| `-i imgtype` | Specify image format (raw, ewf/E01, aff, vmdk, vhd) if autodetection fails |
| `-z zone` | Set timezone for displayed timestamps in `-l` mode |
| `-s seconds` | Adjust timestamps by a fixed offset |

Run `fls -h` or consult the sleuthkit.org man page to confirm exact flag availability for the installed TSK version before quoting syntax in a report — flag sets have shifted slightly across TSK 3.x/4.x releases.

### Finding the offset

If the image contains a partition table rather than a single filesystem, first run `mmls` (see `tsk-mmls`) to find the starting sector of the partition of interest, then pass that value to `fls -o`.

## Typical Workflow

1. Verify you are working against a validated image (hash-checked), not the source device.
2. If the image is a full disk (not a single partition), run `mmls image.E01` to identify partition offsets.
3. List the root directory, recursively, with full paths:
   ```
   fls -o 2048 -r -p image.E01
   ```
4. Focus on deleted entries only:
   ```
   fls -o 2048 -r -p -d image.E01
   ```
5. Generate a body file for timeline creation:
   ```
   fls -o 2048 -r -m / image.E01 > body.txt
   ```
   The resulting `body.txt` is later fed into `mactime` (see `tsk-mactime`) to build a MAC(B) timeline.
6. To list contents of one directory by inode number, pass that inode as the final argument:
   ```
   fls -o 2048 image.E01 5-128-4
   ```

## Reading fls Output

Default output columns typically show: entry type flag (`r`/`d` for file/directory, `+` prefixed types for slack/orphan entries), allocation flag (`*` prefix means deleted/unallocated), inode/metadata address, and name. Example:

```
r/r * 12-128-1:	deleted_document.docx
d/d 15:	Documents
```

The `*` marks an unallocated (deleted) entry — the name may still be valid even though content may be partially or fully overwritten. Always cross-check with `istat` (see `tsk-file-content`) before asserting a file is recoverable.

## Troubleshooting

| Symptom | Likely Cause | Action |
|---|---|---|
| "Cannot determine file system type" | Wrong `-o` offset or unsupported/corrupt filesystem | Re-run `mmls` to confirm offset; try `-f` to force a type |
| Output looks empty or truncated | Recursion not enabled | Add `-r`; confirm inode argument wasn't restricting scope |
| Garbled/incorrect filenames | Wrong character encoding assumption for the filesystem | Check TSK version supports the filesystem's encoding (e.g., NTFS UTF-16, HFS+ UTF-8) |
| Tool reports unsupported image format | `-i` type not auto-detected | Specify `-i` explicitly (e.g., `-i ewf`) |
| Timestamps look off by hours | Timezone not set | Use `-z` with the correct zone identifier |

## What This Skill Must Never Do Automatically

- Never run `fls` (or any TSK tool) directly against a physical source device — only against a verified forensic image or read-only mounted copy.
- Never modify, write to, or "repair" the image to make `fls` run.
- Never silently invent or guess an offset — always derive it from `mmls` output or documented case notes, and state the source of the offset used.
- Never present inferred/deleted filenames as confirmed recoverable content without checking actual data recoverability (`icat`/`istat`).
- Never fabricate flag syntax not confirmed by `fls -h`/man page; flag uncertainty explicitly instead.

