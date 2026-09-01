"""Tela de Dados: upload de arquivo, tabela editável no navegador, biblioteca de artes."""
from __future__ import annotations

import csv
import io
import tempfile
from pathlib import Path

from flask import (Blueprint, render_template, request, redirect, url_for,
                    flash, jsonify, send_file, send_from_directory, g)

from core.data.reader import read_data, supported_extensions
from web.services import session_data as sd
from web.services import assets as assets_service
from web.services import collections

bp = Blueprint("data_bp", __name__, url_prefix="/data")


@bp.route("/")
def index():
    dataset = sd.load_dataset()
    return render_template(
        "data/index.html",
        columns=dataset["columns"], rows=dataset["rows"],
        column_labels=sd.COLUMN_LABELS, standard_columns=sd.STANDARD_COLUMNS,
        supported_ext=supported_extensions(),
    )


@bp.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file or not file.filename:
        flash("Selecione um arquivo.", "error")
        return redirect(url_for("data_bp.index"))

    ext = Path(file.filename).suffix.lower()
    if ext not in supported_extensions():
        flash(f"Formato não suportado: {ext}", "error")
        return redirect(url_for("data_bp.index"))

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        file.save(tmp.name)
        tmp_path = Path(tmp.name)
    try:
        rows = read_data(tmp_path)
    except Exception as e:
        flash(f"Erro ao ler arquivo: {e}", "error")
        return redirect(url_for("data_bp.index"))
    finally:
        tmp_path.unlink(missing_ok=True)

    sd.replace_rows_from_import(rows)
    flash(f"{len(rows)} cards importados de “{file.filename}”.", "success")
    return redirect(url_for("data_bp.index"))


@bp.route("/save", methods=["POST"])
def save():
    payload = request.get_json(force=True, silent=True) or {}
    columns = payload.get("columns") or list(sd.STANDARD_COLUMNS)
    rows = payload.get("rows") or []
    sd.save_dataset(columns, rows)
    return jsonify({"ok": True, "count": len(rows)})


@bp.route("/export.csv")
def export_csv():
    dataset = sd.load_dataset()
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=dataset["columns"])
    writer.writeheader()
    for row in dataset["rows"]:
        writer.writerow({c: row.get(c, "") for c in dataset["columns"]})
    mem = io.BytesIO(buf.getvalue().encode("utf-8-sig"))
    return send_file(mem, mimetype="text/csv", as_attachment=True,
                      download_name=f"cardforge_{g.collection}_dados.csv")


# ── Biblioteca de artes (upload inline pro campo "art") ─────────────────────

@bp.route("/art-upload", methods=["POST"])
def art_upload():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"ok": False, "error": "Nenhum arquivo enviado"}), 400
    try:
        fname = assets_service.save_library_image(file, g.collection)
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    return jsonify({"ok": True, "filename": fname,
                     "url": url_for("data_bp.library_file", filename=fname)})


@bp.route("/library")
def library():
    files = assets_service.list_library_images(g.collection)
    return jsonify([
        {"filename": f, "url": url_for("data_bp.library_file", filename=f)}
        for f in files
    ])


@bp.route("/library/<path:filename>")
def library_file(filename):
    return send_from_directory(collections.library_dir(g.collection), filename)
