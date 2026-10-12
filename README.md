# ShotSift

**Edge AI photo culling for event photographers — ASUS UGen AI League Stage I submission.**

ShotSift scores every frame as it's shot, groups bursts, rejects blinks and soft-focus frames, and writes the cull directly into XMP sidecars so Lightroom/Capture One picks it up on import. A live HTML gallery gives the client's social team usable picks during the event.

## Stage I prototype (this repo)

Working on laptop CPU, no accelerator required:

- **Ingest**: discovers JPEGs, extracts EXIF (datetime, camera, embedded ratings if present)
- **Vision**: Haar-cascade face detection, Laplacian-variance focus scoring, histogram exposure scoring, heuristic blink detection
- **Scoring**: burst grouping by capture-time gaps (≤3s), per-burst keeper ranking (70% focus + 30% exposure, hard blink reject)
- **Output**: XMP sidecars (rating, color label, keywords, caption), HTML gallery, `summary.json`

### Run it

```bash
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
./venv/bin/python -m src.main <input_dir> <output_dir>
```

### What's real vs. deferred

| Component | Stage I status |
|---|---|
| Face detection (Haar) | ✅ Working |
| Focus / exposure scoring | ✅ Working |
| Blink reject (heuristic) | ✅ Working |
| Burst grouping (EXIF time) | ✅ Working |
| XMP sidecars | ✅ Working |
| HTML gallery | ✅ Working |
| **Taste model** | ❌ **Deferred to Stage II** |

**Taste model — honest status:** Bryan no longer uses Lightroom (subscription ended), so there is no rating history to train on. We sampled 17 event photos from his archive (across 5 events: Singapore Night Festival, SMU Patrons Day, NTUC Health Volunteer Day, YCS Commencement, YCS Network for Good): **zero embedded EXIF/XMP ratings found in all 17**. The prototype therefore uses a generic quality baseline (focus + exposure). Training a personal taste model on his own keep/reject history is documented as Stage II work, contingent on him re-rating a seed set.

No ratings were fabricated. The deck will present the taste model as a roadmap item, not a completed result.

## Stage II plan (if shortlisted)

Models moving to the Hailo-10H on the ASUS UGen300:

| Model | Task | Source |
|---|---|---|
| SCRFD | Face detection | Hailo Model Zoo (precompiled) |
| ArcFace | Face embeddings → identity clustering | Hailo Model Zoo (precompiled) |
| 3DDFA / landmarks | Eye aspect ratio → blink | Hailo Model Zoo or CPU fallback |
| CLIP image encoder | Semantic + aesthetic embedding | Hailo Model Zoo or CPU fallback |
| Qwen2-VL-2B | Caption + keywords (top picks only) | Hailo GenAI zoo |
| Qwen2-1.5B-FC | Natural-language photo search | Hailo GenAI zoo |

Custom logic (burst grouping, keeper scoring, taste-model head) stays on CPU — no Hailo compiler needed.

## Project structure

```
shotsift/
├── src/
│   ├── ingest/     # discovery, EXIF + embedded rating extraction
│   ├── vision/     # face detection, focus/exposure/blink scoring
│   ├── scoring/    # burst grouping, keeper ranking
│   ├── output/     # XMP writer, HTML gallery
│   └── main.py     # CLI entry point
├── tests/
├── docs/
│   └── architecture.md
├── samples/        # 10 dev samples (not committed)
└── requirements.txt
```

## License

Private — ASUS UGen AI League submission.
