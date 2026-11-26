---
name: "adb-fastboot"
description: "Android Debug Bridge (adb) and Fastboot for interacting with a live-connected Android device: pulling files, listing packages, inspecting logs, sideloading, flashing partitions, or unlocking bootloaders. Trigger on \"adb pull\", \"adb shell\", \"fastboot flash\", \"unlock the bootloader\", \"sideload this APK\", \"get logcat\", \"connect this Android device\". FORENSIC CAVEAT: adb/fastboot are live-device tools, NOT write-blocked acquisition tools - connecting adb and running commands can alter device state (timestamps, wake state, logs, cached files) even for read commands, and fastboot can flash/wipe the device. Different from write-blocked disk imaging (paladin-forensic-workflow) and from parsing a completed extraction (leapp-suite). Never treat this as a passive acquisition method - live interaction requires justification and documentation as a deviation."
---

---
name: adb-fastboot
description: Android Debug Bridge (adb) and Fastboot for interacting with a live-connected Android device — pulling files, listing packages, inspecting logs, sideloading, flashing partitions, or unlocking bootloaders. Trigger on "adb pull", "adb shell", "adb this phone", "fastboot flash", "unlock the bootloader", "sideload this APK", "get logcat", "list installed packages via adb", or "connect this Android device". IMPORTANT FORENSIC CAVEAT: adb/fastboot are live-device interaction tools, NOT write-blocked forensic acquisition tools — connecting adb to a running device and issuing commands can alter device state (timestamps, wake/unlock state, logs, package data, cached files) even for "read" commands, and fastboot operations can flash or wipe the device outright. This is fundamentally different from write-blocked disk imaging (see paladin-forensic-workflow) and different from parsing an already-completed extraction (see leapp-suite). Do not use this skill assuming it is a passive/non-invasive acquisition method — any live-device interaction for forensic purposes is a deviation from passive acquisition that must be justified and documented.
---

# ADB / Fastboot

## What this is

**adb (Android Debug Bridge)** and **fastboot** are Android SDK platform-tools for communicating with a live, powered Android device over USB (or, for adb, over network/Wi-Fi debugging). They are Google's developer/debugging tools, not forensic tools:

- **adb** talks to a device running Android with USB debugging enabled and a running `adbd` daemon — it can shell into the device, pull/push files, install/uninstall packages, read logs, and more.
- **fastboot** talks to a device in **bootloader/fastboot mode** (not a running Android OS) — it can flash partitions, unlock/lock the bootloader, and reboot to other modes. Fastboot operations are typically destructive or state-changing by nature (flashing, unlocking wipes user data on most devices).

## Forensic implications — read this before running anything

Standard digital forensic methodology (e.g., ACPO principles, NIST guidance) calls for acquisition methods that do not alter the original evidence, and for any unavoidable alteration to be understood, justified, and documented. **adb and fastboot do not meet that bar as generally used:**

- Merely connecting a device via USB and enabling/using adb can change: last-connected/mount timestamps, wake-lock/screen state, `logcat` buffers (which continuously roll over — reading them doesn't add entries, but the act of shelling in generates new log entries such as auth/debugging events), and can trigger app or OS background activity (sync, notifications) purely because the device is now awake and possibly network-connected.
- `adb backup` (where still supported) and `adb pull` are non-destructive to the *files being read* but the *act of connecting and running commands* still changes device state as above.
- **Fastboot mode operations that flash, unlock, or wipe are directly destructive to evidence** — unlocking a bootloader on many devices triggers an automatic factory data wipe.
- Because of this, any use of adb/fastboot on a piece of evidence is a **deviation from a purely passive, write-blocked acquisition**. Defensible methodology requires that deviation be:
  1. Justified — why was live interaction necessary (e.g., no other extraction method available for this device/OS combination, device cannot be powered off without losing access due to encryption)?
  2. Documented at the time — what command was run, when, by whom, and what state change it was expected/observed to cause.
  3. Consistent with your lab's SOP and, where applicable, disclosed to opposing parties/legal counsel.

This skill treats adb/fastboot as **an investigative/extraction utility that requires the same forensic-methodology discipline as any other deviation from passive acquisition** — not as a forensic acquisition tool in the write-blocked sense.

## Command reference (verify exact flags against `adb --help` / `fastboot --help`)

I am not fully confident every flag below matches the exact current platform-tools release — confirm against `adb help`, `fastboot help`, or the Android SDK documentation before relying on any of these in a procedure.

### adb — read-oriented (log, don't gate on confirmation, but still document)

```
adb devices -l                 # list connected devices/serials
adb shell getprop               # dump device properties
adb pull <device_path> <local_path>   # copy a file/dir off the device
adb shell dumpsys <service>      # dump system service state (battery, package, etc.)
adb shell pm list packages [-f]  # list installed packages
adb logcat -d                    # dump current log buffer (does not clear unless -c used)
adb bugreport <output.zip>       # generate a full bug report bundle
adb backup ...                   # legacy full/partial backup (deprecated/limited on modern Android; verify support on target OS version)
```

### adb — write-oriented (ALWAYS require explicit user confirmation before running)

```
adb push <local_path> <device_path>   # writes a file TO the device
adb install <apk>                      # installs a package
adb uninstall <package>                # removes a package
adb shell rm ...                       # deletes on-device data
adb shell settings put ...             # changes device settings
adb reboot [bootloader|recovery]       # changes device power/boot state
adb shell input ...                    # simulates taps/keystrokes, changes UI/app state
```

### fastboot — inherently state-changing (ALWAYS require explicit user confirmation; assume evidence-altering)

```
fastboot devices                 # list devices in bootloader mode (read-only, safe to enumerate)
fastboot flashing unlock          # unlocks bootloader — typically wipes user data
fastboot flash <partition> <img>  # overwrites a partition
fastboot erase <partition>        # erases a partition
fastboot reboot                   # changes device boot state
fastboot oem <command>            # vendor-specific, behavior varies and is often destructive
```

`fastboot devices` is the only fastboot command that is purely enumerative; nearly everything else in fastboot's normal use is destructive or state-altering by design, since fastboot exists to flash firmware.

## Typical workflow (when live interaction is the justified path)

1. **Document the justification first.** Record why write-blocked/passive methods (physical extraction via a dedicated tool, LEAPP-compatible full-filesystem pull, chip-off, JTAG) are not available or not viable for this device, before connecting anything.
2. **Photograph/document device state** (screen state, battery level, visible notifications) before connecting, per standard practice for any live-system interaction.
3. **Connect and enumerate only:** `adb devices -l` (or `fastboot devices` if already in bootloader mode) to confirm connectivity and capture the device serial for the log.
4. **Run read-only adb commands** needed for the extraction/investigation (`adb pull`, `adb shell dumpsys`, `adb logcat -d`, `adb bugreport`), logging each exact command, timestamp, and operator.
5. **Never run a write-oriented adb command or any fastboot flashing/unlocking command without stopping to get explicit confirmation first**, restating exactly what will change on the device (e.g., "this will unlock the bootloader, which will trigger a factory data wipe on this device model — proceed?").
6. **Hash/verify pulled files** after transfer, same as any other acquired artifact, and record the pull path/destination.
7. **Feed extracted files into the appropriate parser** (e.g., `leapp-suite` for a resulting filesystem-style extraction) — adb/fastboot's role ends at getting data off the device, not analyzing it.
8. **Document every command run, its timestamp, and its known/observed effect on device state** as part of the case record, and hand this off to `forensic-reporting` for the written methodology section.

## Troubleshooting

| Symptom | Likely cause | What to try |
|---|---|---|
| `adb devices` shows nothing / "unauthorized" | USB debugging not enabled, or device not yet authorized this host's RSA key | Check device screen for an authorization prompt; note that accepting it is itself a device-state-changing interaction and should be logged |
| `adb devices` shows "offline" | Daemon in a bad state, cable/port issue, or device asleep | Try `adb kill-server && adb start-server`; try a different cable/port; note any reconnect attempts in the log |
| `fastboot devices` shows nothing | Device not actually in bootloader/fastboot mode, or missing USB driver (common on Windows hosts) | Confirm device is in bootloader mode (varies by manufacturer key combo); check/install vendor USB drivers |
| `adb pull` fails with permission denied | Target path requires root, or device is not rooted and app-private storage is protected by Android's sandbox | Do not attempt to root the device as a workaround without separate, explicit justification and confirmation — rooting is itself a significant, generally irreversible forensic deviation |
| Bootloader unlock is required to proceed | Device is OEM-locked and blocks the extraction method needed | Stop and escalate: confirm with case lead/counsel whether unlocking (and its expected data wipe) is acceptable before running `fastboot flashing unlock` |

## What this skill must never do automatically

- Never run any write-oriented adb command (`push`, `install`, `uninstall`, `shell rm`, `shell settings put`, `reboot`, `shell input`, etc.) without first stating exactly what it will change and getting explicit user confirmation.
- Never run any fastboot command beyond plain `fastboot devices` without first stating the expected effect (including "this will likely wipe user data") and getting explicit user confirmation.
- Never characterize adb/fastboot use as a passive, write-blocked, or forensically "safe" acquisition method — always frame it as a live-device interaction that alters state and must be justified/documented as a deviation from passive acquisition.
- Never suggest rooting, exploiting, or bypassing lock-screen/bootloader protections as a routine step — these are separate, higher-impact deviations requiring their own explicit justification and confirmation.
- Never invent adb/fastboot flags not confirmed against `--help`/documentation — flag this uncertainty to the user rather than presenting guessed syntax as fact.
- Never claim adb/fastboot presence or version on the examiner's PALADIN system was independently verified by Claude — that is only as reported by the user's own system inventory.
- Never skip logging the exact command, timestamp, and operator for every command run against a live device — this log is what makes the deviation from passive acquisition defensible later.

