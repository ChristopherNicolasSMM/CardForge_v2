"""
Utilitários de exclusão de arquivo/pasta resilientes a bloqueios
transitórios do Windows (antivírus, indexação do Explorer, ou um handle
que a própria aplicação ainda não liberou — ex: uma fonte carregada pelo
PIL/FreeType em cache, ou uma imagem PNG ainda referenciada).

Extraído de web/services/collections.py, que já tinha essa mesma lógica
(retry + liberar cache de fontes + garbage collect entre tentativas) só
para exclusão de coleção inteira. Generalizado aqui depois de um
PermissionError real reportado em produção (Windows) ao excluir um lote
de cards gerado — o mesmo problema existia, sem proteção nenhuma, em
outros pontos que apagam arquivo/pasta (lotes de geração, cards
individuais, templates, PDFs de proxy). Ver
docs/tech/doc-tecnico-exclusao-resiliente.md.
"""
from __future__ import annotations

import gc
import shutil
import stat
import time
from pathlib import Path


def _release_caches() -> None:
    """Libera referências que a própria aplicação pode estar segurando
    (ex: fontes em cache do renderer) antes de tentar de novo — é
    justamente esse tipo de handle "esquecido" que costuma ser a causa
    real do bloqueio no Windows, não o SO por si só."""
    try:
        from core.render.preview_renderer import clear_font_cache
        clear_font_cache()
    except Exception:
        pass
    gc.collect()


def rmtree_retry(path: Path, attempts: int = 5, delay_s: float = 0.3) -> None:
    """shutil.rmtree resiliente: tenta algumas vezes, liberando
    referências entre as tentativas, antes de desistir (aí propaga o
    último erro — não engole silenciosamente uma falha real e
    persistente, só a transitória)."""
    def _on_error(func, target, exc_info):
        # Arquivo/pasta somente-leitura: tenta destravar e refazer antes
        # de contar como falha desta tentativa.
        try:
            import os
            os.chmod(target, stat.S_IWRITE)
            func(target)
        except Exception:
            pass

    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            shutil.rmtree(path, onerror=_on_error)
            return
        except Exception as e:
            last_error = e
            _release_caches()
            time.sleep(delay_s)
    if path.exists():
        raise last_error  # type: ignore[misc]


def unlink_retry(path: Path, attempts: int = 5, delay_s: float = 0.3,
                  missing_ok: bool = False) -> None:
    """Path.unlink() resiliente ao mesmo tipo de bloqueio transitório —
    mesmo princípio do rmtree_retry, pra um arquivo só."""
    if not path.exists():
        if missing_ok:
            return
        path.unlink()  # deixa o FileNotFoundError real estourar, com a mensagem padrão
        return

    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            path.unlink()
            return
        except FileNotFoundError:
            return
        except Exception as e:
            last_error = e
            _release_caches()
            time.sleep(delay_s)
    if path.exists():
        raise last_error  # type: ignore[misc]
