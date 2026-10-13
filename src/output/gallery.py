"""Minimal HTML gallery for the live-picks view (Stage I).

Stage II: FastAPI + htmx LAN gallery.
"""
import base64
import html
from pathlib import Path


def write_gallery(frames: list[dict], out_path: str | Path, title: str = "ShotSift picks") -> Path:
    cards = []
    for f in sorted(frames, key=lambda x: x.get("keeper_score", 0), reverse=True):
        p = Path(f["path"])
        try:
            thumb = base64.b64encode(p.read_bytes()).decode()
            # downscale hint only; browser handles it
            img_tag = f'<img src="data:image/jpeg;base64,{thumb}" loading="lazy">'
        except OSError:
            img_tag = "<div>missing</div>"
        stars = "★" * f.get("stars", 0) + "☆" * (5 - f.get("stars", 0))
        rej = (
            f'<span class="rej">{html.escape(f["rejected"], quote=False)}</span>'
            if f.get("rejected")
            else ""
        )
        cards.append(
            f'<div class="card"><div class="img">{img_tag}</div>'
            f'<div class="meta"><b>{html.escape(p.name, quote=False)}</b><br>'
            f'<span class="stars">{stars}</span> {rej}<br>'
            f'score {f.get("keeper_score", 0)} · focus {f.get("focus", 0)} · '
            f'faces {f.get("faces", 0)}</div></div>'
        )
    page = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>{html.escape(title, quote=False)}</title>
<style>body{{font-family:sans-serif;background:#111;color:#eee;margin:0;padding:16px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}}
.card{{background:#1c1c1c;border-radius:8px;overflow:hidden}}
.card img{{width:100%;display:block}}.meta{{padding:8px;font-size:13px}}
.stars{{color:gold}}.rej{{color:#f66;text-transform:uppercase;font-size:11px}}</style>
</head><body><h1>{html.escape(title, quote=False)}</h1><div class="grid">{''.join(cards)}</div></body></html>"""
    out = Path(out_path)
    out.write_text(page, encoding="utf-8")
    return out
