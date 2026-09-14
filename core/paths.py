"""
Resolução central de caminhos "raiz" da aplicação — o único lugar que
sabe a diferença entre rodar a partir do código-fonte (`python run.py`)
e rodar como executável empacotado (PyInstaller).

Duas raízes, propósitos diferentes:

- `resource_root()` — onde estão os recursos **read-only** empacotados
  com o app: fontes embutidas, ícones de mana, templates/estáticos do
  Flask, manuais (docs/). Em execução normal, é a raiz do repositório.
  Empacotado, é a pasta interna do PyInstaller (`sys._MEIPASS` em
  --onefile, ou a pasta ao lado do executável em --onedir — o
  PyInstaller expõe os dois casos através do mesmo atributo).

- `data_root()` — onde ficam os **dados do usuário**, sempre graváveis:
  coleções, cards gerados, uploads. Em execução normal, é a mesma raiz
  do repositório (comportamento de sempre, sem mudança). Empacotado, é
  **sempre a pasta ao lado do executável** — nunca a pasta temporária de
  extração do PyInstaller, que é apagada/recriada a cada execução em
  modo --onefile. Essa é a decisão que torna o executável "portátil":
  mover a pasta inteira (exe + dados) continua funcionando.

Todo módulo que hoje calcula sua própria "raiz do projeto" via
`Path(__file__).resolve().parent.parent...` para achar um recurso
read-only deveria, em vez disso, importar `resource_root()` daqui — o
cálculo baseado em `__file__` não é confiável sob PyInstaller (o valor
de `__file__` para módulos empacotados varia entre versões/modos).
Módulos que resolvem uma pasta de **dado gravável** devem usar
`data_root()`.

Ver docs/tech/doc-tecnico-executavel.md para o desenho completo do
empacotamento.
"""
from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    """True quando rodando como executável empacotado (PyInstaller)."""
    return bool(getattr(sys, "frozen", False))


def resource_root() -> Path:
    if is_frozen():
        # sys._MEIPASS existe nos dois modos do PyInstaller (--onefile e
        # --onedir) e aponta pra pasta que contém os dados empacotados via
        # `datas` no .spec. Fallback pra pasta do executável só por
        # segurança, caso rode sob um empacotador que não defina isso.
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent
    # Rodando a partir do código-fonte: este arquivo fica em core/, a raiz
    # do repositório é um nível acima.
    return Path(__file__).resolve().parent.parent


def data_root() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent
