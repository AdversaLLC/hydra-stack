---
name: "chaosreader"
description: "Reconstruct application-layer sessions (HTTP, FTP, telnet, and other supported protocols) from a packet capture into browsable HTML pages using chaosreader. Triggers on \"run chaosreader\", \"reconstruct sessions from this pcap\", \"turn this capture into browsable HTML\", \"chaosreader report\", \"rebuild the HTTP session from this capture\". A session-reconstruction tool operating on an already-captured file — not a live capture tool (see tcpdump/tshark-wireshark for that) and not a deep investigative/correlation tool (see the planned wireshark-pcap-analysis skill). Unfamiliar or unexpected reconstructed content is a lead for further review, not proof of malicious activity."
---

---
name: chaosreader
description: Reconstruct application-layer sessions (HTTP, FTP, telnet, and other supported protocols) from a packet capture into browsable HTML pages using chaosreader. Triggers on "run chaosreader", "reconstruct sessions from this pcap", "turn this capture into browsable HTML", "chaosreader report", "rebuild the HTTP session from this capture". A session-reconstruction tool operating on an already-captured file — not a live capture tool (see tcpdump/tshark-wireshark for that) and not a deep investigative/correlation tool (see the planned wireshark-pcap-analysis skill). Unfamiliar or unexpected reconstructed content is a lead for further review, not proof of malicious activity.
---

# chaosreader

`chaosreader` is a Perl-based tool that parses a packet capture file and reconstructs application-layer sessions — TCP/UDP sessions, and for supported protocols (HTTP, FTP, Telnet, and others depending on version) full reassembled conversations — into a set of browsable HTML report pages, plus extracted files/images where they were transferred in the clear. It's a fast way to get a human-readable view of what happened in specific sessions within a capture, as an alternative to manually following streams one at a time in Wireshark.

Presence of `chaosreader` on this PALADIN system was reported by the user via their own system inventory, not independently verified by Claude.

## What chaosreader is and is not

- **Is:** a batch session-reconstruction tool — point it at a capture file, it outputs an `index.html` linking to individual session pages, extracted downloads/images, and a timeline-style report.
- **Is not:** a live capture tool (use `tcpdump`/`tshark-wireshark` to produce the capture first), a decryption tool (it reconstructs only what's visible in cleartext in the capture — encrypted TLS/SSH sessions won't yield readable application content without keys), or a substitute for the deeper correlation/analysis work of the planned `wireshark-pcap-analysis` skill.
- Because it reassembles cleartext application data, its output can include sensitive content (credentials submitted over unencrypted HTTP/FTP/Telnet, personal data in page content) — handle the generated HTML report with the same evidentiary care as the source capture.

## Core syntax

Verify exact flags against `chaosreader -h` / its man page or documentation on the installed system before relying on them — chaosreader is a long-unmaintained but still-used Perl script, and flag availability can vary by the specific packaged version.

```
chaosreader <capture_file.pcap>
```

Common flags (confirm against the installed version):

| Flag | Purpose |
|---|---|
| `-v` | Verbose output during processing |
| `-D` | Direct output to a chosen directory rather than the current working directory |
| `-p <port>` | Restrict processing to specific ports of interest |
| `-i <interface>` | Live-capture mode directly from an interface (if supported by the installed version) — generally better practice in a forensic workflow to capture separately with `tcpdump`/`tshark` and feed chaosreader a file, so the raw capture itself is preserved untouched as evidence |
| `-A` | Look for specific applications/protocols only (version-dependent flag; confirm exact syntax) |
| Output files | Typically produces `index.html`, session files (`session_*.html`), an image/file report, and a raw TCP/UDP data report — exact filenames vary by version |

## Typical forensic workflow

1. **Work from a copy of the capture file**, in its own case-specific working directory — chaosreader will write multiple output files alongside/into that directory.
2. **Run it against the file** (not live, per above) so the source capture stays untouched and independently hashed/preserved:
   ```
   cd /path/to/case_working_dir
   chaosreader /path/to/case_capture.pcap
   ```
3. **Open the generated `index.html`** in a browser to review reconstructed sessions. Treat this as a convenience view of the same bytes present in the original capture — anything material found here should also be verifiable directly in the capture (e.g., via `tshark-wireshark`'s Follow Stream) rather than relied on solely through chaosreader's reconstruction.
4. **Note what protocols were actually reconstructed vs. what's just listed as an opaque TCP/UDP session** — encrypted sessions (TLS, SSH) will not produce readable application content, and that's expected, not a tool failure.
5. **Handle extracted files/images and any reconstructed credential material as sensitive case data** — store within the case's evidence-handling structure, not in a general working folder.
6. **Record which capture file (with its hash) chaosreader was run against**, the chaosreader version if known, and the output directory location, so the reconstruction is reproducible.

## Troubleshooting

| Symptom | Likely cause | What to check |
|---|---|---|
| `chaosreader: command not found` | Not installed, or installed as a `.pl` script requiring `perl chaosreader.pl ...` invocation | `which chaosreader`; check whether it needs to be invoked via `perl` explicitly on this system |
| No sessions reconstructed / empty report | Capture contains only encrypted traffic, or capture file is empty/corrupted | Confirm the capture actually contains cleartext application-layer protocols (check with `tshark-wireshark` first); verify the capture file isn't empty or truncated |
| Missing Perl module errors | chaosreader depends on Perl and may reference modules not installed | Note the specific missing module from the error and check it can be resolved without introducing unvetted external packages onto the forensic system |
| Output HTML pages show garbled/binary content | Session was binary protocol or partially encrypted, not suited to chaosreader's plain-text reconstruction | Expected behavior for non-cleartext-text protocols; use `tshark-wireshark`'s Follow Stream or hex view (`-x`) instead for those sessions |
| Very slow processing on a large capture | Large file size, many sessions | Consider narrowing scope with a `-p` port filter if the case only concerns specific traffic, or pre-filter the capture in `tshark-wireshark` to a smaller sub-capture first |

## What this skill must never do automatically

- Run in live-capture mode against a network interface without the same scoping/authorization considerations as any other capture activity — prefer capturing separately and feeding chaosreader a file.
- Treat reconstructed session content (e.g., an unusual HTTP request, an FTP transfer) as proof of malicious activity — unfamiliar traffic is a lead for further review, not a finding on its own.
- Expose or copy reconstructed credential material, personal data, or extracted files outside the case's documented evidence-handling process.
- Overwrite or run against the original capture file in place in a way that could alter it — always work from a copy in a case working directory.
- Invent chaosreader flags or output filenames not confirmed against the installed version's own help/documentation.

## Handoff

- Producing the source capture → `tcpdump` or `tshark-wireshark`.
- Cross-checking any reconstructed session directly against the raw capture (Follow Stream, filters) → `tshark-wireshark`.
- Deeper correlation of reconstructed sessions with other case evidence, or pattern/timeline analysis → planned `wireshark-pcap-analysis` skill (not yet available — flag the gap).
- Findings, extracted artifacts, and chain-of-custody notes for the capture and its reconstruction → `forensic-reporting`.

