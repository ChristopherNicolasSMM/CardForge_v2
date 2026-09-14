"""Galeria de templates, editor visual (canvas) e endpoints de suporte."""
from __future__ import annotations

import base64
import io
import json
from pathlib import Path

from flask import (Blueprint, render_template, request, redirect, url_for,
                    flash, send_from_directory, jsonify, abort, Response, g)

from core.template.loader import (
    load_template, save_template, create_template, delete_template,
    set_background, list_templates, template_dir,
)
from core.render.preview_renderer import PreviewRenderer
from core.render.font_paths import find_font_file
from web.services import assets as assets_service

bp = Blueprint("templates_bp", __name__, url_prefix="/templates")

# Usado apenas como último fallback, pra campos que nem a coleção ativa nem
# um card de exemplo real tiverem (ex: um template herdado do modelo padrão
# usado numa coleção com esquema totalmente diferente).
BASE_DEMO_ROW = {
    "name": "Nome do Card", "mana_cost": "2R", "type_line": "Tipo — Subtipo",
    "rules_text": "Texto de regras do card aparece aqui.",
    "flavor_text": "\u201cUma frase de sabor.\u201d",
    "power": "3", "toughness": "3", "artist": "Artista",
    "color": "red",
}


def _demo_row() -> dict:
    """Monta uma linha de exemplo pra preview/miniatura usando os campos reais
    da coleção ativa sempre que possível — assim funciona também pra jogos
    com esquema de dados totalmente diferente do padrão MTG."""
    from web.services import session_data as sd
    try:
        dataset = sd.load_dataset()
    except Exception:
        dataset = {"columns": [], "rows": []}
    columns = dataset.get("columns") or []
    rows = dataset.get("rows") or []

    if rows:
        row = dict(rows[0])  # card real: preview o mais fiel possível
    elif columns:
        row = {c: f"[{c}]" for c in columns}  # placeholder legível por campo
    else:
        row = {}

    row.setdefault("color", "colorless")
    for k, v in BASE_DEMO_ROW.items():
        row.setdefault(k, v)
    return row


# ── Galeria ──────────────────────────────────────────────────────────────────

@bp.route("/")
def gallery():
    names = list_templates()
    items = []
    for name in names:
        try:
            t = load_template(name)
            items.append({"name": name, "layers": len(t.layers),
                          "w": t.dimensions.width_mm, "h": t.dimensions.height_mm})
        except Exception as e:
            items.append({"name": name, "error": str(e)})
    return render_template("templates_ui/gallery.html", items=items)


@bp.route("/<path:name>/thumbnail.png")
def thumbnail(name):
    try:
        t = load_template(name)
        tdir = template_dir(name)
        renderer = PreviewRenderer(t, tdir, preview_dpi=110)
        demo = _demo_row()
        img = renderer.render(demo, color_key=demo.get("color", "colorless"))
    except Exception:
        abort(404)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return Response(buf.read(), mimetype="image/png")


# ── Criar / duplicar / excluir ──────────────────────────────────────────────

@bp.route("/new", methods=["GET", "POST"])
def new():
    if request.method == "GET":
        return render_template("templates_ui/new.html", parents=list_templates())

    name = (request.form.get("name") or "").strip()
    parent = (request.form.get("parent") or "").strip() or None
    if not name:
        flash("Dê um nome ao template.", "error")
        return redirect(url_for("templates_bp.new"))
    if name in list_templates():
        flash("Já existe um template com esse nome.", "error")
        return redirect(url_for("templates_bp.new"))

    t = create_template(name, background_src=None, parent=parent)

    bg_file = request.files.get("background")
    if bg_file and bg_file.filename:
        tmp_dir = template_dir(name)
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = tmp_dir / bg_file.filename
        bg_file.save(tmp_path)
        set_background(name, str(tmp_path))
        t = load_template(name)
        bg_layer = t.layer_by_id("background")
        if bg_layer:
            bg_layer.source_image = bg_file.filename
            save_template(t)

    flash(f"Template “{name}” criado.", "success")
    return redirect(url_for("templates_bp.edit", name=name))


@bp.route("/<path:name>/duplicate", methods=["POST"])
def duplicate(name):
    new_name = (request.form.get("new_name") or f"{name}-copia").strip()
    if new_name in list_templates():
        flash("Já existe um template com esse nome.", "error")
        return redirect(url_for("templates_bp.gallery"))
    try:
        t = load_template(name)
    except FileNotFoundError:
        abort(404)

    import shutil
    src_dir = template_dir(name)
    dst_dir = template_dir(new_name)
    shutil.copytree(src_dir, dst_dir)

    raw_path = dst_dir / "base.json"
    if raw_path.exists():
        data = json.loads(raw_path.read_text(encoding="utf-8"))
    else:
        data = t.to_dict()
    data.setdefault("meta", {})["name"] = new_name
    raw_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    flash(f"Template duplicado como “{new_name}”.", "success")
    return redirect(url_for("templates_bp.edit", name=new_name))


@bp.route("/<path:name>/delete", methods=["POST"])
def delete(name):
    delete_template(name)
    flash(f"Template “{name}” excluído.", "success")
    return redirect(url_for("templates_bp.gallery"))


# ── Editor ───────────────────────────────────────────────────────────────────

@bp.route("/<path:name>/edit")
def edit(name):
    try:
        t = load_template(name)
    except FileNotFoundError:
        abort(404)
    tdir = template_dir(name)
    fonts = assets_service.all_font_choices(tdir)
    from web.services import session_data as sd
    dataset_columns = sd.load_dataset().get("columns", [])
    return render_template(
        "templates_ui/editor.html",
        name=name,
        template_json=json.dumps(t.to_dict()),
        dims={"width_mm": t.dimensions.width_mm, "height_mm": t.dimensions.height_mm},
        back_image=t.back_image,
        fonts=fonts,
        gradients=sorted(t.gradients.keys()),
        parents=[p for p in list_templates() if p != name],
        demo_row=json.dumps(_demo_row()),
        dataset_columns=dataset_columns,
    )


@bp.route("/<path:name>/save", methods=["POST"])
def save(name):
    """Recebe o JSON completo do template (formato base.json) vindo do editor JS."""
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"ok": False, "error": "JSON inválido"}), 400
    data.setdefault("meta", {})["name"] = name
    folder = template_dir(name)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "base.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return jsonify({"ok": True})


@bp.route("/<path:name>/background", methods=["POST"])
def upload_background(name):
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"ok": False, "error": "Nenhum arquivo enviado"}), 400
    tdir = template_dir(name)
    tdir.mkdir(parents=True, exist_ok=True)
    tmp_path = tdir / file.filename
    file.save(tmp_path)
    filename = set_background(name, str(tmp_path))
    return jsonify({"ok": True, "filename": filename,
                     "url": url_for("templates_bp.asset", name=name, filename=filename)})


@bp.route("/<path:name>/back-image", methods=["POST"])
def upload_back_image(name):
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"ok": False, "error": "Nenhum arquivo enviado"}), 400
    try:
        t = load_template(name)
    except FileNotFoundError:
        abort(404)
    tdir = template_dir(name)
    tmp_path = tdir / file.filename
    file.save(tmp_path)
    filename = set_background(name, str(tmp_path))  # reaproveita cópia p/ pasta do template
    t.back_image = filename
    save_template(t)
    return jsonify({"ok": True, "filename": filename,
                     "url": url_for("templates_bp.asset", name=name, filename=filename)})


@bp.route("/<path:name>/layer-image", methods=["POST"])
def upload_layer_image(name):
    """Envia uma imagem fixa pra uma camada específica (tipo imagem ou fundo) —
    usada quando a camada não puxa do dataset (campo vazio) e sim mostra
    sempre a mesma imagem (ícone, selo, marca d'água etc.)."""
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"ok": False, "error": "Nenhum arquivo enviado"}), 400
    tdir = template_dir(name)
    tdir.mkdir(parents=True, exist_ok=True)
    tmp_path = tdir / file.filename
    file.save(tmp_path)
    filename = set_background(name, str(tmp_path))  # só copia o arquivo pra pasta do template
    return jsonify({"ok": True, "filename": filename,
                     "url": url_for("templates_bp.asset", name=name, filename=filename)})


@bp.route("/<path:name>/fonts", methods=["POST"])
def upload_font(name):
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"ok": False, "error": "Nenhum arquivo enviado"}), 400
    try:
        family = assets_service.save_font(file, g.collection, template_dir=template_dir(name))
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    return jsonify({"ok": True, "family": family,
                     "fonts": assets_service.all_font_choices(template_dir(name))})


@bp.route("/<path:name>/preview", methods=["POST"])
def preview(name):
    """Renderiza um card único (PNG base64) a partir do JSON do template + uma row.
    Usado tanto pelo editor (preview ao vivo) quanto pela tela de Dados."""
    payload = request.get_json(force=True, silent=True) or {}
    row = payload.get("row") or _demo_row()
    template_data = payload.get("template")

    tdir = template_dir(name)
    if template_data:
        # Constrói o template a partir do estado atual do editor (ainda não salvo em disco)
        from core.template.loader import _build
        t = _build(template_data, name, str(tdir))
    else:
        try:
            t = load_template(name)
        except FileNotFoundError:
            abort(404)

    renderer = PreviewRenderer(t, tdir, preview_dpi=180)
    img = renderer.render(row, color_key=row.get("color", "colorless"))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return jsonify({"ok": True, "image": f"data:image/png;base64,{b64}"})


@bp.route("/<path:name>/asset/<path:filename>")
def asset(name, filename):
    return send_from_directory(template_dir(name), filename)


@bp.route("/<path:name>/font/<family>.ttf")
def font_file(name, family):
    fpath = find_font_file(family, template_dir(name))
    if not fpath:
        abort(404)
    return send_from_directory(fpath.parent, fpath.name)


@bp.route("/api/list")
def api_list():
    return jsonify(list_templates())


# ── Importar template de outra coleção ──────────────────────────────────────

@bp.route("/import")
def import_form():
    from web.services import collections
    others = [c for c in collections.list_collections() if c.slug != g.collection]
    return render_template("templates_ui/import.html", others=others)


@bp.route("/import/list")
def import_list():
    """Lista os templates de outra coleção (pra popular o seletor do formulário)."""
    from web.services import collections
    from core.template.loader import set_templates_root, reset_templates_root
    src = request.args.get("collection", "")
    if not src or not collections.exists(src):
        return jsonify([])
    token = set_templates_root(collections.templates_dir(src))
    try:
        names = list_templates()
    finally:
        reset_templates_root(token)
    return jsonify(names)


@bp.route("/import", methods=["POST"])
def import_run():
    from web.services import collections
    src = request.form.get("collection", "")
    name = request.form.get("template", "")
    new_name = (request.form.get("new_name") or "").strip() or None
    if not src or not name:
        flash("Escolha a coleção de origem e o template.", "error")
        return redirect(url_for("templates_bp.import_form"))
    try:
        imported_name = collections.import_template(g.collection, src, name, new_name)
    except FileNotFoundError as e:
        flash(str(e), "error")
        return redirect(url_for("templates_bp.import_form"))
    flash(f"Template “{imported_name}” importado de “{src}”.", "success")
    return redirect(url_for("templates_bp.edit", name=imported_name))
