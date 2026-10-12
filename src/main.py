"""ShotSift pipeline: discover -> score -> XMP + gallery.

Usage: python -m src.main <input_dir> <output_dir>
"""
from __future__ import annotations

import os
import sys

import cv2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingest import discover
from src.output import write_gallery, write_xmp
from src.scoring import ScoredFrame, group_bursts, rate_burst_best
from src.vision import FaceDetector, exposure_clipping, laplacian_focus


def process_directory(input_dir: str, output_dir: str) -> list[ScoredFrame]:
    os.makedirs(output_dir, exist_ok=True)
    frames = discover(input_dir)
    print("discovered %d frames in %s" % (len(frames), input_dir))
    detector = FaceDetector()
    scored: list[ScoredFrame] = []
    for frame in frames:
        img = cv2.imread(frame.path)
        if img is None:
            print("  skip (unreadable): %s" % frame.path)
            continue
        faces = detector.detect(img)
        exp = exposure_clipping(img)
        s = ScoredFrame(
            frame=frame, faces=faces,
            focus_score=laplacian_focus(img),
            black_clip=exp["black_clip"], white_clip=exp["white_clip"],
            blink=bool(faces) and not any(f.eyes_open for f in faces),
        )
        scored.append(s)
    bursts = group_bursts(scored)
    print("grouped into %d bursts" % len(bursts))
    rate_burst_best(bursts)
    for s in scored:
        write_xmp(s)
    gallery = write_gallery(scored, os.path.join(output_dir, "gallery.html"))
    print("wrote %d XMP sidecars; gallery: %s" % (len(scored), gallery))
    best = [s for s in scored if s.is_burst_best]
    print("burst-best picks: %d" % len(best))
    for s in sorted(best, key=lambda x: x.keeper_score, reverse=True)[:10]:
        print("  [%d stars] %s score=%.2f faces=%d blink=%s"
              % (s.star_rating, os.path.basename(s.frame.path),
                 s.keeper_score, len(s.faces), s.blink))
    return scored


def main() -> None:
    if len(sys.argv) != 3:
        print("usage: python -m src.main <input_dir> <output_dir>")
        sys.exit(1)
    process_directory(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
