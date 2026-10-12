"""Ingest: discover images, extract EXIF metadata."""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime

from PIL import Image
from PIL.ExifTags import TAGS

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}


@dataclass
class Frame:
    path: str
    width: int = 0
    height: int = 0
    captured_at: datetime | None = None
    camera_serial: str = ""
    focal_length: str = ""
    iso: str = ""
    embedded_rating: int | None = None


def _exif_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value.split(".")[0], fmt)
        except ValueError:
            continue
    return None


def read_frame(path: str) -> Frame:
    frame = Frame(path=path)
    try:
        with Image.open(path) as img:
            frame.width, frame.height = img.size
            exif = img.getexif()
            if not exif:
                return frame
            tags = {TAGS.get(k, k): v for k, v in exif.items()}
            # DateTimeOriginal lives in the Exif IFD (0x8769), not top-level
            try:
                exif_ifd = exif.get_ifd(0x8769)
                for k, v in exif_ifd.items():
                    tags.setdefault(TAGS.get(k, k), v)
            except Exception:
                pass
            frame.captured_at = _exif_datetime(str(tags.get("DateTimeOriginal", "")))
            frame.camera_serial = str(tags.get("BodySerialNumber", ""))
            frame.focal_length = str(tags.get("FocalLength", ""))
            frame.iso = str(tags.get("ISOSpeedRatings", ""))
            rating = tags.get("Rating", None)
            if rating is not None:
                try:
                    frame.embedded_rating = int(rating)
                except (TypeError, ValueError):
                    pass
    except Exception:
        pass
    return frame


def discover(directory: str) -> list[Frame]:
    frames: list[Frame] = []
    for root, _dirs, files in os.walk(directory):
        for name in sorted(files):
            if os.path.splitext(name)[1].lower() in IMAGE_EXTS:
                frames.append(read_frame(os.path.join(root, name)))
    return frames
