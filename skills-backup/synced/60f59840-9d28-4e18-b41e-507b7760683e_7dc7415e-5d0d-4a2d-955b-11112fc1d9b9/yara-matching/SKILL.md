---
name: "yara-matching"
description: "Run YARA pattern-matching (the `yara` CLI, custom .yar/.yara rule files, or public rule sets) against extracted files or a mounted evidence copy to identify malware families, packers, or specific artifacts by byte/string/structural pattern. Triggers on \"run yara\", \"match yara rules\", \"write a yara rule\", \"identify this malware family\", \"scan with custom rules\", \"yara-python\". Use for targeted, rule-based identification of known or suspected patterns — not a substitute for signature-database AV sweeps (see clamav-scanning) and not dynamic/behavioral analysis. Always run against copies or read-only-mounted evidence, never the original device."
---

---
name: yara-matching
description: Run YARA pattern-matching (the `yara` CLI, custom .yar/.yara rule files, or public rule sets) against extracted files or a mounted evidence copy to identify malware families, packers, or specific artifacts by byte/string/structural pattern. Triggers on "run yara", "match yara rules", "write a yara rule", "identify this malware family", "scan with custom rules", "yara-python". Use for targeted, rule-based identification of known or suspected patterns — not a substitute for signature-database AV sweeps (see clamav-scanning) and not dynamic/behavioral analysis. Always run against copies or read-only-mounted evidence, never the original device.
---

# YARA Pattern Matching

YARA is a pattern-matching engine that identifies files based on rules combining strings, byte sequences, and structural conditions ("if this file contains string X, and byte pattern Y, and is a PE, and is larger than Z bytes, flag it"). In forensic work it's used to identify malware families, packers, specific tools, or case-specific artifacts that a generic AV signature database (ClamAV) may not catalog.

Presence of `yara`/`yara-python` on this PALADIN system was reported by the user via their own system inventory, not independently verified by Claude.

## What YARA is and is not

- **Is:** a rule-based pattern matcher — as good as the rules loaded against it. Public rule sets (e.g., community malware-family rule repositories) and custom, case-specific rules the examiner writes.
- **Is not:** a self-updating threat database like ClamAV's signature feed, a behavioral/sandbox tool, or a guarantee of "no match = benign." A miss means "no loaded rule matched," nothing more.
- Complements `clamav-scanning` (broad known-signature sweep) — YARA is typically used for the follow-up targeted pass once ClamAV/triage has narrowed down files of interest, or when the examiner already has intelligence about a specific pattern (a known IOC string, a packer signature, a suspicious PE section).

## Core syntax

Verify exact flags against `yara --help` / `man yara` on the installed system before relying on them in a report — the following reflects general knowledge of YARA's documented CLI, not a live version check on this system.

```
yara [options] <rule_file.yar> <target_file_or_directory>
```

Common flags:

| Flag | Purpose |
|---|---|
| `-r` | Recursively scan a directory |
| `-s` | Print matching strings, not just rule names |
| `-m` | Print metadata defined in the rule |
| `-c` | Print number of matches per rule (count) |
| `-n` | Only print non-matching rules (rarely useful in triage; mostly for rule debugging) |
| `-w` | Suppress warnings |
| `-f` | Fast matching mode (skips some string-matching optimizations trade-offs — confirm current behavior) |
| `-x <module>=<file>` | Pass external data to a module (e.g., for the `cuckoo` module) |
| `-t <tag>` | Only evaluate rules with a given tag |
| Multiple rule files | `yara` accepts a single rule file per invocation in some versions — for multiple rule files, concatenate/include them in one `.yar` via `include` statements, or check whether the installed version supports passing several rule files directly |

## Basic rule anatomy (for reference, not invention)

A YARA rule has a `strings` section (text/hex/regex patterns to look for) and a `condition` section (boolean logic over those strings plus metadata like file size or PE characteristics). If asked to write a custom rule, base it strictly on patterns the examiner has actually observed (e.g., a string extracted from a sample, a known hash, a documented IOC) — do not invent a "plausible-looking" byte pattern and present it as a working detection. A minimal, honestly-scoped example shape:

```
rule Example_Suspicious_String
{
    meta:
        description = "Matches a specific string observed in case artifact X"
        author = "examiner"
        date = "YYYY-MM-DD"
    strings:
        $s1 = "exact-string-observed-in-sample" ascii
    condition:
        $s1
}
```

Confirm rule syntax details (module imports like `pe`, `hash`, `math`; regex flavor; string modifiers like `nocase`, `wide`, `fullword`) against current YARA documentation rather than assuming — syntax has evolved across YARA versions.

## Typical forensic workflow

1. **Work against a copy or read-only mount**, never the original evidence device.
2. **Choose rule sources deliberately** and document which ones were used:
   - Public/community rule sets (note the exact repository and commit/version used, since rule sets update over time and results should be reproducible)
   - Case-specific custom rules the examiner writes from observed IOCs
3. **Run the scan with output logged**, not just terminal output:
   ```
   yara -r -s -m /path/to/rules.yar /path/to/mounted_or_extracted_evidence > /path/to/case_yara_results.txt
   ```
4. **Record exactly which rule matched, which strings triggered it, and the file path** — this is the evidentiary trail, not just "YARA flagged something."
5. **Treat every match as a lead, not a conclusion.** A match against a public "APT-tool-X" rule means the file contains patterns associated with that rule — confirm with additional analysis (hash lookups, ClamAV cross-check, manual inspection) before asserting attribution or family identity in a report.
6. **Version and hash the rule file(s) used** alongside the scan results, so the match is reproducible later.

## Troubleshooting

| Symptom | Likely cause | What to check |
|---|---|---|
| `yara: command not found` | Not installed or not on PATH | `which yara`; confirm `yara-python` vs. CLI binary distinction if scripting |
| Rule fails to compile | Syntax error, unsupported module, or version mismatch (rule written for a newer/older YARA) | Check the exact error line; confirm installed YARA version with `yara --version` against rule set's stated compatibility |
| No matches on a file believed to be malicious | Rule set doesn't cover this variant, sample is packed/encrypted, or wrong rule file loaded | Don't conclude "clean" — note "no match with rules used," consider `clamav-scanning`, manual inspection, or sourcing more targeted rules |
| Extremely slow scan over large evidence set | Regex-heavy rules, very large files, recursive scan over huge directory tree | Consider scoping to a targeted subset first (e.g., only executables) rather than scanning everything with expensive rules |
| False-positive-feeling match on a clearly benign file | Overly broad rule (short/common string, weak condition) | Inspect the matched string(s) with `-s`; note in the report that the rule may need tightening rather than treating the match as confirmed malicious |

## What this skill must never do automatically

- Scan the original evidence device or a write-enabled mount.
- Invent YARA syntax, module names, or rule logic not grounded in actual YARA documentation or an observed working example — flag uncertainty and point to `yara --help`/docs instead.
- Fabricate a "case-specific" rule from assumed/guessed IOCs rather than strings/patterns the examiner actually extracted from evidence.
- Present a rule match as confirmed malware family attribution rather than a pattern match requiring further corroboration.
- Auto-download and load a public rule set from an arbitrary internet source without the examiner choosing and confirming the source.

## Handoff

- Broad known-malware sweep before/alongside targeted rule matching → `clamav-scanning`.
- Deeper network-side correlation of anything flagged that touches captured traffic → `tshark-wireshark` / planned `wireshark-pcap-analysis`.
- Match results, rule provenance, and confidence-graded findings → `forensic-reporting`.
- Evidence mounting/read-only setup → `paladin-forensic-workflow`.

