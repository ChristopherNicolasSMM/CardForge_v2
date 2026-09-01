"""
Gerencia o "dataset atual" (lista de cards em edição) por sessão de navegador.

Sem banco de dados: cada sessão vira uma pasta em instance/<sid>/ com:
  data.json     ← {"columns": [...], "rows": [...]}
  output/       ← lotes gerados (PNG/JPEG/WebP/SVG) e proxies PDF
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from flask import session

from web.config import INSTANCE_DIR

# Colunas conhecidas do modelo de dados do CardForge (core/data/reader.py)
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


def get_session_id() -> str:
    sid = session.get("sid")
    if not sid:
        sid = uuid.uuid4().hex[:16]
        session["sid"] = sid
    return sid


def session_dir() -> Path:
    d = INSTANCE_DIR / get_session_id()
    d.mkdir(parents=True, exist_ok=True)
    (d / "output").mkdir(exist_ok=True)
    return d


def _data_path() -> Path:
    return session_dir() / "data.json"


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


def replace_rows_from_import(rows: list[dict]) -> dict:
    """Usado após ler um arquivo (CSV/XLSX/YAML/JSON) via core.data.reader."""
    columns = list(STANDARD_COLUMNS)
    for row in rows:
        for k in row.keys():
            if k not in columns:
                columns.append(k)
    save_dataset(columns, rows)
    return {"columns": columns, "rows": rows}


def output_dir() -> Path:
    return session_dir() / "output"
