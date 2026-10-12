# ShotSift

**Edge AI photo culling for event photographers — the cull happens while you shoot.**

ASUS UGen AI League entry · Creator AI · Battlefield Lightning · Onsite Track

## The problem

An event photographer shoots 1,500–3,000 frames per event. Culling and tagging
takes hours that evening. The client's social team wants usable shots *during*
the event and gets nothing until the next day. Existing tools work after the shoot,
on the photographer's laptop — leaving three gaps:

1. **Timing** — nothing helps during the shoot itself.
2. **Multi-shooter** — several photographers' cards become separate piles to merge.
3. **Privacy** — uploading attendee faces to a cloud service is a PDPA problem
   for corporate clients.

## The solution

ShotSift is an edge appliance (host + ASUS UGen300 accelerator). Cameras push
each frame over FTP-over-Wi-Fi as they shoot. Every frame is scored for focus,
blink, exposure, and burst duplicates. The best frame per burst rises to the top.
Results go to a live LAN gallery for the client's social team, and to XMP
sidecars so Lightroom/Capture One imports with the cull already done.

## Stage I prototype (this repo)

Working laptop prototype demonstrating the full pipeline:

- **Ingest** — directory scan, EXIF extraction (capture time, camera serial)
- **Vision** — YuNet face detection (optional), Laplacian focus scoring,
  histogram exposure clipping
- **Scoring** — burst grouping by capture-time proximity, keeper scoring,
  best-of-burst selection, 1–5 star ratings
- **Output** — XMP sidecars (rating + Lightroom color label), static HTML gallery

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m src.main <input_dir> <output_dir>
.venv/bin/python tests/test_pipeline.py
```

### What's real vs. deferred

| Component | Stage I (this repo) | Stage II (on UGen300) |
|---|---|---|
| Face detection | YuNet on CPU (optional) | SCRFD on Hailo-10H |
| Face embeddings / identity clustering | Not implemented | ArcFace on Hailo-10H |
| Blink detection | Not implemented (conservative default) | 3DDFA landmarks on Hailo-10H |
| Aesthetic / CLIP embeddings | Not implemented | CLIP image encoder on Hailo-10H |
| Captions / keywords | Not implemented | Qwen2-VL-2B on Hailo-10H (GenAI) |
| Natural-language search | Not implemented | Qwen2-1.5B-FC on Hailo-10H (GenAI) |
| **Focus scoring** | **Working (Laplacian)** | Same logic, stays on CPU |
| **Burst grouping** | **Working (EXIF time gaps)** | Same logic, stays on CPU |
| **Keeper scoring** | **Working (heuristic weights)** | Same logic, stays on CPU |
| **XMP sidecars** | **Working** | Same |
| **HTML gallery** | **Working** | FastAPI + LAN gallery |
| Taste model (personal) | **Deferred** — see below | Train on photographer's rating history |

### Taste model status (honest)

The personal taste model — training on the photographer's own historical
keep/reject decisions — is **Stage II work**. The photographer's Lightroom
catalog is not available (subscription lapsed), and no embedded EXIF/XMP ratings
were found in the photo library. Stage I ships with heuristic keeper weights
(documented in `src/scoring/`). No ratings or metrics in this repo are
fabricated; the taste-model accuracy claim is explicitly a Stage II validation
target, not a Stage I result.

## Architecture (Stage II target)

```
Camera A ─┐  FTP over Wi-Fi (venue-local AP)
Camera B ─┼──▶ INGEST (host): vsftpd + inotify
Card/USB ─┘         │  extract JPEG preview, read EXIF
                    ▼
  TIER 1 · Hailo-10H vision: SCRFD → ArcFace → 3DDFA → CLIP
                    ▼
  CPU SCORING: focus, exposure, burst grouping, taste head
                    ▼  (top-N picks only)
  TIER 2 · Hailo-10H GenAI: Qwen2-VL-2B captions, Qwen2-1.5B-FC search
                    ▼
  OUTPUT: XMP sidecars · LAN gallery · auto-delete after delivery
```

Custom logic stays on CPU; only stock pretrained models run on the Hailo.
No Hailo model compilation required.

## Privacy

No cloud. Face embeddings scoped to one event, auto-deleted after delivery.
Selfie search opt-in with consent screen. Raw images never leave the venue.

## License

MIT — see LICENSE.
