from __future__ import annotations

from pathlib import Path
from flask import Flask

from .config import Config


def create_app() -> Flask:
    web_dir = Path(__file__).resolve().parent
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

    app.register_blueprint(main_bp)
    app.register_blueprint(templates_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(generate_bp)
    app.register_blueprint(proxy_bp)
    app.register_blueprint(wiki_bp)

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
