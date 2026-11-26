#!/usr/bin/env python3
"""vault_sync: mirror the hydra wisdom store into an Obsidian vault, and back.

The JSONL store stays the machine source of truth; the vault is the human-browsable,
wikilinked mirror. Stdlib only.

Usage:
  python3 vault_sync.py sync   --vault /path/to/Vault [--store .hydra/wisdom.jsonl]
  python3 vault_sync.py import --vault /path/to/Vault [--store .hydra/wisdom.jsonl]

sync:   every store record becomes a note at
        Vault/Hydra Wisdom/<type>/<stamp>-<slug>.md  (frontmatter: wid, type,
        project, tags, conf, created)  — idempotent via wid (record hash) —
        then rewrites 'Hydra Wisdom/Hydra Wisdom MOC.md' (type: moc) grouping
        all notes by type with wikilinks.
import: notes a human wrote under Hydra Wisdom/ (valid type, no wid yet) are
        appended to the store and stamped with their new wid.

Obsidian rules honored: filenames avoid  # | ^ : % [ ]  (wikilinks resolve by
filename); metadata is YAML frontmatter (Properties).
"""
import argparse, hashlib, json, os, re, sys, time

TYPES = ["insight", "failed_path", "decision", "retro", "meta_param", "meta", "correction"]
FORBIDDEN = re.compile(r"[#|^:%\[\]/\\]")

def wid_of(rec):
    key = f"{rec.get('ts','')}|{rec.get('type','')}|{rec.get('text','')}"
    return hashlib.sha256(key.encode()).hexdigest()[:12]

def slugify(text, maxlen=48):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return (s[:maxlen].rstrip("-")) or "note"

def load_store(path):
    if not os.path.exists(path):
        return []
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out

def note_body(rec, wid):
    tags = rec.get("tags", [])
    fm = ["---", f"wid: {wid}", f"type: {rec.get('type','insight')}",
          f"project: {rec.get('project','-')}",
          "tags: [" + ", ".join(["hydra-wisdom"] + tags) + "]",
          f"conf: {rec.get('conf','U')}", f"created: {rec.get('ts','')}", "---", ""]
    title = rec.get("text", "").split("\n")[0][:80]
    return "\n".join(fm) + f"# {title}\n\n{rec.get('text','')}\n"

def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    fm = {}
    for line in parts[1].splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, parts[2]

def existing_wids(wisdom_dir):
    wids = {}
    for root, _dirs, files in os.walk(wisdom_dir):
        for f in files:
            if f.endswith(".md"):
                p = os.path.join(root, f)
                fm, _ = parse_frontmatter(open(p, encoding="utf-8").read())
                if fm.get("wid"):
                    wids[fm["wid"]] = p
    return wids

def cmd_sync(a):
    recs = load_store(a.store)
    if not recs:
        sys.exit(f"store empty or missing: {a.store}")
    base = os.path.join(a.vault, "Hydra Wisdom")
    os.makedirs(base, exist_ok=True)
    have = existing_wids(base)
    created = 0
    for rec in recs:
        wid = wid_of(rec)
        if wid in have:
            continue
        tdir = os.path.join(base, rec.get("type", "insight"))
        os.makedirs(tdir, exist_ok=True)
        stamp = re.sub(r"[^0-9]", "", rec.get("ts", ""))[:14] or time.strftime("%Y%m%d%H%M%S")
        fname = FORBIDDEN.sub("-", f"{stamp}-{slugify(rec.get('text',''))}") + ".md"
        path = os.path.join(tdir, fname)
        open(path, "w", encoding="utf-8").write(note_body(rec, wid))
        have[wid] = path
        created += 1
    # regenerate MOC (hand-curation goes elsewhere; this file is machine-owned)
    groups = {}
    for wid, p in have.items():
        typ = os.path.basename(os.path.dirname(p))
        groups.setdefault(typ, []).append(os.path.splitext(os.path.basename(p))[0])
    lines = ["---", "type: moc", "tags: [moc, hydra-wisdom]",
             f"updated: {time.strftime('%Y-%m-%d')}", "---",
             "# Hydra Wisdom — Map of Content", "",
             "Machine-generated from the hydra wisdom store. Do not hand-edit; it is rewritten on every sync.", ""]
    for typ in TYPES:
        if typ in groups:
            lines.append(f"## {typ} ({len(groups[typ])})")
            for name in sorted(groups[typ], reverse=True):
                lines.append(f"- [[{name}]]")
            lines.append("")
    lines += ["## Dataview (optional)", "```dataview",
              'table project, conf, created from "Hydra Wisdom" where type != "moc" sort created desc',
              "```", ""]
    open(os.path.join(base, "Hydra Wisdom MOC.md"), "w", encoding="utf-8").write("\n".join(lines))
    print(f"sync: {created} new note(s), {len(have)} total, MOC rewritten")

def cmd_import(a):
    base = os.path.join(a.vault, "Hydra Wisdom")
    if not os.path.isdir(base):
        sys.exit(f"no Hydra Wisdom folder in vault: {a.vault}")
    imported = 0
    for root, _dirs, files in os.walk(base):
        for f in files:
            if not f.endswith(".md") or f == "Hydra Wisdom MOC.md":
                continue
            p = os.path.join(root, f)
            raw = open(p, encoding="utf-8").read()
            fm, body = parse_frontmatter(raw)
            if fm.get("wid") or fm.get("type", "") not in TYPES:
                continue
            text = re.sub(r"^#.*\n", "", body.strip(), count=1).strip()
            if not text:
                continue
            tags = [t.strip() for t in fm.get("tags", "").strip("[]").split(",")
                    if t.strip() and t.strip() != "hydra-wisdom"]
            rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "type": fm["type"], "project": fm.get("project", "-"),
                   "tags": tags, "conf": fm.get("conf", "U") if fm.get("conf") in ("V","S","U") else "U",
                   "text": text}
            d = os.path.dirname(a.store)
            if d:
                os.makedirs(d, exist_ok=True)
            with open(a.store, "a", encoding="utf-8") as out:
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            wid = wid_of(rec)
            open(p, "w", encoding="utf-8").write(raw.replace("---", f"---\nwid: {wid}", 1))
            imported += 1
    print(f"import: {imported} note(s) appended to {a.store}")

def main():
    p = argparse.ArgumentParser(description="hydra wisdom to Obsidian vault bridge")
    p.add_argument("--store", default=os.environ.get("HYDRA_WISDOM", os.path.join(".hydra", "wisdom.jsonl")))
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sync"); s.add_argument("--vault", required=True); s.set_defaults(func=cmd_sync)
    i = sub.add_parser("import"); i.add_argument("--vault", required=True); i.set_defaults(func=cmd_import)
    a = p.parse_args()
    a.func(a)

if __name__ == "__main__":
    main()
