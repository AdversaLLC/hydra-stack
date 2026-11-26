---
name: "guymager"
description: "Operate Guymager, the GUI forensic disk imager bundled on PALADIN, for E01/AFF/raw dd acquisition with built-in hashing and verification. Triggers on \"open Guymager\", \"image with Guymager\", \"acquire to E01 with Guymager\", \"Guymager verification failed\", \"Guymager stuck at X%\", \"set up a Guymager job\", or troubleshooting a Guymager acquisition/info file. Covers the standalone GUI application directly — not the PALADIN Toolbox's own wrapped imaging button (see paladin-forensic-workflow for that higher-level flow) and not command-line acquisition (see dc3dd/dcfldd/ddrescue for CLI imaging, or ewf-tools for scripting E01 creation with ewfacquire)."
---

---
name: guymager
description: Operate Guymager, the GUI forensic disk imager bundled on PALADIN, for E01/AFF/raw dd acquisition with built-in hashing and verification. Triggers on "open Guymager", "image with Guymager", "acquire to E01 with Guymager", "Guymager verification failed", "Guymager stuck at X%", "set up a Guymager job", or troubleshooting a Guymager acquisition/info file. Covers the standalone GUI application directly — not the PALADIN Toolbox's own wrapped imaging button (see paladin-forensic-workflow for that higher-level flow) and not command-line acquisition (see dc3dd/dcfldd/ddrescue for CLI imaging, or ewf-tools for scripting E01 creation with ewfacquire).
---

# Guymager

Guymager is a GUI forensic disk-imaging tool for Linux. It acquires a physical device or an already-attached image to EWF (E01), AFF, or raw (dd) format, computing hashes during acquisition and optionally re-reading the output to verify it. This skill covers driving the Guymager application directly and interpreting its output — it does not cover PALADIN Toolbox's own imaging button, which wraps similar functionality with its own UI (see `paladin-forensic-workflow`).

Presence of Guymager on this PALADIN system was reported by the user via their own system inventory; this skill does not independently verify installation or version.

## What Guymager actually does

- Runs as a GUI application (`guymager`, typically launched from a menu or `sudo guymager` depending on how the distro configures device permissions).
- On launch, it scans and lists local block devices in its main window (device, model, serial, size, state).
- An acquisition is configured through the "Acquire" dialog per device: output format (Linux dd raw, EWF/E01, AFF), destination path/filename, case metadata (examiner, case number, evidence number, description — stored in the E01 header for that format), hash algorithms (MD5 and/or SHA-256), compression level (EWF/AFF only), split/segment size, and whether to verify the source before and/or the image after acquisition.
- During and after acquisition Guymager writes an **info file** (`<image>.info`) alongside the image, recording start/end time, source device identifiers, hash values, and verification result — this is the file to pull into a report.
- Guymager itself does not touch the source beyond reading it; it does not partition, format, or wipe anything.

## Typical workflow

1. **Confirm source/destination roles explicitly** before opening the Acquire dialog — which device is evidence (read-only) and where the image is going (destination path/disk, which must have enough free space for the expected image size, plus segment overhead). If a hardware write-blocker is in use, confirm it's active before Guymager ever lists the device as available.
2. **Launch Guymager** and let it enumerate devices. Cross-check the device Guymager shows (model, serial, size) against `lsblk -o NAME,SERIAL,WWN,MODEL,SIZE` output for the same physical unit — don't rely on Guymager's on-screen label alone to confirm identity.
3. **Open Acquire** on the correct device row. Fill in:
   - Format: E01 (EWF) is the common case-file default; raw/dd if a flat image is required; AFF if the AFF toolchain will be used downstream.
   - Case data fields (examiner, case/evidence numbers, description) — these get embedded in the E01 header, so accuracy matters for chain of custody.
   - Hash algorithms — select at least one; SHA-256 is preferred where the case allows, MD5 is still commonly paired for legacy tool compatibility.
   - "Verify source after acquisition" and/or "verify image after acquisition" checkboxes — enabling these re-reads data to confirm the hash matches; it extends acquisition time but is the built-in verification this tool is chosen for.
4. **This step writes to the destination — confirm explicitly with the user before clicking Start**, stating destination path, format, and estimated size.
5. **Monitor progress** in the main window (percentage, speed, estimated time remaining, and any reported read errors on the source). Do not report a completion time or speed that Guymager itself hasn't displayed.
6. **On completion**, read the `.info` file rather than re-typing figures from memory — it contains the actual hash(es) computed and the verification result (match/mismatch, or not performed if verification wasn't enabled).
7. **Verification result is the gate**: if the info file shows a hash mismatch or verification failure, stop and report it — do not treat the acquisition as usable evidence, and do not silently re-run and report only the second attempt's result without noting the first failure.

## Common flags / non-GUI notes

Guymager is designed as a GUI tool; it does not have a fully-documented standard CLI acquisition mode equivalent to dc3dd/dcfldd. Known command-line-relevant points:

| Item | Notes |
|---|---|
| `guymager` | Launches the GUI. May require root or a configured udev/group permission to see raw devices — if devices aren't listed, this is the first thing to check, not a tool bug. |
| `guymager --debug=<n>` | Debug verbosity flag exists in some versions for troubleshooting device-detection issues; verify exact syntax against `guymager --help` on the running system before relying on it — not confirmed across all versions. |
| `/etc/guymager/*.cfg` | Guymager reads configuration (device filters, default paths, local settings) from a config file location that has varied across versions/distros; check the actual installed config path on this system rather than assuming a fixed location. |

Treat the config-file path and debug flag above as general knowledge, not a live version check — confirm against the installed system before citing either in a report.

## Troubleshooting

| Symptom | Likely cause | What to check |
|---|---|---|
| Device not listed in Guymager | Permissions (not running with sufficient privilege), device not recognized by kernel, filtered by config | Check `lsblk`/`dmesg` show the device outside Guymager first; check how Guymager was launched (root vs. user with udev rule) |
| Acquisition stalls or progress stops advancing | Failing sectors on source causing long retries, destination I/O bottleneck, destination out of space | Check `dmesg` for I/O errors on source; check free space on destination; consider whether an error-tolerant tool (ddrescue) is more appropriate for a failing source |
| Verification reports mismatch | Read errors during acquisition, destination media fault, source changed between passes (should not happen on a write-blocked source) | Re-confirm write-block status; check source SMART health; do not overwrite the failed image — preserve it alongside a re-acquisition attempt for the record |
| Info file missing or incomplete | Guymager killed/crashed mid-acquisition, disk full during write | Check whether the process actually completed; do not treat a partial image as complete without the info file's confirmation |
| E01 case metadata fields blank in report | Fields left empty in Acquire dialog before starting | Confirm they were populated at acquisition time — Guymager does not let you edit them into an already-written E01 after the fact |

## What this skill must never do automatically

- Start an acquisition (click Start / write to a destination) without explicit user confirmation stating source, destination, format, and estimated size.
- Report a hash, verification result, duration, or speed that was not actually shown in the Guymager UI or `.info` file.
- Treat a verification failure or mismatch as resolved without an explicit re-acquisition and a fresh, actually-observed passing result.
- Assume a device is write-blocked because it was write-blocked in a previous session — re-confirm each time.
- Edit or hand-modify an `.info` file or E01 header data to "correct" a value after the fact.

## Handoff

- Acquisition log/info file → `forensic-reporting` for the final writeup.
- Broader source/destination discipline and device identification → `paladin-forensic-workflow`.
- Mounting the resulting E01 for read-only review → `forensic-image-mounting` (mount use case) or `ewf-tools` (E01-specific inspection/verification with `ewfinfo`/`ewfverify`).

