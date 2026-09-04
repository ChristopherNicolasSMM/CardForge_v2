from __future__ import annotations

from flask import Blueprint, render_template, g, jsonify, send_from_directory

from core.template.loader import list_templates
from core.render import mana_symbols
from web.services import session_data as sd
from web.services import collections

bp = Blueprint("main", __name__)


@bp.route("/")
def hub():
    if not g.collection:
        return render_template("hub.html", no_collection=True,
                                template_count=0, row_count=0, batch_count=0,
                                collection=None)

    templates = list_templates()
    dataset = sd.load_dataset()
    batches_dir = sd.output_dir()
    batch_count = len([d for d in batches_dir.iterdir() if (d / "batch.json").exists()]) \
        if batches_dir.exists() else 0
    return render_template(
        "hub.html",
        no_collection=False,
        collection=collections.read_meta(g.collection),
        template_count=len(templates),
        row_count=len(dataset["rows"]),
        batch_count=batch_count,
    )


# ── Símbolos de mana (notação {X}) ──────────────────────────────────────────
# Globais, independentes de coleção — mesmo catálogo pra qualquer template.
# Usado pelo helper visual do editor e da tela de Dados (ver
# web/static/js/symbol-picker.js). Ver docs/09-simbolos-mana.md.

@bp.route("/symbols/manifest")
def symbols_manifest():
    return jsonify(mana_symbols.catalog())


@bp.route("/symbols/icon/<path:filename>")
def symbols_icon(filename):
    return send_from_directory(mana_symbols.ICONS_PNG_DIR, filename)
