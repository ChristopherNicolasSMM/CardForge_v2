"""
Mana Symbols — resolução de notação `{X}` (estilo MTG) para ícones inline.

Ver docs/tech/doc-tecnico-mtg-symbols-frames.md para o mapeamento completo
da decisão de arquitetura.

Fonte visual dos ícones embutidos: compostos a partir dos glifos vendorizados
do projeto Mana (github.com/andrewgioia/mana, licença SIL OFL 1.1 pra fonte,
MIT pro CSS — ver assets/mana-src/ATTRIBUTION.md) mais a paleta oficial de
cores do mesmo projeto, via scripts/generate_mana_icons.py.

Esta engine é agnóstica ao conteúdo visual: resolve notação → caminho de
PNG. Trocar os ícones embutidos no futuro é só regenerar assets/icons_png/
— não exige mudar este módulo.

## Ícones por coleção

Além do catálogo embutido (sempre global, estilo MTG — W/U/B/R/G, genéricos,
tap/untap...), cada Coleção pode ter seu próprio conjunto de símbolos, sem
tocar em nada global:

  collections/<coleção>/assets/icons_png/
    manifest.json      ← opcional: notações customizadas dessa coleção
    <arquivos .png>     ← os ícones referenciados pelo manifest, ou usados
                           pra sobrescrever um ícone embutido (mesmo caminho
                           relativo, ex: colocar um W.png próprio)

`manifest.json` (formato, todas as chaves opcionais exceto `notation`):
  [
    {"notation": "fogo", "file": "fogo.png", "category": "Duelo das Tavernas", "label": "Fogo"},
    ...
  ]

Resolução, por notação (primeiro que existir, vence):
  1. Entrada de `manifest.json` da coleção ativa → arquivo dentro da
     própria pasta collections/<coleção>/assets/icons_png/.
  2. Arquivo com o mesmo caminho relativo do catálogo embutido, mas dentro
     de collections/<coleção>/assets/icons_png/ (reskin de um ícone
     embutido sem mexer no global — ex: um {W} customizado por coleção).
  3. Catálogo embutido global (assets/icons_png/), como sempre foi.

Coleções que não têm manifest nem arquivos próprios continuam se
comportando exatamente como antes — passo 3 sempre foi o único caminho.
"""
from __future__ import annotations

import contextvars
import json
import re
from pathlib import Path
from typing import Optional

from .. import paths as _paths

GLOBAL_ICONS_PNG_DIR = _paths.resource_root() / "assets" / "icons_png"
# Nome antigo, mantido por compatibilidade (código/rotas existentes que já
# importam mana_symbols.ICONS_PNG_DIR continuam funcionando sem mudança).
ICONS_PNG_DIR = GLOBAL_ICONS_PNG_DIR

# Letra de notação -> nome de cor por extenso, usado para montar os caminhos
# dentro de hybrid/ e phyrexian/ (que usam nomes completos, ex: "white-black.svg").
_COLOR_NAMES = {"W": "white", "U": "blue", "B": "black", "R": "red", "G": "green"}

_TOKEN_RE = re.compile(r"\{([^{}]+)\}")

# Cache de resolução — chaveado por (id do diretório de coleção ativa, token),
# não só por token, porque a coleção ativa muda por requisição (ContextVar) e
# o mesmo token pode resolver pra arquivos diferentes em coleções diferentes.
_resolve_cache: dict[tuple[Optional[str], str], Optional[Path]] = {}

# ── Diretório de ícones da coleção ativa (ContextVar) ───────────────────────
# Mesmo padrão de core/template/loader.py (templates_root) e
# core/render/font_paths.py (custom_fonts_dir): a pasta de ícones "ativa" é
# escopada por requisição, não por processo, pra não vazar entre coleções
# sob threads concorrentes.
_collection_icons_override: "contextvars.ContextVar[Optional[Path]]" = \
    contextvars.ContextVar("cardforge_collection_icons_override", default=None)


def set_collection_icons_dir(path: Path) -> contextvars.Token:
    """Define a pasta de ícones da coleção ativa pro escopo atual. Retorna um
    token — guarde-o e passe pra reset_collection_icons_dir() ao final."""
    return _collection_icons_override.set(Path(path))


def reset_collection_icons_dir(token: contextvars.Token) -> None:
    _collection_icons_override.reset(token)


def _collection_icons_dir() -> Optional[Path]:
    return _collection_icons_override.get()


def _collection_manifest() -> list[dict]:
    """Lê manifest.json da coleção ativa, se existir. Formato inválido ou
    ausente: lista vazia, sem levantar erro (mesmo princípio de falha
    silenciosa já usado no resto do projeto)."""
    d = _collection_icons_dir()
    if not d:
        return []
    p = d / "manifest.json"
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


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
    """Caminho do PNG do símbolo, resolvido nesta ordem (primeiro que
    existir, vence):
      1. manifest.json da coleção ativa (notação customizada da coleção)
      2. mesmo caminho relativo do catálogo embutido, mas dentro da pasta
         de ícones da coleção ativa (reskin de um ícone embutido)
      3. catálogo embutido global (comportamento de sempre)
    Retorna None se a notação não for reconhecida em nenhum dos três, ou o
    PNG ainda não tiver sido gerado/enviado."""
    coll_dir = _collection_icons_dir()
    cache_key = (str(coll_dir) if coll_dir else None, token)
    if cache_key in _resolve_cache:
        return _resolve_cache[cache_key]

    result: Optional[Path] = None

    # 1. Notação customizada da coleção ativa (manifest.json)
    if coll_dir:
        t_norm = token.strip()
        for entry in _collection_manifest():
            if str(entry.get("notation", "")).strip() == t_norm and entry.get("file"):
                candidate = coll_dir / str(entry["file"])
                if candidate.exists():
                    result = candidate
                    break

    # 2. Reskin: mesmo caminho relativo do embutido, mas na pasta da coleção
    rel = _resolve_relpath(token)
    if result is None and rel and coll_dir:
        candidate = coll_dir / (rel[:-4] + ".png")
        if candidate.exists():
            result = candidate

    # 3. Catálogo embutido global — comportamento de sempre
    if result is None and rel:
        candidate = GLOBAL_ICONS_PNG_DIR / (rel[:-4] + ".png")
        if candidate.exists():
            result = candidate

    _resolve_cache[cache_key] = result
    return result


def icon_search_dirs() -> list[Path]:
    """Diretórios de ícones em ordem de prioridade — usado pela rota Flask
    que serve os arquivos (/symbols/icon/<file>), pra descobrir de onde
    servir um caminho relativo dado."""
    dirs: list[Path] = []
    coll_dir = _collection_icons_dir()
    if coll_dir:
        dirs.append(coll_dir)
    dirs.append(GLOBAL_ICONS_PNG_DIR)
    return dirs


def resolve_icon_file(relative_path: str) -> Optional[Path]:
    """Resolve um caminho relativo (ex: 'W.png', 'hybrid/white-black.png',
    ou o nome de um arquivo customizado de coleção) contra icon_search_dirs(),
    pra servir via Flask. None se não existir em nenhum dos dois."""
    for d in icon_search_dirs():
        candidate = (d / relative_path).resolve()
        try:
            candidate.relative_to(d.resolve())
        except ValueError:
            continue  # candidate escapou do diretório base (ex: "../"), ignora
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


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
    possível, é a que faz sentido oferecer numa paleta.

    Inclui, no final, as notações customizadas da coleção ativa (definidas
    em manifest.json) — coleções sem manifest não ganham nenhuma entrada
    extra, então o catálogo de qualquer coleção existente hoje (ex: Magic)
    continua idêntico ao de antes."""
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
        if png is None:
            continue
        # file: caminho relativo à raiz de onde a rota Flask deve servir —
        # calculado contra o diretório real que continha o PNG (coleção ou
        # global), já que os dois agora são possíveis.
        for base in icon_search_dirs():
            try:
                rel_to_base = png.relative_to(base)
                break
            except ValueError:
                continue
        else:
            rel_to_base = png.name
        out.append({
            "category": category,
            "notation": notation,
            "label": display_label,
            "file": str(rel_to_base),
        })

    # Notações customizadas da coleção ativa (manifest.json) — só entram se
    # o arquivo referenciado realmente existir.
    coll_dir = _collection_icons_dir()
    if coll_dir:
        seen_notations = {n for _, n, _ in entries}
        for entry in _collection_manifest():
            notation = str(entry.get("notation", "")).strip()
            if not notation or notation in seen_notations:
                continue
            png = resolve_icon_png(notation)
            if png is None:
                continue
            out.append({
                "category": str(entry.get("category") or "Coleção"),
                "notation": notation,
                "label": str(entry.get("label") or notation),
                "file": entry.get("file", png.name),
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
