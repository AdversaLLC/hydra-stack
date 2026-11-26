---
name: zip-files
description: Work with zip and other archive formats in claude.ai. Triggers on .zip, .7z, .tar, .tar.gz, .tar.bz2, "compress", "archive", "extract", "unzip", "bundle", "what's in this zip", "split this for upload", "multi-part archive", "z01/z02/z03", "ezyZip", "nested archives", "zip in a zip", or any task involving archive creation, extraction, inspection, splitting, or assembly. Uses the bash sandbox in /home/claude/ for the work, /mnt/user-data/uploads/ for inputs, /mnt/user-data/outputs/ for results, and present_files for delivery. Single-instance, no Nexus emit, no cross-instance handoff.
---

# Zip Files — claude.ai Archive Toolkit

The job: handle archives competently. Inspect, extract, build, split, reassemble, navigate. The bash sandbox has the standard archive tools; this skill is the workflow guide.

The Claude Code original emitted to a Nexus bus and integrated with WareHouse packaging. Stripped here. The actual archive operations are unchanged because they were always just `unzip` / `tar` / `7z` plus discipline.

---

## When to invoke

- Anything ending in `.zip`, `.7z`, `.tar`, `.tar.gz`, `.tar.bz2`, `.tar.xz`, `.rar`, `.zst`
- Split archives: `.zip.001`, `.zip.002`, `.7z.001`, `.zip.z01`, ezyZip-style
- "What's in this archive without extracting it"
- "Bundle these files into a downloadable"
- "This is too big to upload — how do I split it"
- Nested archives (zip-in-zip)

---

## Workflow

### Step 0 — Run veritas

If the archive was just uploaded, audit it first. Note what's there before extracting.

### Step 1 — List before extracting

For an unfamiliar archive, list contents first:

```bash
unzip -l archive.zip          # zip
tar tzf archive.tar.gz | head # tar.gz
tar tjf archive.tar.bz2 | head
7z l archive.7z               # 7z
```

This tells you what you're dealing with before committing disk space.

### Step 2 — Extract to scratch

Extract to `/home/claude/extracted/` (sandbox-writable, ephemeral). Don't extract to `/mnt/user-data/uploads/` — that's read-only.

```bash
mkdir -p /home/claude/extracted
cd /home/claude/extracted
unzip -q /mnt/user-data/uploads/archive.zip   # -q for quiet
# or
tar xzf /mnt/user-data/uploads/archive.tar.gz
```

For 7z:
```bash
sudo apt-get install -y p7zip-full  # if not pre-installed
7z x /mnt/user-data/uploads/archive.7z -o/home/claude/extracted/
```

For password-protected archives: `unzip -P <password>` or `7z x -p<password>`. If the user shared a password in chat, use it; if they expected a known password, ask — don't guess.

### Step 3 — Handle split archives

**ezyZip / Windows split style** (`.zip.001`, `.zip.002`, ...):

```bash
cat archive.zip.001 archive.zip.002 archive.zip.003 > combined.zip
unzip combined.zip
```

**7z split** (`.7z.001`, `.7z.002`, ...):

```bash
# 7z handles split natively — point it at .001 and it finds the rest
7z x archive.7z.001 -o/home/claude/extracted/
```

**zip multi-volume** (`.z01`, `.z02`, ..., `.zip`):

```bash
zip -s 0 archive.zip --out combined.zip
unzip combined.zip
```

Always assemble before reading individual parts. The parts are not standalone archives — they're slices.

### Step 4 — Nested archives

Zip inside zip is common. After extracting the outer archive, scan for inner archives:

```bash
find /home/claude/extracted -name "*.zip" -o -name "*.7z" -o -name "*.tar.gz"
```

For each inner archive: decide whether to recurse. Usually yes if the inner archive is the actual content; usually no if it's a build artifact bundled with the source.

### Step 5 — Building archives

For deliverables back to the user:

```bash
# zip with deflate
cd /home/claude/work
zip -r /mnt/user-data/outputs/<name>.zip <folder>

# tar.gz with reasonable compression
tar czf /mnt/user-data/outputs/<name>.tar.gz <folder>

# 7z with high compression (good for text-heavy archives)
7z a -mx=9 /mnt/user-data/outputs/<name>.7z <folder>
```

For really small file size: `7z a -mx=9 -m0=lzma2`. For best compatibility (any platform, any user): zip. For best compression on Linux-y users: 7z.

### Step 6 — Splitting for upload limits

If the user needs to upload an archive that exceeds a platform's size limit:

```bash
# Split into 25MB chunks (adjust to platform)
zip -s 25m -r /mnt/user-data/outputs/<name>.zip <folder>
# Produces <name>.zip, <name>.z01, <name>.z02, ...

# Or with 7z
7z a -v25m /mnt/user-data/outputs/<name>.7z <folder>
# Produces <name>.7z.001, <name>.7z.002, ...

# Or with split (works on any tar.gz)
tar czf - <folder> | split -b 25M - /mnt/user-data/outputs/<name>.tar.gz.
# Reassemble with: cat <name>.tar.gz.* > combined.tar.gz
```

Tell the user the reassembly command in the response so they don't have to figure it out.

### Step 7 — Present

`present_files` on the deliverable. For multi-part splits, present_files all parts in order. Include reassembly instructions in the message body.

---

## Inspection without extraction

When the archive is large and you only need metadata:

```bash
# How many files
unzip -l archive.zip | tail -1

# Just file paths
unzip -l archive.zip | awk 'NR>3 {print $NF}' | head -50

# Total uncompressed size
unzip -l archive.zip | tail -1 | awk '{print $1}'

# Read a single file from inside a zip without full extraction
unzip -p archive.zip path/inside/file.txt | head -100
```

For tar:

```bash
tar tzf archive.tar.gz | head -50
tar xzfO archive.tar.gz path/inside/file.txt | head  # extract single file to stdout
```

---

## What got stripped from v1

- **Nexus emission of archive operations** — no bus
- **WareHouse packaging integration** — WareHouse was the chatdev-vm artifact bin; outputs go to `/mnt/user-data/outputs/` here
- **Cross-instance "hand split parts to other Claude" workflows** — single instance only

---

## Anti-patterns

- **Extracting before listing**: don't unzip a 5GB archive to see what's in it. List first.
- **Reassembling parts as if they're independent files**: `archive.zip.001` is not a usable zip on its own.
- **Wrong compression for the content**: don't 7z a directory of already-compressed video files. Modest gain, big CPU cost.
- **Forgetting reassembly instructions**: when delivering a split archive, include the cat/zip/7z command the user runs to reassemble.
- **Extracting paths with `..`**: zip files can include `../../../etc/foo` paths. `unzip` modern versions block these by default; older versions don't. For untrusted archives, use `unzip -j` (junk paths) or extract to an isolated directory.

---

## Tool reference

| Need | Tool |
|---|---|
| List archive | `bash_tool`: `unzip -l`, `tar tzf`, `7z l` |
| Extract | `bash_tool`: `unzip -q`, `tar xzf`, `7z x` |
| Build | `bash_tool`: `zip -r`, `tar czf`, `7z a` |
| Split | `bash_tool`: `zip -s`, `7z a -v`, `split` |
| Inspect inside without extracting | `bash_tool`: `unzip -p`, `tar xzfO` |
| Audit archive contents | `veritas` skill |
| Read code in extracted repo | `codebase-navigator` skill |
| Present results | `present_files` |
