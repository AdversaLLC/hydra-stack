---
name: "volatility2-legacy"
description: "Analyze an already-acquired RAM image with the legacy Volatility 2.6 standalone build (volatility_2.6_lin64_standalone per the user's system inventory) when the image format or source OS/version is not fully supported by Volatility 3, or a case specifically calls for Volatility 2's plugin set. Requires the examiner to explicitly determine and pass an OS/build --profile — unlike Volatility 3, it does not reliably auto-detect this. Triggers on \"volatility 2\", \"vol2\", \"legacy volatility\", \"imageinfo\", \"kdbgscan\", \"what profile is this memory image\", \"vol3 doesn't support this image\", or an older Windows XP/2003/Vista/7-era memory image. Use for older/unsupported image formats or OS versions; for current-format images Volatility 3 already handles, use volatility3 instead — do not default here when vol3 works. Does not cover memory acquisition itself, out of scope and assumed already complete."
---

# Volatility 2 (Legacy Standalone) — Memory Image Analysis

## What this tool does

Volatility 2 is the older major version of the Volatility Framework. This skill specifically covers the standalone Linux 64-bit build reported present on this PALADIN system as `volatility_2.6_lin64_standalone` (presence reported by the user via their own system inventory, not independently verified by Claude — confirm the actual binary name/path on the running system, e.g. via `ls`/`which`, before relying on it).

Unlike Volatility 3, Volatility 2 does **not** reliably determine the source OS/build on its own. The examiner must identify and explicitly pass a `--profile` value (an internal Volatility 2 identifier for a specific OS/service-pack/architecture combination) for almost all plugins to work correctly. This is the single most important operational difference from `volatility3` and the most common source of "it doesn't work" reports against this tool.

## Scope boundary — read this first

- This skill covers **analysis of an already-acquired memory image**, read-only. Acquisition of the memory image itself is out of scope.
- Volatility 2 does not modify the source image in normal use. All output (dumped files, extracted artifacts) should go to a separate working/output directory, never back into the image or its original storage location.
- Use this tool when there is a concrete reason Volatility 3 does not apply — an older OS version/build, an image format vol3's build doesn't parse, or a case requirement to use the legacy plugin set. If unsure which to use, try `volatility3` first; fall back here only if it fails to resolve the image's OS/symbols.

## Command syntax

Volatility 2's general invocation pattern (standalone build):

```
./volatility_2.6_lin64_standalone -f <path-to-memory-image> --profile=<ProfileName> <plugin>
```

Key points about vol2 syntax vs. Volatility 3 (see `volatility3` for the current tool):

- `-f <image>` specifies the memory image file, same concept as vol3.
- `--profile=<ProfileName>` is **required** for the large majority of plugins. Profile names are specific strings representing OS/version/service-pack/architecture (for example, a Windows 7 SP1 64-bit profile has a specific internal name string). Do not guess or invent a profile name — determine it from the image itself using `imageinfo` or `kdbgscan` (below), and confirm exact spelling against the actual output of `--info` on the installed build.
- `--info` lists the plugins and profiles the running Volatility 2 build actually knows about:
  ```
  ./volatility_2.6_lin64_standalone --info
  ```
  This is the authoritative source for available profile names and plugin names on this specific build — profile lists have varied across Volatility 2 releases/plugin contributions, so do not assume a profile name from general knowledge is present on this installed copy.

### Determining the profile (do this before anything else)

Volatility 2 provides scanning plugins specifically to help identify the correct profile for an unknown image:

| Plugin | Purpose |
|---|---|
| `imageinfo` | Suggests likely profile(s) for the image by inspecting kernel-level structures; typically the first plugin run against any new image |
| `kdbgscan` | Scans for the Windows kernel debugger block more exhaustively than `imageinfo`; useful when `imageinfo` gives an ambiguous or low-confidence suggestion, or multiple candidate profiles |

Example:

```
./volatility_2.6_lin64_standalone -f /path/to/case/memory.raw imageinfo
```

`imageinfo` will suggest one or more candidate profile strings — treat its output as a suggestion to verify, not an infallible answer, especially if it lists multiple candidates or low-confidence matches. Cross-check against any known information about the source system (OS version from other evidence) before committing to a profile for the rest of the analysis.

### A handful of well-known plugin concepts (verify exact names before use)

As with Volatility 3, do not present a specific plugin name as certain fact without confirming it against `--info` on the actual installed build. The following are long-standing, well-known Volatility 2 plugin *concepts*:

| Concept | What it's for |
|---|---|
| `imageinfo` | Suggests the profile for an unknown image (see above) |
| `kdbgscan` | More exhaustive kernel-debugger-block scan for profile identification |
| `pslist` | Lists running processes by walking the OS process list |
| `pstree` | Process list rendered as a parent/child tree |
| `psscan` | Pool-scanning process enumeration — can surface processes hidden from `pslist` (e.g., unlinked by rootkit techniques) |
| `connscan` / `netscan` | Network connection enumeration (exact plugin available depends on target OS/build) |
| `dlllist` | Lists DLLs loaded into a given process |
| `malfind` | Looks for indicators of injected/hidden code |
| `hivelist` / `printkey` | Enumerate and read Windows registry hives reconstructed from memory |

Confirm each plugin's exact name and required arguments against `--info` or the plugin's own help before running it, and do not assume Volatility 3's plugin catalog or naming maps directly onto Volatility 2 — the two projects have diverged significantly.

### Example shape of a command (verify profile and plugin name first)

```
./volatility_2.6_lin64_standalone -f /path/to/case/memory.raw --profile=Win7SP1x64 pslist
./volatility_2.6_lin64_standalone -f /path/to/case/memory.raw --profile=Win7SP1x64 pstree
./volatility_2.6_lin64_standalone -f /path/to/case/memory.raw --profile=Win7SP1x64 connscan
```

`Win7SP1x64` above is illustrative of the *shape* of a profile string, not a guaranteed-correct value — the exact profile string for the image in hand must come from `imageinfo`/`kdbgscan` output on that image, or from `--info` confirming it exists in this build's profile list.

## Typical workflow

1. **Confirm the image file's integrity** — verify the working copy's hash matches the acquisition record, consistent with `paladin-forensic-workflow`.
2. **Confirm this is actually the right tool for the image** — if there's no concrete reason Volatility 3 fails on this image, prefer `volatility3` instead.
3. **Run `imageinfo`** (and `kdbgscan` if `imageinfo` is ambiguous) to determine the correct `--profile` value. Record the exact profile string used — every subsequent plugin invocation depends on it, and it belongs in the case notes for reproducibility.
4. **Run `--info`** to confirm which plugins this specific build actually provides before assuming a plugin exists.
5. **Run targeted plugins** with the confirmed `--profile`, starting with process enumeration (`pslist`/`pstree`/`psscan`) to orient, then network and more specific plugins as the investigative question requires.
6. **Cross-check `pslist` against `psscan`** specifically — a process appearing in `psscan` (pool scan) but not `pslist` (linked-list walk) is a classic indicator worth flagging (possible unlinking/hiding), but confirm it's not simply a terminated process whose pool tag hasn't been reused, rather than asserting rootkit activity outright.
7. **Save output per plugin run** to a case working directory, including the exact command line (with profile) used, for reproducibility.
8. **Hand off confirmed findings** to `forensic-reporting`, citing Volatility 2.6, the profile used, and exact commands.

## Troubleshooting

| Symptom | Likely cause | What to check |
|---|---|---|
| Plugin errors out immediately or returns garbage | Wrong or missing `--profile` | Re-run `imageinfo`/`kdbgscan`; confirm the profile string is spelled exactly as suggested/listed, including case sensitivity |
| `imageinfo` suggests multiple profiles with similar confidence | Ambiguous kernel version match (common with certain SP/build variants) | Try each candidate profile on a low-risk plugin like `pslist` and see which produces sane-looking output; corroborate with other case evidence of the source OS version if available |
| Plugin name not recognized | Plugin doesn't exist in this build, or typo | Run `--info` and check the actual plugin list for this build rather than assuming from general knowledge |
| Very slow scanning plugins (`kdbgscan`, `psscan`, `malfind`) | Expected — these do exhaustive memory scans rather than following pointers | Expected behavior on large images; don't assume a hang without checking process activity |
| Output looks like it's from the wrong OS entirely | Wrong profile silently "succeeding" with nonsense output | Sanity-check results against any independently known facts about the source system before trusting them |
| Image doesn't work with vol2 either | Format not supported by either version, or image corrupted/truncated | Verify image integrity/hash against acquisition record; check image format assumptions (raw vs. crash dump vs. hiberfil-derived) |

## What this skill must never do automatically

- Never invent or assume a `--profile` value — always derive it from `imageinfo`/`kdbgscan` output on the actual image, or from a value already confirmed present in `--info`'s profile list.
- Never invent or assert a specific plugin name/flag as certain fact without confirming it against `--info`/plugin help on the actual installed build.
- Never write to or modify the original acquired memory image; direct all extracted output to a separate working directory.
- Never treat a `pslist`/`psscan` discrepancy or a `malfind` hit as a confirmed rootkit/malware finding without cross-checking against other plugin output or independent evidence.
- Never default to this legacy tool over `volatility3` without a stated, concrete reason (unsupported image format/OS version, or explicit case requirement).
- Never report a plugin catalog or profile list for this build without having actually run `--info` in this session to observe it.

## Handoff

- Confirmed findings → `forensic-reporting`, citing Volatility 2.6, the exact profile, and commands used.
- If Volatility 3 later turns out to handle this image after all → prefer `volatility3` for the remainder of the analysis and note in the report why the legacy tool was tried first.
- Suspected encrypted volume referenced in memory → `memory-key-recovery` for cold-boot-style AES key recovery from the same image, where legally authorized.

