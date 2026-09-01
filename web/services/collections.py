"""
Coleções — a unidade organizadora do CardForge.

Cada coleção representa um jogo (ou uma atualização/expansão de um jogo) e é
uma pasta própria e autocontida em collections/<slug>/:

  collections/<slug>/
    collection.json      ← nome, descrição, jogo, quando foi criada/mudou
    templates/<nome>/     ← os modelos de card dessa coleção
    assets/library/        ← imagens de arte enviadas nessa coleção
    assets/fonts_custom/    ← fontes .ttf enviadas nessa coleção
    data.json               ← o dataset de cards em edição
    output/                 ← lotes gerados + PDFs de proxy

Templates, dados, fontes e artes de uma coleção NUNCA se misturam com os de
outra — cada uma é isolada em disco. A única ponte entre coleções é a
importação explícita de um template (ver import_template).
"""
from __future__ import annotations

import json
import re
import shutil
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from flask import session

from web.config import COLLECTIONS_DIR, TEMPLATES_DIR, LIBRARY_DIR, CUSTOM_FONTS_DIR, INSTANCE_DIR

LEGACY_SLUG = "geral"
SESSION_KEY = "active_collection"


@dataclass
class CollectionMeta:
    slug: str
    name: str
    description: str = ""
    game: str = ""
    based_on: str | None = None
    created_at: float = 0.0
    updated_at: float = 0.0
    template_count: int = 0
    row_count: int = 0


# ── Slug / caminhos ──────────────────────────────────────────────────────────

def slugify(name: str) -> str:
    norm = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    norm = re.sub(r"[^\w\s-]", "", norm).strip().lower()
    norm = re.sub(r"[\s_]+", "-", norm)
    norm = re.sub(r"-+", "-", norm).strip("-")
    return norm or f"colecao-{int(time.time())}"


def collection_dir(slug: str) -> Path:
    return COLLECTIONS_DIR / slug


def templates_dir(slug: str) -> Path:
    d = collection_dir(slug) / "templates"
    d.mkdir(parents=True, exist_ok=True)
    return d


def library_dir(slug: str) -> Path:
    d = collection_dir(slug) / "assets" / "library"
    d.mkdir(parents=True, exist_ok=True)
    return d


def custom_fonts_dir(slug: str) -> Path:
    d = collection_dir(slug) / "assets" / "fonts_custom"
    d.mkdir(parents=True, exist_ok=True)
    return d


def output_dir(slug: str) -> Path:
    d = collection_dir(slug) / "output"
    d.mkdir(parents=True, exist_ok=True)
    return d


def data_path(slug: str) -> Path:
    return collection_dir(slug) / "data.json"


def _meta_path(slug: str) -> Path:
    return collection_dir(slug) / "collection.json"


# ── CRUD ─────────────────────────────────────────────────────────────────────

def exists(slug: str) -> bool:
    return _meta_path(slug).exists()


def read_meta(slug: str) -> CollectionMeta:
    p = _meta_path(slug)
    raw = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    from core.template.loader import set_templates_root, reset_templates_root, list_templates
    token = set_templates_root(templates_dir(slug))
    try:
        tcount = len(list_templates())
    finally:
        reset_templates_root(token)
    dp = data_path(slug)
    rcount = 0
    if dp.exists():
        try:
            rcount = len(json.loads(dp.read_text(encoding="utf-8")).get("rows", []))
        except Exception:
            rcount = 0
    return CollectionMeta(
        slug=slug,
        name=raw.get("name", slug),
        description=raw.get("description", ""),
        game=raw.get("game", ""),
        based_on=raw.get("based_on"),
        created_at=raw.get("created_at", 0.0),
        updated_at=raw.get("updated_at", 0.0),
        template_count=tcount,
        row_count=rcount,
    )


def list_collections() -> list[CollectionMeta]:
    if not COLLECTIONS_DIR.exists():
        return []
    slugs = sorted(
        (d.name for d in COLLECTIONS_DIR.iterdir() if d.is_dir() and (d / "collection.json").exists()),
    )
    metas = [read_meta(s) for s in slugs]
    return sorted(metas, key=lambda m: m.updated_at, reverse=True)


def create_collection(name: str, description: str = "", game: str = "",
                       based_on: str | None = None) -> str:
    slug = slugify(name)
    base_slug = slug
    n = 2
    while exists(slug):
        slug = f"{base_slug}-{n}"
        n += 1
    d = collection_dir(slug)
    d.mkdir(parents=True, exist_ok=True)
    (d / "templates").mkdir(exist_ok=True)
    (d / "assets" / "library").mkdir(parents=True, exist_ok=True)
    (d / "assets" / "fonts_custom").mkdir(parents=True, exist_ok=True)
    (d / "output").mkdir(exist_ok=True)
    now = time.time()
    _meta_path(slug).write_text(json.dumps({
        "name": name, "description": description, "game": game,
        "based_on": based_on, "created_at": now, "updated_at": now,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return slug


def update_meta(slug: str, **fields) -> None:
    p = _meta_path(slug)
    raw = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    raw.update(fields)
    raw["updated_at"] = time.time()
    p.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")


def delete_collection(slug: str) -> None:
    d = collection_dir(slug)
    if d.exists():
        shutil.rmtree(d)


def duplicate_collection(src_slug: str, new_name: str,
                          include_templates: bool = True,
                          include_assets: bool = True,
                          include_data: bool = False) -> str:
    """Duplica uma coleção. O que copiar é escolhido na hora (ex: uma
    'atualização de jogo' geralmente quer templates+fontes, mas dados zerados)."""
    src = collection_dir(src_slug)
    new_slug = create_collection(new_name, game=read_meta(src_slug).game, based_on=src_slug)
    dst = collection_dir(new_slug)

    if include_templates and (src / "templates").exists():
        shutil.rmtree(dst / "templates", ignore_errors=True)
        shutil.copytree(src / "templates", dst / "templates")
    if include_assets:
        for sub in ("library", "fonts_custom"):
            src_sub = src / "assets" / sub
            if src_sub.exists():
                shutil.rmtree(dst / "assets" / sub, ignore_errors=True)
                shutil.copytree(src_sub, dst / "assets" / sub)
    if include_data and (src / "data.json").exists():
        shutil.copy2(src / "data.json", dst / "data.json")

    return new_slug


def import_template(dest_slug: str, src_slug: str, template_name: str,
                     new_name: str | None = None) -> str:
    """Copia um template de outra coleção pra dentro da coleção de destino."""
    src_path = templates_dir(src_slug) / template_name
    if not src_path.exists():
        raise FileNotFoundError(f"Template '{template_name}' não encontrado na coleção '{src_slug}'")
    target_name = new_name or template_name
    dst_path = templates_dir(dest_slug) / target_name
    n = 2
    base_target = target_name
    while dst_path.exists():
        target_name = f"{base_target}-{n}"
        dst_path = templates_dir(dest_slug) / target_name
        n += 1
    shutil.copytree(src_path, dst_path)
    # Ajusta o nome dentro do base.json copiado
    raw_path = dst_path / "base.json"
    if raw_path.exists():
        data = json.loads(raw_path.read_text(encoding="utf-8"))
        data.setdefault("meta", {})["name"] = target_name
        raw_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return target_name


# ── Coleção ativa (por sessão de navegador) ──────────────────────────────────

def get_active_slug() -> str | None:
    slug = session.get(SESSION_KEY)
    if slug and exists(slug):
        return slug
    return None


def set_active_slug(slug: str) -> None:
    session[SESSION_KEY] = slug


def clear_active_slug() -> None:
    session.pop(SESSION_KEY, None)


# ── Migração de projetos pré-coleções ────────────────────────────────────────

def migrate_legacy_if_needed() -> None:
    """
    Se o projeto tem templates/assets no formato antigo (pré-coleções, direto
    na raiz) e ainda não existe nenhuma coleção, cria automaticamente uma
    coleção "Geral" e move tudo pra dentro dela. Roda uma única vez — depois
    da migração, essa função não encontra mais nada pra migrar e não faz nada.
    """
    if exists(LEGACY_SLUG):
        return
    has_legacy_templates = TEMPLATES_DIR.exists() and any(TEMPLATES_DIR.iterdir())
    has_legacy_assets = (
        (LIBRARY_DIR.exists() and any(LIBRARY_DIR.iterdir())) or
        (CUSTOM_FONTS_DIR.exists() and any(CUSTOM_FONTS_DIR.iterdir()))
    )
    if not (has_legacy_templates or has_legacy_assets):
        return

    slug = create_collection(
        "Geral",
        description="Coleção criada automaticamente com os templates e assets "
                     "que já existiam no projeto antes do sistema de coleções.",
    )
    dst = collection_dir(slug)

    if has_legacy_templates:
        shutil.rmtree(dst / "templates", ignore_errors=True)
        shutil.copytree(TEMPLATES_DIR, dst / "templates")
    if LIBRARY_DIR.exists() and any(LIBRARY_DIR.iterdir()):
        shutil.rmtree(dst / "assets" / "library", ignore_errors=True)
        shutil.copytree(LIBRARY_DIR, dst / "assets" / "library")
    if CUSTOM_FONTS_DIR.exists() and any(CUSTOM_FONTS_DIR.iterdir()):
        shutil.rmtree(dst / "assets" / "fonts_custom", ignore_errors=True)
        shutil.copytree(CUSTOM_FONTS_DIR, dst / "assets" / "fonts_custom")

    # Dataset legado (se havia alguma sessão antiga com dados) — pega a mais
    # recente, se existir, só por conveniência; não é crítico.
    if INSTANCE_DIR.exists():
        candidates = sorted(INSTANCE_DIR.glob("*/data.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if candidates:
            shutil.copy2(candidates[0], dst / "data.json")
