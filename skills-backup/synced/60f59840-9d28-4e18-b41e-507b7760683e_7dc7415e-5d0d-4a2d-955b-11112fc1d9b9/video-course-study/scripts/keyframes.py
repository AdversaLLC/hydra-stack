"""Save one downscaled JPEG per slide change for each course video (OpenCV, no external ffmpeg),
and with --ocr also write page.txt: the OCR'd lines of all kept frames, in order, duplicates dropped.

    ~/.local/share/uv/tools/skill-seekers/bin/python -I keyframes.py SRC_DIR OUT_DIR [--every 3] [--threshold 0.02] [--ocr]

Samples a frame every N seconds, keeps it when it differs enough from the last kept frame
(mean absolute grey-level difference on a 64x36 thumbnail), and names it by timestamp so it
lines up with the .srt. Scrolling a dark lesson page changes the mean very little, hence the
low default threshold. RapidOCR drops most spaces between words; a reader can still follow it.
"""
import argparse
import re
import sys
from pathlib import Path

import cv2
import numpy as np


def ocr_lines(engine, image_path: Path, min_score: float = 0.6) -> list[str]:
    result, _ = engine(str(image_path))
    return [text.strip() for _box, text, score in (result or []) if score >= min_score and text.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--every", type=float, default=3.0, help="seconds between sampled frames")
    ap.add_argument("--threshold", type=float, default=0.02, help="fraction of grey range that counts as a new slide")
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--ocr", action="store_true", help="OCR kept frames into page.txt (RapidOCR)")
    args = ap.parse_args()
    engine = None
    if args.ocr:
        from rapidocr_onnxruntime import RapidOCR
        engine = RapidOCR()

    for v in sorted(args.src.rglob("*.mp4")):
        dest = args.out / v.relative_to(args.src).with_suffix("")
        if dest.exists() and any(dest.iterdir()):
            print(f"skip  {dest.name}", flush=True)
            continue
        dest.mkdir(parents=True, exist_ok=True)
        cap = cv2.VideoCapture(str(v))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        step = max(1, int(round(fps * args.every)))
        last, idx, kept = None, 0, 0
        while True:
            if not cap.grab():
                break
            if idx % step == 0:
                ok, frame = cap.retrieve()
                if not ok:
                    break
                thumb = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (64, 36)).astype(np.float32) / 255.0
                if last is None or float(np.mean(np.abs(thumb - last))) > args.threshold:
                    h, w = frame.shape[:2]
                    if w > args.width:
                        frame = cv2.resize(frame, (args.width, int(h * args.width / w)))
                    t = idx / fps
                    cv2.imwrite(str(dest / f"{int(t // 60):02}m{int(t % 60):02}s.jpg"), frame,
                                [cv2.IMWRITE_JPEG_QUALITY, 80])
                    last, kept = thumb, kept + 1
            idx += 1
        cap.release()
        if engine is not None:
            seen, page = set(), []
            for jpg in sorted(dest.glob("*.jpg")):
                page.append(f"--- {jpg.stem}")
                for line in ocr_lines(engine, jpg):
                    key = re.sub(r"\W+", "", line.lower())
                    if len(key) > 3 and key not in seen:
                        seen.add(key)
                        page.append(line)
            (dest / "page.txt").write_text("\n".join(page) + "\n", encoding="utf-8")
        print(f"done  {dest.name}  kept={kept}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
