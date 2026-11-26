import os
import re
import sqlite3
import difflib


def rhv_sanitize_title(title, max_len=120):
    """A node title is not a filename. Strip reserved characters before using it as one."""
    s = re.sub(r'[/\\:*?"<>|]', "-", str(title)).strip().strip(".")
    return s[:max_len] or "untitled"


def rhv_flatten_content(content):
    """Message content from a frame transcript may be a list of typed blocks, not a string.
    str(content) prints Python repr of that structure - this pulls out actual prose."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(block.get("text") or block.get("content") or "")
            else:
                parts.append(str(block))
        return "\n".join(p for p in parts if p)
    return str(content or "")


def rhv_chunk_messages(messages, max_chars=24000, per_msg_cap=4000):
    """Flatten and chunk a message list into strings under max_chars each."""
    chunks, cur, size = [], [], 0
    for m in messages:
        t = rhv_flatten_content(m.get("content"))[:per_msg_cap]
        if not t:
            continue
        cur.append(t)
        size += len(t)
        if size > max_chars:
            chunks.append("\n\n".join(cur))
            cur, size = [], 0
    if cur:
        chunks.append("\n\n".join(cur))
    return chunks


def rhv_extract_with_retry(host, chunks, instruction, tools, max_concurrency=4, model=None):
    """Fan out extraction calls, then retry any empty/errored slot SERIALLY.
    Measured: concurrency=4 returned empty text for 10 of 11 chunks where an identical serial
    call succeeded every time. Returns a list of raw host.llm result dicts, one per chunk."""
    reqs = [dict(prompt=instruction + "\n\n---TRANSCRIPT SPAN---\n" + c,
                 tools=tools, tool_choice={"type": "tool", "name": tools[0]["name"]},
                 max_tokens=4000, model=model)
            for c in chunks]
    results = host.llm(reqs, max_concurrency=max_concurrency) if len(reqs) > 1 else [host.llm(reqs[0])]
    for i, r in enumerate(results):
        ok = r and not r.get("error") and (r.get("tool_use") or r.get("text"))
        if not ok:
            results[i] = host.llm(reqs[i])
    return results


def rhv_body_similarity(a, b):
    """Cheap token-set + sequence similarity, 0..1. Use to catch re-phrased-title duplicates
    that a normalized-title match misses."""
    ta, tb = set(a.lower().split()), set(b.lower().split())
    if not ta or not tb:
        return 0.0
    jaccard = len(ta & tb) / len(ta | tb)
    seq = difflib.SequenceMatcher(None, a[:600], b[:600]).ratio()
    return max(jaccard, seq)


def rhv_find_similar(candidate_body, existing, threshold=0.55):
    """existing: list of (id, body) tuples already in the same folder. Returns the best match
    id if its similarity clears threshold, else None."""
    best_id, best_score = None, 0.0
    for eid, ebody in existing:
        s = rhv_body_similarity(candidate_body or "", ebody or "")
        if s > best_score:
            best_id, best_score = eid, s
    return best_id if best_score >= threshold else None


def rhv_merge_transaction(db_path, work_fn, timeout=15):
    """Wrap a graph.db write in try/finally with a lock timeout, so an exception mid-merge
    cannot leak the connection and lock the database for the rest of the session."""
    con = sqlite3.connect(db_path, timeout=timeout)
    try:
        return work_fn(con)
    finally:
        con.close()


def rhv_write_node(vault, folder, title, body, node_type="claim", status="", source="",
                    links=None):
    """Write one node's markdown file (sanitized filename) - does not touch graph.db."""
    d = os.path.join(vault, folder)
    os.makedirs(d, exist_ok=True)
    fm = "---\ntitle: %s\ntype: %s\nstatus: %s\nsource: %s\n---\n\n" % (
        title, node_type, status, source)
    rel = ""
    if links:
        rel = "\n\n## Related\n" + "\n".join("- [[%s]]" % l for l in links)
    path = os.path.join(d, rhv_sanitize_title(title) + ".md")
    open(path, "w").write(fm + (body or "").strip() + rel + "\n")
    return path


def rhv_is_grounded(candidate):
    """Grounding gate: a claim needs either links to other nodes or an explicit UNGROUNDED
    source declaration. Reject silently-unsupported claims here, not downstream."""
    has_links = bool(candidate.get("links"))
    is_declared = str(candidate.get("source", "")).startswith("UNGROUNDED")
    return has_links or is_declared
