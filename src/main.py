"""ShotSift pipeline: discover -> score -> XMP + gallery.

Usage: python -m src.main <input_dir> <output_dir>
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import cv2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingest import discover
from src.output import write_gallery, write_xmp
from src.scoring import ScoredFrame, group_bursts, rate_burst_best
from src.vision import FaceDetector, exposure_clipping, laplacian_focus, resize_quality_image


def process_directory(input_dir: str, output_dir: str) -> list[ScoredFrame]:
    input_root = Path(input_dir)
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    frames = discover(str(input_root))
    print("discovered %d frames in %s" % (len(frames), input_dir))
    detector = FaceDetector()
    scored: list[ScoredFrame] = []
    for frame in frames:
        img = cv2.imread(frame.path)
        if img is None:
            print("  skip (unreadable): %s" % frame.path)
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = detector.detect(img, gray)
        quality = resize_quality_image(gray)
        exp = exposure_clipping(quality)
        s = ScoredFrame(
            frame=frame, faces=faces,
            focus_score=laplacian_focus(quality),
            black_clip=exp["black_clip"], white_clip=exp["white_clip"],
            blink=bool(faces) and not any(f.eyes_open for f in faces),
        )
        scored.append(s)
    bursts = group_bursts(scored)
    print("grouped into %d bursts" % len(bursts))
    rate_burst_best(bursts)
    for s in scored:
        write_xmp(s, input_root, output_root)
    gallery = write_gallery(scored, output_root / "gallery.html", input_root=input_root)
    star_counts = {str(stars): sum(s.star_rating == stars for s in scored) for stars in range(1, 6)}
    (output_root / "summary.json").write_text(
        json.dumps({
            "discovered_frame_count": len(frames),
            "scored_frame_count": len(scored),
            "unreadable_frame_count": len(frames) - len(scored),
            "burst_count": len(bursts),
            "keeper_count": sum(s.is_burst_best for s in scored),
            "star_rating_counts": star_counts,
        }, indent=2) + "\n",
        encoding="utf-8",
    )
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
