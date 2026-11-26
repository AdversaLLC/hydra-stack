---
name: "ewf-tools"
description: "Use the libewf command-line tool family (ewfacquire, ewfinfo, ewfverify, ewfexport, ewfmount) to create, inspect, verify, convert, and mount Expert Witness Format (E01/Ex01) forensic images from the command line. Triggers on \"ewfacquire\", \"ewfinfo\", \"ewfverify\", \"ewfexport\", \"check this E01 header\", \"verify this E01 hash\", \"convert E01 to raw\", \"acquire E01 from the command line\", or \"read E01 metadata\". Focused on E01 format handling specifically — for GUI-driven E01 acquisition use guymager instead; for general read-only mounting of an already-acquired image (E01, AFF, VHD, etc.) as a use case rather than format internals, see forensic-image-mounting; for AFF/AFF4 format tools see afflib-aff4."
---

---
name: ewf-tools
description: Use the libewf command-line tool family (ewfacquire, ewfinfo, ewfverify, ewfexport, ewfmount) to create, inspect, verify, convert, and mount Expert Witness Format (E01/Ex01) forensic images from the command line. Triggers on "ewfacquire", "ewfinfo", "ewfverify", "ewfexport", "check this E01 header", "verify this E01 hash", "convert E01 to raw", "acquire E01 from the command line", or "read E01 metadata". Focused on E01 format handling specifically — for GUI-driven E01 acquisition use guymager instead; for general read-only mounting of an already-acquired image (E01, AFF, VHD, etc.) as a use case rather than format internals, see forensic-image-mounting; for AFF/AFF4 format tools see afflib-aff4.
---

# ewf-tools (libewf family)

The `libewf` project provides a family of command-line tools for working with the Expert Witness Format (EWF), commonly known by its file extension **E01** (and the newer **Ex01**/EWF2 variant). This is the format most forensic case files use. This skill covers the tool family's format-specific operations — creating, inspecting, verifying, converting — as command-line utilities, distinct from Guymager's GUI wrapper around similar acquisition functionality.

Presence of these tools on this PALADIN system was reported by the user via their own system inventory, not independently verified by Claude.

## The tool family

| Tool | Purpose |
|---|---|
| `ewfacquire` | Interactive/scriptable command-line acquisition of a device or raw image into E01/Ex01 format, with hashing |
| `ewfinfo` | Print metadata/header information from an existing E01 file (case data, hash values stored in the file, acquisition parameters, segment info) |
| `ewfverify` | Re-read an E01 file and verify its stored hash(es) against a freshly computed hash of the data — confirms the image hasn't been altered/corrupted since acquisition |
| `ewfexport` | Convert/export an E01 image to another format (raw dd, or a different EWF variant), optionally re-segmenting or recompressing |
| `ewfmount` | Mount an E01 file as a virtual raw device for read access (see also `forensic-image-mounting` for the general mounting use case) |

## ewfacquire — creating an E01

Interactive by default (prompts for case information); can also take command-line flags for scripted/unattended use. Verify exact flag syntax against `ewfacquire --help` or `man ewfacquire` on the installed system before relying on it in a report — flags below reflect general knowledge of libewf's documented interface, not a live version check.

Typical prompted/settable fields: case number, evidence number, examiner name, description/notes, acquisition/system date, media/source type, hash algorithm(s) (MD5/SHA-1/SHA-256), compression level, segment file size, EWF format variant (EnCase 6, EWF2/Ex01, etc.).

```
ewfacquire /dev/sdX
```
run interactively, or with flags to preset values non-interactively (exact flag names such as `-C` case number, `-E` evidence number, `-e` examiner, `-D` description, `-t` target basename, `-S` segment size, `-d` hash digest have appeared in various libewf versions — confirm current spelling on this system before using them in a script).

**This writes to a destination image file — get explicit user confirmation before running**, with source, destination basename, and hash settings stated first, exactly as with any other acquisition tool.

## ewfinfo — reading metadata (read-only, safe)

```
ewfinfo case001_drive1.E01
```
Prints acquisition metadata and the hash(es) recorded at acquisition time. This is read-only and safe to run without special confirmation — it does not modify the image. Use this to pull actual case metadata and hash values into a report rather than retyping them from memory or a prior session.

## ewfverify — verifying integrity (read-only, safe)

```
ewfverify case001_drive1.E01
```
Re-reads the full image, recomputes the hash(es), and compares against the value(s) stored in the E01 header, reporting match/mismatch. Read-only with respect to the image (it only reads); safe to run. Always report the actual PASS/FAIL output — never assume a match without having seen this command's result.

## ewfexport — converting/exporting (writes a new output file)

```
ewfexport -t /path/output_raw -f raw case001_drive1.E01
```
(illustrative — confirm `-t`/`-f` and format names such as `raw`, `ewf`, `files` against the live `--help`). This creates a new output file at the destination path — treat it as a write operation requiring the same explicit confirmation as any acquisition/export step, even though the source E01 itself isn't modified.

## Typical workflow

1. For **new acquisition**: declare source/destination explicitly, confirm write-block status on the source, get explicit confirmation before running `ewfacquire`, same as any imaging tool.
2. For **inspecting an existing E01**: run `ewfinfo` freely (read-only) to pull real metadata/hash values.
3. For **verifying an existing E01**: run `ewfverify` and report the actual result. If it reports a mismatch, stop and flag it — do not proceed to treat the image as trustworthy for analysis.
4. For **converting/exporting**: confirm the destination path and format before running `ewfexport`, since it writes a new file.
5. For **mounting an E01 for review**: `ewfmount` (see also `forensic-image-mounting` for mounting mechanics and read-only discipline that apply across formats, not just E01).

## Troubleshooting

| Symptom | Likely cause | What to check |
|---|---|---|
| `ewfacquire`/`ewfinfo`/etc.: command not found | libewf-tools not installed or not on PATH | `which ewfinfo` (or the specific tool); confirm presence rather than assuming |
| `ewfverify` reports hash mismatch | Image corrupted/altered since acquisition, incomplete transfer of segment files, media bit rot | Check all `.E01`/`.E02`... segment files are present and complete before concluding tampering; re-copy segments from a known-good backup if available and re-verify |
| `ewfinfo` shows blank/missing case fields | Fields weren't populated during the original `ewfacquire` run | Note as a genuine gap in the report, don't infer values |
| Acquisition segments missing (`.E02`, `.E03`, ...) | Only part of a multi-segment image was copied/transferred | Confirm full segment set is present before running `ewfverify` or mounting — a partial segment set will fail or misbehave |
| `ewfexport` output larger/smaller than expected | Compression level differences between source and target format, or only part of image exported | Compare exact byte counts of source (uncompressed logical size per `ewfinfo`) vs. exported output |
| Slow acquisition/verification | Compression level set high, or media/read speed limits | Note as observed behavior; don't fabricate a specific cause without checking `ewfinfo`/system I/O |

## What this skill must never do automatically

- Run `ewfacquire` (a write/acquisition operation) without explicit confirmation of source, destination basename, and hash settings.
- Run `ewfexport` to a destination path without confirming that path and its format first.
- Report a hash, case field, or verification result that wasn't actually shown in the tool's output.
- Treat an `ewfverify` mismatch as resolved without an actual, observed passing re-verification.
- Modify or hand-edit E01 header metadata after acquisition.

## Handoff

- Acquisition/verification logs and hash results → `forensic-reporting`.
- GUI-driven E01 acquisition instead of command-line → `guymager`.
- Mounting an E01 for read-only review (mechanics, read-only mount options) → `forensic-image-mounting`.
- AFF/AFF4-format equivalents → `afflib-aff4`.
- Source/destination and write-block discipline → `paladin-forensic-workflow`.

