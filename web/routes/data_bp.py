"""Tela de Dados: upload de arquivo, tabela editável no navegador, biblioteca de artes."""
from __future__ import annotations

import csv
import io
import tempfile
from pathlib import Path

from flask import (Blueprint, render_template, request, redirect, url_for,
                    flash, jsonify, send_file, send_from_directory, g)

from core.data.reader import read_data, supported_extensions
from core.fsutil import unlink_retry
from web.services import session_data as sd
from web.services import assets as assets_service
from web.services import collections

bp = Blueprint("data_bp", __name__, url_prefix="/data")


@bp.route("/")
def index():
    dataset = sd.load_dataset()
    slug = collections.get_active_slug()
    meta = collections.read_meta(slug)
    return render_template(
        "data/index.html",
        columns=dataset["columns"], rows=dataset["rows"],
        column_labels=sd.COLUMN_LABELS, standard_columns=sd.STANDARD_COLUMNS,
        supported_ext=supported_extensions(),
        identifier_field=meta.identifier_field,
        resolved_identifier_field=collections.resolve_identifier_field(slug, dataset["columns"]),
    )


@bp.route("/identifier-field", methods=["POST"])
def set_identifier_field():
    slug = collections.get_active_slug()
    value = request.form.get("identifier_field", "").strip()
    collections.update_meta(slug, identifier_field=value)
    flash("Campo identificador atualizado.", "success")
    return redirect(url_for("data_bp.index"))


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
        unlink_retry(tmp_path, missing_ok=True)

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
    files = [f for f in request.files.getlist("files") if f and f.filename]
    if not files:
        single = request.files.get("file")
        files = [single] if single and single.filename else []
    if not files:
        return jsonify({"ok": False, "error": "Nenhum arquivo enviado"}), 400
    saved = []
    try:
        for file in files:
            fname = assets_service.save_library_image(file, g.collection)
            saved.append({"filename": fname,
                          "url": url_for("data_bp.library_file", filename=fname)})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    first = saved[0]
    return jsonify({"ok": True, "files": saved, **first})


@bp.route("/library")
def library():
    files = assets_service.list_library_images(g.collection)
    dataset = sd.load_dataset()
    return jsonify([
        {"filename": f, "url": url_for("data_bp.library_file", filename=f),
         "usage_count": len(assets_service.find_image_references(dataset, f))}
        for f in files
    ])


@bp.route("/library/<path:filename>")
def library_file(filename):
    return send_from_directory(collections.library_dir(g.collection), filename)


@bp.route("/library/<path:filename>/replace", methods=["POST"])
def library_replace(filename):
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"ok": False, "error": "Nenhum arquivo enviado"}), 400
    try:
        saved = assets_service.replace_library_image(file, g.collection, filename)
    except FileNotFoundError:
        return jsonify({"ok": False, "error": "Imagem não encontrada."}), 404
    except (ValueError, OSError) as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    return jsonify({"ok": True, "filename": saved,
                    "url": url_for("data_bp.library_file", filename=saved)})


@bp.route("/library/<path:filename>/rename", methods=["POST"])
def library_rename(filename):
    payload = request.get_json(force=True, silent=True) or {}
    requested = (payload.get("name") or "").strip()
    if not requested:
        return jsonify({"ok": False, "error": "Informe o novo nome."}), 400
    dataset = sd.load_dataset()
    try:
        new_name = assets_service.rename_library_image(g.collection, filename, requested)
        updated = assets_service.rename_image_references(dataset, filename, new_name)
        if updated:
            sd.save_dataset(dataset.get("columns") or [], dataset.get("rows") or [])
    except FileNotFoundError:
        return jsonify({"ok": False, "error": "Imagem não encontrada."}), 404
    except (ValueError, OSError) as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    return jsonify({"ok": True, "filename": new_name, "updated_references": updated})


@bp.route("/library/<path:filename>/usage")
def library_usage(filename):
    references = assets_service.find_image_references(sd.load_dataset(), filename)
    return jsonify({"ok": True, "filename": filename, "count": len(references),
                    "references": references})


@bp.route("/library/<path:filename>/delete", methods=["POST"])
def library_delete(filename):
    dataset = sd.load_dataset()
    references = assets_service.find_image_references(dataset, filename)
    payload = request.get_json(force=True, silent=True) or {}
    if references and not payload.get("confirmed"):
        return jsonify({"ok": False, "requires_confirmation": True,
                        "usage_count": len(references)}), 409
    try:
        assets_service.delete_library_image(g.collection, filename)
    except FileNotFoundError:
        return jsonify({"ok": False, "error": "Imagem não encontrada."}), 404
    except (ValueError, OSError) as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    return jsonify({"ok": True, "usage_count": len(references)})
