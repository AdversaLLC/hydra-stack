---
name: "exiftool-metadata"
description: "Extract and interpret embedded metadata (EXIF, IPTC, XMP, and hundreds of other format-specific metadata schemas) from images, documents, audio, and video files using ExifTool. Triggers on \"check the EXIF data\", \"what metadata is in this file\", \"run exiftool\", \"find the GPS coordinates in this photo\", \"who created this document (metadata)\", \"check for metadata cleanup/removal\", or \"compare metadata across these files\". Read-only inspection by default — removing or writing metadata requires explicit confirmation before running against any evidence file, and should always target a copy."
---

---
name: exiftool-metadata
description: Extract and interpret embedded metadata (EXIF, IPTC, XMP, and hundreds of other format-specific metadata schemas) from images, documents, audio, and video files using ExifTool (Phil Harvey). Triggers on "check the EXIF data", "what metadata is in this file", "run exiftool", "find the GPS coordinates in this photo", "who created this document (metadata)", "check for metadata cleanup/removal", or "compare metadata across these files". Read-only inspection by default — removing or writing metadata (exiftool can also edit files) requires explicit confirmation before running against any evidence file, and should always target a copy.
---

# ExifTool (Metadata Extraction)

ExifTool reads (and can write/strip) metadata across an unusually wide range of file formats — not just camera EXIF data, but IPTC, XMP, maker notes, PDF document properties, Office document metadata, audio ID3 tags, video container metadata, and more.

## Workflow

1. **Read-only extraction is safe to run directly**: `exiftool <file>` for human-readable output, or `exiftool -j <file>` for JSON. `exiftool -a -u -g1 <file>` shows all tags including duplicates, grouped by category — useful for a thorough pass.
2. **Batch/recursive extraction**: `exiftool -r -j <directory>` for JSON across a directory tree (verify current flag behavior against `exiftool -h` since output structure for batch JSON can differ from single-file JSON).
3. **GPS/location data**: `exiftool -gps:all <file>` or check for `GPSLatitude`/`GPSLongitude`/`GPSDateStamp` tags specifically — common in phone-camera photos, less common in scanned/edited images.
4. **Interpreting results — confidence discipline applies**: metadata reflects what a device/application wrote at capture/save time. It can be absent (stripped by the platform — many social media/messaging services strip EXIF on upload), inaccurate (wrong camera clock), or deliberately altered (metadata can be edited by the same tool that reads it). State findings as "the file's embedded metadata indicates X" rather than "this proves X happened," especially for authorship/location/timestamp claims.
5. **Comparing metadata across a set of files** can help establish whether files share a common source/device/software — useful for corroboration, but a match is "supporting" evidence, not "confirmed" on its own.

## Editing/removing metadata (write operations)

`exiftool -all= <file>` strips all metadata; `-GPS:all=` strips just GPS tags; specific tag writes use `-TagName=value`. **Any of these write operations require explicit confirmation before running**, must target a copy rather than the original evidence file, and should be logged (exact command, target file, before/after hash) if performed during an examination — this is consistent with the rest of this library's evidence-integrity rules.

## What this skill must never do automatically

- Write, strip, or modify metadata on an original evidence file — always work on a copy, and only after explicit confirmation.
- Treat absence of expected metadata (e.g., no GPS tag) as proof nothing happened at that location — many platforms strip this data on upload/transfer.
- Treat present metadata as unforgeable fact — note when metadata could plausibly have been edited, especially if a finding is central to a conclusion.
- Report a tag value that wasn't actually observed in real tool output.

## Troubleshooting

| Symptom | Likely cause | Steps |
|---|---|---|
| No metadata found on an image known to have been camera-shot | Platform stripped it (common on messaging apps/social media) | Note this explicitly as a limitation, not as "no metadata existed originally" |
| GPS tags present but coordinates look implausible | Camera without GPS lock defaulted to (0,0) or stale cached location, or manual EXIF editing occurred | Cross-check plausibility against other case context before treating as reliable location evidence |
| exiftool reports "Unknown file type" | Corrupted file, unsupported format, or renamed extension mismatching actual content | Check actual file type via file-signature tools separately before assuming exiftool failure means no metadata exists |
| Timestamps in metadata don't match filesystem timestamps | Expected — EXIF capture time and filesystem mtime/ctime are independent and commonly diverge (edits, transfers, timezone handling) | Document both separately; do not assume one "corrects" the other without other corroboration |

## Handoff

- Broader file-carving/recovery before metadata analysis is possible → `foremost`, `scalpel`, `bulk-extractor`.
- Steganography checks alongside metadata review → `steganography-analysis`.
- Correlating file timestamps with a broader timeline → `tsk-mactime`, `plaso-log2timeline`.
- Writing up findings with appropriate confidence grading → `forensic-reporting`.

