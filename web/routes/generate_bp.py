"""Tela de Geração: renderiza todos os cards do dataset em lote (síncrono)."""
from __future__ import annotations

import io
import json
import time
import zipfile
from pathlib import Path

from flask import (Blueprint, render_template, request, redirect, url_for,
                    flash, send_from_directory, send_file, abort)

from core.template.loader import load_template, list_templates, template_dir
from core.render.preview_renderer import PreviewRenderer
from core.render.svg_builder import SVGBuilder, save_svg
from core.render.raster_exporter import export as raster_export, supported as raster_formats
from web.services import session_data as sd

bp = Blueprint("generate_bp", __name__, url_prefix="/generate")

# Acima disso, avisamos o usuário que a geração síncrona pode demorar.
SYNC_WARN_THRESHOLD = 100


@bp.route("/")
def index():
    dataset = sd.load_dataset()
    templates = list_templates()
    batches = _list_batches()
    return render_template(
        "generate/index.html",
        templates=templates, row_count=len(dataset["rows"]),
        formats=raster_formats(), warn_threshold=SYNC_WARN_THRESHOLD,
        batches=batches,
    )


@bp.route("/run", methods=["POST"])
def run():
    dataset = sd.load_dataset()
    rows = dataset["rows"]
    template_name = request.form.get("template")
    formats = request.form.getlist("formats")

    if not template_name:
        flash("Escolha um template.", "error")
        return redirect(url_for("generate_bp.index"))
    if not rows:
        flash("Não há cards nos Dados. Importe ou adicione cards primeiro.", "error")
        return redirect(url_for("generate_bp.index"))
    if not formats:
        flash("Escolha ao menos um formato de saída.", "error")
        return redirect(url_for("generate_bp.index"))

    try:
        t = load_template(template_name)
    except FileNotFoundError:
        flash("Template não encontrado.", "error")
        return redirect(url_for("generate_bp.index"))

    tdir = template_dir(template_name)
    renderer = PreviewRenderer(t, tdir, preview_dpi=t.dimensions.dpi)
    builder = SVGBuilder(t, tdir)

    batch_id = f"{template_name}-{int(time.time())}"
    batch_dir = sd.output_dir() / batch_id
    cards_meta = []

    for i, row in enumerate(rows):
        name = row.get("name") or f"card_{i:03d}"
        color = row.get("color", "colorless")
        entry = {"name": name, "files": {}}

        if "SVG" in formats:
            svg_str = builder.build(row, color)
            p = save_svg(svg_str, name, batch_dir / "svg")
            entry["files"]["SVG"] = p.name

        needs_raster = any(f in formats for f in ("PNG", "JPEG", "WEBP"))
        if needs_raster:
            img = renderer.render(row, color)
            for fmt in ("PNG", "JPEG", "WEBP"):
                if fmt in formats:
                    p = raster_export(img, name, fmt, batch_dir / fmt.lower())
                    entry["files"][fmt] = p.name
        cards_meta.append(entry)

    meta = {"template": template_name, "formats": formats,
            "count": len(rows), "created_at": time.time(), "cards": cards_meta}
    (batch_dir).mkdir(parents=True, exist_ok=True)
    (batch_dir / "batch.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2),
                                            encoding="utf-8")

    flash(f"{len(rows)} cards gerados com sucesso.", "success")
    return redirect(url_for("generate_bp.results", batch_id=batch_id))


def _list_batches():
    out = sd.output_dir()
    if not out.exists():
        return []
    batches = []
    for d in sorted(out.iterdir(), reverse=True):
        meta_path = d / "batch.json"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                meta["id"] = d.name
                batches.append(meta)
            except Exception:
                pass
    return batches


def _load_batch(batch_id: str) -> dict:
    meta_path = sd.output_dir() / batch_id / "batch.json"
    if not meta_path.exists():
        abort(404)
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["id"] = batch_id
    return meta


@bp.route("/results/<batch_id>")
def results(batch_id):
    meta = _load_batch(batch_id)
    preview_fmt = "PNG" if "PNG" in meta["formats"] else \
                  ("JPEG" if "JPEG" in meta["formats"] else
                   ("WEBP" if "WEBP" in meta["formats"] else None))
    return render_template("generate/results.html", meta=meta, preview_fmt=preview_fmt)


@bp.route("/file/<batch_id>/<fmt>/<path:filename>")
def file(batch_id, fmt, filename):
    d = sd.output_dir() / batch_id / fmt.lower()
    return send_from_directory(d, filename)


@bp.route("/zip/<batch_id>")
def zip_download(batch_id):
    meta = _load_batch(batch_id)
    batch_dir = sd.output_dir() / batch_id
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as zf:
        for fmt in meta["formats"]:
            fmt_dir = batch_dir / fmt.lower()
            if fmt_dir.exists():
                for f in fmt_dir.iterdir():
                    zf.write(f, arcname=f"{fmt.lower()}/{f.name}")
    mem.seek(0)
    return send_file(mem, mimetype="application/zip", as_attachment=True,
                      download_name=f"cardforge_{batch_id}.zip")
