"""
Data Reader — importa CSV, JSON e YAML e normaliza para lista de dicts.

Saída sempre: list[dict[str, str]]
  • Todos os valores são strings
  • Chaves são normalizadas para snake_case minúsculo
  • Aliases PT/EN são aplicados automaticamente
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Iterator

# Aliases: nome da coluna → campo interno
FIELD_ALIASES: dict[str, str] = {
    # PT → interno
    "nome":            "name",
    "custo_mana":      "mana_cost",
    "custo mana":      "mana_cost",
    "tipo":            "type_line",
    "linha de tipo":   "type_line",
    "texto_regras":    "rules_text",
    "texto regras":    "rules_text",
    "regras":          "rules_text",
    "texto_flavor":    "flavor_text",
    "texto flavor":    "flavor_text",
    "flavor":          "flavor_text",
    "poder":           "power",
    "resistencia":     "toughness",
    "resistência":     "toughness",
    "artista":         "artist",
    "raridade":        "rarity",
    "imagem":          "art",
    "caminho_imagem":  "art",
    "art_path":        "art",
    "cor":             "color",
    # Também aceita diretamente o nome interno
    "name": "name", "mana_cost": "mana_cost", "type_line": "type_line",
    "rules_text": "rules_text", "flavor_text": "flavor_text",
    "power": "power", "toughness": "toughness", "artist": "artist",
    "rarity": "rarity", "color": "color", "art": "art",
    "set_info": "set_info", "number": "number",
}


def _normalize_key(k: str) -> str:
    """Converte header da planilha para campo interno."""
    key = k.strip().lower()
    key = re.sub(r"\s+", "_", key)
    return FIELD_ALIASES.get(key, key)


def _normalize_row(row: dict) -> dict:
    return {_normalize_key(k): str(v).strip() if v is not None else ""
            for k, v in row.items()}


def _iter_csv(path: Path) -> Iterator[dict]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield _normalize_row(row)


def _iter_json(path: Path) -> Iterator[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        for row in data:
            yield _normalize_row(row)
    elif isinstance(data, dict):
        for key, val in data.items():
            row = dict(val or {})
            row.setdefault("name", key)
            yield _normalize_row(row)


def _iter_yaml(path: Path) -> Iterator[dict]:
    try:
        import yaml
    except ImportError:
        raise ImportError("pyyaml é necessário para YAML. Execute: pip install pyyaml")
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if isinstance(data, list):
        for row in data:
            yield _normalize_row(row)
    elif isinstance(data, dict):
        for key, val in data.items():
            row = dict(val or {})
            row.setdefault("name", key)
            yield _normalize_row(row)


def _iter_excel(path: Path) -> Iterator[dict]:
    try:
        import openpyxl
    except ImportError:
        raise ImportError("openpyxl é necessário para .xlsx. Execute: pip install openpyxl")
    wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
    ws = wb.active
    rows   = ws.iter_rows(values_only=True)
    header = next(rows, None)
    if header is None:
        return
    keys = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(header)]
    for row in rows:
        if all(v is None for v in row):
            continue
        yield _normalize_row({keys[i]: v for i, v in enumerate(row)})
    wb.close()


READERS = {
    ".csv":  _iter_csv,
    ".json": _iter_json,
    ".yml":  _iter_yaml,
    ".yaml": _iter_yaml,
    ".xlsx": _iter_excel,
    ".xls":  _iter_excel,
}


def read_data(path: Path | str) -> list[dict]:
    """
    Lê qualquer formato suportado e retorna lista de dicts normalizados.
    Filtra linhas sem 'name'.
    """
    path = Path(path)
    ext  = path.suffix.lower()
    reader_fn = READERS.get(ext)
    if not reader_fn:
        raise ValueError(f"Formato não suportado: {ext}. "
                         f"Use: {', '.join(READERS)}")
    rows = [r for r in reader_fn(path) if r.get("name")]
    return rows


def supported_extensions() -> list[str]:
    return list(READERS.keys())
