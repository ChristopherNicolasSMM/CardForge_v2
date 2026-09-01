"""
Wiki / manuais — renderiza os arquivos .md de docs/ como páginas navegáveis
dentro do próprio CardForge, sem depender de nada externo (GitHub, etc.).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import markdown as md_lib
from flask import Blueprint, render_template, abort, redirect, url_for

from web.config import DOCS_DIR

bp = Blueprint("wiki_bp", __name__, url_prefix="/wiki")

SLUG_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")


@dataclass
class DocEntry:
    slug: str
    title: str


def _title_from_markdown(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return fallback


def list_docs() -> list[DocEntry]:
    """Lista os manuais disponíveis, ordenados pelo prefixo numérico do arquivo."""
    entries = []
    for path in sorted(DOCS_DIR.glob("*.md")):
        slug = path.stem
        text = path.read_text(encoding="utf-8")
        pretty_fallback = re.sub(r"^\d+-", "", slug).replace("-", " ").capitalize()
        title = _title_from_markdown(text, pretty_fallback)
        entries.append(DocEntry(slug=slug, title=title))
    return entries


@bp.route("/")
def index():
    docs = list_docs()
    if not docs:
        return render_template("wiki/empty.html")
    return redirect(url_for("wiki_bp.page", slug=docs[0].slug))


@bp.route("/<slug>")
def page(slug):
    if not SLUG_RE.match(slug):
        abort(404)
    path = DOCS_DIR / f"{slug}.md"
    if not path.exists():
        abort(404)

    docs = list_docs()
    text = path.read_text(encoding="utf-8")

    current = next((d for d in docs if d.slug == slug), None)
    title = current.title if current else slug

    # O título já aparece no cabeçalho da página — remove o "# Título" do corpo
    # pra não duplicar, mantendo o resto do conteúdo intacto.
    body_lines = text.splitlines()
    for i, line in enumerate(body_lines):
        if line.strip().startswith("# "):
            del body_lines[i]
            break
    body = "\n".join(body_lines)

    converter = md_lib.Markdown(
        extensions=["fenced_code", "tables", "toc", "sane_lists", "attr_list"],
        extension_configs={"toc": {"anchorlink": False}},
    )
    html = converter.convert(body)
    toc_tokens = converter.toc_tokens

    return render_template(
        "wiki/page.html",
        docs=docs, slug=slug, title=title, content=html, toc=toc_tokens,
    )
