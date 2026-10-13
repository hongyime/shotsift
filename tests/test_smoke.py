"""Smoke tests for ShotSift Stage I prototype."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / ".."))

import numpy as np

from src.vision.quality import focus_score, exposure_score, likely_blink
from src.scoring.burst import group_bursts
from src.output.xmp import write_xmp
from datetime import datetime, timedelta
import tempfile


def test_focus_score():
    sharp = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    # Add edges to make it "sharp"
    sharp[40:60, :] = 255
    blurry = np.full((100, 100, 3), 128, dtype=np.uint8)
    assert focus_score(sharp) > focus_score(blurry), "sharp should score higher"
    print("  focus_score OK")


def test_exposure_score():
    good = np.full((100, 100, 3), 128, dtype=np.uint8)
    clipped = np.zeros((100, 100, 3), dtype=np.uint8)
    assert exposure_score(good) > exposure_score(clipped), "good exposure should win"
    print("  exposure_score OK")


def test_burst_grouping():
    base = datetime(2024, 1, 1, 12, 0, 0)
    files = [Path(f"img_{i}.jpg") for i in range(5)]
    dts = {
        str(files[0]): base,
        str(files[1]): base + timedelta(seconds=1),
        str(files[2]): base + timedelta(seconds=2),
        str(files[3]): base + timedelta(seconds=10),  # gap -> new burst
        str(files[4]): base + timedelta(seconds=11),
    }
    bursts = group_bursts(files, dts)
    assert len(bursts) == 2, f"expected 2 bursts, got {len(bursts)}"
    assert len(bursts[0]) == 3 and len(bursts[1]) == 2
    print("  burst grouping OK")


def test_xmp_writer():
    with tempfile.TemporaryDirectory() as td:
        img = Path(td) / "test.jpg"
        img.write_bytes(b"fake")
        out = write_xmp(img, rating=5, label="Red", keywords=["test"], caption="hi")
        assert out.exists()
        content = out.read_text()
        assert 'xmp:Rating="5"' in content
        assert "test" in content
    print("  xmp writer OK")


if __name__ == "__main__":
    print("Running ShotSift smoke tests...")
    test_focus_score()
    test_exposure_score()
    test_burst_grouping()
    test_xmp_writer()
    print("All smoke tests passed.")
