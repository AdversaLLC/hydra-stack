---
name: research-harvest-verified
description: Extract findings from a long conversation transcript into a typed research graph (research-base's graph.db format) using structured LLM output rather than free-text JSON parsing, with body-aware dedupe and a grounding gate that rejects unsupported claims. Triggers on "harvest this session", "extract findings and merge to the graph", "check in before the fold", or when context-compact's harvest step needs re-running after producing empty or malformed results. Documents three specific failure modes found in production - free-text JSON parsing silently returns empty/malformed output under concurrency even when an identical single call succeeds; title-only dedupe misses re-phrased duplicates; a merge exception leaks the sqlite connection and locks graph.db for the rest of the session - and the fix for each. Companion to research-base (reads the graph) and context-compact (owns the same harvest step); use this when hardening or debugging that step specifically.
---

# Research Harvest, Verified

Three defects surfaced in production while building a transcript-harvest pipeline for a
research graph. Each failure was silent or partially silent — the code returned success with
degraded or empty output. This skill exists so the next implementation doesn't rediscover them
by burning an hour of wall-clock time against rate limits.

## 1. Structured output, not free-text JSON

**Symptom:** a parallel fan-out (`host.llm([...], max_concurrency=4)`) extracting JSON from
transcript chunks returned empty `text` for most slots, or malformed JSON on others — while an
identical SINGLE request succeeded and returned 5KB of valid JSON in ~24s.

**Root cause:** asking an LLM to "return a JSON array" in free text is fragile under load —
truncation, preamble text, or empty completions are all silently indistinguishable from "found
nothing" if you don't check for them.

**Fix:** request a `tool_choice` / schema-constrained response instead of parsing free text.
A malformed response becomes a schema violation the harness can retry, not a string your own
regex has to babysit. If retrying at the transport level (see #2) isn't enough, this is the
fix that actually removes the failure class.

## 2. Fan-out failures need a retry-serially fallback, not a shrug

**Symptom:** `max_concurrency=4` returned empty text for 10 of 11 chunks; concurrency=1 (serial)
on the same chunks worked every time.

**Fix:** fan out for speed, then retry any empty/errored slot SERIALLY before giving up on it.
Fast when the fan-out works, correct when it doesn't. Record the measured discrepancy as a code
comment — the number (not "sometimes fails") is what stops the next person from "optimizing"
the retry away.

```python
def harvest_chunk_with_retry(chunks, extract_fn, max_concurrency=4):
    results = extract_fn(chunks, max_concurrency=max_concurrency)
    for i, r in enumerate(results):
        if not (r or {}).get("text"):
            results[i] = extract_fn([chunks[i]])[0]  # serial retry, single slot
    return results
```

## 3. Dedupe on body similarity, not title match alone

**Symptom:** three separate graph nodes described one finding after a harvest pass, because each
extraction phrased the title slightly differently ("KNC core vs IPU tile microarchitecture
comparison" / "KNC core vs MK2 IPU tile: compute and memory parity" / "... confirmed by testing").
Title-normalized matching (`cc_norm(title)`) never collided.

**Fix:** before inserting, compare the candidate's body against existing nodes in the same
folder with a cheap similarity check (token-set overlap or difflib ratio); above a threshold,
treat as a merge candidate and surface it for confirmation rather than silently inserting a
duplicate.

## 4. Wrap the merge transaction — an exception must not leak the connection

**Symptom:** a merge failed partway (unrelated FTS schema mismatch), the exception propagated
past `con.close()`, and `graph.db` stayed locked for the rest of the session — a SECOND,
unrelated-looking failure on the next attempt (`sqlite3.OperationalError: database is locked`).

**Fix:** always wrap the write transaction in `try/finally`, and open with a timeout so a
transient lock doesn't hang:

```python
def merge_transaction(db_path, work_fn, timeout=15):
    import sqlite3
    con = sqlite3.connect(db_path, timeout=timeout)
    try:
        return work_fn(con)
    finally:
        con.close()
```

## 5. Sanitize titles before they become filenames

**Symptom:** a harvested title containing `/` ("KNC core vs MK2 IPU tile: compute and memory
parity") was used directly as a filename, creating an unintended subdirectory and a
`FileNotFoundError` on write.

**Fix:** `re.sub(r'[/\\:*?"<>|]', "-", title).strip().strip(".")[:120]` before any
`open(os.path.join(folder, title + ".md"), "w")`.

## The grounding gate (keep, don't weaken)

Every extracted claim needs a `links` field naming what it relates to, OR an explicit
`source="UNGROUNDED: <why>"` string. Reject claims with neither at merge time. This is not
paranoia — in one production run it correctly rejected 17 of 100 extracted claims that the
session's own author had asserted confidently in conversation with no supporting measurement.
Keep the rejection list; it is evidence the gate works, not noise to suppress.

## Workflow

1. Fetch the transcript (or folded-span text) into a plain list of `{role, content}` dicts —
   flatten structured content blocks to prose first (`str(m.get("content"))` is NOT flattening;
   it prints Python repr of typed blocks).
2. Chunk to a safe request size (~24000 chars) and extract via schema-constrained `host.llm`
   calls per §1, with the serial-retry wrapper per §2.
3. Before merging, run body-similarity dedupe per §3 against existing nodes in the same folder.
4. Merge inside `merge_transaction` per §4, sanitizing filenames per §5.
5. Reject any claim lacking `links` or an `UNGROUNDED` source.
6. Log what happened — added / merged / rejected counts — as a correction node if any of #1-#5
   fired, so the defect is visible in the graph rather than silently absorbed.
