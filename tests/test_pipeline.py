"""Smoke tests for the ShotSift Stage I prototype."""
from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingest import Frame
from src.scoring import ScoredFrame, group_bursts, rate_burst_best, score_keeper


def make_frame(name: str, seconds_ago: int = 0) -> ScoredFrame:
    f = Frame(path="/tmp/" + name)
    f.captured_at = datetime(2026, 10, 13, 12, 0, 0) - timedelta(seconds=seconds_ago)
    return ScoredFrame(frame=f, focus_score=500.0)


class TestBursts(unittest.TestCase):
    def test_burst_grouping(self):
        a = make_frame("a.jpg", 0)
        b = make_frame("b.jpg", 1)
        c = make_frame("c.jpg", 30)
        bursts = group_bursts([a, b, c])
        self.assertEqual(len(bursts), 2)
        sizes = sorted(len(b) for b in bursts)
        self.assertEqual(sizes, [1, 2])

    def test_best_of_burst(self):
        frames = [make_frame(str(i) + ".jpg", i) for i in range(4)]
        frames[2].blink = True
        frames[2].focus_score = 50.0
        bursts = group_bursts(frames)
        rate_burst_best(bursts)
        best = [s for s in frames if s.is_burst_best]
        self.assertEqual(len(best), 1)
        self.assertFalse(best[0].blink)
        self.assertGreaterEqual(best[0].star_rating, 3)

    def test_blink_penalty(self):
        sharp = make_frame("sharp.jpg")
        sharp.focus_score = 1200.0
        blinky = make_frame("blink.jpg")
        blinky.focus_score = 1200.0
        blinky.blink = True
        self.assertGreater(score_keeper(sharp), score_keeper(blinky))


class TestXmp(unittest.TestCase):
    def test_xmp_roundtrip(self):
        from src.output import write_xmp
        s = make_frame("x.jpg")
        s.star_rating = 4
        with tempfile.TemporaryDirectory() as d:
            input_root = Path(d) / "input"
            input_root.mkdir()
            source = input_root / "x.jpg"
            source.write_bytes(b"fake")
            s.frame.path = str(source)
            output_root = Path(d) / "output"
            sidecar = write_xmp(s, input_root, output_root, caption="test caption", keywords=["event"])
            self.assertTrue(sidecar.exists())
            body = sidecar.read_text(encoding="utf-8")
            self.assertIn("xmp:Rating=\"4\"", body)
            self.assertIn("test caption", body)


if __name__ == "__main__":
    unittest.main(verbosity=2)
