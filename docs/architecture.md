# ShotSift Architecture

## Stage I (this repo) — laptop prototype

```
input_dir/
  frame001.jpg ─┐
  frame002.jpg ─┼──▶ discover() → Frame(path, EXIF time, camera serial)
  frame003.jpg ─┘
                        │
                        ▼
              FaceDetector (YuNet, optional)
              laplacian_focus() → focus_score
              exposure_clipping() → black/white clip fractions
                        │
                        ▼
              group_bursts() → bursts by 3s EXIF time gaps
                        │
                        ▼
              score_keeper() → 0..1 (heuristic weights)
              rate_burst_best() → best-of-burst, 1–5 stars
                        │
                        ▼
              write_xmp() → .xmp sidecar per frame
              write_gallery() → gallery.html (burst-best picks)
```

## Stage II (target) — ASUS UGen300 (Hailo-10H)

```
Camera A ─┐  FTP over Wi-Fi (venue-local AP, not house Wi-Fi)
Camera B ─┼──▶ INGEST (host): vsftpd + inotify watcher
Card/USB ─┘         │  extract embedded JPEG preview from RAW
                    │  (exiftool; never full RAW decode)
                    │  read EXIF: timestamp, body serial, focal length
                    ▼
  ┌────────── TIER 1 · every frame · Hailo-10H vision ──────────┐
  │ SCRFD face detection → face crops                            │
  │   ├─ ArcFace embeddings        → identity clustering        │
  │   └─ 3DDFA 68-pt landmarks     → eye aspect ratio → blinks  │
  │ CLIP image encoder (full frame) → semantic + aesthetic      │
  └──────────────────────────────────────────────────────────────┘
                    ▼
  CPU SCORING (cheap, no compilation needed)
    Laplacian variance on face/subject crop → focus score
    histogram clipping → exposure score
    burst grouping: EXIF time gap + CLIP cosine similarity
    TASTE HEAD: logistic regression / small MLP on
      [CLIP embedding ‖ quality features], trained on the
      photographer's rating history (Stage II — no Lightroom
      history available for Stage I)
    → keeper score → best-of-burst → star rating
    HDBSCAN on ArcFace embeddings → person clusters
                    ▼  (top-N picks only)
  ┌────────── TIER 2 · Hailo-10H GenAI ─────────────────────────┐
  │ Qwen2-VL-2B: caption + alt text + keywords, as JSON           │
  │ Qwen2-1.5B-Function-Calling: natural-language search         │
  └──────────────────────────────────────────────────────────────┘
                    ▼
  OUTPUT: XMP sidecars (rating/label/keywords/caption)
          FastAPI + SQLite → LAN live gallery
          opt-in "find my photos" selfie kiosk (consent screen)
          all in Docker Compose; event data wiped after delivery
```

## Key design decision

Custom logic stays on CPU. Only stock pretrained models run on the Hailo-10H
(from the Hailo Model Zoo + GenAI zoo). This avoids Hailo's model compiler
entirely — the hardest part of building for the platform.

## Model map

| Model | Task | Stage I | Stage II | Source |
|---|---|---|---|---|
| YuNet | Face detection | CPU (optional) | — | opencv_zoo |
| SCRFD | Face detection | — | Hailo-10H | Hailo Model Zoo |
| ArcFace | Identity embeddings | — | Hailo-10H | Hailo Model Zoo |
| 3DDFA | Landmarks → blink | — | Hailo-10H | Hailo Model Zoo |
| CLIP ViT-B/32 | Semantic + aesthetic | — | Hailo-10H | Hailo Model Zoo |
| Qwen2-VL-2B | Captions | — | Hailo-10H | Hailo GenAI zoo |
| Qwen2-1.5B-FC | NL search | — | Hailo-10H | Hailo GenAI zoo |
| Laplacian | Focus score | CPU ✓ | CPU | custom |
| Histogram | Exposure | CPU ✓ | CPU | custom |
| Burst grouping | EXIF time gaps | CPU ✓ | CPU | custom |
| Keeper scoring | Heuristic weights | CPU ✓ | CPU | custom |
| Taste head | Personal model | — (deferred) | CPU | custom |
