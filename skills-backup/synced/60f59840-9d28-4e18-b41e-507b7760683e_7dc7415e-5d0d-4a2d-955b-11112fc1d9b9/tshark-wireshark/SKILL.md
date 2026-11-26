---
name: "tshark-wireshark"
description: "Tool-usage layer for tshark (CLI) and Wireshark (GUI) — how to run a packet capture, apply capture and display filters, and read basic conversation/protocol/statistics views. Triggers on \"capture packets with tshark\", \"wireshark display filter\", \"tshark command\", \"capture filter syntax\", \"open this pcap in wireshark\", \"protocol hierarchy statistics\", \"conversations view\". This skill covers tool mechanics only: capture/filter syntax, reading built-in views, exporting objects. It explicitly does NOT cover deeper investigative analysis — correlating findings across a capture, identifying beaconing/exfiltration patterns, building a network timeline, or drawing conclusions about intent — that is owned by the planned wireshark-pcap-analysis skill (not yet built). If asked for that kind of analysis, use this skill to gather the raw views/output and note that deeper correlation belongs to that (currently unavailable) skill."
---

---
name: tshark-wireshark
description: Tool-usage layer for tshark (CLI) and Wireshark (GUI) — how to run a packet capture, apply capture and display filters, and read basic conversation/protocol/statistics views. Triggers on "capture packets with tshark", "wireshark display filter", "tshark command", "capture filter syntax", "open this pcap in wireshark", "protocol hierarchy statistics", "conversations view". This skill covers tool mechanics only: capture/filter syntax, reading built-in views, exporting objects. It explicitly does NOT cover deeper investigative analysis — correlating findings across a capture, identifying beaconing/exfiltration patterns, building a network timeline, or drawing conclusions about intent — that is owned by the planned wireshark-pcap-analysis skill (not yet built). If asked for that kind of analysis, use this skill to gather the raw views/output and note that deeper correlation belongs to that (currently unavailable) skill.
---

# tshark / Wireshark — Tool Usage

`tshark` is the command-line packet analyzer bundled with Wireshark; `wireshark` is the GUI. Both read live captures or `.pcap`/`.pcapng` files and let you filter, inspect, and export packet data. This skill covers **how to operate the tool** — capture syntax, filter syntax, and how to read its built-in summary views. It does not cover investigative interpretation of what a capture means for a case.

**Scope boundary:** interpreting patterns across a capture (e.g., "does this look like beaconing," "correlate this with DNS activity elsewhere in the case," "build a timeline of network events") is explicitly out of scope here and belongs to the planned `wireshark-pcap-analysis` skill, which does not exist yet in this library. If asked for that kind of analysis, use the commands below to produce the relevant views/exports, then say plainly that deeper correlation/analysis is outside this skill's current scope.

Presence of `tshark`/`wireshark` on this PALADIN system was reported by the user via their own system inventory, not independently verified by Claude.

## Capture vs. display filters — the most common confusion

- **Capture filters** (BPF syntax) are applied *while capturing* — they permanently discard non-matching packets before they're even written. Set with `-f` in tshark, or in Wireshark's capture options.
- **Display filters** (Wireshark's own filter language) are applied *after* capture, to a file already on disk — packets aren't discarded, just hidden/shown. Set with `-Y` in tshark (or `-2 -R` for a two-pass filtered read in some versions), or the filter bar in the GUI.
- These are **different syntaxes** — a valid display filter is often not valid as a capture filter, and vice versa. Confirm which one is being asked for before writing a filter expression.

## Core tshark syntax

Verify exact flags against `tshark --help` / `man tshark` on the installed system before relying on them — flag behavior has shifted across Wireshark/tshark versions.

```
tshark -i <interface> -f "<capture_filter>" -w <output.pcapng>
tshark -r <input.pcap> -Y "<display_filter>"
```

Common flags:

| Flag | Purpose |
|---|---|
| `-i <iface>` | Interface to capture on (`-D` lists available interfaces) |
| `-f "<bpf>"` | Capture filter (BPF syntax), applied during live capture only |
| `-w <file>` | Write raw captured packets to a file |
| `-r <file>` | Read from an existing capture file instead of live capture |
| `-Y "<filter>"` | Display filter (Wireshark syntax), applied when reading |
| `-c <n>` | Stop after capturing `n` packets |
| `-a duration:<sec>` | Stop capture after a given number of seconds |
| `-T fields -e <field>` | Extract specific fields as structured output (e.g., for scripting/export) |
| `-z <statistic>` | Print a built-in statistics view (e.g., `-z conv,ip`, `-z io,phs` for protocol hierarchy) |
| `-x` | Include a hex/ASCII dump of packet bytes |
| `-V` | Verbose per-packet protocol tree output |

## Common capture filters (BPF syntax)

| Filter | Matches |
|---|---|
| `host 192.168.1.10` | Traffic to/from that IP |
| `net 192.168.1.0/24` | Traffic within that subnet |
| `port 443` | Traffic on port 443 (either direction) |
| `tcp port 80` | TCP traffic on port 80 |
| `not port 22` | Exclude a port (e.g., exclude the examiner's own SSH session if capturing on a shared segment) |
| `host A and host B` | Traffic specifically between two hosts |

## Common display filters (Wireshark syntax)

| Filter | Matches |
|---|---|
| `ip.addr == 192.168.1.10` | Packets to/from that IP |
| `tcp.port == 443` | TCP traffic on port 443 |
| `http` | HTTP protocol packets |
| `dns` | DNS protocol packets |
| `tls.handshake.type == 1` | TLS ClientHello packets |
| `tcp.flags.syn == 1 and tcp.flags.ack == 0` | TCP SYN packets (connection attempts) |
| `frame contains "search-term"` | Raw byte/string match anywhere in the frame (slow on large captures) |
| `ip.addr == A and ip.addr == B` | Traffic specifically between two hosts |

Confirm exact field names (`tls.` vs older `ssl.` namespace, etc.) against the installed Wireshark version's filter reference — field names have been renamed/reorganized across major versions.

## Basic built-in views (still tool-usage, not analysis)

| View | How to get it | What it shows |
|---|---|---|
| Protocol Hierarchy | GUI: Statistics > Protocol Hierarchy; CLI: `tshark -r file.pcap -z io,phs` | Breakdown of packet counts by protocol layer |
| Conversations | GUI: Statistics > Conversations; CLI: `tshark -r file.pcap -z conv,tcp` (or `conv,ip`, `conv,udp`) | Pairwise endpoint traffic volume/duration |
| Endpoints | GUI: Statistics > Endpoints | List of distinct hosts seen in the capture |
| Follow Stream | GUI: right-click a packet > Follow > TCP/UDP/HTTP Stream | Reassembled application-layer conversation for one stream |
| Export Objects | GUI: File > Export Objects > HTTP/SMB/etc. | Pulls out transferred files/objects from supported protocols |

Reading these views and reporting their raw contents (counts, endpoints, protocols present) is in scope here. Concluding *why* a pattern exists, whether it indicates compromise, or how it correlates with other case evidence is analysis — flag that as outside this skill's scope.

## Typical workflow

1. **Work from a copy of the capture file**, not a live tap on production/evidence infrastructure, unless the task is specifically an authorized live capture.
2. **If capturing live**: scope with a capture filter (`-f`) matching only what's relevant, set a duration or packet-count limit, write to a named file (`-w`).
3. **If reading an existing file**: open with `-r`, apply display filters (`-Y`) to narrow the view, use `-z` statistics for a quick overview before drilling into individual packets.
4. **Export what's needed** (fields via `-T fields -e`, objects via GUI Export Objects, or a filtered sub-capture via `-w` combined with `-Y`... note: some tshark versions require `-2` for a filtered write pass — confirm current syntax).
5. **Hand off raw findings** (protocol breakdown, endpoint list, exported objects, filtered packet sets) to deeper analysis rather than asserting conclusions from this tool-usage layer.

## Troubleshooting

| Symptom | Likely cause | What to check |
|---|---|---|
| `tshark: command not found` | Not installed or not on PATH | `which tshark`; GUI Wireshark and CLI tshark are sometimes packaged separately |
| Permission denied capturing on an interface | Missing capture permissions (needs elevated privileges or capture-group membership on most Linux setups) | Check how live capture is permissioned on this PALADIN system rather than assuming sudo is appropriate |
| Capture filter syntax rejected | Using display-filter syntax (`-Y` style) where a capture filter (`-f`, BPF) is expected, or vice versa | Confirm which filter type is needed for the current step — they are not interchangeable |
| Display filter turns red/invalid in Wireshark GUI | Typo, deprecated field name, or wrong field namespace (e.g. `ssl.` vs `tls.`) | Use the GUI's filter autocomplete/expression builder, or check the current field reference |
| No packets captured on expected interface | Wrong interface selected, traffic not actually reaching that interface (e.g., switched network without a mirror/tap) | Confirm with `-D`/`tshark -D` for interface list; confirm the capture point actually sees the traffic of interest |
| Extremely large capture file is slow to filter/open | File size vs. available RAM/CPU for GUI parsing | Prefer `tshark -r ... -Y ...` (streaming, lighter) over opening huge files directly in the GUI |

## What this skill must never do automatically

- Start a live capture on any interface without confirming scope (what's being captured, for how long, and why) first, given capture can incidentally collect unrelated third-party traffic.
- Treat unfamiliar or unusual-looking traffic as automatically malicious — a display filter surfacing something unexpected is a lead for further (out-of-scope-here) analysis, not a finding on its own.
- Perform or claim to perform the deeper correlation/analysis work that belongs to the planned `wireshark-pcap-analysis` skill — state plainly when a request needs that skill instead.
- Invent display-filter field names or `-z` statistic identifiers not confirmed against actual Wireshark/tshark documentation — flag uncertainty and point to the filter reference/`--help` instead.
- Export or transmit capture contents (which may include third-party personal data or credentials in cleartext protocols) outside the case's documented handling process.

## Handoff

- Deeper pattern correlation, beaconing/exfiltration analysis, timeline building across a capture → planned `wireshark-pcap-analysis` skill (not yet available — flag this gap to the user rather than improvising the analysis here).
- IP reputation/ownership/geolocation context → planned `ip-intelligence` skill (not yet available).
- Command-line-only capture without Wireshark's parsing/statistics layer → `tcpdump`.
- Reconstructing full application-layer sessions (HTTP/FTP/telnet) into browsable HTML → `chaosreader`.
- Findings and exported evidence → `forensic-reporting`.

