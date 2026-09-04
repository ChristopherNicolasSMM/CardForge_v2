#!/usr/bin/env python3
"""
CardForge 2.0 — lançador do executável empacotado (PyInstaller).

Diferenças em relação a `run.py` (usado ao rodar a partir do código-fonte):
  - nunca liga debug/reloader do Flask (o reloader re-executa o processo
    via sys.argv, o que quebra dentro de um binário congelado)
  - escolhe uma porta livre automaticamente, em vez de assumir 5000 fixo
  - abre o navegador padrão sozinho, pro usuário não-dev não precisar
    saber que existe um endereço pra digitar
  - imprime onde os dados desta instalação estão gravados (útil pra quem
    for fazer backup ou mover a pasta)

Ver docs/tech/doc-tecnico-executavel.md para o desenho completo.
"""
from __future__ import annotations

import socket
import sys
import threading
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.paths import data_root  # noqa: E402


def _find_free_port(preferred: int = 5000) -> int:
    """Tenta a porta preferida primeiro (comportamento familiar pra quem já
    usa o CardForge a partir do código-fonte); se estiver ocupada, tenta
    algumas seguintes; por fim deixa o sistema operacional escolher
    qualquer porta livre."""
    candidates = [preferred, *range(preferred + 1, preferred + 11)]
    for port in candidates:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main() -> None:
    from web import create_app
    app = create_app()

    port = _find_free_port()
    url = f"http://127.0.0.1:{port}/"

    print("=" * 60)
    print("CardForge 2.0")
    print(f"Dados desta instalação: {data_root()}")
    print(f"Abrindo {url} no navegador...")
    print("Feche esta janela para encerrar o CardForge.")
    print("=" * 60)

    threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
