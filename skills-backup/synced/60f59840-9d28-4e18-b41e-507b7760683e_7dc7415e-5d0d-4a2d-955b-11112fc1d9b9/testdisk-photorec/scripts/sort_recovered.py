#!/usr/bin/env python3
"""Sort PhotoRec recup_dir.* output into something usable.

Usage:
  sort_recovered.py OUTPUT_DIR [--by ext|date] [--dedupe] [--copy] [--dest DIR] [--dry-run]

  --by ext    sort into folders per lowercase extension (default)
  --by date   sort into YYYY-MM folders using EXIF DateTimeOriginal when
              available (needs Pillow), else file mtime
  --dedupe    skip byte-identical duplicates (sha256)
  --copy      copy instead of move (originals untouched)
  --dest DIR  destination root (default: OUTPUT_DIR/sorted)
  --dry-run   print planned actions, touch nothing

Stdlib-only; Pillow is optional and only used for EXIF dates.
"""

import argparse
import hashlib
import shutil
import sys
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image, ExifTags  # optional
    _EXIF_TAG = next(k for k, v in ExifTags.TAGS.items() if v == "DateTimeOriginal")
except Exception:
    Image = None
    _EXIF_TAG = None


def sha256(path: Path, bufsize: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(bufsize):
            h.update(chunk)
    return h.hexdigest()


def exif_month(path: Path) -> str | None:
    if Image is None:
        return None
    try:
        with Image.open(path) as im:
            exif = im.getexif()
            raw = exif.get(_EXIF_TAG) or exif.get(306)  # 306 = DateTime fallback
            if raw:
                dt = datetime.strptime(str(raw)[:19], "%Y:%m:%d %H:%M:%S")
                return dt.strftime("%Y-%m")
    except Exception:
        pass
    return None


def bucket_for(path: Path, mode: str) -> str:
    if mode == "ext":
        return path.suffix.lower().lstrip(".") or "noext"
    month = exif_month(path)
    if month is None:
        month = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m")
    return month


def unique_dest(dest: Path) -> Path:
    if not dest.exists():
        return dest
    stem, suffix = dest.stem, dest.suffix
    for i in range(1, 100000):
        cand = dest.with_name(f"{stem}_{i}{suffix}")
        if not cand.exists():
            return cand
    raise RuntimeError(f"could not find unique name for {dest}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("output_dir", type=Path,
                    help="PhotoRec output dir containing recup_dir.* folders")
    ap.add_argument("--by", choices=["ext", "date"], default="ext")
    ap.add_argument("--dedupe", action="store_true")
    ap.add_argument("--copy", action="store_true")
    ap.add_argument("--dest", type=Path, default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root = args.output_dir.resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 1

    dest_root = (args.dest or root / "sorted").resolve()
    sources = sorted(root.glob("recup_dir.*")) or [root]
    op = shutil.copy2 if args.copy else shutil.move
    op_name = "copy" if args.copy else "move"

    if args.by == "date" and Image is None:
        print("note: Pillow not installed — using file mtime instead of EXIF "
              "(pip install Pillow for EXIF dates)", file=sys.stderr)

    seen: dict[str, Path] = {}
    moved = skipped = dupes = 0

    for src_dir in sources:
        for f in sorted(p for p in src_dir.rglob("*") if p.is_file()):
            if dest_root in f.parents:
                continue
            if f.name in ("photorec.ses", "report.xml"):
                skipped += 1
                continue
            if args.dedupe:
                digest = sha256(f)
                if digest in seen:
                    dupes += 1
                    if args.dry_run:
                        print(f"DUPE  {f}  == {seen[digest]}")
                    continue
                seen[digest] = f
            bucket = bucket_for(f, args.by)
            target = unique_dest(dest_root / bucket / f.name)
            if args.dry_run:
                print(f"{op_name.upper():5} {f} -> {target}")
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                op(str(f), str(target))
            moved += 1

    print(f"\n{op_name}d: {moved}  duplicates skipped: {dupes}  "
          f"other skipped: {skipped}\ndestination: {dest_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
