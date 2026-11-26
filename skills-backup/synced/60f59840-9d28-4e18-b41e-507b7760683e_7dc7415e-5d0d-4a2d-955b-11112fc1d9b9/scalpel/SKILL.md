---
name: "scalpel"
description: "Fast, configurable signature-based file carving with scalpel, a rewritten successor to foremost tuned for performance on large images (lower memory footprint, multi-pass design, and support for carving on multiple CPU cores in later forks such as scalpel 2.x). Use when the user says \"carve with scalpel\", \"run scalpel on this image\", \"recover files faster than foremost\", \"carve a large disk image\", or wants fine-grained control over which signatures to carve via scalpel.conf. Do not use for TestDisk/PhotoRec workflows (use the testdisk-photorec skill instead). If the user just wants a quick default carve without tuning a config file, foremost (see the foremost skill) may be simpler to start with."
---

---
name: scalpel
description: Fast, configurable signature-based file carving with scalpel, a rewritten successor to foremost tuned for performance on large images (lower memory footprint, multi-pass design, and support for carving on multiple CPU cores in later forks such as scalpel 2.x). Use when the user says "carve with scalpel", "run scalpel on this image", "recover files faster than foremost", "carve a large disk image", or wants fine-grained control over which signatures to carve via scalpel.conf. Do not use for TestDisk/PhotoRec workflows (use the testdisk-photorec skill instead). If the user just wants a quick default carve without tuning a config file, foremost (see the foremost skill) may be simpler to start with.
---

# Scalpel

## What this tool does

Scalpel is a file carving tool descended from foremost's carving engine, rewritten (originally by Golden G. Richard III) to be faster and more memory-efficient, particularly on large images. Like foremost, it performs signature-based carving: it scans a raw byte stream (disk image, partition image, memory dump, unallocated space extract) for configured header/footer patterns and extracts matching regions to an output directory, without needing an intact filesystem.

Key differences from foremost that motivate choosing scalpel:
- Scalpel's carving engine was historically optimized to use less memory and complete carving passes faster on very large images, by building the list of matches first and carving in a separate, more efficient pass.
- Configuration is entirely driven by `scalpel.conf` (commonly at `/etc/scalpel/scalpel.conf`) — **all signatures are commented out (disabled) by default** in the stock config, so you must explicitly uncomment or add the file types you want before running scalpel, or it will find nothing.
- Some maintained forks (e.g. `sleuthkit/scalpel` / later community versions, "scalpel 2.x") add multithreaded carving support for multi-core performance on large images — confirm this is present in the installed version rather than assuming it.

**Presence note:** if this skill was told scalpel is installed on the PALADIN system, that was reported by the user via their own system inventory, not independently verified here. Confirm with `scalpel -v`/`which scalpel` and check which `scalpel.conf` it actually loads.

## Command syntax (verify against `scalpel -h`/man page for your installed version)

Basic invocation:

```
scalpel -c <scalpel.conf> -o <output_dir> <image_or_device>
```

Common flags (verify exact behavior on the installed version — flag sets have varied across scalpel 1.x vs. later forks):

- `-c <config>` — path to the scalpel configuration file defining enabled signatures. Required in practice, since the default config ships with everything disabled.
- `-o <dir>` — output directory. As with foremost, scalpel generally expects to create/write into a directory that does not already contain conflicting prior output.
- `-b` — carve to the end of the maximum defined carve size even if a footer isn't found (useful when footers are unreliable), rather than only carving header-to-footer.
- `-q <num>` — quick mode / block-alignment tuning, aligning search to a given block size boundary for speed (naming/behavior has varied by version — verify with `-h`).
- `-i <file>` — read a list of input images from a file (batch mode), in some builds.
- `-n` — do not organize carved output into per-type subdirectories, in some builds.
- `-o` output audit: like foremost, scalpel writes an audit log (commonly `audit.txt`) into the output directory summarizing what was carved.

Because scalpel's flags have shifted across the original Richard/Nazario codebase and later community forks, treat any flag not confirmed against `scalpel -h` or `man scalpel` on the actual installed binary as unverified — say so explicitly rather than presenting it as fact.

## Editing scalpel.conf

The config file lists candidate file types as commented-out lines, each defining (in order, per that file's own header comments) roughly: extension, case sensitivity, max carve size, header hex/string, optional footer hex/string. To enable a type, uncomment its line. To add a custom signature, follow the exact column format documented in the comments at the top of that specific `scalpel.conf` — do not guess at the column order; read the file's own header before editing it.

## Realistic workflow

1. **Work only from a verified image**, never the original evidence media — image and hash-verify first if you haven't already (see `paladin-forensic-workflow`).
2. Locate and review `scalpel.conf` on the system; confirm which file-type signatures are currently enabled. Enable the types relevant to the case (photos, documents, archives, etc.) before running — an all-disabled config will silently produce zero carved files, not an error.
3. **Choose an output directory on separate media from the evidence** (examiner scratch/working storage) — never write output back onto the source image's volume or any write-blocked evidence mount.
4. Run scalpel, e.g.:
   ```
   scalpel -c /home/examiner/case_scalpel.conf -o /mnt/casework/case001_scalpel_out /mnt/evidence_ro/case001.dd
   ```
5. Review the audit log in the output directory for what was carved, offsets, and any truncated/oversized-and-cut carves.
6. Validate carved files manually — as with any signature-based carver, expect false positives and partial/corrupted files.
7. Record the exact scalpel version, the config file used (and its hash, since it's user-editable and affects results), the command line, input image hash, and output location in case documentation (`forensic-reporting` skill).

## Troubleshooting

| Symptom | Likely cause / next step |
|---|---|
| Scalpel finds zero files | Almost always because every signature in `scalpel.conf` is commented out (the shipped default). Open the config and uncomment the file types you need. |
| Run is extremely slow on a large image | Check whether the installed version supports multithreading and whether it's enabled/available; also verify you're not accidentally scanning far more signatures than the case needs. |
| Carved files are all truncated at a fixed max size | The config's max-carve-size column for that signature is too small for the real files in this case; increase it in a copy of the config (never edit blindly without understanding the column format). |
| "output directory exists" type error | Use a fresh/empty output directory rather than reusing one from a prior run, to avoid ambiguity about which files came from which run. |
| Unsure of correct config column syntax | Read the comments at the top of the actual `scalpel.conf` on the system, or `man scalpel` — do not invent a column format. |
| Need footer-less carving (no reliable end-of-file marker) | Check the `-b` (carve to max size) option behavior in the installed version's `-h` output before relying on it. |

## What this skill must never do automatically

- Never point `-o` at the evidence image's own media, a write-blocked evidence mount, or any location inside the source evidence directory tree.
- Never silently enable file-type signatures in a shared/default `scalpel.conf` — edit a case-specific copy, and tell the user what was changed.
- Never reuse or overwrite a prior case's output directory without explicit confirmation.
- Never present scalpel's carved output as verified evidence without flagging that signature carving yields false positives and needs manual review.
- Never invent scalpel flag syntax or config column formats not confirmed via `-h`, `man scalpel`, or the config file's own documented format.
- Never claim scalpel (or a specific version/fork of it) is installed on a system beyond what the user reported from their own inventory.

