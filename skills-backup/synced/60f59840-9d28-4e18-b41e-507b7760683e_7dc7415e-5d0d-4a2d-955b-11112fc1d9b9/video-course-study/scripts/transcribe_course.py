"""Transcribe a folder of course videos to text with faster-whisper (CPU, int8).

Run with the Skill Seekers tool environment, which has faster-whisper and PyAV:
    ~/.local/share/uv/tools/skill-seekers/bin/python -I transcribe_course.py SRC_DIR OUT_DIR [--model small.en] [--only N]

One .txt (plain paragraphs) and one .srt per video, mirroring the course's section folders.
Videos that already have a non-empty .txt are skipped, so the run can be resumed.
"""
import argparse
import re
import sys
import time
from pathlib import Path

from faster_whisper import WhisperModel


def lesson_key(path: Path):
    # Sort "2 - Section/10 - Lesson.mp4" numerically by section, then lesson.
    nums = [int(m) for part in path.parts[-2:] for m in re.findall(r"^(\d+)", part)]
    return nums + [path.name]


def stamp(t: float) -> str:
    h, rem = divmod(int(t * 1000), 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--model", default="small.en")
    ap.add_argument("--only", type=int, default=0, help="transcribe only the first N videos (testing)")
    ap.add_argument("--beam", type=int, default=5, help="beam size; 1 = greedy, roughly twice as fast")
    ap.add_argument("--prompt", default="Claude, Claude Code, Anthropic, CLAUDE.md, MCP, subagent, SDK, "
                    "API, JSON, Opus, Sonnet, Haiku, Fable, agentic loop, hooks, skills.",
                    help="vocabulary hint so product names are spelled right")
    args = ap.parse_args()

    videos = sorted(args.src.rglob("*.mp4"), key=lesson_key)
    if args.only:
        videos = videos[: args.only]
    model = WhisperModel(args.model, device="cpu", compute_type="int8", cpu_threads=8)

    total_audio = total_wall = 0.0
    for v in videos:
        # Append extensions instead of with_suffix(): titles like "messages.create()" contain dots.
        rel = v.relative_to(args.src).with_suffix("")
        txt, srt = args.out / rel.parent / f"{rel.name}.txt", args.out / rel.parent / f"{rel.name}.srt"
        if txt.exists() and txt.stat().st_size > 0:
            print(f"skip  {rel}", flush=True)
            continue
        txt.parent.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        segments, info = model.transcribe(str(v), language="en", vad_filter=True, beam_size=args.beam,
                                          initial_prompt=args.prompt)
        lines, cues = [], []
        for i, seg in enumerate(segments, 1):
            lines.append(seg.text.strip())
            cues.append(f"{i}\n{stamp(seg.start)} --> {stamp(seg.end)}\n{seg.text.strip()}\n")
        wall = time.time() - t0
        srt.write_text("\n".join(cues), encoding="utf-8")
        txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
        total_audio += info.duration
        total_wall += wall
        print(f"done  {rel}  audio={info.duration/60:.1f}m wall={wall/60:.1f}m "
              f"speed={info.duration/max(wall, 1e-6):.1f}x", flush=True)
    if total_wall:
        print(f"TOTAL audio={total_audio/60:.1f}m wall={total_wall/60:.1f}m "
              f"speed={total_audio/total_wall:.1f}x", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
