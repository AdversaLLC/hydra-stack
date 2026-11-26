import os, re, sqlite3, datetime

GG_GRADES = ("critical", "high", "medium", "low", "design-gap", "met")
GG_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "design-gap": 4, "met": 5}

def gg_promises(skill_md_text):
    """Split a SKILL.md into checkable promises: the description sentences plus any
    line in the body that asserts a behaviour. Returns list of strings."""
    m = re.search(r"description: (.*?)\n---", skill_md_text, re.S)
    desc = m.group(1) if m else ""
    out = [s.strip() for s in re.split(r"(?<=[.;]) ", desc) if len(s.strip()) > 25]
    for line in skill_md_text.split("\n"):
        t = line.strip("- *`").strip()
        if re.match(r"(?i)^(returns|writes|reads|extracts|dedupes|produces|emits|gives) ", t):
            out.append(t)
    return out

def gg_grade(promise, observed, reached_deliverable=False, raised=False, caught_by_gate=False):
    """Grade a promise/observation gap by RESEARCH impact.
    reached_deliverable: the wrong or weakened value got into a saved artifact or prose.
    raised: the skill threw rather than returning something plausible.
    caught_by_gate: an external validator stopped it before any harm."""
    if promise.strip().lower() in (observed or "").strip().lower():
        return "met"
    if reached_deliverable:
        return "critical"
    if caught_by_gate:
        return "low"
    if raised:
        return "medium"
    return "high"          # ran clean, returned less than promised - the dangerous case

def gg_log(base, skill, grade, what, evidence, fix, node_writer=None):
    """Record a defect as a graph node plus a `challenges` edge to the skill.
    node_writer: callable(folder, title, body, status, source, edges) - pass rb_note/rb_edge
    wrapper from research-base. Returns the defect id."""
    assert grade in GG_GRADES, "grade must be one of %s" % (GG_GRADES,)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    did = "Defect - %s - %s" % (skill, what[:48])
    body = ("**Skill:** `%s`\n**Grade:** %s\n**Found:** %s\n\n"
            "**Promise:** %s\n\n**Observed:** %s\n\n**Fix:** %s\n") % (
                skill, grade, stamp, what, evidence, fix)
    if node_writer:
        node_writer("Defects", did, body, "open", "postmortem", [(skill, "challenges")])
    return dict(id=did, skill=skill, grade=grade, body=body)

def gg_open(defects, skill=None):
    """Sort open defects worst-first. defects: list of dicts with grade/skill/id/status."""
    d = [x for x in defects if x.get("status", "open") == "open"]
    if skill:
        d = [x for x in d if x.get("skill") == skill]
    return sorted(d, key=lambda x: GG_ORDER.get(x.get("grade", "high"), 9))

def gg_close(defect, how):
    """Close a defect. Returns the closure record - the caller writes a `corrects` edge
    and keeps the original node."""
    d = dict(defect)
    d["status"] = "closed"
    d["closed_how"] = how
    d["closed_at"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    return d

def gg_report(defects):
    """One-line-per-defect summary, worst first, for a session close-out."""
    rows = gg_open(defects)
    counts = {}
    for x in defects:
        counts[x.get("grade", "?")] = counts.get(x.get("grade", "?"), 0) + 1
    lines = ["%-11s %-22s %s" % (x.get("grade"), x.get("skill"),
                                  (x.get("id") or x.get("what") or "(unlabelled)")[:70])
             for x in rows]
    return dict(counts=counts, n_open=len(rows), n_total=len(defects), lines=lines)
