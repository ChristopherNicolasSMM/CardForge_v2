# Documento Técnico — Suporte a Símbolos de Mana e Frames por Cor (estilo MTG)

**Projeto:** CardForge 2.0
**Escopo:** Extensão do motor de renderização para suportar notação de símbolos inline (`{W}`, `{T}`, `{2/R}` etc.) e seleção de moldura ("frame") por campo de dado, inspirado no fluxo de cartas de Magic: The Gathering.
**Status:** Symbol Replacement Engine implementado (preview PIL + export SVG) e validado com render de teste. Ver seção 11.
**Origem da análise:** Estudo do repositório `mtg_card_maker` (Ruby, fork de joe-sharp) como referência de arquitetura, e do projeto `Mana` (andrewgioia/mana) como fonte de assets.

---

## 1. Contexto e motivação

O CardForge 2.0 já é schema-agnostic por desenho — não há mais nenhum vínculo hardcoded ao formato de carta de MTG. Esta feature reintroduz capacidades *inspiradas* em MTG (símbolos inline no texto de regras, frame variável por cor), mas como **capacidades genéricas do motor**, disponíveis a qualquer collection que queira usá-las — não como um schema fixo.

Durante o mapeamento, foi avaliado o gem Ruby `mtg_card_maker` como referência de arquitetura (layered rendering, symbol replacement engine, sprite sheets). Ele **não será usado como fonte de código ou assets**, por estar sob licença `CC-BY-NC-ND 4.0` (No-Derivatives), incompatível com o espírito MIT do CardForge. Serviu apenas como inspiração conceitual.

---

## 2. Fonte dos assets de símbolo: projeto Mana

- **Fonte:** [andrewgioia/mana](https://github.com/andrewgioia/mana) — pictographic font com todos os símbolos de mana, tap/untap, energia, híbridos e phyrexian de MTG.
- **Licenciamento:**
  - Fonte (glifos): **SIL OFL 1.1** — livre para redistribuição e modificação, inclusive em projetos com outra licença.
  - CSS/LESS/Sass de apoio: **MIT**.
  - Ressalva permanente: a representação visual dos símbolos de mana continua sendo IP da Wizards of the Coast, sob a Fan Content Policy — isso não é resolvido pela licença da fonte, é uma condição inerente a qualquer ferramenta de conteúdo de fã de MTG. Não é um problema introduzido por esta feature, apenas uma condição pré-existente que se mantém.

### 2.1 Decisão: rasterização única, não uso da fonte em runtime

O Mana aplica cor aos símbolos via CSS (círculo de fundo colorido por classe), não via glifo monocromático da fonte. Renderizar a fonte diretamente em runtime no PIL perderia essa caracterização visual.

**Decisão:** gerar os ícones **uma única vez**, via Playwright (já usado no projeto para os screenshots do README), rasterizando cada símbolo com sua cor/composição correta em PNG. Os PNGs resultantes são versionados no repositório.

**Justificativa para versionar (não gerar em setup):** o conjunto de símbolos de mana é estável — não muda com frequência. O custo de manter os PNGs no repo é aceitável frente ao ganho de simplicidade de instalação (zero passo extra de build para novos colaboradores).

---

## 3. Estrutura de pastas

```
assets/                          # NOVO: nível global, fora de collections/
  symbols/
    mana/
      w.png, u.png, b.png, r.png, g.png, c.png, s.png
      t.png, q.png, e.png                # tap, untap, energy
      2-w.png, 2-u.png, ...               # two-brid
      w-b.png, w-r.png, ...               # hybrid
      w-p.png, r-p.png, ...               # phyrexian
      w-b-p.png, ...                      # phyrexian hybrid
      x.png, 0.png ... 99.png             # genérico/numérico

collections/
  <slug>/
    assets/
      frame_white.png
      frame_blue.png
      frame_black.png
      frame_red.png
      frame_green.png
      frame_gold.png
      frame_colorless.png
      frame_artifact.png
```

- `assets/symbols/mana/` é **global**, carregado uma vez pelo motor, disponível para qualquer collection.
- `frame_*.png` continuam **por collection/template**, seguindo o isolamento já adotado no projeto.

---

## 4. Symbol Replacement Engine

### 4.1 Responsabilidade

Permitir que campos de texto (tipicamente `rules_text`) contenham notação `{X}` que é substituída, no momento da renderização, por um ícone inline — preservando o comportamento correto de quebra de linha (word wrap).

### 4.2 Desenho conceitual

1. **Parser:** varre o texto do campo e separa em tokens de dois tipos — texto puro e símbolo (`{...}`). Regex simples (`\{[^}]+\}`) é suficiente para a extração; o mapeamento de notação → arquivo é resolvido contra o inventário de `assets/symbols/mana/`.
2. **Medição:** cada símbolo recebe uma largura equivalente ao tamanho da fonte corrente da camada, para entrar corretamente no cálculo de quebra de linha junto com o texto.
3. **Layout customizado:** substitui o `draw.text()` simples por um layout que itera pelos tokens, decide quebras de linha considerando símbolo como uma "palavra" indivisível, e no desenho faz `image.paste()` do ícone (redimensionado à altura da linha corrente) para tokens de símbolo, e desenho normal de texto para os demais.
4. **Fallback de token não reconhecido:** se a notação dentro de `{}` não corresponder a nenhum arquivo em `assets/symbols/mana/`, o token é desenhado como texto literal (ex: `{ZZ}` aparece como texto `{ZZ}` na carta) — evita falha silenciosa de ícone ausente sem quebrar a geração.

### 4.3 Escopo de reuso

Esta capacidade é implementada no `core/` de forma genérica — qualquer collection pode usar notação `{X}` em qualquer campo de texto, não fica restrita a um dataset "MTG". O inventário de símbolos disponíveis é que hoje é o de mana, mas a estrutura permite adicionar outros pacotes de símbolo no futuro seguindo o mesmo padrão de pasta.

---

## 5. Frame por cor (seleção de moldura por campo de dado)

### 5.1 Decisão: sem mudança de engine

Confirmado que o mecanismo de camada de imagem já aceita lookup de campo do dataset (equivalente ao lookup já usado em campos de texto) e já busca o arquivo resolvido **dentro da pasta de assets do template**. Não é necessária nenhuma feature nova no motor de renderização.

### 5.2 Como se usa, na prática

- A collection inclui uma coluna no dataset (ex: `frame_asset`) preenchida com o **nome do arquivo já resolvido** (ex: `frame_red.png`), não com o valor "cru" (`Red`).
- A camada de imagem de frame no editor de template é configurada para ler esse campo, exatamente como uma camada de texto lê `{name}`.
- Os arquivos `frame_*.png` residem na pasta de assets do próprio template.

### 5.3 Por que coluna explícita, e não fórmula/derivação automática

Evita falha silenciosa por diferença de capitalização ou nomenclatura (`Red` vs `red` vs `frame_Red.png`). O valor final fica visível e revisável na planilha antes da geração em lote.

### 5.4 Duplicação de assets entre templates — aceita conscientemente

Como a busca de asset é por pasta de template (isolamento por collection), múltiplos templates que usem o mesmo conjunto de cores precisariam duplicar os mesmos PNGs de frame em cada pasta. **Decisão:** aceitar essa duplicação. Justificativa: escopo de projeto de fã, volume de assets pequeno, sem impacto relevante de armazenamento/performance. Caso o projeto cresça a ponto disso importar, a mitigação futura seria introduzir uma pasta de assets compartilhados entre templates — não faz parte do escopo atual.

### 5.5 Fallback de campo não correspondente — decisão de dado, não de engine

Assumido (por analogia ao comportamento já conhecido de campos de texto não mapeados) que, se `frame_asset` apontar para um arquivo inexistente, a camada simplesmente não é desenhada (renderização silenciosa sem a camada), sem interromper a geração do lote.

**Decisão:** não implementar lógica de fallback (`frame_default.png`) no engine. A robustez fica a cargo da preparação dos dados — a coluna `frame_asset` deve sempre ser preenchida com um valor válido antes da geração.

**✅ Validado por leitura de código (não apenas por analogia):** em `core/render/preview_renderer.py::_resolve_asset_path` e no equivalente em `svg_builder.py`, quando o valor do campo não corresponde a nenhum arquivo em nenhum dos locais de busca, a função retorna `None` e `_draw_image`/`_add_image` simplesmente fazem `return` sem desenhar nada — não há `raise` em nenhum ponto desse caminho. Confirmado: comportamento (a), como assumido. Nenhuma mudança de engine necessária.

---

## 6. Helper visual no editor de template

Adicionar, ao editor visual, um componente de paleta/seletor que insere a notação `{X}` correta no campo de texto sem que o usuário precise decorar a sintaxe — navegando visualmente pelos ícones disponíveis em `assets/symbols/mana/`.

---

## 7. Documentação (wiki)

Nova página em `docs/` (ex: `docs/simbolos-mana.md`), renderizada pelo sistema de wiki já existente em `/wiki`, contendo uma tabela: **notação → miniatura do ícone → descrição**. Serve de referência para quem prepara datasets/CSVs, tanto para o uso de símbolos inline quanto (indiretamente) para a convenção de nomes de `frame_asset`.

---

## 8. Pontos de falha conhecidos e manutenção futura

- **Resolução de path de asset por campo:** a mesma peça de código que resolve `frame_asset` → arquivo é, muito provavelmente, a mesma rotina afetada pelo bug já mapeado da biblioteca de imagens (upload salvo em `assets/library/`, mas o renderer busca apenas na pasta do template). Recomenda-se tratar os dois no mesmo momento, já que compartilham a mesma superfície de código.
- **Fallback de imagem ausente:** ver pendência de validação na seção 5.5.
- **Duplicação de frames entre templates:** ver decisão consciente na seção 5.4 — ponto a revisitar caso o número de templates/collections cresça.
- **Símbolo não reconhecido no texto:** tratado com fallback textual (seção 4.2, item 4) — não deve gerar exceção.

---

## 9. Itens fechados vs. pendentes

| Item | Status |
|---|---|
| Fonte dos ícones (Mana, OFL) | ✅ Fechado |
| Rasterização única, versionada no repo | ✅ Fechado |
| Estrutura de pastas (global vs. por collection) | ✅ Fechado |
| Symbol Replacement Engine (desenho) | ✅ Fechado |
| Frame por cor via campo de dado | ✅ Fechado — sem mudança de engine |
| Duplicação de assets entre templates | ✅ Aceita conscientemente |
| Fallback de frame ausente | ✅ Confirmado por leitura de código — nenhuma exceção, silencioso |
| Helper visual no editor | ⏳ Ainda não implementado — fora do escopo desta rodada |
| Página de documentação no wiki | ✅ Implementado — `docs/09-simbolos-mana.md` |

---

## 10. Próximos passos sugeridos (fora do escopo deste documento)

1. ~~Validar empiricamente o comportamento de campo de imagem não correspondente~~ — feito, ver seção 5.5.
2. ~~Confirmar a rotina exata de resolução de path de asset por campo~~ — feito, ver seção 11.2: é a mesma rotina do bug da biblioteca de imagens, em ambos os renderers.
3. Substituir os PNGs placeholder pelos ícones reais do projeto Mana (rasterizados via `scripts/generate_mana_icons.py` a partir de SVGs equivalentes aos do Mana, ou adaptando o script pra rasterizar a fonte diretamente).
4. Implementar o helper visual no editor de template.
5. ~~Escrever a página de wiki~~ — feito, `docs/09-simbolos-mana.md`.
6. Investigar e corrigir o bug de unidades encontrado em `svg_builder.py` (seção 11.3) — não bloqueia esta feature, mas afeta a qualidade do export SVG de forma geral.

---

## 11. Registro de implementação (esta rodada)

### 11.1 O que foi confirmado no código antes de implementar

- O tipo de layer `"mana"` já existia no modelo (`core/template/models.py`), mas nenhum template o instanciava — o gancho estava pronto e sem uso.
- Já existia uma pasta global `assets/icons/` (fora de `collections/`) com ~90 SVGs, incluindo `hybrid/` e `phyrexian/` já estruturados por nome de cor por extenso (ex: `white-black.svg`). Inspeção do conteúdo mostrou que **não são os símbolos reais de mana** — são ícones placeholder (estilo Google Material Symbols; `W.svg` e `white.svg` têm o mesmo path de glifo). Zero risco de licença herdado daí, mas também zero autenticidade visual — confirma a necessidade da troca planejada pelos ícones do Mana (seção 3).
- O projeto **não tem nenhuma dependência de rasterização de SVG** (`cairosvg`, `svglib` etc.) em `requirements.txt` — confirma a decisão da seção 2.1 (nada de SVG em runtime).

### 11.2 O que foi implementado

- `core/render/mana_symbols.py` — parser de notação `{X}` → caminho de PNG, com fallback textual para notação não reconhecida.
- `scripts/generate_mana_icons.py` — rasteriza `assets/icons/**/*.svg` → `assets/icons_png/` (mesma árvore de pastas). Rodado uma vez nesta rodada; os PNGs resultantes foram versionados.
- `core/render/preview_renderer.py` — `_draw_text` reescrito para tratar linhas como sequência de unidades (palavra ou símbolo), com símbolo entrando no cálculo de quebra de linha como unidade atômica do tamanho do ícone.
- `core/render/svg_builder.py` — `_add_text` agora detecta se a linha contém símbolo reconhecido; se não, usa exatamente o caminho antigo (`<text>` + `<tspan>` por linha, zero mudança de comportamento); se sim, usa um novo caminho (`_add_rich_text`) que emite `<text>` por palavra e `<image>` por símbolo, posicionados explicitamente — porque `<tspan>` não suporta intercalar imagem no meio do fluxo. A medição de largura de palavra usa `PIL` apenas como régua (mesmo mecanismo de fonte do preview), sem gerar nenhum raster no output final.
- `docs/09-simbolos-mana.md` — página de wiki com a tabela de notação.

### 11.3 Achado à parte, fora do escopo desta feature

Durante o teste de validação (renderizar um card de exemplo com `SVGBuilder`), foi observado que o texto de `card_name` — que não usa nenhuma notação de símbolo e passa pelo caminho de renderização original, inalterado — aparece desproporcionalmente grande no SVG exportado. A causa aparente é um descompasso de unidades entre `font-size` (especificado em `pt`) e o sistema de coordenadas do `viewBox` (em `mm`, sem conversão explícita). Confirmado que **não é uma regressão desta implementação** (reproduz com texto puro, sem nenhum símbolo envolvido, no caminho de código que não foi tocado). Registrado aqui para virar um item de investigação separado — não foi corrigido nesta rodada para não misturar escopos.

### 11.4 Limpeza de assets não utilizados

Após implementar a engine, foi feita uma auditoria em `assets/icons/` (grep por todo o repositório — código, templates, JS, configs — sem depender só de leitura visual) pra confirmar quais dos 87 arquivos originais são de fato resolvidos por `mana_symbols.py`. 10 arquivos não tinham nenhuma referência em lugar nenhum e foram removidos (de `assets/icons/` e dos PNGs correspondentes em `assets/icons_png/`):

- `white.svg`, `black.svg`, `blue.svg`, `red.svg`, `green.svg` — duplicados por extenso dos arquivos de letra (`W.svg` etc.), que são os efetivamente resolvidos pela notação.
- `single-digit.svg`, `double-digit.svg` — continham números de exemplo fixos ("3", "16"); a engine usa os arquivos individuais `0.svg`...`9.svg`.
- `tap_legacy.svg` — só `tap.svg` é referenciado.
- `cardforge.ico`, `cardforge.png` — cópias soltas do ícone do app, sem relação com símbolos de mana; o favicon real vem de `web/static/favicon*`.

Não foi encontrado nenhum `glob`/`listdir` dinâmico sobre a pasta em nenhuma rota ou template, então a remoção não afeta nenhuma listagem automática de ícones. `assets/icons/` e `assets/icons_png/` ficaram com exatamente 77 arquivos cada, em correspondência 1:1.

### 11.5 Validação realizada

Renderização de teste com `mana_cost="{3}{U}{R}"` e `rules_text` contendo `{T}`, `{W}`, `{U}`, `{2/R}`, via `_default_template`:
- **Preview PIL:** símbolos aparecem inline, quebra de linha respeita o símbolo como unidade atômica, texto sem símbolo continua idêntico ao comportamento anterior.
- **Export SVG:** 7 elementos `<image>` embutidos corretamente para os símbolos usados; ressalva da seção 11.3 quanto ao tamanho do texto (não relacionado aos símbolos em si).
