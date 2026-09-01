"""Coleções — criar, escolher, duplicar ('atualização de jogo') e excluir."""
from __future__ import annotations

from flask import Blueprint, render_template, request, redirect, url_for, flash, g

from web.services import collections

bp = Blueprint("collections_bp", __name__, url_prefix="/collections")


@bp.route("/")
def index():
    items = collections.list_collections()
    return render_template("collections/index.html", items=items, active=g.collection)


@bp.route("/new", methods=["GET", "POST"])
def new():
    if request.method == "GET":
        return render_template("collections/new.html")

    name = (request.form.get("name") or "").strip()
    description = (request.form.get("description") or "").strip()
    game = (request.form.get("game") or "").strip()
    if not name:
        flash("Dê um nome à coleção.", "error")
        return redirect(url_for("collections_bp.new"))

    slug = collections.create_collection(name, description=description, game=game)
    collections.set_active_slug(slug)
    flash(f"Coleção “{name}” criada e selecionada.", "success")
    return redirect(url_for("main.hub"))


@bp.route("/<slug>/select", methods=["POST"])
def select(slug):
    if not collections.exists(slug):
        flash("Coleção não encontrada.", "error")
        return redirect(url_for("collections_bp.index"))
    collections.set_active_slug(slug)
    flash(f"Coleção “{collections.read_meta(slug).name}” selecionada.", "success")
    return redirect(url_for("main.hub"))


@bp.route("/<slug>/edit", methods=["GET", "POST"])
def edit(slug):
    if not collections.exists(slug):
        flash("Coleção não encontrada.", "error")
        return redirect(url_for("collections_bp.index"))

    if request.method == "GET":
        meta = collections.read_meta(slug)
        return render_template("collections/edit.html", meta=meta)

    name = (request.form.get("name") or "").strip()
    description = (request.form.get("description") or "").strip()
    game = (request.form.get("game") or "").strip()
    if not name:
        flash("Dê um nome à coleção.", "error")
        return redirect(url_for("collections_bp.edit", slug=slug))
    collections.update_meta(slug, name=name, description=description, game=game)
    flash("Coleção atualizada.", "success")
    return redirect(url_for("collections_bp.index"))


@bp.route("/<slug>/duplicate", methods=["GET", "POST"])
def duplicate(slug):
    if not collections.exists(slug):
        flash("Coleção não encontrada.", "error")
        return redirect(url_for("collections_bp.index"))

    if request.method == "GET":
        meta = collections.read_meta(slug)
        return render_template("collections/duplicate.html", meta=meta)

    new_name = (request.form.get("new_name") or "").strip()
    if not new_name:
        flash("Dê um nome à nova coleção.", "error")
        return redirect(url_for("collections_bp.duplicate", slug=slug))

    new_slug = collections.duplicate_collection(
        slug, new_name,
        include_templates="include_templates" in request.form,
        include_assets="include_assets" in request.form,
        include_data="include_data" in request.form,
    )
    collections.set_active_slug(new_slug)
    flash(f"Coleção “{new_name}” criada a partir de “{collections.read_meta(slug).name}”.", "success")
    return redirect(url_for("main.hub"))


@bp.route("/<slug>/delete", methods=["POST"])
def delete(slug):
    if not collections.exists(slug):
        flash("Coleção não encontrada.", "error")
        return redirect(url_for("collections_bp.index"))
    name = collections.read_meta(slug).name
    collections.delete_collection(slug)
    if g.collection == slug:
        collections.clear_active_slug()
    flash(f"Coleção “{name}” excluída.", "success")
    return redirect(url_for("collections_bp.index"))
