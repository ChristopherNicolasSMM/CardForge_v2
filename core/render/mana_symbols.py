"""
Mana Symbols — resolução de notação `{X}` (estilo MTG) para ícones inline.

Ver docs/tech/doc-tecnico-mtg-symbols-frames.md para o mapeamento completo
da decisão de arquitetura.

Fonte visual dos ícones: compostos a partir dos glifos vendorizados do
projeto Mana (github.com/andrewgioia/mana, licença SIL OFL 1.1 pra fonte,
MIT pro CSS — ver assets/mana-src/ATTRIBUTION.md) mais a paleta oficial de
cores do mesmo projeto, via scripts/generate_mana_icons.py.

Esta engine é agnóstica ao conteúdo visual: resolve notação → caminho de
PNG pré-gerado em assets/icons_png/. Trocar os ícones no futuro é só
regenerar essa pasta — não exige mudar este módulo.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent.parent
ICONS_PNG_DIR = ROOT / "assets" / "icons_png"

# Letra de notação -> nome de cor por extenso, usado para montar os caminhos
# dentro de hybrid/ e phyrexian/ (que usam nomes completos, ex: "white-black.svg").
_COLOR_NAMES = {"W": "white", "U": "blue", "B": "black", "R": "red", "G": "green"}

_TOKEN_RE = re.compile(r"\{([^{}]+)\}")

_resolve_cache: dict[str, Optional[Path]] = {}


def _resolve_relpath(token: str) -> Optional[str]:
    """Notação normalizada (ex: 'W', 'T', '2/R', 'W/P', 'W/B/P') -> caminho
    relativo "lógico" (extensão .svg por convenção histórica interna —
    resolve_icon_png() troca por .svg->.png e resolve contra
    assets/icons_png/, que é a árvore real gerada). Retorna None se a
    notação não for reconhecida (quem chama deve cair para desenhar o
    token como texto)."""
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
        # Genérico de 0-20 e 100 têm ícone dedicado (glifos vendorizados do
        # Mana); outros valores de 2+ dígitos caem no fallback textual em
        # tokenize().
        return f"{n}.svg" if (0 <= n <= 20 or n == 100) else None

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
            # resolve_icon_png() confere a existência real do PNG depois —
            # aqui só monta o caminho candidato, sem checar disco (o gerador
            # atual já emite as duas ordens, a-b e b-a).
            return f"phyrexian/{_COLOR_NAMES[a]}-{_COLOR_NAMES[b]}.svg"
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


def catalog() -> list[dict]:
    """Lista curada de notações pra UI (helper visual no editor/dados) —
    cada entrada só entra se o PNG correspondente já existir de fato.
    Não é uma enumeração exaustiva de toda combinação matematicamente
    possível, é a que faz sentido oferecer numa paleta."""
    entries: list[tuple[str, str, str]] = []  # (categoria, notação, rótulo)

    entries += [
        ("Cores", "W", "Branco"), ("Cores", "U", "Azul"), ("Cores", "B", "Preto"),
        ("Cores", "R", "Vermelho"), ("Cores", "G", "Verde"),
        ("Cores", "C", "Incolor"), ("Cores", "S", "Neve"),
    ]
    entries += [
        ("Genérico e especiais", str(n), str(n)) for n in list(range(21)) + [100]
    ]
    entries += [
        ("Genérico e especiais", "X", "X"),
        ("Genérico e especiais", "T", "Ativar (tap)"),
        ("Genérico e especiais", "Q", "Desativar (untap)"),
        ("Genérico e especiais", "E", "Energia"),
    ]
    for a, b in [("W", "U"), ("W", "B"), ("W", "R"), ("W", "G"), ("U", "B"),
                 ("U", "R"), ("U", "G"), ("B", "R"), ("B", "G"), ("R", "G")]:
        entries.append(("Híbrido", f"{a}/{b}", f"{a}/{b} híbrido"))
    for c in ["W", "U", "B", "R", "G"]:
        entries.append(("Two-brid", f"2/{c}", f"2/{c}"))
    for c in ["W", "U", "B", "R", "G", "C"]:
        entries.append(("Phyrexian", f"{c}/P", f"{c} phyrexian"))
    for a, b in [("W", "B"), ("W", "R"), ("W", "G"), ("W", "U"), ("B", "R"),
                 ("B", "G"), ("B", "U"), ("R", "G"), ("R", "U"), ("G", "U")]:
        entries.append(("Phyrexian híbrido", f"{a}/{b}/P", f"{a}/{b} phyrexian"))

    out = []
    for category, notation, display_label in entries:
        png = resolve_icon_png(notation)
        if png is not None:
            out.append({
                "category": category,
                "notation": notation,
                "label": display_label,
                "file": str(png.relative_to(ICONS_PNG_DIR)),
            })
    return out


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
