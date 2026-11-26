---
name: "dislocker-bitlocker"
description: "Mount and decrypt Microsoft BitLocker-encrypted volumes on Linux using the dislocker suite (dislocker-fuse, dislocker-bek, dislocker-metadata) for read access during forensic examination. Triggers on \"mount this BitLocker volume\", \"decrypt BitLocker with dislocker\", \"I have a .bek recovery key file\", \"dislocker-fuse\", \"read this encrypted Windows partition\", or \"BitLocker recovery key/password decryption on Linux\". Requires a valid decryption credential the examiner is authorized to use (recovery password, recovery key .bek file, clear key, or user password) — this is not a BitLocker-cracking tool. For the PALADIN Toolbox's own built-in BitLocker support (Logical Imager module), see paladin-forensic-workflow instead; use this skill for direct command-line dislocker usage or when finer control over decryption method is needed."
---

---
name: dislocker-bitlocker
description: Mount and decrypt Microsoft BitLocker-encrypted volumes on Linux using the dislocker suite (dislocker-fuse, dislocker-bek, dislocker-metadata) for read access during forensic examination. Triggers on "mount this BitLocker volume", "decrypt BitLocker with dislocker", "I have a .bek recovery key file", "dislocker-fuse", "read this encrypted Windows partition", or "BitLocker recovery key/password decryption on Linux". Requires a valid decryption credential the examiner is authorized to use (recovery password, recovery key .bek file, clear key, or user password) — this is not a BitLocker-cracking tool. For the PALADIN Toolbox's own built-in BitLocker support (Logical Imager module), see paladin-forensic-workflow instead; use this skill for direct command-line dislocker usage or when finer control over decryption method is needed.
---

# Dislocker (BitLocker Decryption)

`dislocker` decrypts Microsoft BitLocker full-volume encryption on Linux, exposing the decrypted volume as a virtual raw device (via FUSE) that can then be mounted normally and examined read-only. It requires a valid credential — it does not brute-force or attack BitLocker.

## Authorization gate

Before running any dislocker command, confirm the examiner has a valid, authorized decryption credential for this specific volume: a recovery password (48-digit), a recovery key file (`.bek`), a clear key, or the user's password. If no such credential is available, this skill does not apply — do not suggest brute-forcing or guessing as an alternative; that is outside dislocker's design and outside this skill's scope.

## Credential types dislocker accepts

| Method | Flag (verify exact spelling against `dislocker-fuse --help`) | Source |
|---|---|---|
| Recovery password | `-p<48-digit-password>` | Printed/saved when BitLocker was enabled, or from AD/Intune escrow |
| Recovery key file | `-f <path-to.bek>` | `.bek` file exported from BitLocker setup or AD |
| Clear key | `-c` | Used when BitLocker protection is suspended (rare in evidence) |
| User password | `-u<password>` | If the volume uses password-based unlock |

Flag letters above reflect common dislocker usage patterns from public documentation but should be confirmed with `dislocker-fuse --help` or `man dislocker-fuse` before use, since exact flag sets have varied across dislocker versions.

## Workflow

1. **Identify the encrypted volume.** Confirm via `blkid` or `fsstat` that the partition is BitLocker-encrypted (signature `-FVE-FS-` at the start of the volume, or filesystem type reported as `BitLocker`).
2. **Confirm this is a read operation against a copy or write-blocked source.** Dislocker itself only reads the encrypted volume to decrypt; mount the source read-only or work against a verified image, never the original write-unprotected device.
3. **Mount the decrypted view via FUSE**, e.g. (verify exact syntax): `dislocker-fuse -V /path/to/encrypted_volume -p<recovery-password> -- /mnt/dislocker-mountpoint`. This exposes a virtual `dislocker-file` representing the raw decrypted volume.
4. **Mount the decrypted virtual volume normally, read-only**: `mount -o ro,loop /mnt/dislocker-mountpoint/dislocker-file /mnt/decrypted-volume`.
5. **Examine the now-readable filesystem** using standard tools (fls, mmls not needed here since you're past the volume layer; standard file browsing/TSK file-content tools apply within the decrypted filesystem).
6. **Unmount cleanly in reverse order** when done: unmount the decrypted filesystem, then unmount the dislocker FUSE mount.

## What this skill must never do automatically

- Attempt to guess, brute-force, or otherwise "recover" a BitLocker credential — that is out of scope; direct the examiner to `memory-key-recovery` (AES key recovery from RAM) or documented recovery-key escrow sources instead if the credential is genuinely unknown, and only within their actual legal authority.
- Mount the decrypted volume read-write without explicit confirmation — default to read-only.
- Mount or decrypt against the original source device rather than an image/write-blocked source without confirming that's intended.
- Report a successful decryption or mount that wasn't actually observed.

## Troubleshooting

| Symptom | Likely cause | Steps |
|---|---|---|
| "Not a BitLocker volume" error | Wrong partition selected, or volume isn't actually BitLocker | Re-check `blkid`/signature; confirm partition offset via `mmls` |
| Decryption fails with correct-looking password | Password format wrong (dashes/spacing in 48-digit key), wrong protector type | Re-enter without formatting characters if applicable; confirm which protector (password vs. key file) applies to this volume |
| FUSE mount succeeds but inner mount fails | Volume type inside isn't NTFS/exFAT as expected, or loop device conflict | Check `fsstat` on the dislocker-file; try a fresh loop device |
| Permission denied on FUSE mount point | User lacks FUSE permissions or mountpoint doesn't exist | Create mountpoint directory first; check `user_allow_other` in `/etc/fuse.conf` if needed |

## Handoff

- Volume identification before decryption → `tsk-mmls`, `tsk-fsstat`.
- Examining files inside the decrypted volume → `tsk-fls`, `tsk-file-content`.
- If the BitLocker key must be recovered from a memory image rather than being already known → `memory-key-recovery`.
- Writing up the decryption method and credential source used → `forensic-reporting`.

