#!/usr/bin/env python3
"""Wisdom store: append-only JSONL + tf-idf keyword search. Pure stdlib, no deps.

Usage:
  python3 wisdom.py add --type insight --project myapp --tags "auth,jwt" --conf V "text of the insight"
  python3 wisdom.py search "query terms" [--project myapp] [--type failed_path] [--limit 5]
  python3 wisdom.py list [--limit 10]
  python3 wisdom.py stats

Store path: env HYDRA_WISDOM, default ./.hydra/wisdom.jsonl
Record: {"ts","type","project","tags","conf","text"}
"""
import argparse, collections, json, math, os, re, sys, time

try:
    import fcntl  # POSIX file locking for concurrent swarm writers
except ImportError:  # pragma: no cover (Windows) - best-effort append
    fcntl = None

DEFAULT_PATH = os.environ.get("HYDRA_WISDOM", os.path.join(".hydra", "wisdom.jsonl"))
PATH = DEFAULT_PATH


def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def load():
    if not os.path.exists(PATH):
        return []
    records = []
    with open(PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"warn: skipped malformed line", file=sys.stderr)
    return records


def cmd_add(args):
    directory = os.path.dirname(PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)
    rec = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "type": args.type,
        "project": args.project,
        "tags": [t.strip() for t in args.tags.split(",") if t.strip()],
        "conf": args.conf,
        "text": " ".join(args.text).strip(),
    }
    if not rec["text"]:
        sys.exit("error: empty text")
    with open(PATH, "a", encoding="utf-8") as f:
        if fcntl:
            fcntl.flock(f, fcntl.LOCK_EX)
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        f.flush()
        if fcntl:
            fcntl.flock(f, fcntl.LOCK_UN)
    print(f"added [{rec['type']}/{rec['conf']}] to {PATH}")


def show(rec):
    tags = ",".join(rec.get("tags", []))
    print(f"[{rec.get('ts','?')}] ({rec.get('type','?')}/{rec.get('conf','?')}) "
          f"project={rec.get('project','-')} tags={tags}\n  {rec.get('text','')}\n")


def cmd_search(args):
    records = load()
    if args.project:
        records = [r for r in records if r.get("project") == args.project]
    if args.type:
        records = [r for r in records if r.get("type") == args.type]
    query = tokenize(" ".join(args.query))
    if not query:
        for r in records[-args.limit:]:
            show(r)
        return
    n_docs = len(records) or 1
    doc_tokens, df = [], collections.Counter()
    for r in records:
        toks = tokenize(r.get("text", "") + " " + " ".join(r.get("tags", [])))
        doc_tokens.append(toks)
        for t in set(toks):
            df[t] += 1
    scored = []
    for r, toks in zip(records, doc_tokens):
        if not toks:
            continue
        tf = collections.Counter(toks)
        score = sum((tf[t] / len(toks)) * math.log(1 + n_docs / df[t])
                    for t in query if t in tf)
        if score > 0:
            scored.append((score, r))
    scored.sort(key=lambda x: -x[0])
    if not scored:
        print("no matches")
        return
    for _, r in scored[:args.limit]:
        show(r)


def cmd_list(args):
    for r in load()[-args.limit:]:
        show(r)


def cmd_stats(_args):
    records = load()
    print(f"store: {PATH}\ntotal: {len(records)}")
    for key in ("type", "project", "conf"):
        counts = collections.Counter(r.get(key, "-") for r in records)
        pretty = ", ".join(f"{k}={v}" for k, v in counts.most_common())
        print(f"  by {key}: {pretty or '-'}")


def main():
    p = argparse.ArgumentParser(description="hydra wisdom store")
    p.add_argument("--store", help="override store path (else env HYDRA_WISDOM, else ./.hydra/wisdom.jsonl)")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add")
    a.add_argument("--type", default="insight",
                   choices=["insight", "failed_path", "decision", "retro",
                            "meta_param", "meta", "correction"])
    a.add_argument("--project", default="-")
    a.add_argument("--tags", default="")
    a.add_argument("--conf", default="U", choices=["V", "S", "U"],
                   help="V=verified against reality, S=sourced to a document, U=unverified")
    a.add_argument("text", nargs="+")
    a.set_defaults(func=cmd_add)

    s = sub.add_parser("search")
    s.add_argument("query", nargs="*")
    s.add_argument("--project")
    s.add_argument("--type")
    s.add_argument("--limit", type=int, default=5)
    s.set_defaults(func=cmd_search)

    l = sub.add_parser("list")
    l.add_argument("--limit", type=int, default=10)
    l.set_defaults(func=cmd_list)

    st = sub.add_parser("stats")
    st.set_defaults(func=cmd_stats)

    args = p.parse_args()
    if args.store:
        global PATH
        PATH = args.store
    args.func(args)


if __name__ == "__main__":
    main()
