# ShotSift — Submission Status

**Deadline:** Wed Oct 14, 17:00 SGT · **Repo:** github.com/hongyime/shotsift (public)
**Theme:** Creator AI · **Battlefield:** Lightning · **Track:** Onsite

## Done (overnight)

- [x] Working prototype on L390 (`~/Projects/shotsift`), all 4 tests pass
- [x] End-to-end verified: 3-frame burst → 1 burst → sharp frame picked as 4-star best
- [x] XMP sidecars + HTML gallery output working
- [x] Public GitHub repo created and pushed
- [x] README with honest real-vs-deferred table
- [x] 20-slide deck outline (`docs/deck.md`) — [BRACKET] numbers need your data
- [x] 3-minute video script (`docs/video-script.md`) with shot list
- [x] Architecture doc (`docs/architecture.md`)

## What's real vs. deferred (no fabrications)

**Working:** burst grouping, focus scoring, keeper ranking, star ratings,
XMP sidecars, HTML gallery, EXIF extraction.

**Deferred to Stage II:** face detection (YuNet model download failed; pipeline
runs without it), blink detection (needs 3DDFA), CLIP embeddings, captions,
natural-language search, taste model (no Lightroom history available).

## Bryan's morning checklist

1. **Fill [BRACKET] numbers in docs/deck.md** — frames shot vs. delivered
   across your last [N] events, hours spent culling per event.
2. **Film the video** (script in docs/video-script.md):
   - Get 2–3 consenting friends as subjects — consent forms BEFORE filming.
   - Hero demo (0:45–1:10) is non-negotiable: shoot a burst, show the gallery
     updating, the best frame starred.
   - Do NOT claim blink detection — show soft-focus reject instead.
   - Upload as Unlisted, verify link in incognito.
3. **Build the deck** from docs/deck.md (20 slides max + appendix).
4. **Verify competitor claims** on slide 5 against their current websites.
5. **Submit by ~12:00 Wed** for buffer before the 17:00 deadline.
   Evening is SINCON Welcome Party — no deadline-night crunch.

## Key decisions (locked)

- Taste model: honestly framed as Stage II work. Do not invent accuracy numbers.
- If asked about metrics: only report what the prototype actually measured.
- Track is Onsite — the live demo (photographing judges) is the pitch.
