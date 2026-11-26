---
name: veritas
description: Upload completeness auditor for claude.ai. Triggers automatically whenever files are uploaded, the user says "verify everything", "did you read X", "what did you miss", "audit uploads", "progress report", or "did you check all of them". Forces 100% coverage of every uploaded file with explicit READ/NOTED/ASSEMBLED/DUPLICATE/PARTIAL/BLOCKED status. Catches silent omissions, flags split archives that need reassembly, detects byte-identical duplicates, and reports exact percentage progress when uploads exceed session capacity. Run this before starting any build, analysis, or transformation work on uploaded content.
---

# Veritas — claude.ai Upload Audit

Single job: when files are uploaded, every single one gets a status. No silent skipping. No "I'll get to that later" without saying so explicitly.

claude.ai version. This skill is one of the lucky ones — it works almost identically to the Claude Code original because uploads at `/mnt/user-data/uploads/` are real and inspectable here. The only thing stripped is the Nexus bus emit step.

---

## Trigger Protocol

When ANY upload is detected (zip, single file, multiple files, anything mentioned in `<uploaded_files>` blocks), IMMEDIATELY:

```
1. List every file under /mnt/user-data/uploads/ with size + extension
2. Categorize each: READABLE / SPLIT_ARCHIVE / DUPLICATE / BINARY_SKIP
3. Assemble split archives FIRST (z01/z02/z03/.7z.001 etc → combined)
4. For each readable file: report what was found (1 sentence each)
5. Print the audit table BEFORE doing any other work
```

The audit table comes first. The user's actual request comes after, anchored on what was actually in the uploads.

---

## Status Codes

| Code | Meaning |
|---|---|
| ✅ READ | File opened, content catalogued, ready to use |
| ✅ NOTED | Binary or out-of-scope — recorded what it is and why we're not parsing |
| ✅ ASSEMBLED+READ | Split archive reassembled, then read |
| ✅ DUPLICATE | Confirmed byte-identical to another upload (give the other file's name) |
| ⚠️ PARTIAL | Opened but didn't finish — say WHY (size, time, complexity) |
| ❌ BLOCKED | Cannot open. Reason required (encrypted, unknown format, etc.) |
| ❓ UNKNOWN | Not yet processed (only valid mid-audit, never as a final state) |

Every upload ends in one of the ✅/⚠️/❌ states. `❓ UNKNOWN` is a process-internal marker only.

---

## Self-check passes (before reporting done)

After the audit, run three silent checks:

**Coverage check:** Walk every entry in `/mnt/user-data/uploads/`. Does each one appear in the audit table with a status? If any are missing, that's a SILENT OMISSION — fix before reporting.

**Duplicate check:** For files of identical size, run a quick hash (`md5sum` or `sha256sum`) to confirm. Don't claim duplicate without actually comparing.

**Partial check:** Any `⚠️ PARTIAL` entries — is the partial-ness justified? If a file was just skipped because it was tedious, that's not partial-with-reason, that's silent omission. Either finish it or say explicitly "deferred because [X]".

These self-checks replace the "Shadow Clone Verification" framing from the original skill — same checks, no theatrics about parallel agents.

---

## Audit table format

Print it as a table, not a bulleted list. Markdown table is fine.

```
| File | Size | Status | Note |
|------|------|--------|------|
| skills.zip | 526 KB | ✅ READ | 134 SKILL.md files, see breakdown below |
| photo.jpg | 2.1 MB | ✅ NOTED | image of whiteboard, will OCR if asked |
| logs.tar.gz.001 | 4 GB | ⚠️ PARTIAL | first part of split archive, need .002 to assemble |
```

Then a one-paragraph summary of what's actually IN the uploads (the substantive content), so the user can verify Claude actually understood it.

---

## Capacity overflow protocol

If the upload set is too large to fully audit in one turn (rare in claude.ai because uploads are usually small, but possible for big zips with hundreds of files):

1. Audit what you can in this turn
2. Report `audited X of Y files (Z%)`
3. State exactly which files are deferred
4. Ask the user before doing anything else: continue auditing, or proceed with the partial set?

Never pretend to have audited what you haven't. Never silently sample.

---

## Specific patterns

**Zip files:** Use `unzip -l` first to list contents without extracting. Decide if extraction is needed for the user's task. If yes, extract to `/home/claude/extracted/` (writable scratch).

**Split archives:** ezyZip-style splits (`.zip.001`, `.zip.002`) need concatenation: `cat file.zip.001 file.zip.002 > combined.zip`. 7z splits use `7z x file.7z.001`. Don't try to read the parts individually.

**Nested archives:** Zip-in-zip is common in Joshua's workflow. Document the nesting depth in the note column.

**Images:** If the file is in the context as a base64 image, you already see it — note it as `✅ READ (visible inline)` and describe what you see. If it's a path-only image, view via the `view` tool.

**PDFs:** Already in context for ones under the size threshold. For larger PDFs, use the `pdf-reading` skill workflow rather than naively `cat`-ing them.

**Code files / SKILL.md:** Treat as text. `view` works fine.

---

## What this skill is NOT

- Not a Nexus bus emitter — there's no bus to emit to in claude.ai
- Not a "shadow clone" verifier in the literal multi-agent sense — the three self-check passes are sequential, by one Claude
- Not a permanent file persister — uploads live for this session only

---

## End condition

The audit is done when:
- Every upload has a status that is NOT `❓ UNKNOWN`
- Every `⚠️ PARTIAL` has a stated reason
- Every `❌ BLOCKED` has a stated reason
- The summary paragraph captures the substantive content
- The user sees the table BEFORE Claude does any other work on the uploads

Then proceed to the user's actual request.
