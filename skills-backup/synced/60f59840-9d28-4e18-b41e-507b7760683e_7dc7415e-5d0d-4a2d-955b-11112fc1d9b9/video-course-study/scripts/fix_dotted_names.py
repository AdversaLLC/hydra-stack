"""Rename transcripts that an older transcribe_course.py cut at a dot in the lesson title.

    python3 -I fix_dotted_names.py SRC_DIR COURSE_DIR

"messages.create() — one call" was written as "messages.txt" because Path.with_suffix()
treats everything after the last dot as the extension.
"""
import sys
from pathlib import Path

src, root = Path(sys.argv[1]), Path(sys.argv[2])
for v in sorted(src.rglob("*.mp4")):
    rel = v.relative_to(src).with_suffix("")
    for ext in (".txt", ".srt"):
        bad = root / "transcripts" / rel.with_suffix(ext)
        good = root / "transcripts" / rel.parent / f"{rel.name}{ext}"
        if bad != good and bad.exists() and not good.exists():
            bad.rename(good)
            print("renamed", bad.name, "->", good.name)
