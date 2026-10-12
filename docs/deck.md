# ShotSift — Stage I Deck Outline (20 slides max)

> Creator AI · Battlefield Lightning · Onsite Track
> Items in [BRACKETS] must be filled from Bryan's real data. Do not invent numbers.

## Act 1 — The problem (slides 1–5)

### 1. Title
"ShotSift: the cull happens while you shoot."
Creator AI · Battlefield Lightning · Onsite Track. Bryan Seah, SMU.
GitHub: github.com/hongyime/shotsift
Background: your best event photo, full-bleed, with a ShotSift star overlay.

### 2. Midnight after every event
Personal hook with YOUR numbers from your photo library:
- Frames shot vs. frames delivered across your last [N] events
- [Hours] spent culling per event
Visual: a 2,000-thumbnail grid screenshot.
This slide works because it's real data from a working photographer.

### 3. Three gaps
- **Timing:** nothing helps during the shoot.
- **Multi-shooter:** frames scattered across cards, merged by hand.
- **Privacy:** corporate clients don't want attendee faces in the cloud (PDPA).
One icon + one sentence each.

### 4. Who feels it
Three personas: the event photographer (you), the client's comms/social team
waiting for content during the event, the AV/production house coordinating crew.

### 5. Existing tools and the gap
Comparison table — ShotSift vs. existing culling tools on:
during-vs-after shoot · on-device vs. cloud · multi-shooter · generic vs. personal taste.
Verify every competitor cell against their current websites. Cite on slide 20.

## Act 2 — The solution (slides 6–9)

### 6. ShotSift in one sentence
"Shoot → seconds later, starred picks in a live gallery → import to Lightroom
with the cull already done."

### 7. User journey
Before: plug in the box + AP, cameras connect over FTP.
During: live gallery, person tagging.
After: XMP sidecars, deliverable shortlist, auto-deletion of event data.

### 8. Innovation 1: it learns your taste
Diagram: rating history → CLIP embeddings + quality features → small taste model
on CPU → keeper score. Generic "aesthetic" scores don't match how professionals choose.
**Honest framing:** taste-model training is Stage II work (no Lightroom history
available for Stage I). Stage I demonstrates the pipeline with heuristic weights.

### 9. Innovation 2: three-tier cascade on one Hailo-10H
Vision models score every frame. VLM captions only top picks. Function-calling LLM
handles search. One chip, round-robin scheduling. Targets "uniqueness of hardware
integration" directly.

## Act 3 — How it's built (slides 10–15)

### 10. Hardware architecture
Physical diagram: 2–3 cameras → venue-local Wi-Fi AP → host (Pi 5 or mini PC) +
UGen300 → display/LAN gallery. Card reader fallback. Show M.2 and USB variants.

### 11. Software architecture
Pipeline diagram: ingest → Tier 1 → CPU scoring → Tier 2 → outputs.
(See docs/architecture.md for the detailed version.)

### 12. Model map
Table: model | task | where it runs | source.
SCRFD, ArcFace, 3DDFA, CLIP image encoder → Hailo-10H (Model Zoo).
Qwen2-VL-2B, Qwen2-1.5B-FC → Hailo-10H (GenAI zoo).
Focus, exposure, burst grouping, HDBSCAN, taste head → CPU.
Footnote: "custom logic stays on CPU — no custom compilation required."

### 13. Privacy by design
No cloud. Embeddings scoped to one event, auto-deleted. Selfie search opt-in.
Raw images never leave the venue. Frame in PDPA terms.

### 14. Stage I prototype: what works today
Screenshots of the working pipeline. Honest statement: burst grouping, focus
scoring, keeper ranking, XMP sidecars, and gallery are demonstrated. Face
detection, blink detection, captions, and search are Stage II.

### 15. Expected outcomes and validation plan (targets, not claims)
Shutter-to-gallery latency · sustained FPS · precision@K vs. historical picks
(held out by whole event — Stage II) · duplicate collapse rate · watts at wall ·
minutes saved per event.

## Act 4 — Delivery and business (slides 16–20)

### 16. Four-week Stage II plan
- Week 1: port Tier 1 to Hailo-10H, benchmark.
- Week 2: GenAI tier + device sharing.
- Week 3: live gallery, XMP, multi-camera ingest.
- Week 4: validation on two real shoots, documentation.

### 17. Risks and mitigations
- Model availability on Hailo-10H → CPU fallback
- VLM latency → background queue, top picks only
- Venue Wi-Fi → own AP
- Taste-model overfitting → event-level holdout + generic baseline
- Hardware arrival timing → host-agnostic Docker build

### 18. Business model
1. Per-event rental through AV/production houses (your world — line item on the AV kit list).
2. Per-seat subscription for multi-shooter studios.
3. ProArt + UGen300 creator bundle as ASUS channel opportunity.
Use your real rental-market knowledge, not invented market sizes.

### 19. Go-to-market and why me
First pilots from your own photographer/AV network. XMP = zero workflow change.
Why you: working event photographer + AV operator who builds self-hosted AI.

### 20. References and links
GitHub repo · demo video · Hailo Model Zoo · GenAI zoo · InsightFace/SCRFD/ArcFace ·
CLIP · Qwen2-VL · HDBSCAN · XMP spec · PDPA biometric guidance · competitor sites.

## Appendix (not counted)
A1. Metric definitions and test protocol.
A2. Consent form template for demo subjects.
A3. Detailed competitor notes.
A4. Full repo structure.
