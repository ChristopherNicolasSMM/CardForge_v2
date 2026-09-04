# -*- mode: python ; coding: utf-8 -*-
"""
Spec do PyInstaller pro CardForge 2.0.

Modo escolhido: --onedir (pasta), não --onefile. Motivos:
  1. Inicialização mais rápida (--onefile precisa descompactar tudo numa
     pasta temporária a cada execução; --onedir já está pronto no disco).
  2. Mais fácil de raciocinar sobre onde os dados do usuário ficam — a
     pasta gerada aqui (CardForge/) é literalmente a pasta portátil que o
     usuário move/copia/faz backup, com o executável e os dados lado a lado.

Rodar (numa máquina com o SO alvo, dentro de um venv com requirements.txt
+ pyinstaller instalados):
    pyinstaller cardforge.spec

Resultado: dist/CardForge/ — essa pasta inteira é o "app" a distribuir.
Na primeira execução, CardForge/collections/ e outras pastas de dado são
criadas ao lado do executável (ver core/paths.py, web/config.py).
"""
from pathlib import Path

ROOT = Path(SPECPATH)  # noqa: F821 -- SPECPATH é injetado pelo PyInstaller

# Recursos read-only que precisam ir dentro do bundle, preservando a
# estrutura de pastas relativa (é isso que core/paths.py:resource_root()
# espera encontrar em tempo de execução).
datas = [
    (str(ROOT / "web" / "templates"), "web/templates"),
    (str(ROOT / "web" / "static"), "web/static"),
    (str(ROOT / "assets" / "fonts"), "assets/fonts"),
    (str(ROOT / "assets" / "icons_png"), "assets/icons_png"),
    (str(ROOT / "docs"), "docs"),
]

a = Analysis(  # noqa: F821
    ["desktop_launcher.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CardForge",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,  # janela de terminal visível -- mostra a URL e onde os dados ficam
    icon=str(ROOT / "cardforge.ico"),
)

coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="CardForge",
)
