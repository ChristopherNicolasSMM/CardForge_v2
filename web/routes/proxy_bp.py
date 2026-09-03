"""Tela de Proxy: monta folha de impressão (A4/A3/Letter) com marcas de corte e verso."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from flask import (Blueprint, render_template, request, redirect, url_for,
                    flash, send_from_directory, abort)

from core.template.loader import load_template, list_templates, template_dir
from core.render.preview_renderer import PreviewRenderer
from core.proxy.sheet_composer import ProxyConfig, compose_proxy, save_pdf, PAGE_FORMATS
from web.services import session_data as sd

bp = Blueprint("proxy_bp", __name__, url_prefix="/proxy")


@bp.route("/")
def index():
    dataset = sd.load_dataset()
    templates = list_templates()
    back_image = None
    selected = request.args.get("template")
    if selected in templates:
        try:
            back_image = load_template(selected).back_image
        except Exception:
            back_image = None
    proxies = _list_proxies()
    return render_template(
        "proxy/index.html",
        templates=templates, row_count=len(dataset["rows"]),
        page_formats=list(PAGE_FORMATS.keys()), selected=selected,
        back_image=back_image, proxies=proxies,
    )


@bp.route("/back-image/<path:name>")
def back_image_preview(name):
    try:
        t = load_template(name)
    except FileNotFoundError:
        abort(404)
    if not t.back_image:
        abort(404)
    return send_from_directory(template_dir(name), t.back_image)


@bp.route("/run", methods=["POST"])
def run():
    dataset = sd.load_dataset()
    rows = dataset["rows"]
    template_name = request.form.get("template")

    if not template_name:
        flash("Escolha um template.", "error")
        return redirect(url_for("proxy_bp.index"))
    if not rows:
        flash("Não há cards nos Dados para montar a folha.", "error")
        return redirect(url_for("proxy_bp.index"))

    try:
        t = load_template(template_name)
    except FileNotFoundError:
        flash("Template não encontrado.", "error")
        return redirect(url_for("proxy_bp.index"))

    tdir = template_dir(template_name)
    cfg = ProxyConfig(
        page_format=request.form.get("page_format", "A4"),
        cols=int(request.form.get("cols", 3)),
        rows=int(request.form.get("rows", 3)),
        margin_mm=float(request.form.get("margin_mm", 10.0)),
        gap_mm=float(request.form.get("gap_mm", 2.0)),
        crop_marks=bool(request.form.get("crop_marks")),
        crop_mark_mm=float(request.form.get("crop_mark_mm", 3.0)),
        include_back=bool(request.form.get("include_back")),
        back_image=t.back_image or "",
    )

    back_override = request.files.get("back_image_file")
    back_source = None
    if back_override and back_override.filename:
        back_source = tdir / f"__proxy_back_override__{back_override.filename}"
        back_override.save(back_source)
    elif t.back_image:
        candidate = tdir / t.back_image
        if candidate.exists():
            back_source = candidate

    renderer = PreviewRenderer(t, tdir, preview_dpi=t.dimensions.dpi)
    card_images = [renderer.render(row, row.get("color", "colorless")) for row in rows]

    pages = compose_proxy(card_images, cfg, back_source=back_source)

    if back_source and back_source.name.startswith("__proxy_back_override__"):
        back_source.unlink(missing_ok=True)

    proxy_dir = sd.output_dir() / "proxy"
    proxy_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%d%m%Y_%H%M%S")
    filename = f"{template_name}-proxy-{stamp}.pdf"
    save_pdf(pages, proxy_dir / filename)

    flash(f"Folha de proxy gerada: {len(pages)} página(s).", "success")
    return redirect(url_for("proxy_bp.index", generated=filename))


def _list_proxies():
    proxy_dir = sd.output_dir() / "proxy"
    if not proxy_dir.exists():
        return []
    return sorted((p.name for p in proxy_dir.glob("*.pdf")), reverse=True)


@bp.route("/download/<path:filename>")
def download(filename):
    proxy_dir = sd.output_dir() / "proxy"
    return send_from_directory(proxy_dir, filename, as_attachment=True)


@bp.route("/delete/<path:filename>", methods=["POST"])
def delete(filename):
    proxy_dir = sd.output_dir() / "proxy"
    target = proxy_dir / filename
    try:
        target.resolve().relative_to(proxy_dir.resolve())
    except ValueError:
        abort(404)
    if target.exists() and target.is_file():
        target.unlink()
        flash(f"PDF “{filename}” excluído.", "success")
    else:
        flash("Arquivo não encontrado.", "error")
    return redirect(url_for("proxy_bp.index"))
