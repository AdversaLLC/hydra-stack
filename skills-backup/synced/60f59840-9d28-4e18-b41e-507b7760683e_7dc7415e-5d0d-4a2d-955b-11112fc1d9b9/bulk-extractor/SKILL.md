---
name: "bulk-extractor"
description: "High-speed feature extraction from raw disk/memory images with bulk_extractor — scans raw bytes (it does not need or parse a filesystem) to pull out email addresses, URLs, domains, credit card numbers, phone numbers, search terms, EXIF data, JSON fragments, network packet/PCAP-like features, encryption keys, and other recognizable \"features\" wherever they appear, including in unallocated space, slack space, swap, hibernation files, and memory dumps. Use when the user says \"run bulk_extractor\", \"extract emails/URLs from this image\", \"scan this image for credit card numbers\", \"find artifacts across the whole disk regardless of filesystem\", or wants a fast triage pass before deeper analysis. Not a file carver in the foremost/scalpel/photorec sense (it does not primarily reconstruct whole files by header/footer, though its scanners include some carving-like extraction such as exif and jpeg carving) and not for partition/boot-sector repair (use testdisk-photorec for that)."
---

---
name: bulk-extractor
description: High-speed feature extraction from raw disk/memory images with bulk_extractor — scans raw bytes (it does not need or parse a filesystem) to pull out email addresses, URLs, domains, credit card numbers, phone numbers, search terms, EXIF data, JSON fragments, network packet/PCAP-like features, encryption keys, and other recognizable "features" wherever they appear, including in unallocated space, slack space, swap, hibernation files, and memory dumps. Use when the user says "run bulk_extractor", "extract emails/URLs from this image", "scan this image for credit card numbers", "find artifacts across the whole disk regardless of filesystem", or wants a fast triage pass before deeper analysis. Not a file carver in the foremost/scalpel/photorec sense (it does not primarily reconstruct whole files by header/footer, though its scanners include some carving-like extraction such as exif and jpeg carving) and not for partition/boot-sector repair (use testdisk-photorec for that).
---

# bulk_extractor

## What this tool does

bulk_extractor is a high-throughput digital forensics tool that scans a disk image, file, or raw device byte-by-byte for recognizable "features" using a set of pluggable scanners — it does not require the input to have a parseable or intact filesystem, and it does not walk directory structures. This makes it effective on raw/corrupted images, unallocated space, memory dumps, and pagefiles/swap, where filesystem-aware tools find nothing.

Typical scanners (enabled/disabled individually) extract things like:
- Email addresses, URLs, domains, and search-engine query terms
- Credit card numbers (with Luhn-check validation) and other structured numeric identifiers
- EXIF metadata from embedded JPEG fragments
- JSON fragments, base64-encoded data, and compressed (zlib) data streams
- Network-related artifacts (e.g., IP/Ethernet-like patterns) and some file-carving-adjacent scanners (e.g., `exif`, `jpeg`) that pull out embedded images
- Windows-specific artifacts in some builds (e.g., `.lnk` fragments, registry-ish patterns) depending on the scanner set compiled in

Because it works directly on raw bytes at high speed (and can use multiple threads), bulk_extractor is commonly used as a fast first-pass triage step across an entire image, in parallel with or before more targeted analysis in Autopsy/Sleuth Kit or file carving with foremost/scalpel.

It also builds a **histogram-based "feature file" output set** — plain text files, one per feature type (e.g., `email.txt`, `url.txt`, `ccn.txt`, `domain.txt`), each line giving the byte offset and the extracted feature — plus optional context. A companion GUI/report viewer (`bulk_extractor_viewer`/BEViewer, where available) can browse these results with an accompanying "context" hex view.

**Presence note:** if this skill was told bulk_extractor is installed on the PALADIN system, that was reported by the user via their own system inventory, not independently verified here. Confirm with `bulk_extractor -h`/`which bulk_extractor` and check which scanners are actually compiled in on this build (`bulk_extractor -help` typically lists them).

## Command syntax (verify against `bulk_extractor -h` for your installed version)

Basic invocation:

```
bulk_extractor -o <output_dir> <image_or_device>
```

Common flags (verify exact behavior with `-h`, since scanner names/availability differ by build):

- `-o <dir>` — output directory for feature files and reports. Like the carving tools, bulk_extractor generally expects a fresh output directory and will refuse to run into one that already has output, to avoid mixing runs.
- `-e <scanner>` — enable a specific scanner (e.g. `-e exif`).
- `-x <scanner>` — disable a specific scanner.
- `-E <scanner>` — run in "exclusive" mode: disable all scanners except the one named.
- `-h` / `-H` — list available scanners and help/detailed help.
- `-j <n>` — number of analysis threads to use (tune for available CPU cores).
- `-r <file>` — recursively re-process a specific feature file (e.g., re-scan recovered fragments), in some workflows.
- `-S name=value` — set a scanner-specific tuning parameter.
- `-f <regex>` or `-F <file>` — search for a specific pattern/regex, or a file of patterns, in addition to standard scanners, in builds that support it.

Because scanner names and some flags differ across bulk_extractor 1.x releases and forks, verify the exact set with `bulk_extractor -h` and `bulk_extractor -H` on the installed binary before relying on a specific scanner name.

## Realistic workflow

1. **Work only from a verified image**, never the original evidence media directly — image and hash-verify first (see `paladin-forensic-workflow`) if that hasn't happened yet.
2. **Choose an output directory on separate media from the evidence** — bulk_extractor's output (feature files, potentially large) must not be written back onto the source image's volume or any write-blocked evidence mount.
3. Optionally review available scanners (`bulk_extractor -h`) and decide whether to run the full default scanner set or narrow scope (e.g., only email/URL/ccn scanners for a specific investigative question) for speed.
4. Run, e.g.:
   ```
   bulk_extractor -o /mnt/casework/case001_be_out /mnt/evidence_ro/case001.dd
   ```
5. Review the feature files produced in the output directory (e.g. `email.txt`, `url.txt`, `ccn.txt`, `domain.txt`) and the `report.xml` summary bulk_extractor writes describing the run (scanners used, image hash, runtime).
6. Cross-reference interesting hits back to their byte offsets in the image using the context bulk_extractor provides, or a hex viewer / BEViewer, to understand where in the image (allocated file, slack space, unallocated space, swap) each feature was found.
7. Treat raw feature hits as leads, not conclusions — e.g., a matched credit-card-number pattern is not proof of an actual stored card number; false positives happen, especially on structured numeric data. Validate before including in a report.
8. Record the bulk_extractor version, scanner configuration used, input image hash, and output location in case documentation (see `forensic-reporting`).

## Troubleshooting

| Symptom | Likely cause / next step |
|---|---|
| "output directory already exists" / refuses to run | bulk_extractor expects a fresh output directory per run; use a new empty directory rather than reusing one. |
| Run takes a very long time on a large image | Increase thread count with `-j` if CPU cores are available, or disable scanners you don't need with `-x` / narrow with `-E` to only the scanner(s) relevant to the case. |
| A feature file (e.g. `ccn.txt`) is empty | That scanner may not have found any matches, or may not have been enabled/compiled into this build — check `bulk_extractor -h` for the actual scanner list. |
| Too many false positives in a feature file | Expected for pattern-matched data like phone numbers or CCNs; cross-check hits manually, and consult that scanner's known limitations (some have validation like Luhn-check for CCNs, others are pure pattern match). |
| Unsure which scanners exist in this build | Run `bulk_extractor -h` and `bulk_extractor -H` on the actual installed binary — scanner sets vary by build/compile options. |
| Want to review results with a GUI | Check whether `bulk_extractor_viewer`/BEViewer is installed alongside bulk_extractor on this system; it is a separate companion application, not guaranteed present. |

## What this skill must never do automatically

- Never point `-o` at the evidence image's own media, a write-blocked evidence mount, or any path inside the source evidence directory tree.
- Never reuse/overwrite a prior case's output directory without explicit user confirmation.
- Never present raw feature-file hits (emails, URLs, CCNs, etc.) as confirmed findings without noting they require manual validation and context (byte offset, allocated vs. unallocated, surrounding data).
- Never invent bulk_extractor scanner names or flags not confirmed via `-h`/`-H` on the installed binary.
- Never claim bulk_extractor is installed/available, or that a specific scanner is compiled in, beyond what the user has reported from their own system inventory.

