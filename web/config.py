"""Configuração central da aplicação Flask e dos caminhos do projeto."""
from __future__ import annotations

from pathlib import Path

BASE_DIR          = Path(__file__).resolve().parent.parent
TEMPLATES_DIR      = BASE_DIR / "templates"          # legado (pré-coleções) — usado só na migração
ASSETS_DIR         = BASE_DIR / "assets"
LIBRARY_DIR        = ASSETS_DIR / "library"           # legado (pré-coleções)
CUSTOM_FONTS_DIR   = ASSETS_DIR / "fonts_custom"       # legado (pré-coleções)
INSTANCE_DIR       = BASE_DIR / "instance"             # legado (pré-coleções)
DOCS_DIR           = BASE_DIR / "docs"                 # manuais em .md exibidos na wiki (/wiki) — sempre global
COLLECTIONS_DIR    = BASE_DIR / "collections"          # cada coleção é uma pasta própria aqui dentro

for _p in (TEMPLATES_DIR, LIBRARY_DIR, CUSTOM_FONTS_DIR, INSTANCE_DIR, DOCS_DIR, COLLECTIONS_DIR):
    _p.mkdir(parents=True, exist_ok=True)


class Config:
    SECRET_KEY = "cardforge-dev-secret-troque-em-producao"
    MAX_CONTENT_LENGTH = 60 * 1024 * 1024  # 60MB — templates com fundos/artes grandes
    JSON_SORT_KEYS = False
    TEMPLATES_AUTO_RELOAD = True
