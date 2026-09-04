from __future__ import annotations

from pathlib import Path
from flask import Flask, g, request, redirect, url_for, flash

from .config import Config
from core.paths import resource_root

# Blueprints que não dependem de uma coleção ativa — sempre acessíveis.
_COLLECTION_EXEMPT_BLUEPRINTS = {"wiki_bp", "collections_bp", "main", "static", None}


def create_app() -> Flask:
    # web/templates e web/static são recurso empacotado (read-only) — usa
    # resource_root() em vez de Path(__file__), que não é confiável sob
    # execução empacotada (ver core/paths.py).
    web_dir = resource_root() / "web"
    app = Flask(
        __name__,
        template_folder=str(web_dir / "templates"),
        static_folder=str(web_dir / "static"),
    )
    app.config.from_object(Config)

    from .routes.main import bp as main_bp
    from .routes.templates_bp import bp as templates_bp
    from .routes.data_bp import bp as data_bp
    from .routes.generate_bp import bp as generate_bp
    from .routes.proxy_bp import bp as proxy_bp
    from .routes.wiki_bp import bp as wiki_bp
    from .routes.collections_bp import bp as collections_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(templates_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(generate_bp)
    app.register_blueprint(proxy_bp)
    app.register_blueprint(wiki_bp)
    app.register_blueprint(collections_bp)

    from .services import collections as collections_service
    from core.template.loader import set_templates_root, reset_templates_root
    from core.render.font_paths import set_custom_fonts_dir, reset_custom_fonts_dir

    # Migração única: se o projeto tem templates/assets no formato antigo
    # (pré-coleções) e nenhuma coleção existe ainda, cria a coleção "Geral"
    # automaticamente com esse conteúdo.
    with app.app_context():
        collections_service.migrate_legacy_if_needed()

    @app.before_request
    def _bind_active_collection():
        g.collection = collections_service.get_active_slug()
        g.collections_list = collections_service.list_collections()
        g._cf_tokens = None

        requires_collection = request.blueprint not in _COLLECTION_EXEMPT_BLUEPRINTS
        if requires_collection and not g.collection:
            flash("Escolha ou crie uma coleção antes de continuar.", "error")
            return redirect(url_for("collections_bp.index"))

        if g.collection:
            # Aponta o motor de renderização (core/) pra pasta da coleção ativa,
            # só durante esta requisição — vale pra qualquer rota, inclusive as
            # isentas (ex: o hub mostra estatísticas da coleção ativa).
            g._cf_tokens = (
                set_templates_root(collections_service.templates_dir(g.collection)),
                set_custom_fonts_dir(collections_service.custom_fonts_dir(g.collection)),
            )

    @app.teardown_request
    def _unbind_active_collection(exc):
        tokens = getattr(g, "_cf_tokens", None)
        if tokens:
            t_templates, t_fonts = tokens
            reset_templates_root(t_templates)
            reset_custom_fonts_dir(t_fonts)

    @app.context_processor
    def inject_nav():
        return {"nav_items": [
            ("main.hub", "Início"),
            ("templates_bp.gallery", "Templates"),
            ("data_bp.index", "Dados"),
            ("generate_bp.index", "Gerar"),
            ("proxy_bp.index", "Proxy / PDF"),
            ("wiki_bp.index", "Manual"),
        ]}

    return app
