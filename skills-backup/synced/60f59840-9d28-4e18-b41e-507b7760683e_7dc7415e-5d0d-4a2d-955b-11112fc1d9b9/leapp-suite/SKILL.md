---
name: "leapp-suite"
description: "Parses already-extracted mobile filesystem images/backups into categorized HTML/timeline reports via the LEAPP family: iLEAPP (iOS), aLEAPP (Android), rLEAPP (carrier/warrant returns), vLEAPP (vehicle infotainment). Trigger on \"run iLEAPP\", \"parse this iOS extraction\", \"aLEAPP this image\", \"process this Android dump\", \"rLEAPP this return\", \"vLEAPP this infotainment extraction\", \"generate a LEAPP report\". Read-only parsers of extraction files already on disk (tar/zip/UFED/GrayKey/Cellebrite output) - they do NOT connect to or image a live device. Not for acquiring the extraction (see adb-fastboot for Android live pulls) and not for the final case narrative (see forensic-reporting)."
---

---
name: leapp-suite
description: Parses already-extracted mobile filesystem images/backups into categorized HTML/timeline forensic artifact reports using the LEAPP family — iLEAPP (iOS full filesystem/backup extractions), aLEAPP (Android full filesystem/physical/logical extractions), rLEAPP (returns/warrant-style reports, e.g. carrier or provider return data), and vLEAPP (vehicle infotainment system extractions, e.g. Berla/iVe outputs). Trigger on "run iLEAPP", "parse this iOS extraction", "aLEAPP this image", "process this Android dump", "rLEAPP this return", "parse this warrant return", "vLEAPP this infotainment extraction", "generate a LEAPP report", or "what artifacts are in this extraction". These tools are read-only parsers that operate on extraction files already on disk (tar/zip/dd/dar/UFED/GrayKey/Cellebrite output, folder structures, etc.) — they do NOT connect to, image, or otherwise interact with a live device. Not for acquiring the extraction itself (use the device's own acquisition tool, e.g. adb-fastboot skill for Android live pulls, or a dedicated iOS/Android forensic acquisition tool) and not for writing the final case narrative (see forensic-reporting skill).
---

# LEAPP Suite (iLEAPP / aLEAPP / rLEAPP / vLEAPP)

## What this is

The LEAPP ("**L**og, **E**vent, **A**nd **P**rotobuf **P**arser") family, authored primarily by Alexis Brignoni (@AlexisBrignoni) and community contributors, is a set of Python-based forensic artifact parsers that share one underlying framework (`leapp-utils`/plugin architecture). Each variant targets a different source of extracted data:

| Tool | Targets | Typical input |
|---|---|---|
| **iLEAPP** | iOS devices | Full filesystem extraction, iTunes/Finder backup, GrayKey/Cellebrite/Magnet full-FS dumps |
| **aLEAPP** | Android devices | Full filesystem, physical image, ADB backup, Cellebrite/Magnet Android extractions |
| **rLEAPP** | "Returns" — carrier, cloud-provider, or warrant-return data | Structured provider return packages (varies by carrier/provider format) |
| **vLEAPP** | Vehicle infotainment systems | Berla iVe exports and similar automotive extraction formats |

All four:
- Are **read-only parsers**. They walk an already-existing extraction (a directory tree, a `.zip`/`.tar`, or a mounted image) and read files from it. They never write back to source evidence.
- Run a library of per-artifact "plugins" (Python scripts), each of which knows how to find and parse one artifact type (e.g., `iOS SMS`, `Android WhatsApp`, `Chrome History` inside a phone extraction).
- Produce an **output report bundle**: an `index.html` navigable report, per-artifact HTML/TSV/CSV tables, a combined SQLite/TSV timeline, and a processing log — written to a user-specified output folder. They do not modify the input.
- Ship both a CLI and a GUI. GUI variants exist as `ileappGUI` / `aleappGUI` / etc. (or a `--GUI`/GUI launch mode depending on version) — same parsing engine, point-and-click front end for selecting input/output paths and artifact modules instead of flags. Mention this to the examiner but default to CLI usage in written procedure since flags are more auditable/reproducible in a report.

## Command syntax (verify against `--help` — versions drift)

General pattern for the CLI form of each tool:

```
ileapp -t <input_type> -i <input_path> -o <output_path> [--artifact_paths] [-p <plugin_name(s)>]
aleapp -t <input_type> -i <input_path> -o <output_path>
rleapp -t <input_type> -i <input_path> -o <output_path>
vleapp -t <input_type> -i <input_path> -o <output_path>
```

Where, to the best of current documented knowledge:
- `-t` / `--extraction_type` selects the input format (e.g., `fs` for filesystem folder, `tar`, `zip`, `gz`, or a backup-specific type). **Exact accepted values differ between iLEAPP/aLEAPP/rLEAPP/vLEAPP and change between releases** — do not assume a value works without confirming via `ileapp -h` (etc.) first.
- `-i` / `--input_path` is the path to the extraction (folder or archive).
- `-o` / `--output_path` is the destination folder for the report.
- `-p` / a plugin-selection flag can narrow which artifact modules run (naming and exact flag differ by tool/version — verify with `-h`).
- `--gui` or running the `*GUI.py` entry point launches the graphical version.

**Flag this explicitly to the user rather than presenting it as settled fact:** I am not fully confident of every current flag name/spelling across all four tools and across recent version updates (the project is actively developed on GitHub and flags have changed release to release). Before running any of these commands, run the tool's own help first:

```
ileapp -h
aleapp -h
rleapp -h
vleapp -h
```

and confirm the exact flags for the installed version before building the real command line.

## Typical workflow

1. **Confirm the extraction is what it claims to be.** Note the extraction's origin (tool used, examiner, date), and verify integrity (hash match against acquisition-time hash) before parsing, per standard chain-of-custody practice. LEAPP parsing does not itself verify hashes.
2. **Identify extraction type/format** — full filesystem tar/zip, iTunes-style backup, Cellebrite UFDR-derived folder, etc. — to pick the correct `-t` value.
3. **Choose a clean output directory** — never point `-o` back into the evidence/extraction folder itself.
4. **Run the appropriate LEAPP variant** with `-i` (extraction), `-o` (report destination), and confirmed flags from `-h`.
5. **Review the processing log** the tool writes to the output folder for parser errors or artifacts that failed to parse (corrupt DBs, unsupported OS/app versions, etc.) — note these as limitations in case notes.
6. **Open `index.html`** in the output bundle to browse categorized artifacts (messages, call logs, installed apps, location data, browser history, etc.) and the combined timeline.
7. **Export/cite specific artifact tables** (the per-artifact HTML/TSV/CSV/XLSX files) as exhibits; do not just screenshot the HTML viewer for a report — reference the underlying data file path so the finding is reproducible.
8. Hand off exported artifacts and their provenance (which extraction, which LEAPP version, which command line was run) to the `forensic-reporting` skill for narrative writeup.

## Troubleshooting

| Symptom | Likely cause | What to try |
|---|---|---|
| Tool exits immediately with an argument error | Wrong `-t` value or missing required flag for that version | Re-run with `-h`; confirm accepted extraction-type values for the installed version |
| Report has very few/no populated artifacts | Extraction type mismatch (e.g., pointed at a backup folder but specified `fs` type), or extraction is partial/logical-only and lacks the underlying files a plugin needs | Re-check extraction contents against what each plugin expects; confirm this is a full filesystem extraction where relevant, not a logical-only pull |
| Specific artifact category missing entirely | Corresponding app/database absent from the extraction (app not installed, data cleared) or a version mismatch between app schema and the plugin's parser | Check the processing log for that plugin's error; verify manually by looking for the underlying database in the extraction; note as a limitation if unparseable |
| Processing log shows repeated SQLite "database disk image is malformed" | Source database was corrupt or extraction was incomplete/truncated for that file | Attempt to recover/repair a copy of the database with standard SQLite recovery methods before re-running that plugin only; document as a data-integrity limitation |
| GUI won't launch / no display | Running headless or over SSH without X forwarding | Use the CLI form instead, or ensure a display/X11 forwarding is available for the GUI |
| Output folder already has partial data from a prior run | Re-running into the same output path | Use a fresh output folder per run to keep runs auditable and avoid mixing partial results |

## What this skill must never do automatically

- Never treat presence of these tools on the examiner's PALADIN system as independently verified by Claude — tool availability/version was reported by the user via their own system inventory, not confirmed here.
- Never invent or assume a specific `-t`/extraction-type value, plugin name, or output flag for a given LEAPP variant/version without the user confirming it via `-h`/documentation first — flags differ across iLEAPP/aLEAPP/rLEAPP/vLEAPP and across versions.
- Never point the output path at the original extraction/evidence location, and never modify, rename, or delete files inside the source extraction.
- Never fabricate or assume artifact findings (message content, timestamps, locations) that were not actually produced in an output report — only report what the tool's HTML/TSV output actually contains.
- Never skip noting parser errors/failures from the processing log when summarizing results — silent gaps in coverage must be disclosed, not smoothed over.
- Never present a LEAPP report as a substitute for verifying the extraction's chain of custody or hash integrity — parsing is a downstream analysis step, not an acquisition-integrity check.

