"""Output: XMP sidecars + HTML gallery."""
from __future__ import annotations

import html
import os
from xml.sax.saxutils import escape

from ..scoring import ScoredFrame


def label_for(stars: int) -> str:
    return {5: "Red", 4: "Yellow", 3: "Green", 2: "Blue", 1: "Purple"}.get(stars, "None")


def write_xmp(scored: ScoredFrame, caption: str = "", keywords: list[str] | None = None) -> str:
    kw = "".join("<rdf:li>" + escape(k) + "</rdf:li>" for k in (keywords or []))
    content = (
        "<x:xmpmeta xmlns:x=\"adobe:ns:meta/\">\n"
        " <rdf:RDF xmlns:rdf=\"http://www.w3.org/1999/02/22-rdf-syntax-ns#\">\n"
        "  <rdf:Description rdf:about=\"\" xmlns:xmp=\"http://ns.adobe.com/xap/1.0/\"\n"
        "    xmlns:dc=\"http://purl.org/dc/elements/1.1/\"\n"
        "    xmp:Rating=\"" + str(scored.star_rating) + "\"\n"
        "    xmp:Label=\"" + label_for(scored.star_rating) + "\">\n"
        "   <dc:description><rdf:Alt><rdf:li xml:lang=\"x-default\">"
        + escape(caption) + "</rdf:li></rdf:Alt></dc:description>\n"
        "   <dc:subject><rdf:Bag>" + kw + "</rdf:Bag></dc:subject>\n"
        "  </rdf:Description>\n </rdf:RDF>\n</x:xmpmeta>\n"
    )
    sidecar = os.path.splitext(scored.frame.path)[0] + ".xmp"
    with open(sidecar, "w", encoding="utf-8") as f:
        f.write(content)
    return sidecar


def write_gallery(scored_frames: list[ScoredFrame], out_path: str,
                  title: str = "ShotSift Picks") -> str:
    picks = sorted([s for s in scored_frames if s.is_burst_best],
                   key=lambda s: s.keeper_score, reverse=True)
    cards = []
    for s in picks:
        name = html.escape(os.path.basename(s.frame.path))
        stars = "\u2605" * s.star_rating + "\u2606" * (5 - s.star_rating)
        blink_txt = "yes" if s.blink else "no"
        cards.append(
            "<div class=\"card\"><div class=\"stars\">" + stars + "</div>"
            "<div class=\"name\">" + name + "</div>"
            "<div class=\"meta\">score " + ("%.2f" % s.keeper_score)
            + " | faces " + str(len(s.faces))
            + " | blink " + blink_txt + "</div></div>"
        )
    page = (
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\">"
        "<title>" + html.escape(title) + "</title>"
        "<style>body{font-family:system-ui;background:#111;color:#eee;margin:0;padding:24px}"
        "h1{font-size:20px}"
        ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px}"
        ".card{background:#1c1c1c;border-radius:8px;padding:12px}"
        ".stars{color:#f5c518;font-size:18px}"
        ".name{font-size:13px;margin:6px 0;word-break:break-all}"
        ".meta{font-size:11px;color:#999}</style>"
        "</head><body><h1>" + html.escape(title) + " — " + str(len(picks)) + " picks</h1>"
        "<div class=\"grid\">" + "".join(cards) + "</div></body></html>"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(page)
    return out_path
