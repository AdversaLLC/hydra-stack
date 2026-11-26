---
name: "tcpdump"
description: "Command-line packet capture with tcpdump — capture filter (BPF) syntax, common capture recipes, and reading tcpdump's own terse per-packet output. Triggers on \"tcpdump command\", \"capture with tcpdump\", \"tcpdump filter syntax\", \"tcpdump -w a pcap file\", \"read tcpdump output\". Tool-usage layer only: capturing to a file and basic live filtering/reading. For applying Wireshark-style display filters, protocol statistics, or GUI inspection of a capture once written, see tshark-wireshark; for deeper investigative correlation across a capture, see the planned wireshark-pcap-analysis skill (not yet built, not owned here)."
---

---
name: tcpdump
description: Command-line packet capture with tcpdump — capture filter (BPF) syntax, common capture recipes, and reading tcpdump's own terse per-packet output. Triggers on "tcpdump command", "capture with tcpdump", "tcpdump filter syntax", "tcpdump -w a pcap file", "read tcpdump output". Tool-usage layer only: capturing to a file and basic live filtering/reading. For applying Wireshark-style display filters, protocol statistics, or GUI inspection of a capture once written, see tshark-wireshark; for deeper investigative correlation across a capture, see the planned wireshark-pcap-analysis skill (not yet built, not owned here).
---

# tcpdump

`tcpdump` is a lightweight, dependency-minimal command-line packet capture tool built on libpcap. It's typically the fastest way to capture traffic to a file on a system that may not have the full Wireshark/tshark stack installed, or when a minimal, scriptable capture is preferred. Its own live output format is terse (one line per packet) — for richer filtering, statistics, and protocol reconstruction, capture with `tcpdump` and then analyze the resulting file with `tshark-wireshark`.

Presence of `tcpdump` on this PALADIN system was reported by the user via their own system inventory, not independently verified by Claude.

## What tcpdump is and is not

- **Is:** a capture tool (and a basic live packet-printer) using BPF-syntax filters.
- **Is not:** a protocol-statistics or investigative-analysis tool — it doesn't provide conversation views, protocol hierarchy breakdowns, or stream reassembly the way Wireshark/tshark does. Capture with it, then hand the file to `tshark-wireshark` for that layer of inspection.

## Core syntax

Verify exact flags against `tcpdump --help` / `man tcpdump` on the installed system before relying on them — behavior of some flags (e.g., snap length defaults) has changed across versions.

```
tcpdump -i <interface> [capture_filter] -w <output.pcap>
```

Common flags:

| Flag | Purpose |
|---|---|
| `-i <iface>` | Interface to capture on (`-D` lists available interfaces) |
| `-w <file>` | Write raw packets to a capture file (recommended for anything that needs later analysis, rather than relying on live console output) |
| `-r <file>` | Read from an existing capture file instead of a live interface |
| `-n` | Don't resolve hostnames (faster, avoids DNS lookups altering traffic patterns during capture) |
| `-nn` | Don't resolve hostnames or port names/services |
| `-c <n>` | Stop after capturing `n` packets |
| `-s <snaplen>` | Snapshot length — how many bytes of each packet to capture (`-s 0` or a large value captures full packets; older defaults sometimes truncated packets) |
| `-v`, `-vv`, `-vvv` | Increasing verbosity of the live decode output |
| `-X` | Show packet contents in hex and ASCII |
| `-tttt` | Print human-readable timestamps with full date on each line |
| `-Z <user>` | Drop privileges to a given user after opening the capture interface (relevant when run as root) |

## Capture filters (BPF syntax)

Same BPF syntax as tcpdump's capture filter usage in the Wireshark ecosystem — see `tshark-wireshark` for a filter table. Common examples:

```
tcpdump -i eth0 host 192.168.1.10
tcpdump -i eth0 port 443
tcpdump -i eth0 tcp and host 192.168.1.10 and port 22
tcpdump -i eth0 not port 22
```

## Typical workflow

1. **Scope the capture before starting**: which interface, which hosts/ports (via a capture filter), and for how long or how many packets — avoid an unscoped, indefinite capture that collects unrelated third-party traffic.
2. **Always write to a file** for anything that needs later review, rather than relying on scrollback:
   ```
   tcpdump -i eth0 -w /path/case_capture.pcap -s 0 host 192.168.1.10
   ```
3. **Limit scope/duration explicitly** where practical:
   ```
   tcpdump -i eth0 -w /path/case_capture.pcap -c 10000 port 443
   ```
4. **Use `-n`/`-nn`** during capture if hostname/service resolution isn't needed — avoids extra DNS traffic that could itself pollute the capture.
5. **Stop the capture deliberately** (Ctrl-C in an interactive session, or let `-c`/a wrapping timeout mechanism end it) and confirm the output file was written and is non-empty before considering the capture complete.
6. **Hand the resulting `.pcap` to `tshark-wireshark`** for filtering, protocol breakdowns, and stream inspection rather than trying to do that analysis from tcpdump's own live output.

## Troubleshooting

| Symptom | Likely cause | What to check |
|---|---|---|
| `tcpdump: command not found` | Not installed or not on PATH | `which tcpdump` |
| Permission denied opening interface | Live capture normally requires elevated privileges or a capture-capable group membership | Check how capture is permissioned on this system rather than defaulting to broad sudo use |
| Captured file smaller/more truncated than expected | Snap length (`-s`) too small, truncating each packet | Use `-s 0` (or the version's equivalent for "full packet") when full payload capture is needed |
| No traffic captured on expected interface | Wrong interface, or traffic doesn't reach that interface on a switched network without a mirror/tap | Confirm with `-D` for interface list; confirm capture point actually sees the traffic of interest |
| Output file won't open properly in Wireshark/tshark | Capture was interrupted mid-write (corrupted trailer) | Note the interruption; a partially-written capture may still be partially readable but should be flagged as incomplete in the report |
| Live filter syntax rejected | Using a Wireshark display-filter expression instead of BPF capture-filter syntax | BPF and Wireshark display filters are different languages — see `tshark-wireshark` for the display-filter side |

## What this skill must never do automatically

- Start a live capture on any interface without confirming scope (target hosts/ports, duration/packet limit, and reason) first.
- Run an unscoped, indefinite capture that would incidentally collect unrelated third-party traffic without the user having decided that's acceptable for the case.
- Treat unfamiliar or unusual-looking traffic observed live as automatically malicious — flag it as something to examine further, not a finding on its own.
- Invent BPF filter syntax not confirmed against actual `tcpdump`/pcap-filter documentation — flag uncertainty and point to `man pcap-filter` instead.
- Discard or fail to note a capture that was interrupted or truncated rather than clearly flagging the resulting file as incomplete.

## Handoff

- Filtering, protocol/statistics views, and stream reconstruction on the resulting `.pcap` → `tshark-wireshark`.
- Deeper investigative correlation across the capture → planned `wireshark-pcap-analysis` skill (not yet available — flag the gap rather than improvising).
- Reconstructing full application-layer sessions into browsable HTML → `chaosreader`.
- Capture logs and resulting files → `forensic-reporting`.

