"""Tier 1 vision — face, focus, and exposure scoring."""
from __future__ import annotations

import os
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class FaceResult:
    box: tuple[int, int, int, int]
    eyes_open: bool = True
    focus_score: float = 0.0
    confidence: float = 0.0


class FaceDetector:
    def __init__(self, model_path: str | None = None) -> None:
        self.available = False
        self.detector = None
        if model_path is None:
            here = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.normpath(
                os.path.join(here, "..", "..", "models", "face_detection_yunet_2023mar.onnx"))
        try:
            if os.path.exists(model_path) and os.path.getsize(model_path) > 10000:
                self.detector = cv2.FaceDetectorYN_create(model_path, "", (320, 320), 0.6, 0.3, 5000)
                self.available = True
        except (cv2.error, OSError):
            print("  face detector unavailable; continuing without it")

    def detect(self, image: np.ndarray, gray: np.ndarray | None = None) -> list[FaceResult]:
        if not self.available or self.detector is None:
            return []
        h, w = image.shape[:2]
        self.detector.setInputSize((w, h))
        _retval, faces = self.detector.detect(image)
        results: list[FaceResult] = []
        if faces is None:
            return results
        gray = _gray_image(image) if gray is None else gray
        for det in faces:
            x, y, ww, hh = (int(v) for v in det[:4])
            conf = float(det[14])
            x2, y2 = max(0, x), max(0, y)
            x3, y3 = min(w, x + ww), min(h, y + hh)
            if x3 <= x2 or y3 <= y2:
                continue
            face_roi = gray[y2:y3, x2:x3]
            results.append(FaceResult(
                box=(x, y, ww, hh),
                eyes_open=not _likely_blink(face_roi),
                confidence=conf,
            ))
        return results


def _gray_image(image: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image


def resize_quality_image(image: np.ndarray) -> np.ndarray:
    """Return a grayscale image no larger than a 1920 by 1080 preview."""
    gray = _gray_image(image)
    height, width = gray.shape[:2]
    scale = min(1.0, 1920 / width, 1080 / height)
    if scale == 1.0:
        return gray
    return cv2.resize(
        gray,
        (round(width * scale), round(height * scale)),
        interpolation=cv2.INTER_AREA,
    )


def laplacian_focus(image: np.ndarray) -> float:
    gray = resize_quality_image(image)
    return float(cv2.Laplacian(gray, cv2.CV_32F).var())


def exposure_clipping(image: np.ndarray) -> dict[str, float]:
    gray = resize_quality_image(image)
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).ravel()
    total = hist.sum() or 1.0
    return {"black_clip": float(hist[:4].sum() / total),
            "white_clip": float(hist[-4:].sum() / total)}


def _likely_blink(face_roi: np.ndarray) -> bool:
    """Use the existing upper-face edge-density heuristic for closed eyes."""
    if face_roi.size == 0:
        return False
    height = face_roi.shape[0]
    eye_band = face_roi[int(height * 0.25):int(height * 0.45), :]
    if eye_band.size == 0:
        return False
    edges = cv2.Canny(eye_band, 50, 150)
    return edges.mean() / 255.0 < 0.02
