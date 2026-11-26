---
name: "clamav-scanning"
description: "Run ClamAV (clamscan CLI, freshclam signature updates, clamtk GUI) to scan extracted files, mounted evidence copies, or exported artifacts for known malware signatures during forensic examination. Triggers on \"scan for malware\", \"run clamav\", \"clamscan this folder\", \"check for known viruses\", \"update virus definitions\", \"clamtk\", \"AV scan the evidence\". Signature-based detection only — flags known/cataloged threats, does not detect novel or obfuscated malware (see yara-matching for custom pattern rules) and does not perform behavioral/dynamic analysis or reverse engineering. Always scan a copy or read-only-mounted image, never the original evidence device directly."
---

---
name: clamav-scanning
description: Run ClamAV (clamscan CLI, freshclam signature updates, clamtk GUI) to scan extracted files, mounted evidence copies, or exported artifacts for known malware signatures during forensic examination. Triggers on "scan for malware", "run clamav", "clamscan this folder", "check for known viruses", "update virus definitions", "clamtk", "AV scan the evidence". Signature-based detection only — flags known/cataloged threats, does not detect novel or obfuscated malware (see yara-matching for custom pattern rules) and does not perform behavioral/dynamic analysis or reverse engineering. Always scan a copy or read-only-mounted image, never the original evidence device directly.
---

# ClamAV Scanning

ClamAV is an open-source, signature-based antivirus engine. In a forensic context it is used to sweep extracted files, exported artifacts, or a read-only-mounted evidence image against a database of known malware signatures — a fast triage step to flag already-cataloged threats, not a substitute for deeper malware analysis.

Presence of ClamAV (`clamscan`, `freshclam`, `clamtk`) on this PALADIN system was reported by the user via their own system inventory, not independently verified by Claude.

## What ClamAV is and is not

- **Is:** a signature/hash/heuristic matcher against ClamAV's own signature database (`.cvd`/`.cld` files), covering known viruses, trojans, and other cataloged malware families.
- **Is not:** a behavioral or sandboxed dynamic-analysis tool, a general-purpose YARA rule engine (though ClamAV does support loading some YARA-compatible rules — see below), or proof of "clean" — a miss means "not matched to a known signature," not "benign."
- Complements `yara-matching` (custom/public pattern rules, better for targeted or non-mainstream threats) and any dynamic/sandbox analysis the examiner performs separately.

## Core components

| Component | Purpose |
|---|---|
| `clamscan` | Command-line, single-threaded on-demand scanner |
| `clamdscan` | Client for the `clamd` daemon (faster on repeat scans since signatures stay loaded in memory) — only usable if `clamd` is installed/running |
| `freshclam` | Updates the local signature database from ClamAV's mirrors |
| `clamtk` | GUI front-end for `clamscan`/`clamd`, useful for examiners who prefer a visual workflow |
| `sigtool` | Inspect/build/convert signature databases |

## Core syntax

Verify exact flags against `clamscan --help` / `man clamscan` on the installed system before relying on them in a report — the following reflects general knowledge of ClamAV's documented options, not a live version check on this system.

```
clamscan [options] <file_or_directory>
```

Common flags:

| Flag | Purpose |
|---|---|
| `-r`, `--recursive` | Scan directories recursively |
| `-i` | Only print infected files (suppress clean-file noise) |
| `--infected` | Same intent as `-i` in some versions — confirm current name |
| `-l <file>`, `--log=<file>` | Write scan results to a log file |
| `--move=<dir>` | Move infected files to a quarantine directory (destructive — see cautions below) |
| `--copy=<dir>` | Copy (not move) infected files to a directory for later review — safer default than `--move` |
| `--remove` | Delete infected files outright (destructive — avoid on evidence) |
| `--max-filesize=`, `--max-scansize=` | Size limits per file / per scan session |
| `--bytecode=yes/no` | Enable/disable bytecode signature execution |
| `-d <file/dir>` | Load additional/custom signature database |
| `freshclam` | Run with no args to update signatures using the configured mirror; `--version` to check current DB version |

## Typical forensic workflow

1. **Never scan the original evidence device or a live write-enabled mount.** Work against:
   - A forensic image mounted **read-only**, or
   - A copy of exported/extracted files in a working directory.
2. **Update signatures first** (unless the case requires scanning with a specific, documented signature-database snapshot for reproducibility):
   ```
   freshclam
   ```
   Note the resulting database version/date for the report — a scan's findings are only as current as the signatures used.
3. **Run the scan against the copy**, logging output rather than relying on terminal scrollback:
   ```
   clamscan -r -i --log=/path/to/case_scan.log /path/to/mounted_or_extracted_evidence
   ```
4. **Do not pass `--move` or `--remove` against evidence.** If quarantine/isolation of a flagged file is needed, use `--copy=<dir>` to a working directory, preserving the original file in place, and document the copy action.
5. **Review every hit manually** — note the exact signature name ClamAV reports (e.g., `Win.Trojan.Foo-12345`), the full file path, and the scan log timestamp. A signature name is a lead for further research, not a final verdict on file behavior.
6. **Cross-reference** ambiguous or interesting hits with `yara-matching` custom rules or external threat-intel lookups, and note in the report that ClamAV's result reflects signature matching only.

## Troubleshooting

| Symptom | Likely cause | What to check |
|---|---|---|
| `clamscan: command not found` | Not installed or not on PATH | `which clamscan`; don't assume presence system-wide |
| `ERROR: Can't open file` on many files | Permission issue, or scanning a raw/locked device node | Confirm you're scanning a mounted read-only copy, not a raw device; check file permissions |
| Signature DB outdated / freshclam fails | No network access on an air-gapped forensic workstation | Confirm network policy for the exam machine; some labs maintain an offline signature-update process — check local procedure before assuming failure |
| Scan extremely slow | Very large directory tree, huge files, or scanning over a slow mount | Consider `--max-filesize`/`--max-scansize` limits (document if used, since they can cause missed detections in oversized files), or scan targeted subsets |
| Everything reports clean on a suspected-malicious file | Signature DB doesn't cover this threat, sample is packed/obfuscated, or it's genuinely benign | Escalate to `yara-matching` with targeted rules and/or manual/dynamic analysis — do not report "confirmed clean," report "no signature match" |
| `clamtk` won't launch / permission dialogs | GUI front-end usually needs the same permissions as `clamscan`/`clamd` underneath | Check it's pointed at the correct scan target, not a live system path |

## What this skill must never do automatically

- Scan, move, or remove files on the original evidence device or a write-enabled mount.
- Use `--move` or `--remove` against any evidence-derived file without explicit user confirmation, given both options alter or delete the original file.
- Report a clean scan as proof of "no malware present" — it only means "no known-signature match at the time of scan with the DB version used."
- Skip logging the signature database version/date used for the scan.
- Auto-submit or upload scanned evidence files to any external service (e.g., online multi-AV scanners) — that is a data-exfiltration/chain-of-custody decision requiring explicit user direction.

## Handoff

- Ambiguous hits or files needing custom pattern matching → `yara-matching`.
- Findings, scan logs, and signature DB version → `forensic-reporting`.
- Evidence mounting/read-only setup → `paladin-forensic-workflow`.

