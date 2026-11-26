---
name: "afflib-aff4"
description: "Use afflib command-line tools (afconvert, affinfo, affcopy, affverify, affuse) and AFF4 tooling (aff4imager / aff4tool) to inspect, convert, verify, and handle Advanced Forensic Format (AFF) and next-generation AFF4 forensic images. Triggers on \"affinfo\", \"afconvert\", \"AFF4 image\", \"aff4imager\", \"convert this AFF image\", \"verify this AFF hash\", \"read AFF metadata\", or \"open an .aff/.aff4 file\". Covers AFF/AFF4 format handling specifically — for E01/EWF format tools use ewf-tools instead; for GUI-driven AFF acquisition use guymager; for general read-only mounting of an already-acquired image as a use case, see forensic-image-mounting (note affuse is an AFF-specific FUSE mount tool and is covered here for that reason, while the general mounting workflow lives in the mounting skill)."
---

---
name: afflib-aff4
description: Use afflib command-line tools (afconvert, affinfo, affcopy, affverify, affuse) and AFF4 tooling (aff4imager / aff4tool) to inspect, convert, verify, and handle Advanced Forensic Format (AFF) and next-generation AFF4 forensic images. Triggers on "affinfo", "afconvert", "AFF4 image", "aff4imager", "convert this AFF image", "verify this AFF hash", "read AFF metadata", or "open an .aff/.aff4 file". Covers AFF/AFF4 format handling specifically — for E01/EWF format tools use ewf-tools instead; for GUI-driven AFF acquisition use guymager; for general read-only mounting of an already-acquired image as a use case, see forensic-image-mounting (note affuse is an AFF-specific FUSE mount tool and is covered here for that reason, while the general mounting workflow lives in the mounting skill).
---

# afflib / AFF4 tools

**AFF** (Advanced Forensic Format) is an open forensic image container format, developed as a patent-unencumbered alternative to proprietary formats. **AFF4** is a substantially redesigned successor format (a different on-disk structure, not just a version bump) intended to handle very large images, distributed/segmented storage, and richer metadata than AFF1. Tooling for the two is largely separate: `afflib` (`afconvert`, `affinfo`, `affcopy`, `affverify`, `affuse`, `affsegment`, etc.) targets classic AFF; `aff4imager`/`aff4tool`/the AFF4 Python/Go tooling targets AFF4. Do not assume the two tool sets share flags or that an AFF file can be opened directly by AFF4-only tooling or vice versa.

Presence of these tools on this PALADIN system was reported by the user via their own system inventory, not independently verified by Claude.

## afflib family (classic AFF)

| Tool | Purpose |
|---|---|
| `affinfo` | Print metadata from an existing AFF file (case info, segment structure, stored hash values) — read-only, safe |
| `afconvert` | Convert between AFF and raw/dd format (in either direction), and between AFF variants | 
| `affcopy` | Copy/duplicate AFF file(s), including re-segmenting | 
| `affverify` | Verify stored hash(es)/signature integrity of an AFF file — read-only, safe |
| `affuse` | Mount an AFF file via FUSE as a virtual raw device for read access |
| `affsegment` | Inspect/manipulate individual AFF segments (lower-level; used less often in routine workflows) |

Exact flag syntax for each of these should be verified against `<tool> --help` or `man <tool>` on the installed system before being relied on in a report — the tool list and general purpose above reflect documented libafflib functionality, not a live version check.

### Typical read-only inspection
```
affinfo case001_drive1.aff
```
Safe to run without confirmation — prints metadata and stored hashes only.

### Typical verification
```
affverify case001_drive1.aff
```
Read-only with respect to the image; report the actual pass/fail result observed, never an assumed match.

### Typical conversion (writes a new output file)
```
afconvert -o case001_drive1.dd case001_drive1.aff
```
(illustrative flag shape — confirm `-o` and direction flags against the live `--help`). This creates a new file at the destination — treat as a write operation requiring explicit confirmation of destination path before running, same as any export/convert step in this library.

## AFF4 tooling

AFF4 tooling is less standardized across distros than libafflib or libewf — the binary may be named `aff4imager`, `aff4tool`, or invoked via a Python module (e.g., `pyaff4`) depending on how it was packaged on this system. Confirm the actual invocation name and available subcommands on the installed system (`aff4imager --help` or equivalent) before presenting any specific command as fact — this skill intentionally does not assert a specific AFF4 CLI syntax as verified, since packaging varies significantly.

General AFF4 operations to expect, at a conceptual level:
- Acquiring a device or image into an AFF4 container (write operation — requires the same source/destination confirmation discipline as any acquisition tool).
- Listing the contents/streams of an AFF4 container (read-only).
- Extracting/exporting a stream from an AFF4 container to a raw file (write operation on the destination).
- Verifying hashes stored within the AFF4 container against recomputed values (read-only).

Do not guess at exact AFF4 subcommand names beyond this general shape; check `--help` on the live tool first.

## Typical workflow

1. **Identify which format and which tool family** you're actually dealing with — an `.aff` file uses afflib tools, an `.aff4` (often a directory-like container or zip-based structure) uses AFF4 tooling. Don't apply afflib flag syntax to an AFF4 container or vice versa.
2. **Read-only inspection first**: `affinfo` (AFF) or the AFF4 tool's listing/info subcommand — safe to run freely to pull real metadata into a report.
3. **Verification**: `affverify` (AFF) or the AFF4 tool's verify subcommand — read-only, report the actual result.
4. **Any acquisition, conversion, or export step that writes a new file**: confirm destination path and format explicitly before running, exactly like any other imaging/export tool in this library.
5. **Mounting for review**: `affuse` for AFF (FUSE-based), or see `forensic-image-mounting` for the general read-only mounting workflow and discipline that applies across formats.

## Troubleshooting

| Symptom | Likely cause | What to check |
|---|---|---|
| `affinfo`/`afconvert`/etc.: command not found | afflib-tools not installed or not on PATH | `which affinfo`; confirm presence rather than assuming |
| AFF4 tool binary name doesn't match expectations | Packaging varies (`aff4imager` vs `aff4tool` vs Python module) | Check what's actually installed (`which aff4imager`, `pip show pyaff4`, or equivalent) before assuming a specific binary name |
| `affverify` or AFF4 verify reports mismatch | Image altered/corrupted since acquisition, incomplete segment set | Confirm all segments/container parts are present before concluding tampering |
| `afconvert` output size looks wrong | Compression differences between AFF and raw, or partial conversion | Compare exact byte counts from `affinfo` (logical size) against the converted output |
| `affuse` mount fails | FUSE not available/loaded, permissions, AFF file corrupt | Check `fusermount`/FUSE kernel module availability; check file integrity with `affverify` first |
| AFF4 container won't open in any tool | Format/tool mismatch (AFF vs AFF4), or tool is genuinely not installed for that variant | Confirm file's actual structure/extension and which tooling is present before assuming corruption |

## What this skill must never do automatically

- Run any conversion, acquisition, or export command that writes a new file without explicit confirmation of the destination path first.
- Report a hash, metadata field, or verification result not actually observed in tool output.
- Assume AFF and AFF4 tools/files are interchangeable.
- Present an unverified AFF4 CLI syntax as confirmed fact — always flag it as needing a live `--help` check given inconsistent packaging.
- Treat a verification mismatch as resolved without an actual, observed passing re-verification.

## Handoff

- Verification/conversion logs and hash results → `forensic-reporting`.
- E01/EWF format equivalents → `ewf-tools`.
- GUI-driven AFF acquisition → `guymager`.
- Mounting an AFF/AFF4 image for read-only review (general mechanics) → `forensic-image-mounting`.
- Source/destination and write-block discipline during original acquisition → `paladin-forensic-workflow`.

