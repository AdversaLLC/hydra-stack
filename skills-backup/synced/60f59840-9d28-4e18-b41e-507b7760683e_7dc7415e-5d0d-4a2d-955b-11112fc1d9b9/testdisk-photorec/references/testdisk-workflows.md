# TestDisk Workflows

TestDisk is an ncurses TUI. Navigation: arrow keys, Enter to select, `q` to go back. It logs everything to `testdisk.log` in the working directory — always tell the user to keep it and paste it if stuck.

## 1. Lost / deleted partition recovery

The bread-and-butter workflow:

1. `sudo testdisk` (or `sudo testdisk disk.img` to work on an image)
2. **Create** log (or Append if resuming)
3. Select the disk — match by size, not by device name guesswork
4. Partition table type — TestDisk's auto-detect is almost always right. `Intel` = MBR, `EFI GPT` = GPT. Only override if you know the auto-detect is wrong (e.g., GPT disk with a leftover protective MBR misread)
5. **Analyse** → shows current partition structure
6. **Quick Search** → lists found partitions
   - Highlight a found partition and press **P** to list its files. If files show correctly, the partition is good
   - Green = recoverable as-is; struck-through / red entries in the file list = deleted files
   - Left/right arrows change a partition's type: `P`=primary, `*`=bootable, `L`=logical, `D`=deleted (won't be written)
7. If Quick Search misses it: **Deeper Search** (scans every cylinder for backup boot sectors and superblocks — slow, hours on big disks)
8. Once the listing looks right: **Write**, confirm, reboot/re-read partition table (`sudo partprobe` or reboot)

Common trap: Deeper Search finds *many* phantom partitions (old installs, backup superblocks). The ones to keep are those whose `P` file listing shows the expected data. Mark everything else `D`.

## 2. FAT/NTFS boot sector repair

Symptom: partition exists but won't mount / "invalid boot sector".

1. Analyse → select partition → **Advanced** menu instead of Quick Search
2. **Boot** option:
   - `Backup BS` / status line shows whether boot sector and its backup match
   - If backup is OK and primary is bad: **Restore BS** (copies backup over primary)
   - If both bad on FAT: **RebuildBS** (reconstructs from filesystem structures)
3. NTFS also offers **Repair MFT** (copies MFT mirror over a damaged MFT). Only helps when MFT start is damaged but the mirror survived.

## 3. Undelete (keeps filenames — try before PhotoRec)

Works on FAT12/16/32, exFAT, NTFS, ext2 only.

1. Advanced → select partition → **Undelete**
2. Deleted entries appear in red. Navigate, `:` to select individual files, `a` to select all
3. **C** (capital) copies selected to a destination you choose — pick a directory on a *different* disk
4. Recovered-file health check: FAT undelete loses the first character of names and fragmented files often come back corrupt. If results are garbage, fall back to PhotoRec.

ext3/ext4: TestDisk cannot undelete these (journal zeroes the block pointers). Options: `extundelete` / `ext4magic` against an unmounted fs image (works only if inode data survives in the journal), else PhotoRec.

## 4. Image-based work

`sudo testdisk disk.img` — everything works the same; `Write` modifies the image's partition table, harmless to real hardware. This is the recommended mode for any uncertain repair: fix the image, verify by loop-mounting (`sudo losetup -fP disk.img && sudo mount /dev/loopXp1 /mnt`), and only then repeat on the real device — or just pull the files off the mounted image and never touch the original.

## 5. Reading testdisk.log

Patterns worth flagging when the user pastes a log:

- `Bad relative sector.` / `Bad ending head` — CHS geometry mismatch; usually cosmetic on modern LBA disks unless the partition also fails to list files
- `check_FAT: Unusual media descriptor` — boot sector damage → workflow 2
- `Warning: number of heads/cylinder mismatches` — disk moved between machines/USB bridges; usually ignorable, but if searches find nothing, try changing geometry (Options → Geometry) to what the log suggests
- Repeated `Read error` lines — failing hardware → STOP, ddrescue image first
- Two partitions overlapping in the found list — only one can be written; pick by file listing
- `partition: read error` on GPT — check the backup GPT at end of disk; TestDisk handles this in Analyse automatically

## 6. Non-interactive / scripted use

TestDisk has `/cmd` syntax but it's limited and risky for writes. For automation prefer: `testdisk /list /dev/sdX` (prints partition structure, no TUI, safe read-only) — good first diagnostic to ask the user to run and paste.
