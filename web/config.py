"""Configuração central da aplicação Flask e dos caminhos do projeto."""
from __future__ import annotations

from pathlib import Path

BASE_DIR          = Path(__file__).resolve().parent.parent
TEMPLATES_DIR      = BASE_DIR / "templates"          # modelos de card (core/template/loader.py)
ASSETS_DIR         = BASE_DIR / "assets"
LIBRARY_DIR        = ASSETS_DIR / "library"           # imagens de arte enviadas pelo usuário
CUSTOM_FONTS_DIR   = ASSETS_DIR / "fonts_custom"       # fontes .ttf enviadas globalmente
INSTANCE_DIR       = BASE_DIR / "instance"             # dados por sessão (dataset + saídas geradas)
DOCS_DIR           = BASE_DIR / "docs"                 # manuais em .md exibidos na wiki (/wiki)

for _p in (TEMPLATES_DIR, LIBRARY_DIR, CUSTOM_FONTS_DIR, INSTANCE_DIR, DOCS_DIR):
    _p.mkdir(parents=True, exist_ok=True)


class Config:
    SECRET_KEY = "cardforge-dev-secret-troque-em-producao"
    MAX_CONTENT_LENGTH = 60 * 1024 * 1024  # 60MB — templates com fundos/artes grandes
    JSON_SORT_KEYS = False
    TEMPLATES_AUTO_RELOAD = True
