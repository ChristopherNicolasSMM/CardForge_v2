"""Normaliza referências de imagens de forma portátil e segura.

O JSON dos cards pode ter sido criado no Windows (``imgs\\arte.png``) ou no
Linux (``imgs/arte.png``). Internamente o CardForge usa sempre ``/``; a
conversão para ``Path`` só acontece no momento de acessar o disco.
"""
from __future__ import annotations

from pathlib import Path, PurePosixPath


def normalize_asset_reference(value: object) -> str:
    """Retorna uma referência relativa, com ``/``, ou string vazia se inválida."""
    raw = str(value or "").strip().replace("\\", "/")
    while raw.startswith("./"):
        raw = raw[2:]
    path = PurePosixPath(raw)
    if not raw or path.is_absolute() or ".." in path.parts:
        return ""
    return path.as_posix()


def asset_reference_basename(value: object) -> str:
    normalized = normalize_asset_reference(value)
    return PurePosixPath(normalized).name if normalized else ""


def contained_candidate(root: Path, reference: object) -> Path | None:
    """Monta um caminho abaixo de ``root`` sem permitir path traversal."""
    normalized = normalize_asset_reference(reference)
    if not normalized:
        return None
    root = root.resolve()
    candidate = (root / Path(*PurePosixPath(normalized).parts)).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate
