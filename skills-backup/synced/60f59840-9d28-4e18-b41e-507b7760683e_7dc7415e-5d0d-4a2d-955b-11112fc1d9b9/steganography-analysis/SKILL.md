---
name: "steganography-analysis"
description: "Detect and extract hidden data embedded in image/audio files using steghide and stegosuite, for cases where concealed data (steganography) is suspected. Triggers on \"check this image for hidden data\", \"run steghide\", \"steganography detection\", \"extract hidden payload\", \"stegosuite\", or \"does this file have a hidden message\". Requires a passphrase to extract steghide-embedded content in most cases — do not represent a failed extraction attempt as proof the file contains nothing hidden."
---

---
name: steganography-analysis
description: Detect and extract hidden data embedded in image/audio files using steghide and stegosuite, for cases where concealed data (steganography) is suspected. Triggers on "check this image for hidden data", "run steghide", "steganography detection", "extract hidden payload", "stegosuite", or "does this file have a hidden message". Requires a passphrase to extract steghide-embedded content in most cases (steghide does not reliably tell you whether a file contains hidden data without the correct passphrase) — do not represent a failed extraction attempt as proof the file contains nothing hidden.
---

# Steganography Analysis (steghide / stegosuite)

Steganography tools hide data inside the least-significant structure of a cover file (commonly JPEG/BMP/WAV for steghide). These tools extract already-embedded content when a passphrase is known or guessable — they are not general-purpose steganography *detectors* in the sense of reliably proving a clean file has nothing hidden.

## Important limitation to state plainly in any report

Failing to extract data with steghide (e.g., wrong passphrase, or the file wasn't embedded with steghide at all) does **not** prove the file contains no hidden data. Steganography can be done many ways, most of which these two tools cannot detect. Any conclusion here should be graded as "Inconclusive" rather than "Confirmed — no hidden data" unless a positive extraction genuinely succeeded.

## Workflow

1. **Confirm you're working from a copy**, not the original evidence file — extraction can be non-destructive read-only in principle, but treat all evidence files as read-only sources regardless.
2. **steghide extraction** (verify exact flags against `steghide --help`): general pattern is `steghide extract -sf <stego-file> [-p <passphrase>]`. If no passphrase is supplied and one is required, steghide will prompt or fail — do not attempt to brute-force the passphrase without documented authorization (this overlaps with the same authorization principle as `hashcat`/`john-the-ripper`; a wordlist-based attempt against a steghide passphrase falls under the same "authorized examiner, documented case" gate).
3. **stegosuite** (GUI tool) — provides a graphical workflow for the same class of operation (embed/extract/detect for common formats), and may include basic statistical detection features; confirm current feature set against the tool's own documentation/UI rather than assuming parity with steghide.
4. **Record the exact command/parameters used and the result** (success/failure, and what was extracted if successful) for the report — never claim an extraction succeeded or a specific payload was found without having actually observed it.

## What this skill must never do automatically

- Claim a file is "clean" (no hidden data) based solely on a failed steghide extraction attempt.
- Brute-force a steghide passphrase without the same documented-authorization gate that applies to password cracking generally.
- Modify or overwrite the original evidence file during extraction testing — always work against a copy.
- Report an extracted payload's contents without having actually seen them.

## Troubleshooting

| Symptom | Likely cause | Steps |
|---|---|---|
| "could not extract any data" | Wrong passphrase, file wasn't embedded via steghide, or file format unsupported | Confirm file format is one steghide supports; do not assume this means "no hidden data" |
| stegosuite GUI won't open a file | Unsupported format or corrupted file | Check the file's actual format/integrity separately (e.g., `exiftool`, `file` command) before concluding stegosuite failed for content reasons |
| Extraction "succeeds" but output looks like garbage | Wrong passphrase produced spurious output, or the embedded data itself is further encrypted/encoded | Don't assume garbled output is a genuine extracted payload — verify plausibility before reporting it as a finding |

## Handoff

- Broader file metadata inspection alongside stego analysis → `exiftool-metadata`.
- If passphrase recovery is pursued under proper authorization → `hashcat`, `john-the-ripper`.
- Writing up findings, including the "inconclusive" framing where extraction failed → `forensic-reporting`.

