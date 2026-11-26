---
name: "foremost"
description: "Signature-based file carving with foremost, recovering files (JPEG, PNG, GIF, PDF, DOC/OLE, ZIP, MPEG, AVI, WAV, EXE, and other types configurable via magic headers/footers) from raw disk images or partitions by scanning for file headers and footers rather than relying on filesystem metadata. Use when the user says \"carve files with foremost\", \"recover deleted photos from this image with foremost\", \"run foremost on this image\", \"extract files by signature\", or asks to recover data from a corrupted/reformatted filesystem where directory structures are gone. Do not use for TestDisk/PhotoRec workflows (use the testdisk-photorec skill instead) and prefer scalpel (see the scalpel skill) when the user wants faster carving, a large custom signature configuration, or carving across multiple CPU cores/threads."
---

---
name: foremost
description: Signature-based file carving with foremost, recovering files (JPEG, PNG, GIF, PDF, DOC/OLE, ZIP, MPEG, AVI, WAV, EXE, and other types configurable via magic headers/footers) from raw disk images or partitions by scanning for file headers and footers rather than relying on filesystem metadata. Use when the user says "carve files with foremost", "recover deleted photos from this image with foremost", "run foremost on this image", "extract files by signature", or asks to recover data from a corrupted/reformatted filesystem where directory structures are gone. Do not use for TestDisk/PhotoRec workflows (use the testdisk-photorec skill instead) and prefer scalpel (see the scalpel skill) when the user wants faster carving, a large custom signature configuration, or carving across multiple CPU cores/threads.
---

# Foremost

## What this tool does

Foremost is a console-based file carving utility originally written for the U.S. Air Force Office of Special Investigations. It scans a raw stream of bytes — a disk image, partition image, or raw device — for known file **headers** and, for some file types, **footers**, and extracts (carves) matching regions as individual files. It does not depend on filesystem metadata (MFT, inode tables, directory entries), so it can recover data even when the filesystem is damaged, reformatted, or the image is a raw unallocated-space dump.

Foremost ships with a default configuration (`foremost.conf`, typically at `/etc/foremost/foremost.conf` or `/usr/local/etc/foremost.conf` depending on distro packaging) that defines signatures for common types: jpg, gif, png, bmp, avi, exe, mpg, wav, riff, wmv, mov, pdf, doc, zip, rar, htm, cpp, and others. You can enable/disable types or add custom signatures by editing this config or supplying your own with `-c`.

**Presence note:** if this skill was told foremost is installed on the PALADIN system, that was reported by the user via their own system inventory — Claude has not independently verified the binary, version, or config file location on that specific system. Confirm with `foremost -V` or `which foremost` before relying on it.

## Command syntax (verify against `foremost -h` for your installed version)

Basic invocation:

```
foremost -i <image_or_device> -o <output_dir>
```

Common flags (verify exact behavior with `foremost -h`, since flag sets have drifted slightly across packaged versions):

- `-i <file>` — input file (image or raw device path). Foremost reads this; it is never written to.
- `-o <dir>` — output directory. **Must not exist yet, or must be empty** — foremost historically refuses to write into a non-empty existing directory to avoid clobbering prior results.
- `-t <types>` — comma-separated list of file types to search for (e.g. `-t jpg,pdf,doc`), matching names in the config file. Omit to use the config's default enabled set.
- `-c <config>` — path to an alternate configuration file defining signatures.
- `-q` — "quick mode": only search at filesystem block boundaries (typically 512-byte aligned), much faster but can miss files that don't start on a block boundary (common in raw carving of unallocated space or non-standard block sizes).
- `-Q` — quiet, suppress output to screen.
- `-v` — verbose mode.
- `-d` — indirect block detection (relevant to certain filesystem-aware carving of UNIX/Linux filesystems).
- `-b <size>` — set block size.
- `-s <num>` — skip the first `num` blocks/bytes of the input before starting.

Do not assume any flag beyond what you can verify with `-h`/`man foremost` on the actual installed binary — treat the above as a well-known baseline, not a guarantee for every packaged version.

## Realistic workflow

1. **Never carve from the original evidence media.** Work only from a verified forensic image (e.g., an `.dd`/`.E01`/raw image produced and hash-verified per the `paladin-forensic-workflow` skill). If you only have the physical device, image and verify it first.
2. **Mount/attach the image read-only, or point foremost directly at the image file** — foremost reads a flat file or device node, it does not require the filesystem to be mounted.
3. **Choose an output directory on separate media from the evidence** — e.g., an examiner's working/scratch drive, never back onto the source disk, the image's own volume, or write-blocked evidence media. This preserves evidence integrity and avoids any accidental write path back to the source.
4. Run foremost, e.g.:
   ```
   foremost -t jpg,png,pdf,doc,zip -i /mnt/evidence_ro/case001.dd -o /mnt/casework/case001_foremost_out
   ```
5. Inspect results: foremost creates subdirectories per file type (e.g. `jpg/`, `pdf/`) plus an `audit.txt` file summarizing what was carved, offsets, and sizes.
6. Review `audit.txt` for carve counts and any errors/truncated files noted.
7. Validate carved output — many carved files will be partial, corrupted, or false positives (a signature match that isn't really a file of that type). Open/hash/triage carved files before treating them as evidence-grade recoveries.
8. Document the exact command line, foremost version, config file used (and its hash if custom), input image hash, and output directory in the case notes — see the `forensic-reporting` skill for writeup structure.

## Troubleshooting

| Symptom | Likely cause / next step |
|---|---|
| "ERROR: output directory already exists" (or similar) | Foremost refuses to write into an existing non-empty output dir. Choose a new empty/nonexistent output directory rather than reusing one. |
| Very slow run on a large image | Try `-q` (quick mode, block-aligned search) if acceptable for the case, or consider `scalpel` for multi-threaded carving on large images. |
| No files recovered / empty output | Confirm the file types you expect are enabled in the config (`-t` list or default config), confirm the image path/offset is correct (e.g. carving a partition image vs. a full disk image with a partition table), and confirm the image isn't encrypted/compressed. |
| Many corrupted/truncated carved files | Expected with signature-only carving — footers may be missing, files may be fragmented, or the "footer" search matched unrelated bytes. Cross-check against `bulk_extractor` or `scalpel` output, and manually validate before reporting as recovered evidence. |
| Carving misses a known file type | Check whether that type's signature exists and is enabled in `foremost.conf` (or your `-c` config); add a custom header/footer entry if needed, following the config file's documented syntax — verify the exact syntax in the config file's own comments/man page rather than guessing. |
| Uncertain which flags are supported | Run `foremost -h` and/or `man foremost` on the actual system — flag support varies by build/package version. |

## What this skill must never do automatically

- Never run foremost with the evidence image itself, an alias/symlink into evidence media, or any write-blocked evidence mount as the `-o` output target.
- Never overwrite or reuse an existing case output directory without explicit user confirmation — treat prior carve output as potential evidence/work product.
- Never modify, move, or delete the source image or original evidence media.
- Never invent or silently substitute foremost flags/config syntax not confirmed via `-h`, `man foremost`, or the config file's own documentation — flag this explicitly to the user instead.
- Never present carved files as confirmed/authentic recovered evidence without noting that signature-based carving produces false positives and partial/corrupted results requiring manual validation.
- Never claim foremost is installed/available on a specific system beyond what the user has reported from their own inventory.

