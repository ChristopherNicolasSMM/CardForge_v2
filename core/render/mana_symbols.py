"""
Mana Symbols — resolução de notação `{X}` (estilo MTG) para ícones inline.

Ver docs/tech/doc-tecnico-mtg-symbols-frames.md para o mapeamento completo
da decisão de arquitetura.

Fonte visual dos ícones hoje: assets/icons/ — SVGs placeholder herdados do
início do projeto (não são os símbolos oficiais de mana; ver seção 2 do
documento técnico sobre a substituição planejada pelos ícones do projeto
Mana, github.com/andrewgioia/mana, licença SIL OFL 1.1).

Esta engine é agnóstica ao conteúdo visual: resolve notação → caminho de
PNG pré-rasterizado em assets/icons_png/ (gerado a partir dos SVGs por
scripts/generate_mana_icons.py). Trocar os ícones no futuro é só trocar os
PNGs dentro da mesma estrutura de pastas — não exige mudar este módulo.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent.parent
ICONS_SVG_DIR = ROOT / "assets" / "icons"
ICONS_PNG_DIR = ROOT / "assets" / "icons_png"

# Letra de notação -> nome de cor por extenso, usado para montar os caminhos
# dentro de hybrid/ e phyrexian/ (que usam nomes completos, ex: "white-black.svg").
_COLOR_NAMES = {"W": "white", "U": "blue", "B": "black", "R": "red", "G": "green"}

_TOKEN_RE = re.compile(r"\{([^{}]+)\}")

_resolve_cache: dict[str, Optional[Path]] = {}


def _resolve_relpath(token: str) -> Optional[str]:
    """Notação normalizada (ex: 'W', 'T', '2/R', 'W/P', 'W/B/P') -> caminho
    relativo dentro de assets/icons/. Retorna None se a notação não for
    reconhecida (quem chama deve cair para desenhar o token como texto)."""
    t = token.strip().upper()
    if not t:
        return None

    simple = {
        "T": "tap.svg", "Q": "untap.svg", "E": "energy.svg",
        "X": "x.svg", "C": "colorless.svg", "S": "snow.svg",
    }
    if t in simple:
        return simple[t]
    if t in _COLOR_NAMES:
        return f"{t}.svg"
    if t.isdigit():
        n = int(t)
        # Genérico de 0-9 tem ícone dedicado; 2+ dígitos ainda não (cai para
        # o fallback textual em tokenize()) — ver limitação conhecida no
        # documento técnico.
        return f"{n}.svg" if 0 <= n <= 9 else None

    parts = t.split("/")
    if len(parts) == 2:
        a, b = parts
        if b == "P":  # phyrexian de cor única, ex: {W/P}
            if a == "C":
                return "phyrexian/colorless.svg"
            if a in _COLOR_NAMES:
                return f"phyrexian/{_COLOR_NAMES[a]}.svg"
        elif a == "2" and b in _COLOR_NAMES:  # two-brid, ex: {2/W}
            return f"hybrid/2-{_COLOR_NAMES[b]}.svg"
        elif a in _COLOR_NAMES and b in _COLOR_NAMES:  # híbrido, ex: {W/B}
            return f"hybrid/{_COLOR_NAMES[a]}-{_COLOR_NAMES[b]}.svg"
    elif len(parts) == 3:
        a, b, p = parts
        if p == "P" and a in _COLOR_NAMES and b in _COLOR_NAMES:  # híbrido phyrexian
            rel = f"phyrexian/{_COLOR_NAMES[a]}-{_COLOR_NAMES[b]}.svg"
            if (ICONS_SVG_DIR / rel).exists():
                return rel
            rel_swapped = f"phyrexian/{_COLOR_NAMES[b]}-{_COLOR_NAMES[a]}.svg"
            if (ICONS_SVG_DIR / rel_swapped).exists():
                return rel_swapped
    return None


def resolve_icon_png(token: str) -> Optional[Path]:
    """Caminho do PNG pré-rasterizado do símbolo, ou None se a notação não
    for reconhecida ou o PNG ainda não tiver sido gerado."""
    if token in _resolve_cache:
        return _resolve_cache[token]
    rel = _resolve_relpath(token)
    result: Optional[Path] = None
    if rel:
        candidate = ICONS_PNG_DIR / (rel[:-4] + ".png")
        if candidate.exists():
            result = candidate
    _resolve_cache[token] = result
    return result


def has_symbols(text: str) -> bool:
    """True se o texto contém ao menos uma notação `{X}` reconhecida."""
    if not text or "{" not in text:
        return False
    return any(resolve_icon_png(m.group(1)) is not None
               for m in _TOKEN_RE.finditer(text))


def tokenize(text: str) -> list[tuple[str, str]]:
    """Separa o texto em unidades ('word', texto) e ('symbol', notação),
    preservando a ordem. Notação sem ícone correspondente vira
    ('word', '{notação}') — desenhada como texto literal, sem quebrar a
    geração (mesmo princípio de falha silenciosa já usado no resto do
    projeto para campos não mapeados)."""
    units: list[tuple[str, str]] = []
    pos = 0
    for m in _TOKEN_RE.finditer(text):
        before = text[pos:m.start()]
        units.extend(("word", w) for w in before.split())
        notation = m.group(1)
        if resolve_icon_png(notation) is not None:
            units.append(("symbol", notation))
        else:
            units.append(("word", m.group(0)))
        pos = m.end()
    units.extend(("word", w) for w in text[pos:].split())
    return units
