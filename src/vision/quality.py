"""Per-frame quality scoring.

- Laplacian variance on face/subject crop -> focus score (higher = sharper)
- Histogram clipping -> exposure score (0-1, 1 = well exposed)
- Eye aspect ratio heuristic for blink detection (Stage I: simple brightness
  variance in upper face region; Stage II: 68-pt landmarks on Hailo)
"""
import cv2
import numpy as np


def focus_score(image: np.ndarray, box: tuple[int, int, int, int] | None = None) -> float:
    """Laplacian variance. Higher = sharper. Typical range 0-1000+."""
    if box is not None:
        x, y, w, h = box
        h_img, w_img = image.shape[:2]
        x, y = max(0, x), max(0, y)
        crop = image[y:y + h, x:x + w]
        if crop.size == 0:
            crop = image
    else:
        crop = image
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def exposure_score(image: np.ndarray) -> float:
    """0-1 score. Penalizes clipped highlights and crushed shadows."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
    total = hist.sum()
    if total == 0:
        return 0.0
    # Clipped: pure black (0-5) or pure white (250-255)
    clipped = (hist[:6].sum() + hist[250:].sum()) / total
    return float(max(0.0, 1.0 - clipped * 3.0))


def likely_blink(face_crop: np.ndarray) -> bool:
    """Heuristic: eyes are in upper third of face. Low horizontal edge
    density in eye band suggests closed eyes. Crude Stage I proxy."""
    if face_crop.size == 0:
        return False
    h = face_crop.shape[0]
    eye_band = face_crop[int(h * 0.25):int(h * 0.45), :]
    if eye_band.size == 0:
        return False
    gray = cv2.cvtColor(eye_band, cv2.COLOR_BGR2GRAY) if len(eye_band.shape) == 3 else eye_band
    edges = cv2.Canny(gray, 50, 150)
    density = edges.mean() / 255.0
    return density < 0.02  # very few edges -> likely closed
