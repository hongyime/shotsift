"""Face detection.

Stage I: OpenCV Haar cascade (no model download needed, works offline).
Stage II: SCRFD via InsightFace/ONNX on Hailo-10H.
"""
import cv2
import numpy as np
from pathlib import Path


class FaceDetector:
    def __init__(self):
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.detector = cv2.CascadeClassifier(cascade_path)
        if self.detector.empty():
            raise RuntimeError("Could not load Haar cascade")

    def detect(self, image: np.ndarray) -> list[tuple[int, int, int, int]]:
        """Returns list of (x, y, w, h) face boxes."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        faces = self.detector.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
        )
        return [tuple(map(int, f)) for f in faces]

    def detect_file(self, path: str | Path) -> list[tuple[int, int, int, int]]:
        img = cv2.imread(str(path))
        if img is None:
            return []
        return self.detect(img)
