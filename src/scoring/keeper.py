"""Keeper scoring: rank frames within each burst, pick the best.

Score components (Stage I, CPU-only):
- focus: Laplacian variance on largest face (normalized per burst)
- exposure: 1 - clipping penalty
- blink: hard reject if likely_blink on the main face

Stage II: adds CLIP aesthetic embedding + personal taste model trained on
the photographer's own rating history (deferred — no Lightroom data yet).
"""
import cv2
import numpy as np
from pathlib import Path

from ..vision.face_detect import FaceDetector
from ..vision.quality import focus_score, exposure_score, likely_blink


def score_frame(path: Path, detector: FaceDetector) -> dict:
    img = cv2.imread(str(path))
    if img is None:
        return {"path": str(path), "error": "unreadable", "keeper_score": 0.0}

    faces = detector.detect(img)
    main_face = max(faces, key=lambda b: b[2] * b[3]) if faces else None

    focus = focus_score(img, main_face)
    expo = exposure_score(img)

    blink = False
    if main_face is not None:
        x, y, w, h = main_face
        crop = img[y:y + h, x:x + w]
        blink = likely_blink(crop)

    return {
        "path": str(path),
        "faces": len(faces),
        "focus": round(focus, 1),
        "exposure": round(expo, 3),
        "blink": blink,
        "keeper_score": 0.0,  # filled in by rank_burst
    }


def rank_burst(frames: list[dict]) -> list[dict]:
    """Normalize focus within burst, apply blink reject, assign keeper score."""
    valid = [f for f in frames if "error" not in f]
    if not valid:
        return frames
    max_focus = max(f["focus"] for f in valid) or 1.0
    for f in valid:
        if f["blink"]:
            f["keeper_score"] = 0.0
            f["rejected"] = "blink"
            continue
        norm_focus = f["focus"] / max_focus
        # 70% focus, 30% exposure
        f["keeper_score"] = round(0.7 * norm_focus + 0.3 * f["exposure"], 3)
    # Best first
    valid.sort(key=lambda f: f["keeper_score"], reverse=True)
    for i, f in enumerate(valid):
        f["rank"] = i + 1
        # Map to star rating: best=5, runner-up=4, rest scaled
        if i == 0:
            f["stars"] = 5
        elif i == 1 and len(valid) > 2:
            f["stars"] = 4
        elif f["keeper_score"] > 0.5:
            f["stars"] = 3
        else:
            f["stars"] = 2 if not f.get("rejected") else 1
    return frames
