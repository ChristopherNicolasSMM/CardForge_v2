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
├── web/                      ← camada Flask (a parte nova da 2.0)
│   ├── routes/                 → blueprints: hub, templates, dados, gerar, proxy
│   ├── services/                → upload de assets, dataset por sessão
│   ├── templates/               → HTML (Jinja2)
│   └── static/                  → CSS + JS (editor de canvas, tabela de dados)
│
├── templates/                ← seus modelos de card (pasta por template, com base.json)
├── assets/
│   ├── fonts/                  → fontes embutidas no CardForge
│   ├── fonts_custom/            → fontes .ttf que você enviar globalmente
│   └── library/                 → imagens de arte enviadas pela interface
├── instance/                 ← dados de sessão (dataset em edição + lotes gerados) — gerado em runtime
├── requirements.txt
└── run.py
```

---

## Fluxo de uso

1. **Templates** — crie um modelo novo (ou duplique um existente) e edite visualmente: arraste as camadas, ajuste fonte/cor/tamanho, defina fundo e verso.
2. **Dados** — importe uma planilha ou monte a tabela direto no navegador. Pra imagens de arte, use o seletor visual (upload ou escolha da biblioteca).
3. **Gerar** — escolha o template e os formatos (PNG/JPEG/WebP/SVG) e gere o lote inteiro. Baixe individualmente ou tudo em `.zip`.
4. **Proxy / PDF** — monte a folha de impressão (A4/A3/Letter), com marcas de corte e verso, pronta pra imprimir.

---

## Adicionando um novo modelo de card facilmente

- Na galeria de **Templates**, clique em **+ Novo template**.
- Pra reaproveitar um modelo existente, use **Herdar de** — o novo template herda todas as camadas do pai e você só ajusta o que for diferente (cor, fonte, posição específica).
- Ou clique **Duplicar** num template existente pra partir de uma cópia completa.

---

## Notas técnicas

- **Sem banco de dados** — tudo é arquivo. O dataset em edição e os lotes gerados ficam isolados por sessão de navegador em `instance/<sessão>/`, mas templates e bibliotecas de assets são compartilhados (é a mesma pasta `templates/` e `assets/` pra qualquer sessão — pensado pra uso local/pessoal, não multi-usuário).
- **Geração síncrona** — a geração em lote roda na mesma requisição (sem fila/worker externo). Para datasets muito grandes (varias centenas de cards), considere gerar em lotes menores.
- **Fontes**: a ordem de busca é `templates/<nome>/fonts/` → `assets/fonts_custom/` → `assets/fonts/`. Isso permite fontes exclusivas de um template sem afetar os demais.
