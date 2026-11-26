---
name: "tsk-usnjls"
description: "Parses and lists entries from an NTFS USN Journal ($UsnJrnl) found in a disk image, using The Sleuth Kit's usnjls command-line tool, to reveal a record of file system changes (creates, renames, deletes, overwrites) that may not appear in a standard directory listing. Trigger phrases include \"usnjls this image\", \"parse the USN journal\", \"show me file change history from NTFS\", \"what changed on this NTFS volume\", \"check the change journal for deleted file names\", or \"USN journal analysis\". Windows/NTFS-specific. Not for GUI Autopsy workflows (see autopsy-analysis), not for the general MAC(B) timeline from filesystem metadata (see tsk-mactime), which is a separate and complementary artifact."
---

---
name: tsk-usnjls
description: Parses and lists entries from an NTFS USN Journal ($UsnJrnl) found in a disk image, using The Sleuth Kit's usnjls command-line tool, to reveal a record of file system changes (creates, renames, deletes, overwrites) that may not appear in a standard directory listing. Trigger phrases include "usnjls this image", "parse the USN journal", "show me file change history from NTFS", "what changed on this NTFS volume", "check the change journal for deleted file names", or "USN journal analysis". Windows/NTFS-specific. Not for GUI Autopsy workflows (see autopsy-analysis), not for the general MAC(B) timeline from filesystem metadata (see tsk-mactime), which is a separate and complementary artifact.
---

# TSK usnjls — NTFS USN Journal Listing

## Purpose

`usnjls` parses the NTFS Update Sequence Number (USN) Journal — stored in the `$Extend\$UsnJrnl` file (`$J` alternate data stream) — and lists the change records it contains: file/directory creation, deletion, renames, data overwrites, extension of files, security/attribute changes, and more, each tied to a timestamp and a filename/parent reference. Because the USN Journal is a rolling log with its own retention independent of standard MFT timestamps, it can reveal activity (e.g., a file that was created and quickly deleted) that no longer appears in a live directory listing or even in `fls`'s view of current/deleted MFT entries if the MFT entry itself was reused.

This is NTFS-specific — it has no equivalent purpose on FAT, ext, or HFS+ images.

Always run against a verified forensic image or read-only mounted copy — never the original device.

## Command Syntax

```
usnjls [options] image [inode]
```

Where `inode` optionally specifies the MFT entry of the `$UsnJrnl:$J` stream directly, if not relying on autodetection.

| Flag | Purpose |
|---|---|
| `-o offset` | Sector offset to the NTFS filesystem within the image (from `mmls`) |
| `-i imgtype` | Image format if not auto-detected |
| `-f fstype` | Should resolve to NTFS; force if autodetection fails |
| `-d` | Show only entries flagged as deletes (verify exact flag against `usnjls -h`) |
| `-H` | Print column headers (verify against `-h`; header/format flags vary) |
| `-m` | Output in a mactime-compatible/body-file-like format (verify support/exact flag against `usnjls -h` for the installed TSK version — USN journal timeline export support has evolved across TSK releases) |

Confirm exact flags for the installed TSK version with `usnjls -h`/man page — `usnjls` is a newer addition to TSK relative to tools like `fls`/`icat`, and flag stability across versions is less battle-tested; treat anything not shown in `-h` output as unverified.

## Typical Workflow

1. Confirm working from a verified forensic image of an NTFS volume.
2. Get the filesystem offset via `mmls` if the image is a full disk (see `tsk-mmls`); confirm NTFS via `fsstat` (see `tsk-fsstat`).
3. Run `usnjls` against the volume:
   ```
   usnjls -o 2048 image.E01
   ```
4. Review the reason codes/flags on each entry (e.g., file created, data overwritten, file deleted, renamed old/new name) to build a picture of activity that may not be visible via `fls` alone.
5. Cross-reference USN Journal timestamps against the `mactime` MAC(B) timeline (see `tsk-mactime`) built from `fls` output — the two are complementary: the MAC(B) timeline reflects current/residual metadata state, while the USN Journal reflects a change log that can show short-lived files or renames the MAC(B) timeline alone would miss.
6. Note that the USN Journal itself has finite retention (it is a capped, rolling log) — absence of an expected event in `usnjls` output does not prove the event didn't happen, only that it fell outside the retained journal window or that journaling was disabled/reset.

## Troubleshooting

| Symptom | Likely Cause | Action |
|---|---|---|
| "Cannot find $UsnJrnl" / no output | USN Journal not enabled on this volume, was cleared, or wrong offset | Confirm NTFS via `fsstat`; check if journaling was ever enabled (not all NTFS volumes have an active/populated journal) |
| Journal entries only cover a short recent time span | Journal is a capped rolling log; old entries get overwritten | Document the observed date range and note that earlier activity may be unrecoverable via this artifact |
| Filenames show as numeric MFT references instead of names | Parent directory metadata not resolved in output | Cross-reference the MFT reference number against `fls`/`istat` output for that inode |
| Tool not found / not installed | `usnjls` may not be present in older TSK builds | Confirm TSK version and that `usnjls` is included; note this as an environment finding rather than assuming user error |

## What This Skill Must Never Do Automatically

- Never run `usnjls` against the original source device — only a verified forensic image or read-only mounted copy.
- Never treat the absence of an event in the USN Journal as proof it never occurred — the journal is capped/rolling and may not cover the full timeframe of interest; state this limitation explicitly in any findings.
- Never conflate USN Journal timestamps with MAC(B) filesystem timestamps in a report without labeling which artifact each came from — they are distinct evidence sources with different retention and semantics.
- Never fabricate reason-code meanings or flag syntax not confirmed via `-h`/man page; explicitly flag any uncertainty, especially given this tool's comparatively newer and less uniformly documented flag set.

