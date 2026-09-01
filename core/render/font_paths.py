"""
Resolução de diretórios de fontes.

Ordem de busca (primeiro que tiver o arquivo, vence):
  1. fonts/ dentro da própria pasta do template  (fonte específica daquele modelo)
  2. assets/fonts_custom/                         (fontes enviadas pelo usuário, globais)
  3. assets/fonts/                                (fontes embutidas no CardForge)

Isso é usado tanto pelo PreviewRenderer (PIL) quanto pelo SVGBuilder (SVG),
para que os dois pipelines de renderização enxerguem exatamente as mesmas fontes.
"""
from __future__ import annotations

from pathlib import Path

ROOT           = Path(__file__).resolve().parent.parent.parent
BUILTIN_FONTS  = ROOT / "assets" / "fonts"
CUSTOM_FONTS   = ROOT / "assets" / "fonts_custom"


def resolve_font_dirs(template_dir: Path | None = None) -> list[Path]:
    dirs: list[Path] = []
    if template_dir is not None:
        tdir_fonts = Path(template_dir) / "fonts"
        if tdir_fonts.exists():
            dirs.append(tdir_fonts)
    if CUSTOM_FONTS.exists():
        dirs.append(CUSTOM_FONTS)
    if BUILTIN_FONTS.exists():
        dirs.append(BUILTIN_FONTS)
    return dirs


def find_font_file(family: str, template_dir: Path | None = None) -> Path | None:
    """Procura <family>.ttf nos diretórios de busca, na ordem de prioridade."""
    for d in resolve_font_dirs(template_dir):
        fpath = d / f"{family}.ttf"
        if fpath.exists() and fpath.stat().st_size > 0:
            return fpath
    return None


def list_available_fonts(template_dir: Path | None = None) -> list[str]:
    """Lista os nomes (sem .ttf) de todas as fontes disponíveis, sem duplicar."""
    seen: dict[str, Path] = {}
    for d in resolve_font_dirs(template_dir):
        for ttf in sorted(d.glob("*.ttf")):
            if ttf.stat().st_size == 0:
                continue
            seen.setdefault(ttf.stem, ttf)
    return sorted(seen.keys())
