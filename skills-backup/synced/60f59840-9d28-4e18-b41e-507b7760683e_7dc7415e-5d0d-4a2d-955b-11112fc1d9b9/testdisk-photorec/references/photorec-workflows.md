# PhotoRec Workflows

PhotoRec carves files by signature from raw sectors. It never writes to the source. Consequences: works on any filesystem or none at all, but recovered files have generated names (`f<sector>.ext`), no directory structure, no timestamps from the fs, and fragmented files often come back broken.

## 1. Standard carving run

1. `sudo photorec` (or `sudo photorec disk.img`)
2. Select disk → select partition, or **[Whole disk]** / **No partition** for formatted/raw media
3. Filesystem type prompt: **ext2/ext3** only if source fs really is ext-family (changes block-alignment assumptions); **Other** for FAT/NTFS/exFAT/HFS+/everything else
4. **Free** vs **Whole**:
   - `Free` = carve unallocated space only → deleted-file recovery on an intact fs (much faster, no duplicates of live files). Only available for fs types PhotoRec understands (ext2/3/4, FAT, NTFS)
   - `Whole` = every sector → formatted/corrupted media
5. Destination — must be on a different disk; PhotoRec creates `recup_dir.N` folders there (500 files per folder)
6. Run. Status screen shows elapsed/remaining and per-family counts

## 2. File Opt — narrow the families

Before starting, **File Opt** menu: `s` toggles all off, then space-enable just what's wanted (e.g., only `jpg`, `png`, `cr2`, `mp4`). Narrowing:
- massively cuts output volume and sort time
- reduces false positives (`txt` and `gz` are noisy carvers — disable unless needed)

`jpg` family also covers most camera thumbnails; RAW formats have their own entries (`cr2`, `nef`, `arw`, `dng`, `orf`, `rw2`...). For "recover my photos" enable: jpg, png, heic (under `mov`/`ftyp` family in older versions — 7.2 has it), tif, plus the camera's RAW format.

## 3. Sessions — pause and resume

PhotoRec writes `photorec.ses` in its working directory. If interrupted (Ctrl-C, crash, reboot), rerun `photorec` from the same directory and it offers to resume. Long carves on multi-TB disks should be run in `tmux`/`screen`. Don't delete `photorec.ses` mid-job.

## 4. Expert mode options worth knowing

Enable in Options → Expert mode: allows setting block size manually (useful when the fs is gone but you know it was 4096-byte clusters — correct block size improves carve alignment and success rate), and low-level "Paranoid" settings:
- `Paranoid: Yes` (default) — validates carved files, discards broken ones
- `Paranoid: Yes (Brute force enabled)` — attempts reassembly of some fragmented JPEGs; much slower, use as a second pass targeting only `jpg` if the first pass returned truncated photos
- `Keep corrupted files: Yes` — for forensic completeness; combine with a second disk of free space

## 5. Non-interactive / scripted

```bash
sudo photorec /log /d /path/to/output /cmd /dev/sdX partition_none,options,mode_ext2,fileopt,everything,disable,jpg,enable,search
```
Chunks: `partition_none` (whole disk) or `partition_i` (i-th), `options` then option toggles, `fileopt` then `everything,disable` + per-family `enable`, finally `search`. Good for demo runs in the sandbox; for real recoveries the TUI is safer because the user confirms each choice.

`fidentify /path/to/file` — identifies a file by the same signature DB; handy for "what did PhotoRec just give me" or checking unknown blobs.

## 6. Volume math (set expectations)

Whole-disk carve output can exceed the used space of the original fs (old deleted data, false positives). Rule of thumb: destination free space ≥ size of the *source device*, not the size of the files the user hopes for. If space is tight: narrow File Opt hard, or carve `Free` space only.

## 7. Reading the status screen / results

- Per-family counts update live; a huge `txt: 200000` count usually means txt carving noise, not real documents
- `Reading sector X/Y, N files found` stuck at the same sector for a long time on a real disk = read errors → stop, ddrescue
- After completion, `report.xml` (if enabled) lists carved files with offsets — useful for forensics
- Truncated JPEGs (grey bottom half) = fragmentation; try the brute-force second pass (section 4)

## 8. SSD reality check

TRIM zeroes deleted blocks, typically within minutes. On an internal SSD with a TRIM-enabled fs (default on virtually all modern systems), PhotoRec on deleted files returns almost nothing. USB thumb drives and SD cards generally don't receive TRIM — recovery prospects there are normal. Say this to the user *before* a long pointless carve.
