"""
Persistência das quantidades de impressão por carta, na tela de Proxy.

Guarda um dict simples {chave_da_linha: quantidade} em
collections/<slug>/proxy_quantities.json — fica salvo entre visitas à
tela (decisão confirmada com o usuário: quantidade "lembrada", não
resetada a cada geração).

Chave de identificação de cada linha: o campo configurado como
"identificador" da coleção (tela de Dados) — `name` por padrão, com
fallback pra primeira coluna do dataset se `name` não existir, e pra
posição da linha se não houver nenhuma coluna. Ver
`collections.resolve_identifier_field()`. Linhas sem valor nesse campo,
ou com valor duplicado entre si, caem/compartilham o fallback por
posição — funciona, mas duas linhas com o mesmo identificador vão
compartilhar a mesma quantidade salva (limitação aceita
conscientemente, documentada no manual).
"""
from __future__ import annotations

import json
from pathlib import Path

from web.services import collections


def row_key(row: dict, idx: int, id_field: str | None = "name") -> str:
    value = str(row.get(id_field, "")).strip() if id_field else ""
    return value if value else f"__row{idx}__"


def load(slug: str) -> dict[str, int]:
    p = collections.proxy_quantities_path(slug)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return {str(k): int(v) for k, v in data.items()}
    except Exception:
        return {}


def save(slug: str, quantities: dict[str, int]) -> None:
    p = collections.proxy_quantities_path(slug)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(quantities, ensure_ascii=False, indent=2), encoding="utf-8")


def quantities_for_rows(slug: str, rows: list[dict], id_field: str | None = "name") -> list[int]:
    """Quantidade de cada linha do dataset atual, na mesma ordem — usa o
    valor salvo se existir, ou 1 como padrão (mesmo comportamento de
    sempre: imprime uma cópia de cada, até a pessoa customizar)."""
    saved = load(slug)
    return [saved.get(row_key(row, i, id_field), 1) for i, row in enumerate(rows)]
