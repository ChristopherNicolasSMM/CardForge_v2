"""
Gerencia o dataset (lista de cards em edição) da coleção ativa.

Antes das Coleções, isso vivia em instance/<sessão-de-navegador>/ — dados
efêmeros por aba do navegador. Agora o dataset é parte da própria Coleção,
salvo em collections/<slug>/data.json, e persiste de verdade em disco junto
com os templates e assets daquela coleção.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from web.services import collections

# Campos padrão sugeridos como ponto de partida (estilo MTG) — só usados
# quando uma coleção nova opta por eles ou quando um dataset fica totalmente
# vazio. Nenhum campo aqui é obrigatório: renomeie, remova ou adicione
# quantos campos quiser pela tela de Dados — cada coleção pode ter um
# esquema de dados completamente diferente.
STANDARD_COLUMNS = [
    "name", "mana_cost", "type_line", "rules_text", "flavor_text",
    "power", "toughness", "artist", "rarity", "art", "color",
]

COLUMN_LABELS = {
    "name": "Nome", "mana_cost": "Custo", "type_line": "Tipo",
    "rules_text": "Texto de regras", "flavor_text": "Texto de sabor",
    "power": "Força", "toughness": "Resistência", "artist": "Artista",
    "rarity": "Raridade", "art": "Arte (imagem)", "color": "Cor",
}


class NoActiveCollection(RuntimeError):
    """Levantado quando uma operação de dados é tentada sem coleção ativa."""


def _require_slug() -> str:
    slug = collections.get_active_slug()
    if not slug:
        raise NoActiveCollection("Nenhuma coleção ativa selecionada.")
    return slug


def _data_path() -> Path:
    return collections.data_path(_require_slug())


def load_dataset() -> dict[str, Any]:
    p = _data_path()
    if not p.exists():
        return {"columns": list(STANDARD_COLUMNS), "rows": []}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"columns": list(STANDARD_COLUMNS), "rows": []}


def save_dataset(columns: list[str], rows: list[dict]) -> None:
    _data_path().write_text(
        json.dumps({"columns": columns, "rows": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    collections.update_meta(_require_slug())


def replace_rows_from_import(rows: list[dict]) -> dict:
    """Usado após ler um arquivo (CSV/XLSX/YAML/JSON) via core.data.reader.

    As colunas vêm dos campos que o arquivo realmente trouxe — não força os
    campos padrão de MTG, já que a coleção pode ser de um jogo com um
    esquema de dados completamente diferente. Se o arquivo vier vazio, mantém
    os campos padrão como ponto de partida (mais fácil que começar do zero)."""
    columns: list[str] = []
    for row in rows:
        for k in row.keys():
            if k not in columns:
                columns.append(k)
    if not columns:
        columns = list(STANDARD_COLUMNS)
    save_dataset(columns, rows)
    return {"columns": columns, "rows": rows}


def output_dir() -> Path:
    return collections.output_dir(_require_slug())
