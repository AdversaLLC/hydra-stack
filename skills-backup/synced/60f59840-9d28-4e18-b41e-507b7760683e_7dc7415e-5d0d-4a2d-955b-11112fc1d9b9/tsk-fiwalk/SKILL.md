---
name: "tsk-fiwalk"
description: "Generates a DFXML (Digital Forensics XML) file inventory of a disk image using The Sleuth Kit's fiwalk command-line tool, capturing detailed per-file metadata in a structured, machine-parseable format for downstream tooling. Trigger phrases include \"fiwalk this image\", \"generate DFXML\", \"create an XML file inventory\", \"produce a machine-readable file listing\", \"export filesystem metadata as XML\", or \"build a DFXML manifest of this image\". Briefly mentions dupemap as a companion tool for duplicate-block mapping from fiwalk output. Not for GUI Autopsy workflows (see autopsy-analysis, though Autopsy can consume DFXML), not for human-readable directory listings (see tsk-fls), and not for MAC(B) timeline text output (see tsk-mactime)."
---

---
name: tsk-fiwalk
description: Generates a DFXML (Digital Forensics XML) file inventory of a disk image using The Sleuth Kit's fiwalk command-line tool, capturing detailed per-file metadata in a structured, machine-parseable format for downstream tooling. Trigger phrases include "fiwalk this image", "generate DFXML", "create an XML file inventory", "produce a machine-readable file listing", "export filesystem metadata as XML", or "build a DFXML manifest of this image". Briefly mentions dupemap as a companion tool for duplicate-block mapping from fiwalk output. Not for GUI Autopsy workflows (see autopsy-analysis, though Autopsy can consume DFXML), not for human-readable directory listings (see tsk-fls), and not for MAC(B) timeline text output (see tsk-mactime).
---

# TSK fiwalk — DFXML File Inventory Generation

## Purpose

`fiwalk` walks a disk image's filesystem(s) and produces a **DFXML (Digital Forensics XML)** document: a structured, standardized XML representation of every file and directory found, including metadata (timestamps, size, hashes if requested, byte-run/block allocation maps) and, optionally, per-file cryptographic hashes computed during the walk. DFXML is designed to be consumed by other forensic tools and scripts (including Autopsy, which can import DFXML) rather than read directly by an examiner, making `fiwalk` primarily useful as a data-generation step feeding other analysis.

Always run against a verified forensic image or read-only mounted copy — never the original source device.

## Command Syntax

```
fiwalk [options] image
```

| Flag | Purpose |
|---|---|
| `-x` | Output DFXML to stdout (or specify with redirection) |
| `-X file` | Write DFXML output to the named file |
| `-g` | Calculate hashes (e.g., MD5) for each file during the walk (verify exact hash algorithm options against `fiwalk -h`, as supported algorithms have changed across versions) |
| `-z` | Include byte-run/block allocation details for each file (verify flag against `-h`) |
| `-b` | Include "extras" like bulk_extractor-style annotations (verify support/flag with `-h`; not all builds include this) |
| `-i` | Specify image format if not auto-detected |

Confirm exact flags for the installed TSK build with `fiwalk -h`/man page. `fiwalk`'s option set has been less stable across TSK releases than core tools like `fls`/`icat`, and some builds package it as an optional component — confirm it is actually present on the system rather than assuming.

Example:
```
fiwalk -X image_dfxml.xml image.E01
```

## Typical Workflow

1. Confirm working from a verified forensic image.
2. Run `fiwalk` to produce the DFXML manifest:
   ```
   fiwalk -X /case/output/image_dfxml.xml image.E01
   ```
3. If per-file hashing is needed and supported by the installed build, enable it (expect significantly longer run time on large images):
   ```
   fiwalk -g -X /case/output/image_dfxml_hashed.xml image.E01
   ```
4. Feed the resulting DFXML into downstream tooling as needed — e.g., importing into Autopsy for GUI-based review (see `autopsy-analysis` once available), or scripted analysis/diffing against DFXML from a different image or a known-good baseline.
5. Retain the DFXML file itself as a durable, structured record of the image's file inventory at time of examination — useful for later comparison or for tools that only accept DFXML as input.

## dupemap (brief mention)

`dupemap` is a companion utility that consumes `fiwalk`'s DFXML output (specifically the byte-run/block information) to identify **duplicate blocks** across files or across multiple images — useful for finding copies of the same file content under different names, or matching content against a reference corpus. It is mentioned here for completeness only; consult its own `-h`/documentation before use, since this skill focuses on `fiwalk` itself and does not cover `dupemap`'s syntax in depth.

## Troubleshooting

| Symptom | Likely Cause | Action |
|---|---|---|
| `fiwalk: command not found` | Not installed/included in this TSK build | Confirm presence on the system before assuming user error; note this in findings rather than guessing a workaround |
| Extremely long runtime | Hashing enabled (`-g`) on a large image | Expected; consider running unhashed first for a quick inventory, then a hashed pass separately if time allows |
| DFXML file is very large | Full metadata + byte-run detail on many files | Expected for large filesystems; ensure adequate output storage; consider whether byte-run detail is actually needed for the task |
| DFXML fails to validate in downstream tooling | Truncated run (image error mid-walk) or version mismatch in DFXML schema expectations | Check `fiwalk` exit status/log for errors during the run; re-run and capture stderr output |
| Autopsy import of DFXML fails | Version/schema mismatch between `fiwalk` output and Autopsy's DFXML importer expectations | Note version numbers of both tools in case notes; this is an environment compatibility issue, not something to work around by editing the XML by hand |

## What This Skill Must Never Do Automatically

- Never run `fiwalk` against the original source device — only a verified forensic image or read-only mounted copy.
- Never hand-edit or "clean up" DFXML output to make it validate elsewhere — a modified DFXML no longer accurately reflects what the tool actually reported, which undermines evidentiary value.
- Never claim per-file hashes are present in the DFXML unless `-g` (or equivalent, per `-h`) was actually used and confirmed in the output.
- Never fabricate flag syntax not confirmed via `-h`/man page — `fiwalk`'s option set is less consistent across TSK builds than core tools, so flag uncertainty explicitly rather than presenting invented syntax as fact.
- Never assume `dupemap` or other DFXML-consuming tools are installed; confirm presence before recommending a specific downstream command.

