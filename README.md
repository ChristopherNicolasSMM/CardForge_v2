<p align="center">
  <img src="\cardforge.png" alt="CardForge" width="180">
</p>

<p align="center"><strong>CardForge By Christopher N. S. M. Mauricio</strong></p>



# CardForge 2.0

Gerador de cards para jogos de carta customizados — agora via navegador (Flask), no lugar da interface desktop (Tkinter) da versão 1.

> Este projeto é a refatoração 2.0 do [CardForge](https://github.com/ChristopherNicolasSMM/Criador_de_Cards_Beta_CardForge).
> O motor de renderização (`core/`) foi reaproveitado quase intacto — a mudança principal é a interface, que passa a rodar 100% no navegador.

---

## Início rápido

```bash
pip install -r requirements.txt
python run.py
```

Depois abra **http://localhost:5000** no navegador.

---

## O que mudou da 1.0 para a 2.0

| | 1.0 (Tkinter) | 2.0 (Flask) |
|---|---|---|
| Interface | Janela desktop | Navegador (qualquer SO) |
| Editor de template | Canvas Tkinter | Canvas HTML5 com drag & drop |
| Dataset | Só arquivo (CSV/XLSX/YAML/JSON) | Arquivo **ou** tabela editável no navegador |
| Imagens de arte | Caminho digitado manualmente | Biblioteca visual + upload direto |
| Fontes | Fixas (Beleren/Mplantin) | Upload de `.ttf` por template |
| Geração em lote | Só local | Resultado em grid com download individual ou `.zip` |
| Proxy de impressão | Sim (A4/A3/Letter + verso) | Mantido, com upload de verso pela interface |
| Persistência | Arquivos no disco | Arquivos no disco (sem banco de dados) |

O motor (`core/`) é o mesmo pipeline da 1.0: **Template (JSON com herança) + Dados → Renderização (PIL/SVG) → Export (PNG/JPEG/WebP/SVG) → Proxy PDF**.

---

## Estrutura do projeto

```
cardforge2/
├── core/                     ← motor de renderização (sem nenhuma dependência de UI)
│   ├── template/              → modelos, herança, carregar/salvar template
│   ├── data/                  → leitura de CSV/XLSX/YAML/JSON
│   ├── render/                → preview PIL, SVG builder, export raster, resolução de fontes
│   └── proxy/                 → composição de folha + PDF
│
├── web/                      ← camada Flask
│   ├── routes/                 → blueprints: hub, coleções, templates, dados, gerar, proxy, wiki
│   ├── services/                → coleções, upload de assets, dataset
│   ├── templates/               → HTML (Jinja2)
│   └── static/                  → CSS + JS (editor de canvas, tabela de dados)
│
├── collections/               ← cada coleção (jogo, ou atualização de jogo) é uma pasta aqui
│   └── <coleção>/
│       ├── collection.json      → nome, descrição, jogo
│       ├── templates/<nome>/     → modelos de card dessa coleção
│       ├── assets/library/        → imagens de arte enviadas nessa coleção
│       ├── assets/fonts_custom/    → fontes .ttf enviadas nessa coleção
│       ├── data.json                → dataset de cards em edição
│       └── output/                   → lotes gerados + PDFs de proxy
│
├── assets/fonts/              ← fontes embutidas no CardForge (sempre globais, todas as coleções)
├── docs/                      ← manuais em .md, exibidos em /wiki
├── requirements.txt
└── run.py
```

---

## Fluxo de uso

0. **Coleções** — crie (ou selecione) a coleção do jogo em que vai trabalhar. Tudo abaixo pertence a ela.
1. **Templates** — crie um modelo novo (ou duplique um existente) e edite visualmente: arraste as camadas, ajuste fonte/cor/tamanho, defina fundo e verso.
2. **Dados** — importe uma planilha ou monte a tabela direto no navegador. Pra imagens de arte, use o seletor visual (upload ou escolha da biblioteca).
3. **Gerar** — escolha o template e os formatos (PNG/JPEG/WebP/SVG) e gere o lote inteiro. Baixe individualmente ou tudo em `.zip`.
4. **Proxy / PDF** — monte a folha de impressão (A4/A3/Letter), com marcas de corte e verso, pronta pra imprimir.

---

## Coleções: um jogo, ou uma atualização de jogo

Cada coleção é uma pasta autocontida — templates, dados, fontes e cards gerados de uma coleção nunca se misturam com os de outra. Use isso para separar jogos diferentes, ou uma expansão/atualização de um jogo já existente.

- **Duplicar** uma coleção (pra criar uma atualização) deixa você escolher o que trazer: templates, fontes/imagens e/ou os dados já cadastrados.
- **Importar um template** de outra coleção copia aquele modelo (com fundo, verso e fontes próprias) pra coleção atual, mantendo as duas independentes depois.

Veja o manual completo em `/wiki` → **Coleções**.

---

## Adicionando um novo modelo de card facilmente

- Na galeria de **Templates**, clique em **+ Novo template**.
- Pra reaproveitar um modelo existente na mesma coleção, use **Herdar de** — o novo template herda todas as camadas do pai e você só ajusta o que for diferente (cor, fonte, posição específica).
- Ou clique **Duplicar** num template existente pra partir de uma cópia completa.
- Pra reaproveitar um template de **outra coleção**, use **Importar de outra coleção** na galeria.

---

## Notas técnicas

- **Sem banco de dados** — tudo é arquivo, organizado por coleção em `collections/<slug>/`. Isso torna cada coleção uma pasta que você pode copiar, arquivar ou versionar isoladamente.
- **Coleção ativa por sessão de navegador** — abas diferentes podem estar trabalhando em coleções diferentes ao mesmo tempo; a seleção fica na sessão, mas os dados em si são sempre persistidos na pasta da coleção (não se perdem ao fechar o navegador).
- **Geração síncrona** — a geração em lote roda na mesma requisição (sem fila/worker externo). Para datasets muito grandes (várias centenas de cards), considere gerar em lotes menores.
- **Fontes**: a ordem de busca é `templates/<nome>/fonts/` (da coleção ativa) → `collections/<coleção>/assets/fonts_custom/` → `assets/fonts/` (embutidas, globais).
- **Migração automática**: projetos criados antes do sistema de coleções têm seus templates/assets migrados automaticamente para uma coleção chamada "Geral" na primeira execução após a atualização.
