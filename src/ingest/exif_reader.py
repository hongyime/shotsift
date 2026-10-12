"""EXIF extraction and embedded rating detection.

Looks for:
- EXIF Rating (0-5 stars) and RatingPercent
- XMP xmp:Rating embedded in JPEG
"""
import struct
from datetime import datetime
from pathlib import Path

try:
    import piexif
    HAS_PIEXIF = True
except ImportError:
    HAS_PIEXIF = False


def get_exif_data(path: str | Path) -> dict:
    """Extract key EXIF fields. Returns dict with datetime, rating, etc."""
    result = {
        "datetime_original": None,
        "rating": None,
        "rating_percent": None,
        "make": None,
        "model": None,
        "focal_length": None,
        "iso": None,
    }
    if not HAS_PIEXIF:
        return result
    try:
        exif = piexif.load(str(path))
        zeroth = exif.get("0th", {})
        exif_ifd = exif.get("Exif", {})

        # Rating tags (EXIF 2.3+)
        rating = zeroth.get(piexif.ImageIFD.Rating)
        if rating is not None:
            result["rating"] = int(rating)
        rating_pct = zeroth.get(piexif.ImageIFD.RatingPercent)
        if rating_pct is not None:
            result["rating_percent"] = int(rating_pct)

        dt = exif_ifd.get(piexif.ExifIFD.DateTimeOriginal)
        if dt:
            try:
                result["datetime_original"] = datetime.strptime(
                    dt.decode() if isinstance(dt, bytes) else dt,
                    "%Y:%m:%d %H:%M:%S",
                )
            except (ValueError, AttributeError):
                pass

        make = zeroth.get(piexif.ImageIFD.Make)
        if make:
            result["make"] = make.decode().strip("\x00") if isinstance(make, bytes) else str(make)
        model = zeroth.get(piexif.ImageIFD.Model)
        if model:
            result["model"] = model.decode().strip("\x00") if isinstance(model, bytes) else str(model)
    except Exception:
        pass
    return result


def get_xmp_rating(path: str | Path) -> int | None:
    """Scan JPEG for embedded XMP xmp:Rating tag. Returns 0-5 or None."""
    try:
        data = Path(path).read_bytes()
        # XMP lives in APP1 segment; crude scan for xmp:Rating="
        idx = data.find(b"xmp:Rating=")
        if idx == -1:
            idx = data.find(b"xmp:Rating =")
        if idx == -1:
            return None
        snippet = data[idx:idx + 40]
        import re
        m = re.search(rb'xmp:Rating\s*=\s*"(\d)"', snippet)
        if m:
            return int(m.group(1))
    except Exception:
        pass
    return None


def get_effective_rating(path: str | Path) -> int | None:
    """Best available rating: XMP first, then EXIF."""
    r = get_xmp_rating(path)
    if r is not None:
        return r
    return get_exif_data(path).get("rating")
