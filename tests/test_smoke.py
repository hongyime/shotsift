"""Active-pipeline smoke tests for ShotSift."""
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import cv2
import numpy as np

from src.ingest import Frame
from src.main import process_directory
from src.output import write_gallery, write_xmp
from src.scoring import ScoredFrame, group_bursts, rate_burst_best
from src.vision import FaceDetector, exposure_clipping, laplacian_focus, resize_quality_image


def scored_frame(name: str, captured_at: datetime | None = None, serial: str = "") -> ScoredFrame:
    return ScoredFrame(
        frame=Frame(path=name, captured_at=captured_at, camera_serial=serial),
        focus_score=500.0,
    )


class TestActivePipeline(unittest.TestCase):
    def test_yunet_model_detects_fixture_face(self) -> None:
        image = cv2.imread(str(Path(__file__).with_name("face_test.jpg")))
        self.assertIsNotNone(image)
        detector = FaceDetector()
        self.assertTrue(detector.available)
        self.assertTrue(detector.detect(image))

    def test_interleaved_camera_bursts_remain_continuous(self) -> None:
        start = datetime(2026, 1, 1, 12, 0, 0)
        frames = [
            scored_frame("a-0.jpg", start, "camera-a"),
            scored_frame("b-0.jpg", start + timedelta(milliseconds=500), "camera-b"),
            scored_frame("a-1.jpg", start + timedelta(seconds=1), "camera-a"),
            scored_frame("b-1.jpg", start + timedelta(seconds=1, milliseconds=500), "camera-b"),
        ]

        bursts = group_bursts(frames)

        self.assertEqual([len(burst) for burst in bursts], [2, 2])
        self.assertEqual({s.frame.camera_serial for s in bursts[0]}, {"camera-a"})
        self.assertEqual({s.frame.camera_serial for s in bursts[1]}, {"camera-b"})

    def test_low_quality_singleton_is_not_a_keeper(self) -> None:
        frame = scored_frame("low.jpg")
        frame.focus_score = 0.0
        frame.black_clip = 1.0
        frame.white_clip = 1.0

        rate_burst_best([[frame]])

        self.assertFalse(frame.is_burst_best)
        self.assertLess(frame.star_rating, 3)

    def test_missing_capture_times_are_isolated(self) -> None:
        bursts = group_bursts([scored_frame("a.jpg"), scored_frame("b.jpg")])

        self.assertEqual([len(burst) for burst in bursts], [1, 1])

    def test_xmp_sidecar_mirrors_nested_source_below_output_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_root = root / "input"
            source = input_root / "nested" / "photo.jpg"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"source")
            output_root = root / "output"
            frame = scored_frame(str(source))
            frame.star_rating = 4

            sidecar = write_xmp(
                frame,
                input_root,
                output_root,
                caption='caption " & <',
                keywords=['keyword " & <'],
            )

            self.assertEqual(sidecar, output_root / "nested" / "photo.jpg.xmp")
            self.assertFalse((input_root / "nested" / "photo.jpg.xmp").exists())
            content = sidecar.read_text(encoding="utf-8")
            self.assertIn("caption &quot; &amp; &lt;", content)
            self.assertIn("keyword &quot; &amp; &lt;", content)

    def test_source_extensions_do_not_collide_in_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_root = root / "input"
            input_root.mkdir()
            jpg = input_root / "photo.jpg"
            png = input_root / "photo.png"
            image = np.full((40, 80, 3), 128, dtype=np.uint8)
            self.assertTrue(cv2.imwrite(str(jpg), image))
            self.assertTrue(cv2.imwrite(str(png), image))
            output_root = root / "output"
            jpg_frame = scored_frame(str(jpg))
            jpg_frame.star_rating = 4
            jpg_frame.keeper_score = 0.8
            jpg_frame.is_burst_best = True
            png_frame = scored_frame(str(png))
            png_frame.star_rating = 3
            png_frame.keeper_score = 0.7
            png_frame.is_burst_best = True

            jpg_xmp = write_xmp(jpg_frame, input_root, output_root)
            png_xmp = write_xmp(png_frame, input_root, output_root)
            write_gallery([jpg_frame, png_frame], output_root / "gallery.html", input_root=input_root)

            self.assertNotEqual(jpg_xmp, png_xmp)
            self.assertTrue((output_root / "previews" / "photo.jpg.jpg").exists())
            self.assertTrue((output_root / "previews" / "photo.png.jpg").exists())

    def test_gallery_contains_preview_image(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_root = root / "input"
            source = input_root / "nested" / "photo.jpg"
            source.parent.mkdir(parents=True)
            self.assertTrue(cv2.imwrite(str(source), np.full((40, 80, 3), 128, dtype=np.uint8)))
            output_root = root / "output"
            output_root.mkdir()
            frame = scored_frame(str(source))
            frame.keeper_score = 0.8
            frame.star_rating = 4
            frame.is_burst_best = True

            gallery = write_gallery([frame], output_root / "gallery.html", input_root=input_root)

            self.assertTrue((output_root / "previews" / "nested" / "photo.jpg.jpg").exists())
            self.assertIn("<img ", gallery.read_text(encoding="utf-8"))

    def test_process_directory_writes_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_root = root / "input"
            input_root.mkdir()
            self.assertTrue(cv2.imwrite(
                str(input_root / "photo.jpg"),
                np.full((40, 80, 3), 128, dtype=np.uint8),
            ))
            (input_root / "unreadable.jpg").write_bytes(b"not an image")
            output_root = root / "output"

            scored = process_directory(str(input_root), str(output_root))
            summary = json.loads((output_root / "summary.json").read_text(encoding="utf-8"))

            self.assertEqual(len(scored), 1)
            self.assertEqual(summary["discovered_frame_count"], 2)
            self.assertEqual(summary["scored_frame_count"], 1)
            self.assertEqual(summary["unreadable_frame_count"], 1)
            self.assertEqual(summary["burst_count"], 1)
            self.assertEqual(summary["keeper_count"], 0)
            self.assertEqual(sum(summary["star_rating_counts"].values()), 1)

    def test_grayscale_quality_helpers_preserve_sharpness_order(self) -> None:
        sharp = np.zeros((100, 100), dtype=np.uint8)
        sharp[:, ::4] = 255
        blurry = cv2.GaussianBlur(sharp, (31, 31), 0)

        self.assertGreater(laplacian_focus(sharp), laplacian_focus(blurry))
        self.assertIn("black_clip", exposure_clipping(sharp))
        self.assertEqual(resize_quality_image(np.zeros((2160, 3840), dtype=np.uint8)).shape, (1080, 1920))


if __name__ == "__main__":
    unittest.main(verbosity=2)
