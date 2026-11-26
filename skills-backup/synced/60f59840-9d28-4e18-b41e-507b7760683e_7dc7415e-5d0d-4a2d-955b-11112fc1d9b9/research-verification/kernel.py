import os, re

RV_HEDGES = ("should", "probably", "seems to", "looks right", "as expected",
             "presumably", "ought to", "i think", "roughly correct")

def rv_check(claims):
    """claims: list of (claim_text, evidence_kind). Returns rows flagged unsupported.
    evidence_kind: measured|primary-quoted|computed|filtered-corpus|graph-edge|readback|ungrounded"""
    ok = {"measured", "primary-quoted", "computed", "filtered-corpus",
          "graph-edge", "readback", "ungrounded"}
    out = []
    for text, kind in claims:
        bad = []
        if kind not in ok:
            bad.append("evidence kind '%s' not recognised" % kind)
        low = (text or "").lower()
        for h in RV_HEDGES:
            if h in low:
                bad.append("hedge word: '%s'" % h)
        if re.search(r"\bmeasured\b", low) and kind != "measured":
            bad.append("says measured but evidence kind is " + kind)
        if re.search(r"\bverified\b", low) and kind not in ("primary-quoted", "readback", "measured"):
            bad.append("says verified but evidence kind is " + kind)
        if bad:
            out.append(dict(claim=text[:90], kind=kind, problems=bad))
    return out

def rv_counts(path, described_dir=None):
    """Extract every integer asserted in a document and, when described_dir is given,
    compare the plausible file-count claims against the actual count. Returns findings."""
    txt = open(path).read()
    nums = [(m.group(0), txt[max(0, m.start()-60):m.start()+40].replace("\n", " "))
            for m in re.finditer(r"\b\d[\d,]{0,8}\b", txt)]
    findings = []
    actual = None
    if described_dir and os.path.isdir(described_dir):
        actual = sum(len(fs) for _, _, fs in os.walk(described_dir))
    for n, ctx in nums:
        v = int(n.replace(",", ""))
        if re.search(r"(?i)\bfiles?\b", ctx) and actual is not None and v != actual:
            findings.append(dict(value=v, actual=actual, context=ctx.strip()[:110],
                                 issue="file-count claim disagrees with directory"))
    return dict(n_integers=len(nums), actual_file_count=actual, findings=findings)

def rv_readback(path, values):
    """Confirm each quoted value appears verbatim in the saved artifact. Returns per-value bool."""
    txt = open(path).read()
    return {str(v): (str(v) in txt) for v in values}

def rv_endpoint(fn, input_a, input_b):
    """An endpoint that returns the same output for two different inputs is silently broken,
    regardless of status code. Returns (ok, detail)."""
    a, b = fn(input_a), fn(input_b)
    same = (a == b)
    return dict(ok=not same, identical_output=same,
                detail=("SILENT FAILURE: two different inputs produced byte-identical output - "
                        "the endpoint is ignoring the query" if same else "distinct outputs, endpoint honours input"))

def rv_deviations(results):
    """Surface declared deviations from subagent results before their numbers are reported."""
    rows = []
    for r in results:
        dev = r.get("deviations")
        rows.append(dict(name=r.get("name") or (r.get("frame_id") or "")[:8],
                         declared=dev if dev else "NONE DECLARED - treat coverage as unknown",
                         undeclared_marker=str(dev).startswith("UNDECLARED")))
    return rows
