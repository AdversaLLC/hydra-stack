---
name: "tsk-recover"
description: "Recovers files from a filesystem inside a disk image to a local output directory, preserving directory structure where possible, using The Sleuth Kit's tsk_recover command-line tool. Trigger phrases include \"recover all files from this image\", \"extract everything to a folder\", \"tsk_recover this partition\", \"bulk export files from the image\", \"recover deleted files to disk\", or \"dump this filesystem to a directory\". Not for GUI Autopsy workflows (see autopsy-analysis), not for single-file extraction by inode (see tsk-file-content), and not for unallocated/slack space carving (see tsk-block-analysis)."
---

---
name: tsk-recover
description: Recovers files from a filesystem inside a disk image to a local output directory, preserving directory structure where possible, using The Sleuth Kit's tsk_recover command-line tool. Trigger phrases include "recover all files from this image", "extract everything to a folder", "tsk_recover this partition", "bulk export files from the image", "recover deleted files to disk", or "dump this filesystem to a directory". Not for GUI Autopsy workflows (see autopsy-analysis), not for single-file extraction by inode (see tsk-file-content), and not for unallocated/slack space carving (see tsk-block-analysis).
---

# TSK tsk_recover — Bulk File Recovery to a Directory

## Purpose

`tsk_recover` walks a filesystem inside an image and copies out files (allocated and, optionally, deleted-but-recoverable) to a destination directory on the examiner's workstation, reconstructing the original directory structure where metadata allows. This is the bulk/batch counterpart to the single-file, inode-targeted extraction done with `icat` (see `tsk-file-content`).

Always run against a verified forensic image or read-only mounted copy — never the original source device. The **destination** directory must be on examiner-controlled storage (a case working directory), never written back onto the evidence image or original media.

## Command Syntax

```
tsk_recover [options] image output_directory
```

| Flag | Purpose |
|---|---|
| `-a` | Recover only allocated files (skip deleted entries) |
| `-e` | Recover all files, including deleted ones (verify exact flag meaning against `tsk_recover -h`, as allocated-vs-all default behavior has been documented inconsistently across versions) |
| `-o offset` | Sector offset to the filesystem within the image (from `mmls`) |
| `-i imgtype` | Image format if not auto-detected |
| `-f fstype` | Force filesystem type |
| `-d dir_inode` | Restrict recovery to a specific directory inode and its contents rather than the whole filesystem |
| `-v` | Verbose output during recovery |

Because the exact semantics of the allocated/deleted flags have shifted across TSK releases, run `tsk_recover -h` on the installed system and confirm current behavior before stating in a report which flag was used and what it recovered.

## Typical Workflow

1. Confirm you are working from a verified, hash-matched forensic image.
2. If the image is a full disk, run `mmls` to find the target partition's offset (see `tsk-mmls`).
3. Create a dedicated, empty output directory on case storage — never reuse a directory that mixes evidence output with unrelated files.
4. Run the recovery:
   ```
   tsk_recover -o 2048 image.E01 /case/output/recovered_files/
   ```
5. To include deleted files (if supported by the installed version's flag set):
   ```
   tsk_recover -o 2048 -e image.E01 /case/output/recovered_files_all/
   ```
6. After recovery completes, generate hashes of the recovered file set (e.g., a hash manifest) and log the exact command line used, for chain-of-custody and reproducibility.
7. Cross-reference the recovered file count/listing against `fls -r` output for the same image to confirm completeness and to identify anything `tsk_recover` could not reconstruct (e.g., deleted files whose original path/name could not be resolved).

## Interpreting Results

- Files recovered from deleted/unallocated entries may have generic or reconstructed names/paths if original metadata was partially overwritten — do not assume the output directory structure exactly matches the original file's live location without cross-checking `fls`/`istat`.
- A file's presence in the output directory does not by itself confirm content integrity — partially overwritten deleted files may recover as truncated or corrupt data. Verify recovered file sizes/hashes and, where feasible, open/validate the file format.

## Troubleshooting

| Symptom | Likely Cause | Action |
|---|---|---|
| "Cannot determine file system type" | Wrong `-o` offset or unsupported filesystem | Re-verify offset via `mmls`; confirm filesystem type via `fsstat` |
| Recovered directory structure looks flattened / missing paths | Deleted files whose parent directory entries could not be resolved | Cross-check with `fls -r -p -d` and `ifind -p` for orphaned file context |
| Some expected files are missing from output | Default flag scope excluded deleted files, or file was fully overwritten | Re-run with the appropriate all/deleted flag (verify against `-h`); if still missing, check `istat`/`blkstat` for overwrite status |
| Recovery is very slow on a large image | Full filesystem walk and copy of many files | Expected for large volumes; consider `-d` to scope to a specific directory if only part of the filesystem is relevant |
| Filenames appear garbled or replaced with placeholder names | Unicode/encoding handling limitation, or unresolvable deleted-entry name | Note as a known TSK limitation for that filesystem type; cross-check raw entry via `fls` |

## What This Skill Must Never Do Automatically

- Never run `tsk_recover` against the original source device — only a verified forensic image or read-only mounted copy.
- Never write output into any location on the evidence image, source media, or shared/uncontrolled storage — always a dedicated case output directory.
- Never overwrite an existing output directory's contents without explicit confirmation, since that could destroy previously recovered evidence output.
- Never claim 100% recovery completeness without cross-checking against `fls` output; state explicitly what was and wasn't recoverable.
- Never fabricate flag syntax/behavior not confirmed via `-h`/man page; explicitly flag any version-dependent uncertainty (e.g., default allocated/deleted scope).

