---
name: "john-the-ripper"
description: "Run John the Ripper (john), the CPU-based password/hash recovery tool, strictly for authorized forensic examiners recovering access to evidence they have legal authority to examine (e.g., an encrypted evidence container, or a suspect device under warrant/consent, within a documented case). Triggers on \"crack this with john\", \"john the ripper\", \"run johnny\", \"unshadow\", \"crack this zip/office/pdf password\", \"single crack mode\". Not a general \"crack any password\" tool — decline or redirect requests lacking documented case/legal-authority context. Covers format detection, wordlist/rules/incremental modes, and session management; complements hashcat (GPU-accelerated, often faster for supported hash types) and does not cover Wi-Fi key recovery (see aircrack-ng)."
---

---
name: john-the-ripper
description: Run John the Ripper (john), the CPU-based password/hash recovery tool, strictly for authorized forensic examiners recovering access to evidence they have legal authority to examine (e.g., an encrypted evidence container, or a suspect device under warrant/consent, within a documented case). Triggers on "crack this with john", "john the ripper", "run johnny", "unshadow", "crack this zip/office/pdf password", "single crack mode". Not a general "crack any password" tool — decline or redirect requests lacking documented case/legal-authority context. Covers format detection, wordlist/rules/incremental modes, and session management; complements hashcat (GPU-accelerated, often faster for supported hash types) and does not cover Wi-Fi key recovery (see aircrack-ng).
---

# John the Ripper

`john` (John the Ripper) is a CPU-based password and hash recovery tool with broad built-in format support (shadow-file hashes, ZIP/Office/PDF password protection, many encrypted-container and application hash formats) and a mature rules/mangling-rule ecosystem. In forensic casework its legitimate use is the same narrow scope as `hashcat`: an examiner with documented legal authority recovering access to evidence they are authorized to examine.

**This is not a general-purpose "crack any password" capability.** It is not for accessing accounts, systems, or data the examiner does not have documented authority over. If a request doesn't include case and legal-basis context, ask for it before proceeding, or decline and explain why.

Presence of `john` on this PALADIN system was reported by the user via their own system inventory, not independently verified by Claude.

## Before running anything

Same as any password-recovery workflow — establish and document before cracking:

1. **What is the hash/protected file, and what case/evidence item does it belong to?**
2. **What is the legal basis for examining this evidence?** (warrant, consent, court order — record it)
3. **How was the hash/file extracted, and by what tool?** (should already be documented by the extraction step)

If any of this is missing, or the target sounds like a system/account outside the examiner's documented authority, stop and ask rather than assuming justification.

## Core concepts

| Concept | What it means |
|---|---|
| Format (`--format=`) | The hash/file type John should attack (e.g., a shadow hash type, `zip`, `office`, `pdf`, a raw hash format). John can often auto-detect but explicit format avoids ambiguity. |
| Cracking modes | **Single crack** (fast, uses username/GECOS-derived guesses — good first pass), **Wordlist** (dictionary + optional rules), **Incremental** (brute-force through character sets, most exhaustive and slowest) |
| Rules | Mangling rules applied to wordlist entries (case changes, appended digits, substitutions) — John ships default rule sets |
| `*2john` helper scripts | Format-conversion utilities (e.g., `zip2john`, `office2john`, `pdf2john`, `ssh2john`) that extract a crackable hash string from a protected file so `john` can attack it |
| `unshadow` | Combines `/etc/passwd` and `/etc/shadow` into a single crackable format for Unix account hashes (relevant if examining a Linux system image, not for third-party live systems) |
| `.pot` file | John's running record of cracked hash:password pairs (`john.pot`), reused across sessions |

## Core syntax

Verify exact flags and format names against `john --help` / `man john` on the installed system before relying on them — format names in particular vary by version and by whether Jumbo-patched John is installed (which adds many more format types than stock John).

```
john [options] <hash_file>
```

Common flags:

| Flag | Purpose |
|---|---|
| `--format=<name>` | Specify hash/file format explicitly |
| `--wordlist=<file>` | Dictionary attack using the given wordlist |
| `--rules[=<ruleset>]` | Apply mangling rules to wordlist candidates |
| `--incremental[=<mode>]` | Brute-force mode using a character-set/length model |
| `--single` | Single crack mode (fast, login/GECOS-based guesses) |
| `--show` | Show cracked results from the `.pot` file for a given hash file |
| `--status` | Check progress of a running/backgrounded session |
| `--session=<name>` | Name a session for later `--restore` |
| `--restore=<name>` | Resume a named session |
| `--fork=<N>` | Run N parallel processes (multi-core CPU use) |

`*2john` helper scripts (naming and exact set vary by distro/build — confirm which are installed with `ls`/tab-completion, e.g. `zip2john`, `office2john`, `pdf2john`, `rar2john`, `ssh2john`):
```
zip2john protected.zip > hash.txt
office2john protected.docx > hash.txt
pdf2john protected.pdf > hash.txt
```

## Typical documented workflow

1. **Extract a crackable hash from the protected file**, if applicable, using the matching `*2john` helper:
   ```
   zip2john /path/evidence.zip > /path/case_hash.txt
   ```
2. **Try single crack mode first** — fastest, and surprisingly effective against passwords derived from usernames/known identifiers relevant to the case:
   ```
   john --single --format=<format> /path/case_hash.txt
   ```
3. **Move to wordlist + rules** if single mode doesn't succeed:
   ```
   john --wordlist=/path/wordlist.txt --rules --format=<format> /path/case_hash.txt
   ```
4. **Fall back to incremental/brute-force** only as a documented last resort given its time cost:
   ```
   john --incremental --format=<format> /path/case_hash.txt
   ```
5. **Check results** with `--show` rather than assuming from console scrollback:
   ```
   john --show --format=<format> /path/case_hash.txt
   ```
6. **Record format used, mode, wordlist/rules, start/end time, and result (including negative results).**
7. **Verify the recovered password actually opens/decrypts the evidence file** before relying on it in the case record.

## Troubleshooting

| Symptom | Likely cause | What to check |
|---|---|---|
| `john: command not found` | Not installed, or only Jumbo build has the needed `*2john` script | `which john`; check if this is stock John or the community "Jumbo" build, since format support differs significantly |
| `*2john` script not found for a given file type | Script not included in this John build, or wrong script name | List available `*john` scripts on the system rather than assuming one exists; confirm the exact file type first |
| "No password hashes loaded" | Format mismatch, malformed hash line, or the `*2john` extraction produced no usable hash (e.g., unsupported encryption variant) | Re-check `--format=` against `john --list=formats`; confirm the hash file's contents look like a valid John hash line |
| Session appears to hang with no output | Long-running incremental/wordlist attack with `--status` not checked | Press a key or check `--status` in another terminal per John's interactive status convention; don't assume it's frozen |
| Cracked in single/wordlist mode already (per `.pot`) but `john` reruns anyway | Normal — John will still process the file but `--show` reveals already-known results | Run `--show` first before re-launching an attack against an already-solved hash |
| Extremely slow vs. hashcat on the same hash type | John is CPU-bound; some hash types are far more efficient on GPU | Consider `hashcat` for GPU-parallelizable formats if available and appropriate for the case |

## What this skill must never do automatically

- Run against a hash or protected file without the user first stating case context and legal basis — ask if not given.
- Frame usage as generic "crack any password" capability or provide attack-tutorial-style guidance divorced from an authorized forensic workflow.
- Run `unshadow`/attack account hashes from any system other than evidence the examiner is authorized to process.
- Fabricate a format name, `*2john` script name, or cracked result not actually produced by a real run.
- Disclose recovered passwords outside the documented case record.

## Handoff

- GPU-accelerated alternative or complement for supported hash types → `hashcat`.
- Where the protected file/hash originated → whichever acquisition/analysis skill produced it (e.g., `paladin-forensic-workflow`).
- Recovered credentials, attack parameters, and timing → `forensic-reporting`, with explicit note of legal authority on file.

