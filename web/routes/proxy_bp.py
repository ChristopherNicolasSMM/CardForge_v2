"""Tela de Proxy: monta folha de impressão (A4/A3/Letter) com marcas de corte e verso."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from flask import (Blueprint, render_template, request, redirect, url_for,
                    flash, send_from_directory, abort)

from core.template.loader import load_template, list_templates, template_dir
from core.render.preview_renderer import PreviewRenderer
from core.proxy.sheet_composer import ProxyConfig, compose_proxy, save_pdf, PAGE_FORMATS
from core.fsutil import unlink_retry
from web.services import session_data as sd
from web.services import proxy_quantities as pq
from web.services import collections
from web.services import template_assignment as ta

bp = Blueprint("proxy_bp", __name__, url_prefix="/proxy")


@bp.route("/")
def index():
    dataset = sd.load_dataset()
    all_rows = dataset["rows"]
    templates = list_templates()
    back_image = None
    selected = request.args.get("template")
    if selected in templates:
        try:
            back_image = load_template(selected).back_image
        except Exception:
            back_image = None
    proxies = _list_proxies()
    slug = collections.get_active_slug()
    id_field = collections.resolve_identifier_field(slug, dataset.get("columns", []))

    # Se a coleção mistura linhas de mais de um template no mesmo dataset,
    # a folha de proxy só pode montar cards do template selecionado — filtra
    # aqui (mesma regra do Gerar, ver web/services/template_assignment.py).
    assignment = ta.analyze(all_rows, selected or "", templates, id_field) if selected else None
    using_template_field = bool(assignment and assignment.using_field)
    rows = assignment.matching if using_template_field else all_rows

    quantities = pq.quantities_for_rows(slug, rows, id_field)
    return render_template(
        "proxy/index.html",
        # row_count = tamanho do dataset inteiro (só decide se mostra a tela
        # "não há cards ainda"); rows = já filtrado pelo template selecionado,
        # é o que preenche a tabela de quantidades.
        templates=templates, row_count=len(all_rows), rows=rows, quantities=quantities,
        id_field=id_field,
        page_formats=list(PAGE_FORMATS.keys()), selected=selected,
        back_image=back_image, proxies=proxies,
        assignment=assignment, using_template_field=using_template_field,
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
    all_rows = dataset["rows"]
    template_name = request.form.get("template")
    force_partial = bool(request.form.get("force_partial"))

    if not template_name:
        flash("Escolha um template.", "error")
        return redirect(url_for("proxy_bp.index"))
    if not all_rows:
        flash("Não há cards nos Dados para montar a folha.", "error")
        return redirect(url_for("proxy_bp.index"))

    try:
        t = load_template(template_name)
    except FileNotFoundError:
        flash("Template não encontrado.", "error")
        return redirect(url_for("proxy_bp.index"))

    slug_for_check = collections.get_active_slug()
    id_field_for_check = collections.resolve_identifier_field(slug_for_check, dataset.get("columns", []))
    assignment = ta.analyze(all_rows, template_name, list_templates(), id_field_for_check)

    if assignment.using_field and assignment.problem_count and not force_partial:
        parts = []
        if assignment.missing:
            parts.append(f"{len(assignment.missing)} card(s) sem _template definido")
        if assignment.invalid:
            parts.append(f"{len(assignment.invalid)} card(s) apontando pra um template inexistente")
        flash(
            " e ".join(parts) + ". Marque \"gerar mesmo assim\" pra ignorar essas linhas, "
            "ou corrija a coluna _template nos Dados antes de montar a folha.",
            "error",
        )
        return redirect(url_for("proxy_bp.index", template=template_name))

    rows = assignment.matching if assignment.using_field else all_rows
    if not rows:
        flash(f"Nenhum card está associado ao template “{template_name}” (coluna _template).", "error")
        return redirect(url_for("proxy_bp.index", template=template_name))

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

    # Quantidade por carta: lê os campos qty_<índice> do formulário (um por
    # linha do dataset, na mesma ordem em que a página foi renderizada).
    # Linha ausente do formulário (não deveria acontecer) cai em 1, mesmo
    # padrão de sempre.
    print_mode = request.form.get("print_mode", "custom")  # "custom" | "full_sheet"
    slug = collections.get_active_slug()
    id_field = collections.resolve_identifier_field(slug, dataset.get("columns", []))
    quantities: dict[str, int] = {}
    for i, row in enumerate(rows):
        raw = request.form.get(f"qty_{i}", "1")
        try:
            qty = max(0, int(raw))
        except ValueError:
            qty = 1
        quantities[pq.row_key(row, i, id_field)] = qty
    pq.save(slug, quantities)

    renderer = PreviewRenderer(t, tdir, preview_dpi=t.dimensions.dpi)
    cards_per_page = cfg.cols * cfg.rows

    card_images = []
    for i, row in enumerate(rows):
        qty = quantities.get(pq.row_key(row, i, id_field), 1)
        if qty <= 0:
            continue
        img = renderer.render(row, row.get("color", "colorless"))
        if print_mode == "full_sheet":
            # Ignora a quantidade digitada -- cada carta selecionada enche
            # uma folha inteira sozinha (decisão confirmada com o usuário:
            # só as marcadas entram, não o dataset inteiro).
            card_images.extend([img] * cards_per_page)
        else:
            card_images.extend([img] * qty)

    if not card_images:
        flash("Nenhuma carta selecionada (todas as quantidades estão em 0).", "error")
        return redirect(url_for("proxy_bp.index"))

    back_override = request.files.get("back_image_file")
    back_source = None
    if back_override and back_override.filename:
        back_source = tdir / f"__proxy_back_override__{back_override.filename}"
        back_override.save(back_source)
    elif t.back_image:
        candidate = tdir / t.back_image
        if candidate.exists():
            back_source = candidate

    pages = compose_proxy(card_images, cfg, back_source=back_source)

    if back_source and back_source.name.startswith("__proxy_back_override__"):
        unlink_retry(back_source, missing_ok=True)

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
        unlink_retry(target)
        flash(f"PDF “{filename}” excluído.", "success")
    else:
        flash("Arquivo não encontrado.", "error")
    return redirect(url_for("proxy_bp.index"))
