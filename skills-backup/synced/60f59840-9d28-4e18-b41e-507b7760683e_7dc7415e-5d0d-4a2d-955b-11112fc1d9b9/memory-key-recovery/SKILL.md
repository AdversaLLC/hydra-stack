---
name: "memory-key-recovery"
description: "Recover AES key schedules from an already-acquired RAM image using aeskeyfind and aesfix — cold-boot-attack tools that scan raw memory for the expanded key schedule AES key expansion leaves behind, and reconstruct a likely correct key from a candidate with bit errors. For legitimate forensic use by an examiner with legal authority to recover a key for an encrypted volume on evidence they are authorized to examine (e.g., a seized/consented device with full-disk/volume encryption) — not a generic \"crack encryption\" or \"hack password\" tool, and not applicable beyond AES key schedules found in memory. Triggers on \"find AES keys in memory\", \"aeskeyfind\", \"aesfix\", \"recover encryption key from RAM\", \"cold boot attack\", \"BitLocker/TrueCrypt/VeraCrypt/LUKS key from memory dump\", or \"candidate key has bit errors\". Excludes memory acquisition (out of scope) and process/network/malware analysis (see volatility3 / volatility2-legacy)."
---

# aeskeyfind + aesfix — Memory-Resident AES Key Recovery

## Legal and ethical framing

This is a **legitimate forensic technique** used by examiners with proper legal authority (a warrant, consent, or other applicable legal basis) to recover an encryption key protecting a volume on evidence they are already authorized to examine — for example, a full-disk-encrypted or container-encrypted drive seized alongside a system whose memory was captured while the volume was mounted/unlocked. It works because AES key expansion, once performed, leaves a highly structured pattern (the full key schedule) in RAM, which persists briefly even after power loss (the basis of the "cold boot attack") and is trivially present in a live memory capture.

This is **not** a generic decryption-cracking tool: it cannot recover a key that was never resident in the captured memory (e.g., a volume that was never unlocked during the capture, or a key already evicted/overwritten), and it does not brute-force passwords or attack the cipher itself. It only locates and reconstructs a key schedule that memory already contains, or an incomplete/bit-flipped version of one.

Before running this on any image, confirm the same legal authority and scope that applies to the rest of the case already covers use of the recovered key to access the associated encrypted volume — recovering the key and then using it to decrypt/mount the volume are two separate actions with the same authorization requirement.

## What these tools actually do

- **aeskeyfind** scans a raw memory image byte-by-byte for the structural signature of an AES key schedule (the expanded round keys AES key setup produces), for both 128-bit and 256-bit AES keys. It reports candidate key(s) it finds, evaluating the internal consistency of the key schedule structure to reduce false positives.
- **aesfix** takes a candidate key schedule that has some bit errors (common with cold-boot-attack captures where memory has begun to decay, less commonly relevant to a clean live-acquired image) and attempts to reconstruct the correct original key by exploiting redundancy in how the AES key schedule is derived from the original key — effectively error-correcting a damaged candidate schedule into a likely-correct key.
- Both tools operate **read-only** against the memory image file. Neither tool touches the original evidence beyond reading the image; neither attempts to mount, decrypt, or access any volume itself — that would be a separate, explicitly authorized follow-up step using different tooling (e.g., the relevant encryption product's own unlock mechanism, or a forensic disk-encryption tool that accepts a raw key).

Presence of `aeskeyfind` and `aesfix` on this PALADIN system was reported by the user via their own system inventory, not independently verified by Claude. Confirm actual binary names/paths and usage output on the running system before relying on syntax below:

```
aeskeyfind --help
aesfix --help
```
(Some builds may not support `--help` and instead print usage on being run with no arguments or a bad argument — check actual behavior on this system rather than assuming.)

## Command syntax

General shape (verify exact flags against the installed build's own usage output before relying on them):

```
aeskeyfind <memory-image-file>
```

`aeskeyfind` typically takes the memory image path as its primary argument and prints any candidate key(s) it finds (commonly as hex). Some builds support flags to select 128-bit vs. 256-bit search, or a threshold/sensitivity option — do not assume specific flag names without checking the tool's own usage output on this system first, since exact options vary by build/fork.

```
aesfix <memory-image-file> <candidate-key-hex>
```

`aesfix` typically takes the memory image (or the region/candidate schedule) and a candidate key with suspected bit errors, and outputs a corrected candidate. Exact argument order and any additional flags should be confirmed against the installed build's usage output — do not invent a flag or argument position not confirmed on this system.

**Do not present a specific flag or argument name for either tool as certain fact without having confirmed it against the tool's own `--help`/usage output in this session.** If usage output cannot be produced, say so explicitly and ask the examiner to run the bare command to observe its own usage text, rather than guessing.

## Typical workflow

1. **Confirm legal authority** covers recovering and using this key before starting — state this explicitly to the examiner if it hasn't already been established for this case.
2. **Confirm the image file's integrity** — hash-verify the working copy against the acquisition record, consistent with `paladin-forensic-workflow`. As with the other memory tools, this step reads the image only.
3. **Determine what's being searched for** — 128-bit vs. 256-bit AES, and which encryption product/volume the key is expected to belong to (BitLocker, LUKS, VeraCrypt/TrueCrypt, etc.), since this affects what a "found" key should be checked against.
4. **Run `aeskeyfind`** against the image and record any candidate key(s) reported, along with the exact command line used.
5. **If a candidate looks incomplete or fails validation** (e.g., known bit-error pattern from a degraded cold-boot capture), pass it to **`aesfix`** to attempt reconstruction of the intact key.
6. **Do not assume a recovered candidate is correct** until it has actually been tested — successfully unlocking/mounting the target encrypted volume (as a separate, explicitly authorized step) is the real confirmation. Report a candidate key as "candidate," not "the key," until that test succeeds.
7. **Record the full chain**: image hash, tool + version/build if determinable, exact command lines, raw candidate output, and (if performed) the outcome of testing the candidate against the actual encrypted volume.
8. **Hand off to `forensic-reporting`** with that full chain — a recovered key is meaningless in a report without the exact provenance of how it was derived and confirmed.

## Troubleshooting

| Symptom | Likely cause | What to check |
|---|---|---|
| No candidate key found | Volume was never unlocked during the capture window, key already evicted from RAM, or image doesn't cover the region where the key schedule resided | Confirm (from other evidence) whether the volume was actually mounted/unlocked at capture time; a clean "not found" result is expected and legitimate, not necessarily a tool failure |
| Multiple candidate keys reported | Memory can contain look-alike structures, or multiple keys are legitimately present (e.g., several encrypted volumes were unlocked) | Test each candidate against the actual target volume as a separate authorized step rather than assuming the first result is correct |
| Candidate key fails to unlock the target volume | False positive from the structural scan, bit errors in the candidate, or wrong AES bit-length assumed | Try `aesfix` on the candidate if bit errors are suspected; re-check whether 128-bit vs. 256-bit search matches the target encryption product's actual key size |
| `aesfix` produces no improved candidate | Errors too extensive to correct, or wrong candidate/region supplied | Re-run `aeskeyfind` for a cleaner initial candidate; confirm the candidate and image argument order match this build's actual usage output |
| Tool behaves differently than described here | Build/fork variation — several forks of these historically research-origin tools exist with differing flags | Trust the installed build's own `--help`/usage output over this document for exact syntax |

## What this skill must never do automatically

- Never run this analysis without first confirming legal authority covers recovering and using the key — this is not a default step to run "just in case" on every memory image.
- Never present a found candidate as a confirmed, working key before it has actually been tested against the target encrypted volume.
- Never use a recovered key to mount, decrypt, or otherwise access the associated volume without separately confirming that action is also within the examiner's authorized scope — key recovery and volume access are distinct actions.
- Never invent a flag, argument order, or output format for `aeskeyfind`/`aesfix` not confirmed against the installed build's own usage output.
- Never treat this as a general password-cracking or encryption-defeating tool in framing to the examiner — it locates/repairs a key schedule already resident in captured memory, nothing more.
- Never write to or modify the original memory image; both tools should be run read-only against a verified working copy.

## Handoff

- Recovered/confirmed key and full provenance chain → `forensic-reporting`.
- Broader process/network/registry analysis of the same memory image → `volatility3` (or `volatility2-legacy` if the image needs the legacy tool).
- Actually mounting/decrypting the target volume with a confirmed key → a dedicated disk-encryption/mounting tool for that specific product, as a separate explicitly authorized step (not covered by this skill).

