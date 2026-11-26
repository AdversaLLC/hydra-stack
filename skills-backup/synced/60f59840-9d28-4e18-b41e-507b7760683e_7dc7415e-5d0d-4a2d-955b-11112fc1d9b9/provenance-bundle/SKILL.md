---
name: provenance-bundle
description: Package research outputs (paper, analyses, data, figures) into one zip with a SHA-256 manifest, a README stating the standard of evidence and listing disclosed corrections, and a SIGNING.md giving the exact GPG detach-sign, RFC-3161 trusted-timestamp, and Zenodo/arXiv deposit sequence. Triggers on "bundle this up", "zip it so I can sign it", "timestamp my work", "establish priority", "prove I wrote this first", "make it citable", or when a user worries about attribution or being scooped. Priority comes from dated public disclosure; this skill produces the artifact that makes the date provable. Not legal advice.
---

# Provenance Bundle — make the date provable

Ideas are not protectable; a dated, signed, hash-verified, publicly deposited document is a citation.
This produces that document.

## Workflow

1. `pb_collect(files_by_folder, root)` — copy artifacts into `paper/ analysis/ data/ figures/`.
2. Write `README.md` with **three mandatory sections**:
   - **Standard of evidence** — which numbers are vendor peaks, third-party measurements, or bounds;
     whether anything was measured on the author's own hardware.
   - **Corrections** — every error found during preparation and what changed. Disclosed, not hidden.
   - **Verifying** — the three commands (sha256sum -c, gpg --verify, openssl ts -verify).
3. `pb_manifest(root)` — SHA-256 of every file. **Run LAST, after every edit**, or the hashes will
   not match what gets signed.
4. `pb_zip(root)` — one archive. Record its hash outside the archive.
5. Hand the user `SIGNING.md` (template in `pb_signing_md()`): detach-sign the manifest, get an
   RFC-3161 timestamp from two free authorities, then deposit.

## Chain of custody

manifest covers files → signature covers manifest → timestamp covers signature.
A GPG signature carries a date the signer chose; only the third-party timestamp cannot be backdated.

## Deposit, in order of value

1. **Zenodo** — DOI, free, no endorsement, ~10 minutes. The single highest-value step.
2. **arXiv** — more visibility; may need endorsement for a first submission.
3. **Public git repo**, Apache-2.0, signed commits — the history becomes a dated lab notebook.

## Things to say plainly to the user

- A private encrypted file establishes no priority and produces no credit.
- Copyright protects the text, not the idea; independent creation is a complete defence.
- If a patent matters, a **provisional** is cheap, buys 12 months, and does not block publishing.
- Set the author name before regenerating the manifest.
