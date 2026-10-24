import os, sqlite3, zipfile, json

VAULT_DIRNAME = "vault"

def rb_find_zip(pattern="ResearchBase.zip"):
    """Newest artifact whose filename ends with pattern; returns local path or None."""
    arts = host.artifacts(limit=300)["artifacts"]
    hits = [a for a in arts if a["filename"].endswith(pattern)]
    if not hits:
        return None
    return host.artifact_path(hits[0]["latest_version_id"])

def rb_load(zip_path=None, extract_to="rb_extract"):
    """Extract the research base and return a query dict. Uses newest artifact if zip_path is None."""
    if zip_path is None:
        zip_path = rb_find_zip()
    if zip_path is None:
        raise FileNotFoundError("no *-ResearchBase.zip artifact in this project")
    os.makedirs(extract_to, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(extract_to)
    roots = [d for d in os.listdir(extract_to) if os.path.isdir(os.path.join(extract_to, d))]
    vault = None
    for r in roots:
        cand = os.path.join(extract_to, r, VAULT_DIRNAME)
        if os.path.exists(os.path.join(cand, "graph.db")):
            vault = cand
    if vault is None:
        raise FileNotFoundError("graph.db not found in extracted base")
    con = sqlite3.connect(os.path.join(vault, "graph.db"))
    con.row_factory = sqlite3.Row
    def q(s, p=()):
        return [dict(r) for r in con.execute(s, p).fetchall()]
    def rd(f):
        p = os.path.join(vault, f)
        return open(p).read() if os.path.exists(p) else ""
    def note(title):
        row = q("SELECT folder FROM nodes WHERE id=?", (title,))
        if not row:
            return None
        p = os.path.join(vault, row[0]["folder"], title + ".md")
        return open(p).read() if os.path.exists(p) else None
    return dict(
        vault=vault, theory=rd("THEORY.md"), napkin=rd("NAPKIN.md"), query=q, note=note,
        search=lambda t, k=8: q("SELECT id,folder,snippet(fts,2,'**','**','...',18) s FROM fts WHERE fts MATCH ? LIMIT ?", (t, k)),
        grounds=lambda c: q("SELECT dst,kind FROM edges WHERE src=? AND kind IN ('supported-by','documented-in')", (c,)),
        challenges=lambda: q("SELECT src,dst,kind FROM edges WHERE kind IN ('challenges','qualifies','corrects')"),
        gates=lambda: q("SELECT src,dst FROM edges WHERE kind='gates'"),
        ungrounded=lambda: q("SELECT id,source FROM nodes WHERE source LIKE 'UNGROUNDED%'"),
        blocking=lambda: q("SELECT id,status FROM nodes WHERE status LIKE 'blocking%'"),
        by_status=lambda s: q("SELECT id FROM nodes WHERE status=?", (s,)),
        central=lambda k=10: q("SELECT dst id, COUNT(*) degree FROM edges GROUP BY dst ORDER BY degree DESC LIMIT ?", (k,)),
        n_nodes=q("SELECT COUNT(*) c FROM nodes")[0]["c"],
        n_edges=q("SELECT COUNT(*) c FROM edges")[0]["c"],
    )

def rb_note(base, folder, title, ntype, body, status, links=None, source="", tags=""):
    """Add a node + markdown note to a loaded base. Claims need a grounding edge or an UNGROUNDED source."""
    vault = base["vault"]
    os.makedirs(os.path.join(vault, folder), exist_ok=True)
    fm = "---\ntitle: %s\ntype: %s\nstatus: %s\n---\n\n" % (title, ntype, status)
    rel = ""
    if links:
        rel = "\n\n## Related\n" + "\n".join("- [[%s]]" % l for l in links)
    open(os.path.join(vault, folder, title + ".md"), "w").write(fm + body.strip() + rel + "\n")
    con = sqlite3.connect(os.path.join(vault, "graph.db"))
    con.execute("INSERT OR REPLACE INTO nodes(id,type,folder,status,source,tags) VALUES (?,?,?,?,?,?)",
                (title, ntype, folder, status, source, tags))
    for l in (links or []):
        con.execute("INSERT INTO edges VALUES (?,?,?)", (title, l, "related"))
    con.execute("INSERT INTO fts VALUES (?,?,?)", (title, folder, body))
    con.commit(); con.close()
    return title

def rb_edge(base, src, dst, kind):
    """Add a typed edge. kind in supported-by, documented-in, challenges, qualifies, corrects, gates, related."""
    allowed = ("supported-by", "documented-in", "challenges", "qualifies", "corrects", "gates", "related")
    if kind not in allowed:
        raise ValueError("kind must be one of %s" % (allowed,))
    con = sqlite3.connect(os.path.join(base["vault"], "graph.db"))
    con.execute("INSERT INTO edges VALUES (?,?,?)", (src, dst, kind))
    con.commit(); con.close()

def rb_audit(base):
    """Honesty audit: ungrounded claims, broken links, orphans, missing challenge edges."""
    q = base["query"]
    claims = {r["id"] for r in q("SELECT id FROM nodes WHERE type='claim'")}
    grounded = {r["src"] for r in q("SELECT src FROM edges WHERE kind IN ('supported-by','documented-in')")}
    declared = {r["id"] for r in q("SELECT id FROM nodes WHERE source LIKE 'UNGROUNDED%'")}
    ids = {r["id"] for r in q("SELECT id FROM nodes")}
    dangling = [e for e in q("SELECT src,dst FROM edges") if e["dst"] not in ids or e["src"] not in ids]
    linked = {e["dst"] for e in q("SELECT dst FROM edges")} | {e["src"] for e in q("SELECT src FROM edges")}
    return dict(
        ungrounded_undeclared=sorted(claims - grounded - declared),
        dangling_edges=dangling,
        orphans=sorted(ids - linked),
        n_challenge_edges=len(base["challenges"]()),
    )

def rb_rebuild(base, out_name="ResearchBase.zip"):
    """Re-zip the extracted base (parent of vault/) after edits. Returns zip path."""
    root = os.path.dirname(base["vault"])
    zn = os.path.basename(root) + "-" + out_name if not os.path.basename(root).endswith("ResearchBase") else os.path.basename(root) + ".zip"
    with zipfile.ZipFile(zn, "w", zipfile.ZIP_DEFLATED) as z:
        for dp, _, fs in os.walk(root):
            for f in fs:
                fp = os.path.join(dp, f)
                z.write(fp, os.path.relpath(fp, os.path.dirname(root)))
    return zn
