"""Configuração central da aplicação Flask e dos caminhos do projeto."""
from __future__ import annotations

from pathlib import Path

from core.paths import resource_root, data_root

# Recursos empacotados (read-only): manuais exibidos na wiki. Sempre
# ao lado do código/bundle, nunca dentro da pasta de dados do usuário.
APP_ROOT           = resource_root()
DOCS_DIR            = APP_ROOT / "docs"

# Dados do usuário (graváveis): em execução empacotada, sempre ao lado do
# executável — é isso que torna o executável portátil (ver core/paths.py).
BASE_DIR            = data_root()
TEMPLATES_DIR       = BASE_DIR / "templates"          # legado (pré-coleções) — usado só na migração
ASSETS_DIR          = BASE_DIR / "assets"
LIBRARY_DIR         = ASSETS_DIR / "library"           # legado (pré-coleções)
CUSTOM_FONTS_DIR    = ASSETS_DIR / "fonts_custom"       # legado (pré-coleções)
INSTANCE_DIR        = BASE_DIR / "instance"             # legado (pré-coleções)
COLLECTIONS_DIR     = BASE_DIR / "collections"          # cada coleção é uma pasta própria aqui dentro

# TEMPLATES_DIR/LIBRARY_DIR/CUSTOM_FONTS_DIR/INSTANCE_DIR são só o caminho
# legado (pré-coleções), lido pela migração em
# web/services/collections.py:migrate_legacy_if_needed() — que está
# desativada (ver web/__init__.py). Não criamos essas pastas eagerly aqui:
# se não existirem, a migração (mesmo que reativada) simplesmente não
# encontra nada pra migrar, e nenhum outro código do app depende delas
# existirem de antemão.
for _p in (DOCS_DIR, COLLECTIONS_DIR):
    _p.mkdir(parents=True, exist_ok=True)


class Config:
    SECRET_KEY = "cardforge-dev-secret-troque-em-producao"
    MAX_CONTENT_LENGTH = 60 * 1024 * 1024  # 60MB — templates com fundos/artes grandes
    JSON_SORT_KEYS = False
    TEMPLATES_AUTO_RELOAD = True
