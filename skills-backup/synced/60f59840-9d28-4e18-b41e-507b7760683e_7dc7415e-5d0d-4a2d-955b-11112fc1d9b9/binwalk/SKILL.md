---
name: "binwalk"
description: "Firmware and embedded-file signature scanning/extraction with binwalk — identifies and extracts embedded files and executable code (filesystems like SquashFS/JFFS2/CramFS, compression formats like gzip/LZMA/zlib, bootloaders, kernel images, certificates, and other magic-signature-recognizable blobs) inside firmware images, embedded-device dumps, router/IoT firmware, and other binary blobs. Use when the user says \"run binwalk on this firmware\", \"extract the filesystem from this firmware image\", \"what's inside this .bin file\", \"analyze this router/IoT dump\", or \"find embedded files in this binary\". Not intended for general disk/partition image carving of everyday photos/documents — for that use foremost, scalpel, or bulk_extractor; not for TestDisk/PhotoRec-style partition or deleted-file recovery (use the testdisk-photorec skill instead)."
---

---
name: binwalk
description: Firmware and embedded-file signature scanning/extraction with binwalk — identifies and extracts embedded files and executable code (filesystems like SquashFS/JFFS2/CramFS, compression formats like gzip/LZMA/zlib, bootloaders, kernel images, certificates, and other magic-signature-recognizable blobs) inside firmware images, embedded-device dumps, router/IoT firmware, and other binary blobs. Use when the user says "run binwalk on this firmware", "extract the filesystem from this firmware image", "what's inside this .bin file", "analyze this router/IoT dump", or "find embedded files in this binary". Not intended for general disk/partition image carving of everyday photos/documents — for that use foremost, scalpel, or bulk_extractor; not for TestDisk/PhotoRec-style partition or deleted-file recovery (use the testdisk-photorec skill instead).
---

# Binwalk

## What this tool does

Binwalk is a tool for analyzing, reverse engineering, and extracting content from binary firmware images and other embedded-device blobs. Its core function is scanning a file for known "magic" byte signatures (headers of filesystems, compression formats, executables, certificates, etc.) at any offset — not just offset 0 — and reporting what it finds along with the offset. It is heavily used in embedded/IoT/firmware forensics and reverse engineering, distinct from the disk-image carving tools (foremost/scalpel/bulk_extractor) which target general-purpose disk images.

Common things binwalk identifies and can extract:
- Filesystem images embedded in firmware: SquashFS, JFFS2, CramFS, YAFFS2, UBI/UBIFS, romfs, and others
- Compressed data streams: gzip, bzip2, LZMA, LZO, zlib
- Compiled code / kernel images: U-Boot images, Linux kernel images, ELF binaries
- Archive formats: ZIP, TAR, CPIO
- Cryptographic material: certificates, RSA keys
- Generic file signatures similar to what `file`/`magic` recognize, but scanned at every offset in the blob rather than just the start

Binwalk has an extraction mode (historically `-e`, and a `--dd` mode for manual carve-by-signature) that can automatically carve out identified sections into an output directory, and in many installations can also recursively extract nested filesystems (e.g., unpacking a SquashFS found inside firmware, then further unpacking files found inside that). Some versions/plugins can invoke external extraction utilities (e.g., `unsquashfs`, `jefferson` for JFFS2, `sasquatch`) as helpers — these are separate dependencies whose presence should not be assumed without checking.

**Presence note:** if this skill was told binwalk is installed on the PALADIN system, that was reported by the user via their own system inventory, not independently verified here. Confirm with `binwalk --help`/`which binwalk`, and separately confirm whether extraction helper dependencies (unsquashfs, jefferson, sasquatch, etc.) are present, since binwalk's automatic extraction quality depends heavily on them.

## Command syntax (verify against `binwalk --help`/man page for your installed version — binwalk 2.x and 3.x have differing flags)

Basic scan (identify signatures, no extraction):

```
binwalk <firmware_image>
```

Common flags (verify exact behavior with `--help`, since binwalk's Python 2.x-era "binwalk 2.x" and the newer Rust-based "binwalk 3.x" rewrite differ in flags and behavior):

- `-e` / `--extract` — automatically extract recognized signatures into a subdirectory (historically named after the input file, e.g. `_firmware.bin.extracted/`).
- `-M` / `--matryoshka` — recursively scan extracted files for further embedded signatures/filesystems (nested extraction).
- `-d` / depth-limiting options — control recursion depth in matryoshka mode, where supported.
- `--dd='<signature>:<extension>'` — manually carve out a specific signature type to a file with the given extension (name/syntax varies by version — verify before use).
- `-B` — scan for common binary/magic signatures (often the default "signature scan").
- `-A` — scan for executable/architecture opcodes (CPU architecture identification), where supported.
- `-E` — calculate entropy across the file, useful for spotting encrypted/compressed regions (high entropy) versus plain data.
- `-o <dir>` / `-C <dir>` — specify an output/extraction directory in versions that support overriding the default extracted-files location.

Because binwalk's flags and defaults changed meaningfully between the classic Python implementation and the newer 3.x rewrite, do not assume a flag exists or behaves a specific way — check `binwalk --help` on the actual installed version first, and note in any generated commands if a flag's availability is uncertain.

## Realistic workflow

1. **Work only from a verified copy of the firmware/binary image**, not the original acquisition media where applicable — if the firmware was dumped from a chip/device, ensure a verified copy exists before running extraction passes against it.
2. **Choose an output/extraction directory on separate media from the source image** — binwalk's `-e`/extraction modes write new files (extracted filesystems, carved blobs) and must not write back into the same directory as the evidence copy in a way that could be confused with original evidence, and never onto write-blocked evidence media.
3. Run an initial signature scan without extraction to see what's present:
   ```
   binwalk /mnt/casework/firmware_copy.bin
   ```
4. Review the offset/signature report. Decide what's worth extracting (e.g., a SquashFS filesystem, a kernel image).
5. Run extraction into a dedicated case output directory, e.g.:
   ```
   cd /mnt/casework/case001_binwalk_out
   binwalk -e --matryoshka /mnt/casework/firmware_copy.bin
   ```
6. Inspect the resulting `*_extracted` (or similarly named) directory tree for unpacked filesystem contents, config files, credentials, certificates, or further nested images worth another carving pass (foremost/scalpel/bulk_extractor) if a generic filesystem image was extracted.
7. Note which extractions succeeded cleanly vs. partially (corrupted/truncated filesystem extraction is common with firmware that uses proprietary or slightly-nonstandard compression/headers).
8. Document binwalk version, exact command line, source image hash, and output location for the case record (`forensic-reporting`).

## Troubleshooting

| Symptom | Likely cause / next step |
|---|---|
| Signature scan finds nothing meaningful | Firmware may be encrypted or use a proprietary/obfuscated header; try `-E` entropy scan to check for high-entropy (likely encrypted/compressed) regions as a diagnostic. |
| `-e` extraction reports a filesystem type but produces empty/corrupt output | The extraction helper for that filesystem (e.g., `unsquashfs`, a JFFS2 tool) may be missing, outdated, or unable to handle a vendor-specific variant — check whether the helper is installed and up to date, and check binwalk's own error output. |
| Matryoshka recursive extraction runs very long or produces excessive nested output | Common on binaries with many false-positive signature matches; consider a non-recursive pass first, review results, then selectively re-run extraction on specific offsets/files. |
| Unsure whether a flag like `--dd` is available/how it's formatted | Flag syntax differs between binwalk versions (classic Python vs. 3.x rewrite) — check `binwalk --help` on the installed binary rather than assuming. |
| Extracted filesystem is missing expected files | Extraction may have only partially succeeded (common with corrupted dumps or unusual padding); try manual carving with `--dd` at a specific offset identified in the initial scan, or fall back to `binwalk -B` output for exact offsets to hand to `dd`/`foremost` manually. |

## What this skill must never do automatically

- Never write extraction output back onto the same media as the original evidence/acquisition or any write-blocked evidence mount.
- Never overwrite a prior case's extraction output directory without explicit user confirmation.
- Never assume extraction helper tools (unsquashfs, jefferson, sasquatch, etc.) are installed — confirm, or note their absence, since silent partial extraction can look like a clean success.
- Never present automatically extracted firmware contents as a complete/authoritative unpacking without noting that certain filesystem types or vendor-customized formats may extract only partially.
- Never invent binwalk flag syntax not confirmed via `--help`/man page for the actual installed version — flag this explicitly given the known 2.x/3.x differences.
- Never claim binwalk (or specific extraction helpers) are installed on a system beyond what the user reported from their own inventory.

