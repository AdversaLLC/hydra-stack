---
name: testdisk-photorec
description: Data recovery with TestDisk and PhotoRec (CGSecurity). Use whenever the user mentions TestDisk, PhotoRec, testdisk, photorec, qphotorec, fidentify, lost partition, deleted partition, corrupted partition table, broken boot sector, unbootable disk, deleted files, formatted drive, file carving, "recover my photos", "recover files from SD card/USB/HDD/SSD", recup_dir folders, photorec.ses sessions, testdisk.log interpretation, or ddrescue imaging before recovery. Covers safe recovery workflow (image first, never write to source), TestDisk partition/boot-sector repair, PhotoRec carving and file-family selection, interpreting logs the user pastes, sorting the recovered recup_dir mess, and running sandbox demos on disk images. Fire this even for casual phrasings like "I deleted my photos" or "my partition disappeared".
---

# TestDisk & PhotoRec — Data Recovery

TestDisk and PhotoRec are packaged together (current stable: 7.2, Feb 2024; 7.3 WIP builds exist on cgsecurity.org). TestDisk repairs partition tables, recovers deleted partitions, fixes boot sectors, and can undelete from FAT/exFAT/NTFS/ext2. PhotoRec is a signature-based file carver — it ignores the filesystem entirely and recovers ~480 file extensions from raw sectors, which means it works on formatted/corrupted media but loses filenames and directory structure.

This skill runs in claude.ai: the actual recovery happens on the **user's machine**. Claude's job is to (1) pick the right tool, (2) generate exact command sequences and menu navigation for the user's OS, (3) interpret pasted output/logs, (4) post-process recovered files with the bundled script, and (5) optionally demo on a loopback disk image in the bash sandbox.

## Iron rules (state these before any recovery work)

1. **Stop writing to the affected disk immediately.** Every write risks overwriting recoverable data. If it's the system disk, shut down and work from a live USB.
2. **Recover TO a different disk** than the one being recovered FROM. PhotoRec enforces this mindset; enforce it in every command you generate.
3. **Failing hardware → image first, recover from the image.** If the drive clicks, throws I/O errors, or SMART shows pending/reallocated sectors climbing, do NOT run recovery on the raw device. Use ddrescue:
   ```bash
   sudo ddrescue -f -n /dev/sdX disk.img mapfile.log   # fast pass, skip bad areas
   sudo ddrescue -f -r3 /dev/sdX disk.img mapfile.log  # retry bad areas 3x
   ```
   Then point testdisk/photorec at `disk.img`.
4. **TestDisk writes are destructive if wrong.** Never tell the user to hit `Write` on a partition table until Quick Search + Deeper Search results have been listed with `P` and the files look right. When in doubt: back up the current partition table first (TestDisk offers this), or work on an image.
5. **Root is required** for raw device access on Linux (`sudo testdisk`, `sudo photorec`).

## Decision: which tool?

| Symptom | Tool |
|---|---|
| Partition disappeared / "disk not initialized" / wrong size shown | TestDisk |
| Won't boot, filesystem intact | TestDisk (boot sector / MBR repair) |
| Deleted files, filesystem healthy, FAT/exFAT/NTFS/ext2 | TestDisk undelete first (keeps filenames), PhotoRec as fallback |
| Deleted files on ext3/ext4, btrfs, or any fs TestDisk can't undelete | PhotoRec (or `extundelete`/`ext4magic` — mention but don't primary) |
| Formatted / reformatted drive | PhotoRec (TestDisk deeper search may find the old partition too — try it first, it preserves structure) |
| Corrupted SD card / camera card | PhotoRec |
| Only need specific file types (e.g., just JPGs) | PhotoRec with File Opt narrowed |
| Unknown file blobs — "what is this file?" | `fidentify` (ships with the package) |

## Install (user's machine)

- Arch/Garuda: `sudo pacman -S testdisk` (one package provides both)
- Debian/Ubuntu: `sudo apt install testdisk`
- Windows/macOS: portable zip from cgsecurity.org — no installer, just extract and run
- Live environment: SystemRescue ISO includes both; good for system-disk recovery

## Workflows

Read the reference file matching the task — don't improvise menu paths from memory:

- `references/testdisk-workflows.md` — partition recovery, boot sector repair, MFT repair, undelete, log interpretation
- `references/photorec-workflows.md` — carving runs, file-family selection, session pause/resume, free-space-only mode, expert options, output volume math

## Post-recovery: taming recup_dir

PhotoRec dumps everything into `recup_dir.1 … recup_dir.N` with meaningless names (`f1234567.jpg`). Run the bundled sorter on the user's machine (or in the sandbox if they upload the output):

```bash
python3 scripts/sort_recovered.py /path/to/recovery_output --by ext        # sort into folders per extension
python3 scripts/sort_recovered.py /path/to/recovery_output --by date      # EXIF/mtime date folders (YYYY-MM)
python3 scripts/sort_recovered.py /path/to/recovery_output --dedupe       # drop byte-identical duplicates
```

Flags combine. The script is stdlib-only except optional Pillow for EXIF dates (falls back to mtime without it). It moves files by default; `--copy` preserves originals.

## Sandbox demos

The bash sandbox can install testdisk (`apt-get install -y testdisk`) and exercise both tools non-interactively on a loopback image — useful to show the user what a run looks like or to test the sorter:

```bash
dd if=/dev/zero of=/tmp/demo.img bs=1M count=64
mkfs.vfat /tmp/demo.img          # no loop mount needed for photorec
# copy files in via mtools or mount if loop devices available, delete them, then:
photorec /log /d /tmp/out /cmd /tmp/demo.img partition_none,options,search
```

No raw physical devices exist in the sandbox — demos only. Real recovery is always on the user's hardware.

## Interpreting pasted output

When the user pastes `testdisk.log`, PhotoRec status screens, or partition listings: identify partition table type (Intel/MBR vs EFI/GPT), flag any partition marked with a structure warning, compare found geometry against expected sizes, and check the "files found" counts per family in PhotoRec output. Details and common log patterns are in the reference files.

## Anti-patterns

- Suggesting recovery writes to the source disk — never.
- Running PhotoRec when TestDisk undelete would preserve filenames — check the filesystem first.
- Telling the user to `Write` a found partition table without listing files (`P`) first.
- Running either tool on a mounted target partition — unmount first.
- Promising recovery success — fragmentation, TRIM on SSDs, and overwrites make results probabilistic. SSDs with TRIM enabled: deleted-file recovery is usually hopeless; say so early.
