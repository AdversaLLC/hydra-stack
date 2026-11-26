---
name: "chromium-artifact-parser"
description: "Parses Chromium-based browser artifacts (history, downloads, cookies, autofill, login data, bookmarks, IndexedDB/LevelDB, cache, session/tab state) from an already-extracted browser profile directory using ccl_chromium_reader (CCL Solutions Group / Alex Caithness). Covers Chrome, Chromium, Edge, Brave, Opera, and other Chromium-derived browser profiles pulled from a disk image, mobile extraction, or live-acquired user data folder. Trigger on \"parse Chrome history\", \"read this Chromium profile\", \"extract browser cookies\", \"ccl_chromium_reader\", \"parse IndexedDB\", \"get autofill data from this profile\", \"what sites did they visit\", or \"analyze this browser profile\". Operates read-only on a copy of an already-extracted profile folder or the individual SQLite/LevelDB files within it — does not connect to a live browser process, does not decrypt OS-level credential-store encryption on its own, and is not a disk-imaging or mobile-extraction tool (see paladin-forensic-workflow and leapp-suite for those steps)."
---

---
name: chromium-artifact-parser
description: Parses Chromium-based browser artifacts (history, downloads, cookies, autofill, login data, bookmarks, IndexedDB/LevelDB, cache, session/tab state) from an already-extracted browser profile directory using ccl_chromium_reader (CCL Solutions Group / Alex Caithness). Covers Chrome, Chromium, Edge, Brave, Opera, and other Chromium-derived browser profiles pulled from a disk image, mobile extraction, or live-acquired user data folder. Trigger on "parse Chrome history", "read this Chromium profile", "extract browser cookies", "ccl_chromium_reader", "parse IndexedDB", "get autofill data from this profile", "what sites did they visit", or "analyze this browser profile". Operates read-only on a copy of an already-extracted profile folder or the individual SQLite/LevelDB files within it — does not connect to a live browser process, does not decrypt OS-level credential-store encryption on its own, and is not a disk-imaging or mobile-extraction tool (see paladin-forensic-workflow and leapp-suite for those steps).
---

# Chromium Artifact Parser (ccl_chromium_reader)

## What this is

`ccl_chromium_reader` is a Python library and set of command-line scripts by Alex Caithness / CCL Solutions Group for parsing the on-disk artifact formats used by Chromium-based browsers (Google Chrome, Chromium, Microsoft Edge, Brave, Opera, Vivaldi, and other Chromium derivatives, including mobile Chrome-on-Android profiles). It reads the underlying SQLite databases and Chromium's custom LevelDB-based stores directly, independent of whether the browser itself is installed or running.

Artifacts it can parse (module/coverage varies by version — verify against the project's README/CLI help for the installed version):
- **History** (`History` SQLite DB — visits, URLs, visit counts, transition types)
- **Downloads** (from the same `History` DB)
- **Cookies** (`Cookies` SQLite DB)
- **Autofill** (`Web Data` SQLite DB — form autofill entries)
- **Login Data** (`Login Data` SQLite DB — saved credential metadata; encrypted secret values require separate OS-level decryption the tool may or may not perform depending on platform/version — verify)
- **Bookmarks** (JSON file, not SQLite)
- **IndexedDB / LevelDB** (per-origin LevelDB stores, including parsing Chromium's custom Snappy-compressed LevelDB blob format — this is one of the library's more specialized capabilities)
- **Session/Tab restore state** (SNSS-format session files)
- **Cache** (Chromium disk cache block-file format, in some versions)

It ships as a Python package (`pip install ccl_chromium_reader` or run from source) with both an importable library API and standalone CLI scripts (commonly named per-artifact, e.g. a history-parsing script, a cookies-parsing script, an IndexedDB-parsing script — exact script names differ by version/release, confirm what's installed via the package's own listing or `--help`).

## Command syntax (verify — do not treat as fixed)

I do not have high confidence in exact current script names or flags for the installed version — the project has evolved from individual scripts toward more of a unified library API across releases. Before building a real command line:

```
python -m ccl_chromium_reader --help
```
or, if installed as standalone scripts, list what's on the PATH / in the package's `scripts`/`bin` directory and check each script's own `--help` or `-h`.

General shape you should expect (confirm exact form for your installed version):

```
<ccl_chromium_reader entry point> <artifact-type> -i <path to profile or specific DB file> -o <output path/format>
```

Where `-i` typically points either at a specific file (e.g., a copied-out `History` SQLite file) or at a whole profile directory (e.g., `.../Default/`), depending on the script/module. Output is often CSV/JSON/SQLite depending on the script and requested format.

If used as a library rather than CLI, the typical pattern is importing the relevant submodule (e.g., a history reader class, a cookies reader class) and calling it against a file path in a short Python script — confirm current class/module names against the installed version's source or README rather than assuming names from memory.

## Typical workflow

1. **Never parse artifacts in place against a live browser's active profile.** Work only against a copy — either an already-extracted profile folder from a disk image / mobile extraction, or a copy of a live user's profile folder made through a proper (write-blocked or otherwise justified/documented) acquisition step. This skill assumes that acquisition already happened.
2. **Identify the profile structure** — locate the relevant files/folders inside the Chromium user-data directory: `History`, `Cookies`, `Web Data`, `Login Data`, `Bookmarks`, the `IndexedDB/` subfolder, `Sessions/`/`Session Storage/`, `Cache/`. Layout is consistent across Chromium-derived browsers but the parent path differs (e.g., `Local\Google\Chrome\User Data\Default` on Windows-derived extractions, `~/Library/Application Support/Google/Chrome/Default` on macOS, `~/.config/google-chrome/Default` on Linux, and Chrome-on-Android's app-private data path in a full filesystem mobile extraction).
3. **Hash the source files before parsing** (or confirm the extraction's manifest hash covers them) so parsed results can be tied back to a verifiable source.
4. **Run the confirmed CLI script/module** against each artifact file or the whole profile, per its `--help` output, directing output to a case-specific analysis folder — never back into the extraction/evidence path.
5. **Cross-check timestamps.** Chromium timestamps are typically **WebKit/Chrome epoch** (microseconds since 1601-01-01), which differs from Unix epoch — confirm the tool's output already converts these, and if not, convert explicitly and note the conversion method used, since a wrong epoch assumption is a common source of forensic timestamp errors.
6. **Note encryption limitations explicitly.** Saved password values and some cookie values are encrypted using OS-level mechanisms (DPAPI on Windows, Keychain on macOS, kwallet/gnome-keyring or a hardcoded key path on Linux depending on version). Whether the parser decrypts these depends on the platform the parsing is run on and the specific tool version/build — verify this rather than assuming decrypted values will be present, and if values come back encrypted/opaque, report that as a limitation rather than treating a blank/garbled field as "no data."
7. **Correlate across artifacts and with the LEAPP report** if this profile was pulled from a mobile extraction already processed by `leapp-suite` — LEAPP's own browser-artifact plugins may already cover common cases, and this tool is most valuable for deeper IndexedDB/LevelDB parsing LEAPP's plugins may not fully cover.
8. **Hand off exported CSV/JSON with source-file provenance** to `forensic-reporting`.

## Troubleshooting

| Symptom | Likely cause | What to try |
|---|---|---|
| "database is locked" or similar SQLite error | Parsing against a live/open browser profile, or a copy made while the browser was running (WAL/journal files not fully flushed) | Work only against a proper closed-file copy; ensure any `-wal`/`-shm` sidecar files were copied alongside the main DB, since Chromium uses WAL mode and recent data may live there, not in the main file |
| Timestamps look decades off | WebKit/Chrome epoch not converted, or converted against the wrong epoch/units (seconds vs microseconds) | Verify the specific epoch/units the tool uses for that artifact type before trusting a converted value; spot-check one known-time entry against ground truth if available |
| Password/cookie values return empty or as encrypted blobs | OS-level encryption (DPAPI/Keychain/kwallet) not resolved by the tool on this platform | Document as a limitation; do not attempt ad hoc decryption with unverified keys/methods, and do not treat empty output as evidence no password was saved |
| IndexedDB parsing fails or returns nothing | LevelDB store format/version mismatch, corrupted `.ldb`/`.log` files from an incomplete extraction, or a newer schema than the tool version supports | Check the tool's changelog/issues for known schema-version gaps; verify the extraction actually copied the full `IndexedDB/` folder including `.ldb`, `.log`, and `MANIFEST` files, not just some of them |
| Bookmarks parse but History doesn't (or vice versa) | Different underlying formats (JSON vs SQLite) hit different failure modes independently | Diagnose each artifact type separately rather than assuming one failure implies all failed |

## What this skill must never do automatically

- Never run parsing directly against a live, currently-open browser profile — only against a copy/extraction already obtained through a proper acquisition step.
- Never invent script names, module names, class names, or CLI flags for `ccl_chromium_reader` beyond what's confirmed via the installed version's `--help`/README/source — flag uncertainty explicitly instead.
- Never attempt to decrypt OS-protected credential/cookie secrets using guessed keys or undocumented methods; report encrypted/opaque values as a limitation.
- Never assume a timestamp is Unix epoch without confirming the artifact's actual epoch convention (Chromium commonly uses WebKit/Chrome epoch, microseconds since 1601-01-01).
- Never write parser output back into the source evidence/extraction directory.
- Never claim tool presence/version on the examiner's PALADIN system was independently verified by Claude — only as reported via the user's own system inventory.
- Never present a parsed artifact as complete/authoritative without disclosing any parser errors or unparsed files encountered along the way.

