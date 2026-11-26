---
name: "magicrescue"
description: "Recipe-based file carving with magicrescue — scans a raw disk/partition image or device for user-defined \"magic\" byte patterns (recipes describing a file type's header and how to locate its end) and writes matching regions out as recovered files, similar in spirit to foremost/scalpel but driven by simple external recipe scripts/files rather than a single built-in config format. Use when the user says \"run magicrescue\", \"carve files with magicrescue recipes\", \"recover files using a magic recipe\", or needs a custom carving recipe for a file type not well covered by foremost/scalpel's default signatures. Mention magicsort only briefly as the companion tool for organizing/deduplicating magicrescue's raw numbered output afterward. Not for TestDisk/PhotoRec workflows (use the testdisk-photorec skill instead); for mainstream file types with strong existing signature support, foremost or scalpel (see those skills) are usually simpler starting points."
---

---
name: magicrescue
description: Recipe-based file carving with magicrescue — scans a raw disk/partition image or device for user-defined "magic" byte patterns (recipes describing a file type's header and how to locate its end) and writes matching regions out as recovered files, similar in spirit to foremost/scalpel but driven by simple external recipe scripts/files rather than a single built-in config format. Use when the user says "run magicrescue", "carve files with magicrescue recipes", "recover files using a magic recipe", or needs a custom carving recipe for a file type not well covered by foremost/scalpel's default signatures. Mention magicsort only briefly as the companion tool for organizing/deduplicating magicrescue's raw numbered output afterward. Not for TestDisk/PhotoRec workflows (use the testdisk-photorec skill instead); for mainstream file types with strong existing signature support, foremost or scalpel (see those skills) are usually simpler starting points.
---

# magicrescue

## What this tool does

magicrescue is a file carving tool that recovers files from a disk image, partition, or block device by scanning for byte patterns defined in small external **recipe** files, rather than a single centralized config listing every type (as foremost/scalpel do). Each recipe describes how to recognize the start of a file of a given type and, depending on the recipe, how to determine or estimate where it ends. Recipes are typically small shell/text-based scripts or pattern definitions distributed with magicrescue or written/adjusted by the examiner for a specific file type.

Because recipes are simpler, independent units, magicrescue is often reached for when:
- The built-in signature sets of foremost/scalpel don't cover a needed file type well
- The examiner wants to write or tweak a narrow, purpose-built recipe for one unusual format
- A quick recipe-driven scan is preferable to editing a large shared config file

Output from magicrescue is typically a flat/numbered dump of recovered files (named by sequence and/or offset, since the original filenames don't exist in raw carved data) — this is much less organized than foremost/scalpel's type-named subdirectories, which is why the companion tool **magicsort** is commonly run afterward.

**magicsort** (companion tool, mention briefly, do not treat as covered in depth here) — a separate utility distributed alongside magicrescue that helps organize the raw numbered output magicrescue produces: it can sort recovered files into directories (e.g., by type or other heuristics) and help identify/remove duplicate carved files. Treat magicsort's exact flags as unverified unless checked against its own `--help`/man page — it is mentioned here only so the examiner knows it exists as the natural next step after a magicrescue run.

**Presence note:** if this skill was told magicrescue (and/or magicsort) is installed on the PALADIN system, that was reported by the user via their own system inventory, not independently verified here. Confirm with `magicrescue --help`/`which magicrescue`/`which magicsort`, and confirm where the recipe files actually live on this system (commonly under a `recipes` directory shipped with the package, e.g. `/usr/share/magicrescue/recipes` or similar — verify the actual path rather than assuming).

## Command syntax (verify against `magicrescue --help`/man page for your installed version)

Basic invocation:

```
magicrescue -r <recipe> -d <output_dir> <image_or_device>
```

Common flags (verify exact behavior with `--help`, since exact option letters should be confirmed on the installed build):

- `-r <recipe>` — specify a recipe to use; can be given multiple times to search for several file types in one pass.
- `-d <dir>` — output directory for recovered files.
- `-b <size>` — block size to align scanning to, where supported (tuning speed vs. thoroughness).
- `-M` — treat the input as unable to seek backwards efficiently in some builds (e.g., for reading directly from certain device types) — verify this exists and its exact meaning before relying on it.
- A recipes directory is usually bundled with the package; recipe names are passed to `-r` either as a path or a bare name that magicrescue resolves against its known recipe directories, depending on version — confirm the resolution behavior on the installed build.

Because magicrescue is a smaller, less actively maintained project than foremost/scalpel, flag availability and recipe path resolution can vary meaningfully by packaged version and distro. Verify against `magicrescue --help`/man page on the actual installed binary rather than assuming any flag beyond `-r` and `-d`.

## Realistic workflow

1. **Work only from a verified image**, never the original evidence media directly — image and hash-verify first if not already done (see `paladin-forensic-workflow`).
2. Identify or write the recipe(s) needed for the file type(s) in question. Check what recipes ship with the installed package before writing a new one.
3. **Choose an output directory on separate media from the evidence** — never write recovered output back onto the source image's volume or any write-blocked evidence mount.
4. Run magicrescue, e.g.:
   ```
   magicrescue -r jpeg-jfif -r png -d /mnt/casework/case001_magicrescue_out /mnt/evidence_ro/case001.dd
   ```
5. Because output filenames are numbered/offset-based rather than descriptive, run **magicsort** (or manually triage) afterward to organize the raw output into something reviewable — verify magicsort's actual flags on the system before using them.
6. Validate recovered files manually — as with any signature-based carver, expect false positives, partial, or corrupted recoveries, especially for recipes that estimate file length rather than finding a true footer.
7. Document the magicrescue version, exact recipe(s) used (and their contents/hash if custom-written), command line, input image hash, and output location for the case record (`forensic-reporting`).

## Troubleshooting

| Symptom | Likely cause / next step |
|---|---|
| magicrescue finds nothing | Confirm the recipe name/path actually resolves (check where recipes live on this install) and that the recipe matches the file type actually present; try running with a recipe you know should match test data first. |
| Output is a pile of oddly-named files with no type organization | Expected — magicrescue's raw output is numbered/offset-based. Use magicsort (verify its flags first) or manual triage (e.g., `file` on each recovered item) to organize. |
| Recovered files are truncated or contain trailing garbage | The recipe's end-of-file detection is heuristic for many file types; check whether a better/more specific recipe exists, or accept manual trimming/validation as part of review. |
| Unsure of correct recipe file syntax to write a custom one | Read the format and comments of an existing shipped recipe file on the system as the concrete example, and check `man magicrescue` / project documentation — do not invent recipe syntax. |
| Run is slow on a large image | Check block-size/alignment flags in `--help` for the installed version; scanning many recipes at once is slower than a narrow, targeted set. |

## What this skill must never do automatically

- Never write recovered output back onto the evidence image's own media, a write-blocked evidence mount, or any path inside the source evidence directory tree.
- Never overwrite a prior case's output directory without explicit user confirmation.
- Never invent magicrescue recipe syntax or magicsort flags not confirmed against the installed package's own recipe examples, `--help`, or man page.
- Never present carved output as verified evidence without noting that recipe-based carving (especially length-estimating recipes) commonly yields truncated or false-positive results requiring manual validation.
- Never claim magicrescue or magicsort are installed on a system, or that specific recipes ship with the package, beyond what the user reported from their own inventory.

