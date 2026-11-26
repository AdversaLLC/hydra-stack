"""Join each lesson's speech transcript and on-screen page text into one study file.

    python3 -I bundle_lessons.py COURSE_DIR [MODULE_PREFIX]

COURSE_DIR holds transcripts/<module>/<lesson>.txt and frames/<module>/<lesson>/page.txt.
Writes lessons/<module>/<lesson>.md for every lesson that has both parts; prints what is missing.
"""
import sys
from pathlib import Path


def main() -> int:
    root = Path(sys.argv[1])
    prefix = sys.argv[2] if len(sys.argv) > 2 else ""
    ready = missing = 0
    for tr in sorted((root / "transcripts").rglob("*.txt")):
        rel = tr.relative_to(root / "transcripts")
        rel = rel.parent / rel.name[: -len(".txt")]  # not with_suffix(): titles contain dots
        if prefix and not str(rel).startswith(prefix):
            continue
        page = root / "frames" / rel / "page.txt"
        if not page.exists():
            print(f"waiting for page text: {rel}")
            missing += 1
            continue
        out = root / "lessons" / rel.parent / f"{rel.name}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            f"# {rel.name}\n\nModule: {rel.parent}\n\n"
            "## On-screen lesson page (OCR; spaces between words are often missing)\n\n"
            f"{page.read_text(encoding='utf-8')}\n"
            "## Spoken narration (speech-to-text, base.en; product names may be misheard)\n\n"
            f"{tr.read_text(encoding='utf-8')}",
            encoding="utf-8",
        )
        ready += 1
    print(f"bundled {ready} lessons, {missing} waiting")
    return 0


if __name__ == "__main__":
    sys.exit(main())
