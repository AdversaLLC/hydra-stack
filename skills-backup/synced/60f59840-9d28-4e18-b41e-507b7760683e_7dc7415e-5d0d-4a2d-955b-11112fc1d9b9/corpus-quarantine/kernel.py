import re

def cq_split(df, text_cols, strong_pattern, flags=None):
    """Split a DataFrame into (kept, quarantined) by a strong domain regex over text_cols.
    Returns (kept, quarantined, rate) where rate is the false-positive fraction."""
    import pandas as pd
    if flags is None:
        flags = re.IGNORECASE
    pat = re.compile(strong_pattern, flags)
    text = df[list(text_cols)].fillna("").astype(str).agg(" ".join, axis=1)
    mask = text.apply(lambda s: bool(pat.search(s)))
    kept, quar = df[mask].copy(), df[~mask].copy()
    rate = 0.0 if len(df) == 0 else len(quar) / len(df)
    return kept, quar, rate

def cq_report(kept, quar, name):
    """One-line provenance sentence for the document."""
    n, m = len(kept), len(kept) + len(quar)
    return "%d retained of %d %s records (%.0f%% keyword false positives, quarantined separately)" % (
        n, m, name, 100.0 * (m - n) / max(m, 1))

def cq_save(kept, quar, stem):
    """Write both files; returns the two paths."""
    a, b = stem + "_corpus.csv", stem + "_false_positives.csv"
    kept.to_csv(a, index=False); quar.to_csv(b, index=False)
    return a, b
