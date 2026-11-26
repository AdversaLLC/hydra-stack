---
name: "dumpzilla"
description: "Extracts and parses Firefox (and other Mozilla/Gecko-based browser, e.g. Thunderbird/Tor Browser where applicable) profile artifacts — history, downloads, cookies, cache, form/search history, saved passwords (encrypted), bookmarks, add-ons, and preferences — from an already-extracted browser profile directory using dumpzilla (Busindre). Trigger on \"run dumpzilla\", \"parse this Firefox profile\", \"get Firefox history\", \"extract Firefox cookies\", \"Firefox form history\", \"what did they search for in Firefox\", or \"analyze this Mozilla profile\". Operates read-only against a copy of an already-extracted .default/profile folder (places.sqlite, cookies.sqlite, formhistory.sqlite, etc.) — does not connect to a live running browser, does not itself decrypt the master-password-protected password store without the master password/key being supplied, and is not a disk-imaging or mobile-extraction tool (see paladin-forensic-workflow and leapp-suite for those steps)."
---

---
name: dumpzilla
description: Extracts and parses Firefox (and other Mozilla/Gecko-based browser, e.g. Thunderbird/Tor Browser where applicable) profile artifacts — history, downloads, cookies, cache, form/search history, saved passwords (encrypted), bookmarks, add-ons, and preferences — from an already-extracted browser profile directory using dumpzilla (Busindre). Trigger on "run dumpzilla", "parse this Firefox profile", "get Firefox history", "extract Firefox cookies", "Firefox form history", "what did they search for in Firefox", or "analyze this Mozilla profile". Operates read-only against a copy of an already-extracted `.default`/profile folder (places.sqlite, cookies.sqlite, formhistory.sqlite, etc.) — does not connect to a live running browser, does not itself decrypt the master-password-protected password store without the master password/key being supplied, and is not a disk-imaging or mobile-extraction tool (see paladin-forensic-workflow and leapp-suite for those steps).
---

# Dumpzilla (Firefox/Gecko Profile Parser)

## What this is

**Dumpzilla** (by Busindre, Python-based, single-script tool) parses the SQLite databases and supporting files inside a Firefox (or other Gecko-based browser, e.g. Thunderbird, Tor Browser, SeaMonkey — coverage for non-Firefox Gecko browsers may be partial, verify) profile directory and prints/exports the artifacts it finds. It is read-only against the profile files it is pointed at.

Artifacts it can extract (to the best of documented knowledge — confirm current coverage against the tool's own `-h`/README for the installed version, since dumpzilla has had periodic updates as Firefox's internal schemas changed):
- **Browsing history and downloads** (`places.sqlite`)
- **Cookies** (`cookies.sqlite`), including flags for filtering by domain/date
- **Cache** entries (Firefox cache directory/format)
- **Form history / search bar history** (`formhistory.sqlite`)
- **Saved logins** (`logins.json` / legacy `signons.sqlite`) — values are encrypted via NSS (`key4.db`/legacy `key3.db`); dumpzilla can decrypt these **only if it has access to the correct NSS key database alongside the profile and, if a master password was set by the user, that master password is supplied** — without the master password, encrypted credential values cannot be recovered
- **Bookmarks**
- **Add-ons/extensions** installed
- **Preferences** (`prefs.js`) relevant to privacy/security settings (e.g., proxy settings, DNS-over-HTTPS, private browsing defaults)
- **Session/tab restore data** (`sessionstore.jsonlz4` or similar, format has changed across Firefox versions)

## Command syntax (verify against `-h` — flags are numerous and version-sensitive)

I do not have high confidence in the complete, current flag set — dumpzilla has many single-letter flags for selecting artifact categories and output options, and exact flags/behavior can differ by release. Always confirm with:

```
python3 dumpzilla.py --help
```

General shape (confirm every flag before using it in a real procedure):

```
python3 dumpzilla.py <path_to_profile_folder> [--Cookies] [--Historial|--History] [--Forms] [--Downloads] [--Bookmarks] [--Addons] [--Passwords] [--Cache] [--Session] [--Summary] [-o <output_dir>]
```

- The **first positional argument** is the path to the Firefox profile folder (the one containing `places.sqlite`, `prefs.js`, etc.), not an individual file.
- Category flags (cookies, history, forms, downloads, bookmarks, add-ons, passwords, cache, session) select which artifact types to output — running with no category flags may print a summary or require at least one flag, verify current default behavior for the installed version.
- Filtering flags for domain, date range, or keyword search commonly exist in dumpzilla but exact flag names/spellings should be confirmed via `--help` rather than assumed.
- Output is typically printed to stdout and can usually be redirected/exported; check `--help` for a dedicated export/output flag versus simple shell redirection.

## Typical workflow

1. **Work only against a copy of the profile**, obtained from a disk image, a mobile extraction (Firefox for Android/iOS uses a similar but not always identical profile layout — verify), or a properly justified/documented live acquisition. Never point dumpzilla at a live user's active profile directory.
2. **Confirm the profile folder is complete** — a partial copy missing `key4.db` (or legacy `key3.db`) alongside `logins.json` will prevent password decryption even with the correct master password, since the decryption key material lives in that file.
3. **Hash the source files** before parsing so results are tied to a verifiable source.
4. **Run dumpzilla with `--help` first** to confirm current flags for the installed version, then run with the specific artifact-category flags needed rather than guessing a "get everything" flag exists.
5. **If saved passwords are in scope and a master password was used**, this requires either the master password (if lawfully obtained/known) or documented inability to decrypt — do not attempt to brute-force or guess the master password as a default step; treat that as a separate, explicitly-authorized action if pursued at all.
6. **Note Firefox timestamp conventions.** `places.sqlite` typically stores visit times as **microseconds since Unix epoch** (different from Chromium's WebKit epoch) — confirm the tool's displayed timestamps are already converted correctly rather than assuming.
7. **Export/redirect output to a case analysis folder**, never back into the evidence/extraction path.
8. **Hand off exported artifacts with source-file provenance** to `forensic-reporting`.

## Troubleshooting

| Symptom | Likely cause | What to try |
|---|---|---|
| "no such file" / profile not recognized | Pointed at a parent folder or a single file instead of the actual profile directory (the one containing `places.sqlite` directly) | Point at the specific `<hash>.default` (or `.default-release`) folder, not `Profiles/` or a single `.sqlite` file |
| Passwords show as encrypted/unreadable | No master password supplied, or `key4.db`/`key3.db` missing from the copied profile | Confirm whether a master password exists on this profile; if known/authorized, supply it per the tool's password-input method (verify via `--help`); otherwise document as a limitation — do not attempt unauthorized decryption |
| History/cookies queries return nothing despite file being present | SQLite file locked/corrupted from being copied while Firefox was running (missing WAL/SHM sidecar files) | Ensure `-wal` and `-shm` sidecar files were copied alongside the main `.sqlite` file; Firefox uses WAL mode and recent activity may only exist there |
| Cache or session data won't parse | Format changed across Firefox versions (e.g., `sessionstore.jsonlz4` compression, cache2 format changes) | Check dumpzilla's version/changelog against the source browser's version; note as a limitation if the tool predates the source Firefox version's format |
| Script errors out with a Python exception on a specific profile | Version mismatch between dumpzilla release and the Firefox schema version that produced the profile | Check for a newer dumpzilla release; note the exact Firefox version if known and flag the parsing gap rather than forcing output |

## What this skill must never do automatically

- Never run against a live, currently-open Firefox profile — only against a copy from a completed, documented acquisition.
- Never attempt to guess, brute-force, or bypass a Firefox master password to decrypt saved logins without separate, explicit authorization/justification for that specific action.
- Never invent dumpzilla flags beyond what's confirmed via `--help`/README for the installed version — flag uncertainty explicitly rather than presenting guessed syntax as fact.
- Never assume Firefox's timestamp convention matches Chromium's (they differ) — confirm the actual epoch/units before reporting a converted time as fact.
- Never write output back into the source evidence/extraction directory.
- Never claim dumpzilla's presence/version on the examiner's PALADIN system was independently verified by Claude — only as reported via the user's own system inventory.
- Never omit disclosure of missing sidecar files (`-wal`/`-shm`), missing key databases, or version-mismatch parsing gaps when summarizing results.

