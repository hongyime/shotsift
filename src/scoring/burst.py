"""Burst grouping: cluster frames shot in rapid succession.

Groups by EXIF DateTimeOriginal gaps (default: <= 3 seconds apart = same burst).
Falls back to file mtime if EXIF is missing.
"""
from datetime import datetime, timedelta
from pathlib import Path


def group_bursts(
    files: list[Path],
    datetimes: dict[str, datetime | None],
    max_gap: timedelta = timedelta(seconds=3),
) -> list[list[Path]]:
    """Returns list of bursts (each a list of Paths, in capture order)."""
    def key(f: Path):
        dt = datetimes.get(str(f))
        if dt is None:
            try:
                dt = datetime.fromtimestamp(f.stat().st_mtime)
            except OSError:
                dt = datetime.min
        return dt

    ordered = sorted(files, key=key)
    bursts: list[list[Path]] = []
    current: list[Path] = []
    prev_dt: datetime | None = None

    for f in ordered:
        dt = key(f)
        if prev_dt is not None and (dt - prev_dt) > max_gap:
            if current:
                bursts.append(current)
            current = []
        current.append(f)
        prev_dt = dt
    if current:
        bursts.append(current)
    return bursts
