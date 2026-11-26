---
name: "volatility3"
description: "Analyze an already-acquired RAM image with Volatility 3, the current Volatility Framework major version — process lists/trees, network connections, DLL/handle enumeration, malware/injection detection, registry-from-memory, plugin-based memory forensics. Auto-detects OS/kernel info from the image itself, so no manual --profile is normally needed. Triggers on \"analyze this memory image\", \"run volatility\", \"vol3\", \"list processes from memory\", \"pslist\", \"pstree\", \"netscan this dump\", \"find malware in memory\", \"memory dump analysis\", or \"what plugins does volatility3 have\". Use for current-format images and reasonably recent OSes; use volatility2-legacy instead when the image/OS is unsupported by vol3, a case requires the legacy plugin set, or an explicit --profile must be supplied. Does not cover memory acquisition itself (out of scope, separate concern) — read-only analysis of an image that already exists."
---

# Volatility 3 — Memory Image Analysis

## What this tool does

Volatility 3 is the current major version of the Volatility Framework, a Python-based, plugin-driven toolkit for analyzing memory (RAM) images. Unlike Volatility 2, Volatility 3 generally does **not** require the examiner to manually select an OS "profile" — it inspects the image itself (kernel structures, PDB/symbol information, etc.) and resolves the necessary symbol information automatically in most cases. Volatility 3 works entirely against a memory image file; it never touches a live system or the original source of the capture.

Presence of Volatility 3 on this PALADIN system (and its exact invocation name — commonly `vol3`, `vol`, or a path into a bundled Python environment) was reported by the user via their own system inventory and has not been independently verified by Claude. Confirm the actual command name and version on the running system before relying on any syntax below:

```
vol3 --help
# or, depending on how it's installed/aliased on this system:
vol.py --help
python3 vol.py --help
```

## Scope boundary — read this first

- This skill covers **analysis of an already-acquired memory image**. Acquiring the memory image (live capture via a memory-acquisition tool, pre-boot capture, hibernation-file conversion, etc.) is out of scope — that happens before this skill is ever invoked, using different tooling not covered here.
- All operations below are **read-only against the image file**. Volatility does not modify the source memory image in normal use. Never treat any workflow here as a way to alter, "clean," or otherwise write to the evidence image.
- If the image path given is not clearly a copy/working file, confirm with the user which file is the authoritative acquired image before running anything against it.

## Command syntax

Volatility 3's general invocation pattern:

```
vol3 -f <path-to-memory-image> <plugin-name> [plugin-specific options]
```

Key points about vol3 syntax vs. Volatility 2 (see `volatility2-legacy` for the older tool):

- `-f <image>` specifies the memory image file. Common formats include raw/dd-style memory dumps, and depending on build, formats like AFF4 or crash-dump/hiberfil-derived captures may be supported — check `vol3 --help` and any format-conversion notes for the specific image type in hand.
- **No `--profile` flag is required in typical Volatility 3 usage.** The framework determines the operating system and version by inspecting the image directly (this is the major architectural difference from Volatility 2). Do not invent a `--profile` argument for vol3 — that is a Volatility 2 concept.
- Plugins are namespaced by OS in Volatility 3 (for example, plugins prefixed like `windows.`, `linux.`, or `mac.` in many builds) rather than being one flat list — the exact naming convention has changed across releases, so confirm current plugin names with `vol3 --help` rather than assuming a prefix pattern is still current on the installed version.
- `-o <output-dir>` or similar options may control where extracted artifacts (e.g., dumped files/DLLs) are written — verify the current flag name with `--help` before use, and always direct such output to an analysis working directory, never back into the evidence image or its original storage location.
- `-r <format>` (e.g., pretty table vs. CSV/JSON) may control output rendering in some builds — verify against `--help`.

### A handful of well-known plugin concepts (verify exact names before use)

Volatility 3's plugin catalog has changed across releases, and exact plugin names (including OS-namespace prefixes) are **not guaranteed to match older documentation or Volatility 2 naming**. The following are genuinely well-known, long-standing plugin *concepts* in the Volatility 3 ecosystem — use these as a starting vocabulary, but confirm the exact current name/spelling with `vol3 --help` before running anything, since plugin names have shifted (e.g., prefix changes, renames, splits) between releases:

| Concept | What it's for |
|---|---|
| pslist-style plugin | Lists running processes by walking the OS process list structures in memory |
| pstree-style plugin | Same process enumeration, rendered as a parent/child tree |
| netscan-style plugin | Finds network connection/socket structures in memory (connections, listening ports) |
| dlllist-style plugin | Lists DLLs/modules loaded into a given process |
| filescan-style plugin | Scans memory for file object structures, useful for finding files referenced in memory regardless of process context |
| malfind-style plugin | Looks for indicators of injected/hidden code (e.g., suspicious memory protections, PE headers in unexpected places) |
| registry/hive-related plugin(s) | Enumerate and read Windows registry hives reconstructed from memory |
| cmdline-style plugin | Shows process command-line arguments where recoverable |

Do **not** present a specific plugin invocation (exact string) to the examiner as certain fact unless it has been confirmed against `vol3 --help` (or the plugin's own `--help`) on the actual running system for this session. When uncertain, say so explicitly and show the command to check, rather than guessing a plugin name.

### Example shape of a command (verify plugin name first)

```
vol3 -f /path/to/case/memory.raw windows.pslist
vol3 -f /path/to/case/memory.raw windows.pstree
vol3 -f /path/to/case/memory.raw windows.netscan
```

These are illustrative of the *shape* (`-f <image> <namespaced-plugin>`), not a guarantee that `windows.pslist`/`windows.pstree`/`windows.netscan` are the exact current names on the installed version — confirm with `vol3 --help` first.

## Typical workflow

1. **Confirm the image file and its integrity** before analysis — verify the working copy's hash matches what was recorded at acquisition time, consistent with `paladin-forensic-workflow`. Volatility reads the file as given; it performs no integrity check of its own.
2. **List available plugins for this build** rather than assuming a fixed catalog:
   ```
   vol3 --help
   ```
   This is the authoritative source for what plugins actually exist on this installation.
3. **Identify OS/architecture** — running any core process-listing plugin (once its exact name is confirmed) typically also surfaces basic OS/kernel identification as part of Volatility 3's automatic symbol resolution. There is usually no separate manual "imageinfo"-equivalent step required the way there was in Volatility 2, but if initial symbol resolution fails, check `vol3 --help` for any current isf/symbol-table options.
4. **Run targeted plugins based on the investigative question** — process enumeration first (to orient), then network, then more specific plugins (injection detection, registry, filesystem-in-memory) as the case requires. Run one plugin at a time and review output before chaining further analysis.
5. **Redirect/save output** to a case working directory for later reporting — do not rely on scrollback; capture stdout to a file per plugin run so results are reproducible.
6. **Cross-check unusual findings** (e.g., a malfind-style hit) against other plugin output (e.g., the corresponding process's pslist/dlllist entries) before treating it as a finding — memory analysis produces false positives, especially around packed/legitimate software.
7. **Hand off confirmed findings** to `forensic-reporting`, citing the exact plugin name, version of Volatility 3 used, and the command line run, so the finding is reproducible by another examiner.

## Troubleshooting

| Symptom | Likely cause | What to check |
|---|---|---|
| "Unable to validate the plugin requirements" / symbol table not found | Volatility 3 could not match the image to a known OS symbol table (common with unusual kernel builds or images vol3's symbol packs don't cover) | Check whether a symbol table needs to be manually supplied/downloaded for this OS build (verify current mechanism via `vol3 --help`); consider whether `volatility2-legacy` with an explicit profile is more appropriate for this image |
| Command runs but returns no rows / empty output | Wrong plugin for the OS in the image (e.g., a `windows.*` plugin against a Linux image), or the image is truncated/corrupted | Confirm image OS matches the plugin namespace; verify image file size/hash against acquisition record |
| Extremely slow execution | Large image, plugin doing exhaustive memory scanning (e.g., scan-style plugins), slow storage | Expected for scan-heavy plugins on large images; do not assume a hang — check for CPU/disk activity before killing the process |
| `--profile` flag rejected/unrecognized | Using Volatility 2 syntax against Volatility 3 | Drop `--profile` entirely for vol3; that flag belongs to `volatility2-legacy` |
| Plugin name not found | Plugin renamed/removed/split between versions, or wrong OS namespace prefix guessed | Run `vol3 --help` and search the actual listed plugin names rather than guessing from memory or older docs |
| Output references artifacts to dump but no file appears | Missing or wrong output-directory flag for that plugin | Check plugin-specific `--help` for its actual dump/output option name before assuming failure |

## What this skill must never do automatically

- Never invent or assert a specific plugin name, flag, or exact output field as certain fact without it having been confirmed via `vol3 --help`/plugin `--help` on the actual system — flag uncertainty explicitly instead.
- Never write to, convert-in-place, or modify the original acquired memory image; all output/extraction goes to a separate working/output location.
- Never treat a single plugin's output (especially a heuristic/scan-style plugin like a malfind-style one) as a confirmed finding without cross-checking against at least one other plugin or source.
- Never fall back to Volatility 2 syntax (`--profile`, etc.) when running vol3, or vice versa — the two tools are not interchangeable in invocation.
- Never run acquisition, conversion, or hibernation-file-decompression steps as part of this skill — those are out of scope; this skill assumes a usable memory image already exists.
- Never report a version, plugin catalog, or capability of the installed Volatility 3 build without having actually observed it via `--help`/`--info` in this session.

## Handoff

- Confirmed findings (processes, connections, malware indicators, registry artifacts) → `forensic-reporting` for the written case report, citing exact command lines used.
- Image whose format/OS Volatility 3 cannot resolve → consider `volatility2-legacy` if the image is old enough for that tool's plugin set/profile catalog to apply.
- Suspected encrypted volume found referenced in memory (e.g., via filescan or registry artifacts) → `memory-key-recovery` for cold-boot-style AES key recovery from the same image, where legally authorized.

