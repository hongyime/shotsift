# ShotSift Architecture

## Stage I (laptop prototype — this repo)

```
JPEGs → discover → EXIF extract → burst group (≤3s gaps)
                                    ↓
                         ┌─ per frame ─────────────┐
                         │ Haar face detect         │
                         │ Laplacian focus (face)   │
                         │ Histogram exposure       │
                         │ Blink heuristic          │
                         └──────────────────────────┘
                                    ↓
                         keeper score = 0.7·focus + 0.3·exposure
                         (blink → hard reject, score 0)
                                    ↓
                         rank within burst → stars (5/4/3/2/1)
                                    ↓
                         XMP sidecar + HTML gallery + summary.json
```

All CPU. Dependencies: `opencv-python-headless`, `numpy`, `Pillow`, `piexif`.

## Stage II (ASUS UGen300, Hailo-10H)

```
Camera A ─┐ FTP over Wi-Fi (venue-local AP)
Camera B ─┼──→ ingest: vsftpd + inotify, extract JPEG preview from RAW
Card/USB ─┘         ↓
   ┌── TIER 1 · every frame · Hailo-10H ────────────────┐
   │ SCRFD → faces → ArcFace embeddings (clustering)    │
   │              └→ 68-pt landmarks → eye aspect ratio │
   │ CLIP image encoder → semantic + aesthetic         │
   └────────────────────────────────────────────────────┘
                        ↓  (CPU)
   focus / exposure / burst group / keeper score /
   taste-model head (logistic regression on CLIP + quality feats)
                        ↓  (top-N only)
   ┌── TIER 2 · Hailo-10H GenAI ────────────────────────┐
   │ Qwen2-VL-2B → caption + keywords (JSON)            │
   │ Qwen2-1.5B-FC → natural-language search           │
   └────────────────────────────────────────────────────┘
                        ↓
   XMP sidecars · FastAPI LAN gallery · SQLite · Docker Compose
```

Design rule: only stock precompiled models run on the Hailo (from the Model Zoo / GenAI zoo). All custom logic stays on CPU — no Hailo model compiler needed.

## Data flow (privacy)

- No cloud. All processing on-device / venue-local network.
- Face embeddings scoped to one event, auto-deleted after delivery.
- RAW files never leave the venue; only JPEG previews are processed.
- Opt-in selfie kiosk for "find my photos" (consent screen).
