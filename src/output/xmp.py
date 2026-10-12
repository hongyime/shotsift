"""XMP sidecar writer.

Writes <basename>.xmp next to the image with:
- xmp:Rating (0-5 stars)
- xmp:Label (color label)
- dc:subject (keywords)
- dc:description (caption)

Lightroom / Capture One / darktable pick these up on import.
"""
from pathlib import Path
from xml.sax.saxutils import escape


XMP_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="ShotSift">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:xmp="http://ns.adobe.com/xap/1.0/"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmp:Rating="{rating}"
    xmp:Label="{label}">
   <dc:subject>
    <rdf:Bag>
{keywords}
    </rdf:Bag>
   </dc:subject>
   <dc:description>
    <rdf:Alt>
     <rdf:li xml:lang="x-default">{caption}</rdf:li>
    </rdf:Alt>
   </dc:description>
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>
"""


def write_xmp(
    image_path: str | Path,
    rating: int,
    label: str = "",
    keywords: list[str] | None = None,
    caption: str = "",
    out_dir: str | Path | None = None,
) -> Path:
    image_path = Path(image_path)
    kw_xml = "\n".join(f"     <rdf:li>{escape(k)}</rdf:li>" for k in (keywords or []))
    content = XMP_TEMPLATE.format(
        rating=max(0, min(5, rating)),
        label=escape(label),
        keywords=kw_xml,
        caption=escape(caption),
    )
    dest_dir = Path(out_dir) if out_dir else image_path.parent
    dest = dest_dir / (image_path.stem + ".xmp")
    dest.write_text(content, encoding="utf-8")
    return dest


def stars_to_label(stars: int) -> str:
    return {5: "Red", 4: "Yellow", 3: "Green"}.get(stars, "")
