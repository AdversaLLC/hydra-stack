---
name: "aircrack-ng"
description: "Run the aircrack-ng suite (airmon-ng, airodump-ng, aireplay-ng, aircrack-ng) for Wi-Fi security auditing and WEP/WPA-WPA2 key recovery, strictly for authorized examiners assessing networks/devices they have legal authority to test (e.g., a network security assessment under signed engagement, or evidence device analysis under warrant/consent). Triggers on \"aircrack-ng\", \"capture a handshake\", \"monitor mode wifi\", \"crack this wpa handshake\", \"wifi security audit\", \"airodump-ng\". Not a generic \"crack any wifi\" tool — decline or redirect requests lacking documented authorization. Note: this tool is typically more relevant to network security assessment engagements than to disk-based forensic casework; flag that distinction when scoping a request."
---

---
name: aircrack-ng
description: Run the aircrack-ng suite (airmon-ng, airodump-ng, aireplay-ng, aircrack-ng) for Wi-Fi security auditing and WEP/WPA-WPA2 key recovery, strictly for authorized examiners assessing networks/devices they have legal authority to test (e.g., a network security assessment under signed engagement, or evidence device analysis under warrant/consent). Triggers on "aircrack-ng", "capture a handshake", "monitor mode wifi", "crack this wpa handshake", "wifi security audit", "airodump-ng". Not a generic "crack any wifi" tool — decline or redirect requests lacking documented authorization. Note: this tool is typically more relevant to network security assessment engagements than to disk-based forensic casework; flag that distinction when scoping a request.
---

# aircrack-ng Suite

`aircrack-ng` is a suite of tools for Wi-Fi network auditing: packet capture in monitor mode, deauthentication (for capturing handshakes in an authorized test), and key recovery for WEP and WPA/WPA2 (via dictionary/mask attack against a captured 4-way handshake or PMKID). It is used in **network security assessment engagements** far more often than in disk-image forensic casework — if the request is about examining a seized computer or disk image, this is very likely the wrong tool; confirm what's actually being asked before proceeding.

**This is not a generic "crack any Wi-Fi network" capability.** Legitimate use requires the examiner to have documented legal authority over the network or device being assessed — a signed penetration-testing/security-assessment engagement letter scoping the specific network, or evidence-device analysis under warrant/consent where a captured handshake is part of the evidence. If a request doesn't include that context, ask for it before proceeding, or decline and explain why.

Presence of the `aircrack-ng` suite on this PALADIN system was reported by the user via their own system inventory, not independently verified by Claude.

## Before running anything

Establish and document, before any monitor-mode capture or key-recovery attempt:

1. **What network/device is in scope, and what is the authorization?** (engagement letter with named SSID/BSSID scope, or evidence device/case number with warrant/consent)
2. **Does the authorization cover active techniques** like deauthentication (which affects a live network's legitimate users), or passive capture only? These are different levels of intrusiveness and should be scoped explicitly.
3. **Is this actually the right skill for the task**, or is the underlying goal disk/file forensic examination (wrong tool) versus a genuine wireless-network assessment (right tool)?

## Core components

| Tool | Purpose |
|---|---|
| `airmon-ng` | Enable/disable monitor mode on a wireless interface |
| `airodump-ng` | Capture raw 802.11 frames in monitor mode; used to identify nearby networks/clients and to capture a WPA handshake or PMKID |
| `aireplay-ng` | Inject frames — e.g., deauthentication frames to prompt a client to re-associate (and thus produce a capturable handshake) in an authorized test |
| `aircrack-ng` | Attempt key recovery against a WEP capture (statistical attack) or a WPA/WPA2 handshake/PMKID capture (dictionary/mask attack, similar in spirit to hashcat/john but scoped to Wi-Fi key formats) |

## Core syntax

Verify exact flags against `--help`/man pages for each tool on the installed system before relying on them — the following reflects general knowledge of the suite's documented usage, not a live version check on this system.

```
airmon-ng start <interface>
airodump-ng <monitor_interface>
airodump-ng -c <channel> --bssid <target_bssid> -w <capture_prefix> <monitor_interface>
aireplay-ng --deauth <count> -a <bssid> -c <client_mac> <monitor_interface>
aircrack-ng -w <wordlist> <capture_file.cap>
```

Common flags:

| Flag | Purpose |
|---|---|
| `airmon-ng start <iface>` | Put the wireless adapter into monitor mode |
| `airodump-ng -c <channel>` | Restrict capture to a specific channel |
| `--bssid <mac>` | Restrict capture/injection to a specific access point |
| `-w <prefix>` | Write captured packets to files with this prefix (airodump-ng) |
| `aireplay-ng --deauth <n>` | Send `n` deauthentication frames (active/intrusive — requires explicit authorization for this technique specifically) |
| `aircrack-ng -w <wordlist>` | Dictionary attack against a captured handshake/PMKID |
| `aircrack-ng -a <1|2>` | Force WEP (1) or WPA/WPA2 (2) attack mode |

## Typical documented workflow (authorized assessment)

1. **Confirm scope and authorization in writing** before touching any interface — record the engagement/case reference.
2. **Enable monitor mode**:
   ```
   airmon-ng start wlan0
   ```
3. **Survey/identify target network** (passive):
   ```
   airodump-ng wlan0mon
   ```
4. **Capture targeted traffic** on the specific in-scope BSSID/channel:
   ```
   airodump-ng -c <channel> --bssid <bssid> -w case_capture wlan0mon
   ```
5. **If a handshake/PMKID is needed and the engagement scope explicitly permits active techniques**, deauth to prompt re-association — document this action specifically, since it affects live network availability for legitimate users:
   ```
   aireplay-ng --deauth 5 -a <bssid> -c <client_mac> wlan0mon
   ```
6. **Attempt key recovery** against the captured file:
   ```
   aircrack-ng -w /path/wordlist.txt case_capture-01.cap
   ```
7. **Record**: target BSSID/SSID, capture start/end time, whether active techniques were used, wordlist used, and result (including negative results). Return the interface to managed mode when done:
   ```
   airmon-ng stop wlan0mon
   ```

## Troubleshooting

| Symptom | Likely cause | What to check |
|---|---|---|
| `airmon-ng: command not found` or monitor mode fails | Suite not installed, or wireless adapter/chipset doesn't support monitor mode | `which airmon-ng`; confirm adapter chipset supports monitor mode/packet injection (not all built-in laptop Wi-Fi cards do) |
| No networks appear in `airodump-ng` | Wrong channel, monitor mode didn't actually engage, or adapter issue | Confirm `iwconfig`/`iw dev` shows the interface in monitor mode; try scanning across all channels first |
| Deauth frames sent but no handshake captured | Client didn't reconnect in the capture window, deauth not reaching the client, or client uses protected management frames (PMF) which can block this technique | Re-check capture is running before/during/after the deauth attempt; note PMF as a possible reason a normally-effective technique doesn't work — not a tool failure |
| `aircrack-ng` fails to crack WPA handshake | Password not in wordlist, incomplete/corrupt handshake capture, or wrong BSSID targeted | Verify the capture actually contains a full 4-way handshake (aircrack-ng reports this); document negative result rather than assuming capture error |
| WEP attack yields no key with few captured packets | WEP key recovery needs a substantial volume of captured IVs | Note packet count in the report; more capture time/traffic may be needed |

## What this skill must never do automatically

- Run monitor-mode capture, deauthentication, or key-recovery attempts against any network without the user first stating documented authorization scoped to that specific network/engagement — ask if not given.
- Treat deauthentication or other active/injection techniques as equivalent in intrusiveness to passive capture — flag the distinction and confirm the authorization explicitly covers active techniques before using them.
- Frame usage as a generic "crack any Wi-Fi network" capability, or provide attack-tutorial-style guidance divorced from an authorized assessment workflow.
- Proceed when the actual task is disk/file forensic examination rather than a wireless assessment — flag the mismatch instead of forcing this tool to fit.
- Fabricate a recovered key or capture result not actually produced by a real run.
- Disclose recovered Wi-Fi keys outside the documented engagement/case record.

## Handoff

- If the underlying task turns out to be disk-image/file forensic examination rather than wireless assessment → redirect to `paladin-forensic-workflow` or relevant analysis skill.
- Recovered keys used only as needed to access an in-scope network for further authorized assessment; do not extend use beyond the documented scope.
- Assessment findings, capture logs, and recovered-key results → `forensic-reporting`, with explicit note of the engagement/legal authority on file.

