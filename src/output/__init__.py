"""Output: XMP sidecars + HTML gallery."""
from __future__ import annotations

import html
from pathlib import Path
from urllib.parse import quote

import cv2

from ..scoring import ScoredFrame


def label_for(stars: int) -> str:
    return {5: "Red", 4: "Yellow", 3: "Green", 2: "Blue", 1: "Purple"}.get(stars, "None")


def write_xmp(
    scored: ScoredFrame,
    input_root: str | Path,
    output_root: str | Path,
    caption: str = "",
    keywords: list[str] | None = None,
) -> Path:
    kw = "".join(
        "<rdf:li>" + html.escape(k, quote=True) + "</rdf:li>" for k in (keywords or [])
    )
    content = (
        "<x:xmpmeta xmlns:x=\"adobe:ns:meta/\">\n"
        " <rdf:RDF xmlns:rdf=\"http://www.w3.org/1999/02/22-rdf-syntax-ns#\">\n"
        "  <rdf:Description rdf:about=\"\" xmlns:xmp=\"http://ns.adobe.com/xap/1.0/\"\n"
        "    xmlns:dc=\"http://purl.org/dc/elements/1.1/\"\n"
        "    xmp:Rating=\"" + str(scored.star_rating) + "\"\n"
        "    xmp:Label=\"" + label_for(scored.star_rating) + "\">\n"
        "   <dc:description><rdf:Alt><rdf:li xml:lang=\"x-default\">"
        + html.escape(caption, quote=True) + "</rdf:li></rdf:Alt></dc:description>\n"
        "   <dc:subject><rdf:Bag>" + kw + "</rdf:Bag></dc:subject>\n"
        "  </rdf:Description>\n </rdf:RDF>\n</x:xmpmeta>\n"
    )
    source = Path(scored.frame.path).resolve()
    relative = source.relative_to(Path(input_root).resolve())
    relative = relative.with_name(relative.name + ".xmp")
    sidecar = Path(output_root) / relative
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_text(content, encoding="utf-8")
    return sidecar


def _write_preview(source: Path, destination: Path) -> bool:
    image = cv2.imread(str(source))
    if image is None:
        return False
    height, width = image.shape[:2]
    scale = min(1.0, 1920 / width, 1080 / height)
    if scale < 1.0:
        image = cv2.resize(
            image,
            (round(width * scale), round(height * scale)),
            interpolation=cv2.INTER_AREA,
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        return bool(cv2.imwrite(str(destination), image))
    except cv2.error:
        return False


def write_gallery(
    scored_frames: list[ScoredFrame],
    out_path: str | Path,
    title: str = "ShotSift Picks",
    input_root: str | Path | None = None,
) -> Path:
    gallery = Path(out_path)
    output_root = gallery.parent
    input_root = Path(input_root).resolve() if input_root is not None else None
    output_root.mkdir(parents=True, exist_ok=True)
    picks = sorted([s for s in scored_frames if s.is_burst_best],
                   key=lambda s: s.keeper_score, reverse=True)
    cards = []
    for s in picks:
        source = Path(s.frame.path).resolve()
        name = html.escape(source.name, quote=True)
        stars = "\u2605" * s.star_rating + "\u2606" * (5 - s.star_rating)
        blink_txt = "yes" if s.blink else "no"
        relative = source.name if input_root is None else source.relative_to(input_root)
        relative = Path(relative).with_name(Path(relative).name + ".jpg")
        preview = output_root / "previews" / relative
        if _write_preview(source, preview):
            url = html.escape(quote(preview.relative_to(output_root).as_posix(), safe="/"), quote=True)
            image = '<img src="' + url + '" alt="' + name + ' preview" loading="lazy">'
        else:
            image = '<div class="preview placeholder">preview unavailable</div>'
        cards.append(
            "<div class=\"card\">" + image + "<div class=\"stars\">" + stars + "</div>"
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
        ".card img,.preview{width:100%;max-height:260px;object-fit:contain;background:#000}"
        ".placeholder{display:grid;place-items:center;min-height:140px;color:#999}"
        ".stars{color:#f5c518;font-size:18px}"
        ".name{font-size:13px;margin:6px 0;word-break:break-all}"
        ".meta{font-size:11px;color:#999}</style>"
        "</head><body><h1>" + html.escape(title) + " — " + str(len(picks)) + " picks</h1>"
        "<div class=\"grid\">" + "".join(cards) + "</div></body></html>"
    )
    gallery.write_text(page, encoding="utf-8")
    return gallery
