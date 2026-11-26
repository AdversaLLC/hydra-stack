import os, re, sqlite3, json

def cc_norm(t):
    return re.sub(r"[^a-z0-9 ]", "", (t or "").lower()).strip()

def cc_harvest(frame_id, base, max_messages=400, model=None):
    """Extract candidate findings from a frame transcript. RUN THIS IN THE `repl` TOOL - it calls
    host.frames, which does not exist in the python/r kernels this sidecar auto-loads into.
    From `python`, use cc_fetch_transcript (repl) then cc_harvest_file (python) instead.
    Does NOT write anything - review before calling cc_merge."""
    fr = host.frames(frame_id=frame_id, max_results=max_messages)
    return cc_harvest_messages(fr.get("messages", []), base, model=model)


def cc_harvest_messages(msgs, base, model=None):
    """Extract candidate findings from an already-fetched message list. Kernel-agnostic:
    works in python or repl because it never touches control-plane methods."""
    existing = [r["id"] for r in base["query"]("SELECT id FROM nodes")]
    chunks, cur, size = [], [], 0
    for m in msgs:
        t = cc_text(m.get("content"))[:4000]
        cur.append(t); size += len(t)
        if size > 24000:
            chunks.append("\n\n".join(cur)); cur, size = [], 0
    if cur:
        chunks.append("\n\n".join(cur))
    instr = (
        "Extract durable research FINDINGS from this transcript span. A finding is a claim, a number "
        "with its basis, a correction, or an open question - never a description of what was done.\n"
        "Return JSON: a list of objects with keys title (short noun phrase), folder (one of Claims, "
        "Measurements, Corrections, Questions, Hardware), body (markdown, 40-200 words, keep every "
        "number's peak/measured/bound label), status, source (a citation, or a string starting "
        "UNGROUNDED: with the reason), and links (titles of related findings).\n"
        "Skip anything already covered by these existing node titles: " + "; ".join(existing[:120]) + "\n"
        "Prefer evidence that CHALLENGES the project's thesis over evidence that confirms it. "
        "Return [] if the span contains no durable finding. Output JSON only."
    )
    # Structured output via a tool schema, not free-text JSON. Measured: free-text parsing failed
    # on 10 of 11 chunks (JSONDecodeError on one, empty text on the rest) even with serial retry.
    # A tool schema makes malformed output impossible rather than merely unlikely.
    tool = {
        "name": "record_findings",
        "description": "Record durable research findings extracted from a transcript span.",
        "input_schema": {
            "type": "object",
            "properties": {
                "findings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "folder": {"type": "string",
                                       "enum": ["Claims", "Measurements", "Hardware",
                                                "Corrections", "Questions"]},
                            "title": {"type": "string"},
                            "body": {"type": "string"},
                            "status": {"type": "string"},
                            "source": {"type": "string"},
                            "links": {"type": "array", "items": {"type": "string"},
                                      "description": "Titles of EXISTING or other NEW findings "
                                      "in this same call that this one relates to. Leave empty "
                                      "only if genuinely unconnected - an isolated node is a "
                                      "documented gap, not a convenience."},
                        },
                        "required": ["folder", "title", "body"],
                    },
                }
            },
            "required": ["findings"],
        },
    }
    reqs = [dict(prompt=instr + "\n\nSPAN:\n" + c, model=model or host.reasoning_model(),
                 max_tokens=8000, tools=[tool],
                 tool_choice={"type": "tool", "name": "record_findings"}) for c in chunks]
    outs = host.llm(reqs, max_concurrency=3) if len(reqs) > 1 else [host.llm(reqs[0])]
    cands, failures = [], []
    for n, o in enumerate(outs):
        tu = (o or {}).get("tool_use")
        if not tu:
            failures.append((n, "no tool_use; stop=%s text=%s"
                             % ((o or {}).get("stop_reason"), ((o or {}).get("text") or "")[:60])))
            continue
        block = tu[0] if isinstance(tu, list) and tu else tu
        got = (block or {}).get("input", {}).get("findings", [])
        if not got:
            failures.append((n, "tool_use with empty findings"))
        cands.extend(got)
    if failures and not cands:
        raise RuntimeError(
            "cc_harvest produced NO candidates; %d/%d chunks failed. Silence is a bug, not an "
            "empty session. First: %s" % (len(failures), len(outs), failures[:3]))
    if failures:
        print("cc_harvest: %d of %d chunks yielded nothing (kept %d): %s"
              % (len(failures), len(outs), len(cands), failures[:2]))
    return cands

def cc_review(cands):
    """Print candidates compactly for human/agent review before merging."""
    for i, c in enumerate(cands):
        print("[%d] %-13s %-46s %s" % (i, c.get("folder", "?"), (c.get("title") or "")[:46],
                                       (c.get("status") or "")[:22]))
    return len(cands)

def cc_safe_name(title):
    """A node title is not a filename. Slashes become directory separators, and colons and
    other reserved characters break on some filesystems - sanitise before writing."""
    s = re.sub(r"[/\\:*?\"<>|]", "-", str(title)).strip().strip(".")
    return (s[:120] or "untitled")


def cc_vault(base):
    """research-base's loader does not always expose a 'vault' key. Resolve it from the base,
    falling back to the directory the graph was opened from."""
    v = base.get("vault") or base.get("vault_dir") or base.get("path")
    if v:
        return v
    raise KeyError("base has no vault path - pass base['vault'] = <dir containing graph.db>")


def cc_merge(base, cands, dry_run=False):
    """Dedupe against existing nodes and insert survivors. Returns a receipt dict."""
    vault = cc_vault(base)
    # timeout + try/finally: an exception mid-loop previously leaked the connection and left
    # graph.db locked for the rest of the session, which reads as a mysterious second failure.
    con = sqlite3.connect(os.path.join(vault, "graph.db"), timeout=15)
    try:
        return cc_merge_inner(con, base, cands, vault, dry_run)
    finally:
        try:
            con.close()
        except Exception:
            pass


def cc_merge_inner(con, base, cands, vault, dry_run=False):
    have = {cc_norm(r[0]): r[0] for r in con.execute("SELECT id FROM nodes")}
    added, merged, rejected = [], [], []
    for c in cands:
        title = (c.get("title") or "").strip()
        if not title:
            rejected.append(("<no title>", "empty title")); continue
        key = cc_norm(title)
        if key in have:
            merged.append((title, have[key])); continue
        folder = c.get("folder") or "Claims"
        grounded = bool(c.get("links")) or str(c.get("source", "")).startswith("UNGROUNDED")
        if folder == "Claims" and not grounded:
            rejected.append((title, "claim with no link and no UNGROUNDED source")); continue
        if dry_run:
            added.append(title); continue
        d = os.path.join(vault, folder)
        os.makedirs(d, exist_ok=True)
        fm = "---\ntitle: %s\ntype: %s\nstatus: %s\n---\n\n" % (
            title, "claim" if folder == "Claims" else folder.lower().rstrip("s"), c.get("status", ""))
        rel = ""
        if c.get("links"):
            rel = "\n\n## Related\n" + "\n".join("- [[%s]]" % l for l in c["links"])
        open(os.path.join(d, cc_safe_name(title) + ".md"), "w").write(
            fm + (c.get("body") or "").strip() + rel + "\n")
        con.execute("INSERT OR REPLACE INTO nodes(id,type,folder,status,source,tags) VALUES (?,?,?,?,?,?)",
                    (title, "claim" if folder == "Claims" else folder.lower().rstrip("s"),
                     folder, c.get("status", ""), c.get("source", ""), "harvested"))
        for l in (c.get("links") or []):
            if cc_norm(l) in have:
                con.execute("INSERT INTO edges VALUES (?,?,?)", (title, have[cc_norm(l)], "related"))
        try:
            con.execute("INSERT INTO fts VALUES (?,?,?)", (title, folder, c.get("body") or ""))
        except Exception:
            pass
        have[key] = title
        added.append(title)
    con.commit()
    return dict(added=added, merged=merged, rejected=rejected,
                n_added=len(added), n_merged=len(merged), n_rejected=len(rejected))

def cc_verify(base):
    """Fail-closed check: every claim node must have a grounding edge or an UNGROUNDED source."""
    q = base["query"]
    claims = {r["id"] for r in q("SELECT id FROM nodes WHERE type='claim'")}
    grounded = {r["src"] for r in q("SELECT src FROM edges WHERE kind IN ('supported-by','documented-in')")}
    declared = {r["id"] for r in q("SELECT id FROM nodes WHERE source LIKE 'UNGROUNDED%'")}
    bad = sorted(claims - grounded - declared)
    return dict(ok=not bad, ungrounded_undeclared=bad, n_claims=len(claims))

def cc_recover(phrase):
    """Recover verbatim bytes for a value seen in a folded span. Returns [] if genuinely absent."""
    return host.archive.search('"%s"' % phrase, k=6)

def cc_recite(base, max_chars=420):
    """Three-line bearing block: thesis, current blocker, most recent correction.
    Adapted from the compact-plus recitation pattern - emit this in the turns BEFORE a fold,
    not only after one, so orientation survives the window filling up."""
    q = base["query"]
    thesis = ""
    th = (base.get("theory") or "").split("## The operating theory")
    if len(th) > 1:
        thesis = " ".join(th[1].split("\n\n")[1].split())[:180]
    blk = q("SELECT id FROM nodes WHERE status='blocking-free' LIMIT 1") or \
          q("SELECT id FROM nodes WHERE status LIKE 'blocking%' LIMIT 1")
    corr = q("SELECT id FROM nodes WHERE folder='Corrections' ORDER BY rowid DESC LIMIT 1")
    return "\n".join(l[:max_chars] for l in [
        "THESIS:   " + (thesis or "(no theory loaded)"),
        "BLOCKING: " + (blk[0]["id"] if blk else "(nothing blocking)"),
        "LAST FIX: " + (corr[0]["id"] if corr else "(no corrections yet)")])

def cc_should_checkin(n_findings_since_last=0, turns_since_last=0, folds=0):
    """Threshold heuristic, adapted from compact-plus's usage-threshold trigger.
    Check in EARLY: a finding harvested before a fold is verbatim, one harvested after is
    second-hand through a summary. Returns (bool, reason)."""
    if folds > 0 and n_findings_since_last > 0:
        return True, "fold already occurred with unharvested findings - harvest now and verify values with cc_recover"
    if n_findings_since_last >= 5:
        return True, "5+ unharvested findings"
    if turns_since_last >= 25:
        return True, "25+ turns since last check-in"
    return False, "no threshold crossed"


def cc_fetch_transcript(frame_id, out_path="handoff/transcript.json", max_messages=400):
    """RUN THIS IN THE `repl` TOOL. host.frames is control-plane-only and does not exist in the
    python/r kernels where this sidecar auto-loads, so the transcript must be fetched here and
    handed across the filesystem. Writes a JSON list of messages; returns the path and count."""
    import json, os
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fr = host.frames(frame_id=frame_id, max_results=max_messages)
    msgs = fr.get("messages", [])
    tmp = out_path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(msgs, fh)
    os.replace(tmp, out_path)
    return dict(path=out_path, n_messages=len(msgs), truncated=fr.get("truncated", False))


def cc_harvest_file(path, base, model=None):
    """RUN THIS IN THE `python` TOOL, after cc_fetch_transcript has written `path` from repl.
    Same contract as cc_harvest but reads the transcript from disk instead of calling host.frames."""
    import json
    msgs = json.load(open(path))
    return cc_harvest_messages(msgs, base, model=model)


def cc_text(content):
    """Flatten an Anthropic-style content field (str, or list of typed blocks) to plain text.
    Drops empty thinking blocks and tool noise so the extraction prompt sees prose, not repr()."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    out = []
    for b in content:
        if not isinstance(b, dict):
            out.append(str(b)); continue
        t = b.get("type")
        if t == "text" and b.get("text"):
            out.append(b["text"])
        elif t == "thinking" and b.get("thinking"):
            out.append(b["thinking"])
        elif t == "tool_result":
            c = b.get("content")
            out.append(cc_text(c) if not isinstance(c, str) else c)
    return "\n".join(x for x in out if x)
