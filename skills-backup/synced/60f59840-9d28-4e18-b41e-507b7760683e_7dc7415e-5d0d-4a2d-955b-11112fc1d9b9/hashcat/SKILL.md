---
name: "hashcat"
description: "Run hashcat, the GPU-accelerated password/hash recovery tool, strictly for authorized forensic examiners recovering access to evidence they have legal authority to examine (e.g., an encrypted evidence container, or a suspect device under warrant/consent, within a documented case). Triggers on \"crack this hash with hashcat\", \"recover this password with GPU\", \"hashcat mode for\", \"brute force this hash\", \"dictionary attack with hashcat\", \"hashcat mask attack\". This is not a general \"crack any password\" tool and must not be used, or framed as usable, outside an authorized, documented forensic or legal workflow — decline or redirect requests that lack that context. Covers hash-mode identification, wordlist/rule/mask attack syntax, and session management; does not cover Wi-Fi key recovery (see aircrack-ng) or CPU-only workflows (see john-the-ripper)."
---

---
name: hashcat
description: Run hashcat, the GPU-accelerated password/hash recovery tool, strictly for authorized forensic examiners recovering access to evidence they have legal authority to examine (e.g., an encrypted evidence container, or a suspect device under warrant/consent, within a documented case). Triggers on "crack this hash with hashcat", "recover this password with GPU", "hashcat mode for", "brute force this hash", "dictionary attack with hashcat", "hashcat mask attack". This is not a general "crack any password" tool and must not be used, or framed as usable, outside an authorized, documented forensic or legal workflow — decline or redirect requests that lack that context. Covers hash-mode identification, wordlist/rule/mask attack syntax, and session management; does not cover Wi-Fi key recovery (see aircrack-ng) or CPU-only workflows (see john-the-ripper).
---

# hashcat

`hashcat` is a GPU-accelerated password and hash recovery tool. In forensic casework its legitimate use is narrow and specific: an examiner with documented legal authority (a warrant, consent, a court order, or equivalent lawful basis tied to a specific case) attempting to recover access to a piece of evidence they are authorized to examine — for example, an encrypted evidence container, a password-protected document recovered from a suspect's device, or a locally-recovered password hash from a system the examiner is lawfully processing.

**This is not a general-purpose "crack any password" capability.** It is not for accessing accounts, systems, or data the examiner does not have documented authority to examine. If a request doesn't include that context (a case, evidence item, and legal basis), ask for it before proceeding, or decline and explain why.

Presence of `hashcat` on this PALADIN system was reported by the user via their own system inventory, not independently verified by Claude.

## Before running anything

Establish and document, before cracking:

1. **What is the hash/evidence?** (e.g., "NTLM hash extracted from evidence drive image in Case #____", "hash of the password protecting an encrypted container recovered from evidence item #____")
2. **What is the legal basis for examining this evidence?** (warrant number, consent form, court order, or equivalent — record it, don't just assume it exists)
3. **Where did the hash come from, and how was it extracted?** — the extraction method matters for the report and should already be documented elsewhere (e.g., via the imaging/analysis skill that produced it).

If any of this is missing or the request sounds like it's about a system/account the user doesn't have documented authority over, stop and ask, rather than proceeding on an implied justification.

## Core concepts

| Concept | What it means |
|---|---|
| Hash mode (`-m`) | Numeric code identifying the hash algorithm/format (e.g., NTLM, bcrypt, a specific encrypted-container format). Must match the actual hash type or hashcat won't be attacking the real algorithm. |
| Attack mode (`-a`) | How candidate passwords are generated: straight/dictionary (`0`), combination (`1`), brute-force/mask (`3`), hybrid (`6`/`7`), etc. |
| Wordlist | A file of candidate passwords tried directly or as a base for rules |
| Rules | Transformations applied to wordlist entries (append digits, leading capital, leet-speak substitutions, etc.) |
| Mask | A brute-force pattern describing character sets per position (e.g., `?u?l?l?l?l?d?d` = capital, 4 lowercase, 2 digits) |
| Potfile | hashcat's running record of already-cracked hash:password pairs, reused across sessions |

## Core syntax

Verify exact flags, hash-mode numbers, and mask syntax against `hashcat --help` / `hashcat --example-hashes` on the installed system before relying on them — hash-mode numbers in particular are version-specific and change as new modes are added; do not assume a mode number from memory is current.

```
hashcat -m <hash_mode> -a <attack_mode> <hash_file> [wordlist|mask] [options]
```

Common flags:

| Flag | Purpose |
|---|---|
| `-m <N>` | Hash mode/algorithm identifier — find the correct number with `hashcat --help` (grep for the algorithm name) |
| `-a 0` | Straight/dictionary attack |
| `-a 3` | Brute-force/mask attack |
| `-r <rule_file>` | Apply a rule file to wordlist candidates |
| `-o <file>` | Write cracked results to a file |
| `--show` | Show already-cracked hashes from the potfile without re-running the attack |
| `--status` | Enable periodic status updates during a run |
| `-w <1-4>` | Workload profile (higher = more aggressive GPU use, may affect system responsiveness) |
| `--session=<name>` | Name a session so it can be paused/resumed |
| `--restore` | Resume a previously interrupted session |
| `-1`, `-2`, `-3`, `-4` | Define custom charsets for mask attacks |

## Typical documented workflow

1. **Identify the hash format.** Use `hashcat --help` (or `hashID`/`name-that-hash` if available) to determine the correct `-m` value — running against the wrong mode wastes time and produces no valid result even if the password would otherwise be found.
2. **Choose an attack strategy proportionate to the case**, and document the choice:
   - Dictionary + rules first (fastest, most likely to succeed against real-world passwords), e.g. `hashcat -m <mode> -a 0 hash.txt wordlist.txt -r rules/best64.rule`
   - Mask/brute-force for known patterns (e.g., "we know it's an 8-character PIN") or as a fallback after dictionary attempts are exhausted
3. **Run with output logged and status enabled**, not just watched interactively:
   ```
   hashcat -m <mode> -a 0 -o /path/case_cracked.txt --status /path/hash.txt /path/wordlist.txt
   ```
4. **Record exactly**: hash mode used, attack type, wordlist/rule/mask used, start/end time, and the resulting output (or lack thereof). A failed attempt is still a documented fact for the case file, not a gap to omit.
5. **Verify the recovered password actually works** against the evidence (e.g., successfully decrypts the container) before relying on it — a hashcat "cracked" result should be confirmed against the original evidence.
6. **Do not reuse or disclose recovered passwords outside the case's documented chain of custody.**

## Troubleshooting

| Symptom | Likely cause | What to check |
|---|---|---|
| `hashcat: command not found` | Not installed or not on PATH | `which hashcat`; confirm GPU drivers/OpenCL-CUDA runtime are present for GPU acceleration |
| `No devices found`/falls back to CPU only | Missing or misconfigured GPU driver/runtime | Check `hashcat -I` (device info) against `--help` for the current flag name; confirm proprietary GPU drivers are loaded on this boot environment (live/forensic boot environments often lack them) |
| Hash rejected as "not in a valid format" | Wrong hash mode (`-m`), malformed hash string, or wrong file encoding | Re-derive the exact hash string and format from the extraction tool's actual output; check `hashcat --example-hashes` for the expected format of the mode in use |
| Attack finishes with no result | Password not in wordlist/rule/mask space tried | Document the negative result; consider a different wordlist, added rules, or a mask attack informed by known password-policy constraints — don't fabricate a "likely" password |
| Extremely slow performance | Running on CPU instead of GPU, thermal throttling, or an expensive hash mode (e.g., bcrypt is intentionally slow to crack by design) | Confirm GPU is actually engaged (`--status` device utilization); understand that some algorithms are deliberately cracking-resistant and may not be feasible to recover in case timeframe |
| Session interrupted (power loss, closed terminal) | Long-running crack without `--session` set | Use `--session=<name>` from the start so `--restore` can resume rather than starting over |

## What this skill must never do automatically

- Run against a hash, account, or system without the user first stating the case context and legal basis for the examination — ask if it isn't given.
- Frame usage as generic "crack any password" capability, or provide guidance that reads as an attack tutorial divorced from an authorized forensic workflow.
- Recommend or perform cracking against live production systems, third-party accounts, or anything outside the specific evidence item in question.
- Fabricate a hash-mode number, cracked password, or "likely" result not actually produced by a real hashcat run.
- Disclose or log recovered passwords outside the documented case record, or suggest reusing them for any purpose beyond the authorized evidence access.
- Assume GPU acceleration is available/working on the live forensic boot environment without checking.

## Handoff

- Where the hash originated (extracted from an image, container, or file) → whichever acquisition/analysis skill produced it (e.g., `paladin-forensic-workflow`).
- CPU-based alternative or complement, especially for hash types hashcat handles less efficiently → `john-the-ripper`.
- Recovered credentials, attack parameters, and timing → `forensic-reporting`, with explicit note of legal authority on file.

