# Atribuição — glifos de símbolo de mana

Os arquivos em `glyphs/` são um subconjunto vendorizado dos glifos do
projeto **Mana** (pacote npm `mana-font`, versão 1.18.0):

- Repositório: https://github.com/andrewgioia/mana
- Site: https://mana.andrewgioia.com

## Licenciamento (conforme o README oficial do projeto)

> All mana, tap, and card type symbol images are copyright Wizards of the
> Coast (http://magicthegathering.com)
>
> The Mana font is licensed under the SIL OFL 1.1 (http://scripts.sil.org/OFL)
>
> Mana CSS, LESS, and Sass files are licensed under the MIT License
> (http://opensource.org/licenses/mit-license.html)
>
> Attribution is greatly appreciated but not required!

Ou seja: os **glifos em si** (o que está vendorizado aqui) estão sob
**SIL OFL 1.1** — livre pra redistribuir e modificar, inclusive dentro de
um projeto com outra licença (o CardForge é MIT). A representação visual
de mana da MTG continua sendo IP da Wizards of the Coast — uso de fã, não
comercial, como qualquer ferramenta desse tipo.

## O que foi vendorizado, e por quê

Só os glifos-base usados pela engine de composição do CardForge (ver
`scripts/generate_mana_icons.py`): as 5 cores (w/u/b/r/g), incolor (c),
genérico numérico (0–20, 100), X, tap, untap, energia (e) e o símbolo
Phyrexian genérico (p). Não é o pacote Mana inteiro — o projeto original
tem centenas de símbolos adicionais (habilidades, marcas d'água, contadores
etc.) fora do escopo desta feature.

## Por que compor em vez de usar os SVGs do Mana direto

Os SVGs individuais do Mana contêm só o contorno do símbolo — o círculo
colorido de fundo característico (que dá a "cara" clássica do símbolo de
mana) é aplicado via CSS no projeto original, não faz parte do arquivo
SVG. `scripts/generate_mana_icons.py` reconstrói essa composição
(círculo + glifo + split diagonal para híbridos) usando a paleta oficial
de cores do próprio Mana, em Python/PIL — ver esse script para o
detalhamento completo e docs/tech/doc-tecnico-mtg-symbols-frames.md,
seção 13.

## Como regenerar

```
pip install cairosvg
python scripts/generate_mana_icons.py
```

Os PNGs resultantes (`assets/icons_png/`) são versionados no repositório
— não é necessário rodar isso pra usar o CardForge, só pra alterar os
ícones no futuro.
