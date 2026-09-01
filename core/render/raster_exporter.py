"""
Raster Exporter — salva PIL.Image em PNG, JPEG ou WebP.
"""
from __future__ import annotations
import re
from pathlib import Path
from PIL import Image

FORMATS = {
    "PNG":  (".png",  {}),
    "JPEG": (".jpg",  {"quality": 95, "optimize": True}),
    "WEBP": (".webp", {"quality": 92, "method": 4}),
}


def export(img: Image.Image, name: str, fmt: str, output_dir: Path) -> Path:
    fmt = fmt.upper()
    ext, opts = FORMATS.get(fmt, (".png", {}))
    output_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r'[^\w\-]', '_', name)
    dest = output_dir / f"{safe}{ext}"

    save_img = img.convert("RGB") if fmt == "JPEG" else img.convert("RGBA")
    save_img.save(str(dest), fmt if fmt != "WEBP" else "WEBP", **opts)
    return dest


def supported() -> list[str]:
    return list(FORMATS.keys())
