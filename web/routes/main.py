from __future__ import annotations

from flask import Blueprint, render_template

from core.template.loader import list_templates
from web.services import session_data as sd

bp = Blueprint("main", __name__)


@bp.route("/")
def hub():
    templates = list_templates()
    dataset = sd.load_dataset()
    batches_dir = sd.output_dir()
    batch_count = len([d for d in batches_dir.iterdir() if (d / "batch.json").exists()]) \
        if batches_dir.exists() else 0
    return render_template(
        "hub.html",
        template_count=len(templates),
        row_count=len(dataset["rows"]),
        batch_count=batch_count,
    )
