"""Upload e listagem de assets: imagens de arte/fundo e fontes customizadas.

Tudo aqui é escopado pela coleção ativa — a biblioteca de imagens e as fontes
customizadas de uma coleção não aparecem em outra."""
from __future__ import annotations

import re
from pathlib import Path

from werkzeug.datastructures import FileStorage

from web.services import collections
from core.render.font_paths import list_available_fonts
from core.asset_paths import normalize_asset_reference

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
FONT_EXTS = {".ttf"}


def _safe_stem(name: str) -> str:
    stem = Path(name).stem
    stem = re.sub(r"[^\w\-]+", "_", stem).strip("_") or "arquivo"
    return stem


def _library_relative_path(collection_slug: str, reference: str, *, allow_directory: bool = False) -> tuple[Path, str]:
    normalized = normalize_asset_reference(reference)
    if not normalized:
        if allow_directory and not str(reference or "").strip():
            return collections.library_dir(collection_slug), ""
        raise ValueError("Caminho inválido.")
    root = collections.library_dir(collection_slug).resolve()
    path = (root / Path(*normalized.split("/"))).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        raise ValueError("Caminho inválido.")
    return path, normalized


def save_library_image(file: FileStorage, collection_slug: str, folder: str = "") -> str:
    """Salva imagem na biblioteca da coleção. Retorna o nome do arquivo salvo."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in IMAGE_EXTS:
        raise ValueError(f"Formato de imagem não suportado: {ext or '(sem extensão)'}")
    lib, folder_ref = _library_relative_path(collection_slug, folder, allow_directory=True)
    lib.mkdir(parents=True, exist_ok=True)
    stem = _safe_stem(file.filename)
    fname = f"{stem}{ext}"
    number = 2
    while (lib / fname).exists():
        fname = f"{stem}-{number}{ext}"
        number += 1
    dest = lib / fname
    file.save(dest)
    return f"{folder_ref}/{fname}" if folder_ref else fname


def list_library_images(collection_slug: str) -> list[str]:
    lib = collections.library_dir(collection_slug)
    if not lib.exists():
        return []
    return sorted(
        p.relative_to(lib).as_posix()
        for p in lib.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    )


def list_library_folders(collection_slug: str) -> list[str]:
    lib = collections.library_dir(collection_slug)
    return sorted(p.relative_to(lib).as_posix() for p in lib.rglob("*") if p.is_dir())


def create_library_folder(collection_slug: str, parent: str, name: str) -> str:
    if not str(name or "").strip():
        raise ValueError("Informe o nome da pasta.")
    safe_name = _safe_stem(name)
    parent_path, parent_ref = _library_relative_path(collection_slug, parent, allow_directory=True)
    target = parent_path / safe_name
    if target.exists():
        raise ValueError("Já existe uma pasta com esse nome.")
    target.mkdir(parents=False)
    return f"{parent_ref}/{safe_name}" if parent_ref else safe_name


def library_image_path(collection_slug: str, filename: str) -> Path:
    """Resolve somente nomes de arquivos pertencentes à biblioteca ativa."""
    path, normalized = _library_relative_path(collection_slug, filename)
    if path.suffix.lower() not in IMAGE_EXTS:
        raise ValueError("Formato de imagem não suportado.")
    return path


def replace_library_image(file: FileStorage, collection_slug: str, filename: str) -> str:
    """Substitui o conteúdo mantendo o nome/caminho já usado pelos cards."""
    target = library_image_path(collection_slug, filename)
    if not target.exists():
        raise FileNotFoundError(filename)
    source_ext = Path(file.filename or "").suffix.lower()
    if source_ext not in IMAGE_EXTS:
        raise ValueError(f"Formato de imagem não suportado: {source_ext or '(sem extensão)'}")

    # Extensões iguais podem ser copiadas sem perda. Com extensões diferentes,
    # o Pillow converte o conteúdo para o formato do nome antigo, preservando
    # tanto a URL quanto o MIME correto servido pelo Flask.
    if source_ext == target.suffix.lower() or {source_ext, target.suffix.lower()} <= {".jpg", ".jpeg"}:
        file.save(target)
    else:
        from PIL import Image
        with Image.open(file.stream) as image:
            fmt = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}[target.suffix.lower()]
            if fmt == "JPEG" and image.mode not in ("RGB", "L"):
                background = Image.new("RGB", image.size, "white")
                if image.mode == "RGBA":
                    background.paste(image, mask=image.getchannel("A"))
                else:
                    background.paste(image.convert("RGB"))
                image = background
            image.save(target, fmt)
    return target.name


def image_reference_matches(value: object, filename: str) -> bool:
    """Reconhece o nome canônico e referências legadas library/imgs com barras mistas."""
    normalized = normalize_asset_reference(value)
    if not normalized:
        return False
    target = normalize_asset_reference(filename)
    if not target:
        return False
    if normalized == target:
        return True
    return normalized in {f"assets/library/{target}", f"library/{target}", f"imgs/{target}"}


def find_image_references(dataset: dict, filename: str) -> list[dict]:
    matches = []
    for row_index, row in enumerate(dataset.get("rows") or []):
        for field, value in row.items():
            if image_reference_matches(value, filename):
                matches.append({"row": row_index, "field": field})
    return matches


def rename_image_references(dataset: dict, old_name: str, new_name: str) -> int:
    changed = 0
    for row in dataset.get("rows") or []:
        for field, value in list(row.items()):
            if image_reference_matches(value, old_name):
                row[field] = new_name
                changed += 1
    return changed


def rename_library_image(collection_slug: str, old_name: str, requested_name: str) -> str:
    source = library_image_path(collection_slug, old_name)
    if not source.exists():
        raise FileNotFoundError(old_name)
    old_ref = normalize_asset_reference(old_name)
    old_parent = old_ref.rsplit("/", 1)[0] if "/" in old_ref else ""
    requested = Path(requested_name.strip()).name
    stem = _safe_stem(requested)
    requested_ext = Path(requested).suffix.lower()
    if requested_ext and requested_ext != source.suffix.lower():
        raise ValueError("Para renomear, mantenha a extensão original da imagem.")
    basename = f"{stem}{source.suffix.lower()}"
    new_name = f"{old_parent}/{basename}" if old_parent else basename
    target = library_image_path(collection_slug, new_name)
    if target != source and target.exists():
        raise ValueError("Já existe uma imagem com esse nome.")
    source.rename(target)
    return new_name


def move_library_image(collection_slug: str, filename: str, folder: str) -> str:
    source = library_image_path(collection_slug, filename)
    if not source.exists():
        raise FileNotFoundError(filename)
    folder_path, folder_ref = _library_relative_path(collection_slug, folder, allow_directory=True)
    if not folder_path.is_dir():
        raise ValueError("Pasta de destino não encontrada.")
    new_name = f"{folder_ref}/{source.name}" if folder_ref else source.name
    target = library_image_path(collection_slug, new_name)
    if target != source and target.exists():
        raise ValueError("Já existe uma imagem com esse nome na pasta de destino.")
    source.rename(target)
    return new_name


def delete_library_image(collection_slug: str, filename: str) -> None:
    path = library_image_path(collection_slug, filename)
    if not path.exists():
        raise FileNotFoundError(filename)
    path.unlink()


def save_font(file: FileStorage, collection_slug: str, template_dir: Path | None = None) -> str:
    """
    Salva uma fonte .ttf.
    Se template_dir for informado, a fonte fica específica daquele template
    (templates/<nome>/fonts/); senão vai para a biblioteca de fontes da coleção.
    Retorna o nome da família (sem extensão) para usar em font_family.
    """
    ext = Path(file.filename or "").suffix.lower()
    if ext not in FONT_EXTS:
        raise ValueError("Envie um arquivo .ttf")
    family = _safe_stem(file.filename)
    target_dir = Path(template_dir) / "fonts" if template_dir else collections.custom_fonts_dir(collection_slug)
    target_dir.mkdir(parents=True, exist_ok=True)
    file.save(target_dir / f"{family}.ttf")
    return family


def all_font_choices(template_dir: Path | None = None) -> list[str]:
    return list_available_fonts(template_dir)
