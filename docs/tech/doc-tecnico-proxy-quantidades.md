# Documento Técnico — Quantidade por Carta no Proxy

**Projeto:** CardForge 2.0
**Escopo:** Permitir escolher quantas cópias de cada carta entram na folha de proxy (em vez de sempre uma de cada), com um modo alternativo de "folha cheia por carta", e um campo identificador configurável pra reconhecer cada carta.
**Status:** Implementado e validado (render real de PDF conferido visualmente). Ver seção 5 para a rodada do campo identificador configurável.

---

## 1. Motivação

Até esta feature, `proxy_bp.py` gerava sempre **uma cópia de cada linha do dataset**, sem opção de quantidade nem de excluir uma carta específica da folha. Pedido do usuário: poder montar uma folha que reflita um deck de verdade (ex: "2x Sangue de Druida, 1x Pacto das Sombras"), ou alternativamente gerar uma folha de prova cheia de uma única carta.

## 2. Decisões confirmadas com o usuário antes de implementar

| Decisão | Escolha |
|---|---|
| Persistência das quantidades | **Salva** — lembra entre visitas à tela, por coleção |
| Modo "folha cheia de cada" | Só as cartas com quantidade > 0 (selecionadas) entram — não o dataset inteiro |
| Identificação de cada carta na lista | Campo `name` do dataset, com fallback por posição se ausente |

## 3. Desenho

### 3.1 Persistência (`web/services/proxy_quantities.py`, novo)

Um arquivo por coleção, `collections/<slug>/proxy_quantities.json`, mapeando `{chave_da_linha: quantidade}`. Chave = valor do **campo identificador** da linha (`row_key()`); linha sem valor nesse campo cai num fallback `__row{índice}__`.

**Limitação aceita conscientemente:** duas linhas com o mesmo valor no campo identificador compartilham a mesma quantidade salva (a chave colide). Documentado no manual (`docs/04-proxy.md`) e no troubleshooting (`docs/07-solucao-problemas.md`) — não é tratado como bug, é uma consequência direta de identificar a carta por um campo de texto (a alternativa, um ID técnico interno de linha, seria menos legível pro usuário e mais frágil a reordenação de linhas na tela de Dados).

`quantities_for_rows(slug, rows, id_field)` junta o dataset atual com o que está salvo, preenchendo `1` como padrão pra qualquer linha ainda não customizada — mantém o comportamento de sempre ("uma de cada") até a pessoa mexer.

### 3.2 Construção da lista de imagens (`web/routes/proxy_bp.py`)

A mudança central: em vez de `card_images = [renderer.render(row, ...) for row in rows]` (uma por linha, sempre), agora:

```python
for i, row in enumerate(rows):
    qty = quantities.get(pq.row_key(row, i), 1)
    if qty <= 0:
        continue
    img = renderer.render(row, ...)
    if print_mode == "full_sheet":
        card_images.extend([img] * cards_per_page)   # ignora qty, enche a página
    else:
        card_images.extend([img] * qty)
```

Ponto importante de design: **`compose_proxy()` (em `core/proxy/sheet_composer.py`) não foi alterado**. Ele já paginava uma lista plana de imagens em grupos de `cols × rows`, sequencialmente — o suficiente pros dois modos:

- **Modo customizado:** a lista simplesmente tem repetições e lacunas (cartas excluídas não aparecem) — cartas diferentes continuam podendo compartilhar página, como antes.
- **Modo folha cheia:** cada carta selecionada contribui **exatamente** `cols × rows` cópias consecutivas — como esse número é, por construção, igual à capacidade de uma página inteira, a paginação sequencial existente naturalmente produz uma página por carta, sem precisar de nenhuma lógica de "forçar quebra de página" no composer.

Essa escolha evitou tocar no código de composição de página (menor superfície de mudança, menor risco de regressão no fluxo que já funcionava).

### 3.3 Interface (`web/templates/proxy/index.html`)

- Dois rádios (`print_mode`: `custom` | `full_sheet`) dentro do mesmo `<form>` da geração — não precisa de rota nem de JS assíncrono separado, submete tudo junto com o POST existente.
- Uma tabela (nome + campo numérico `qty_{índice}`) por linha do dataset atual, pré-preenchida com a quantidade salva (ou `1`).
- JS local (sem dependência nova) calcula um contador ao vivo ("N carta(s) selecionada(s) — M cópia(s) no total"), reagindo à digitação e à troca de modo/colunas/linhas — conveniência, não crítico pro funcionamento (o cálculo real acontece no backend, no submit).
- Botões **Marcar todas (1x)** / **Zerar todas** — atalho pra datasets grandes, evita ter que digitar em cada campo individualmente.

## 4. Validação realizada

Testado via `Flask test_client`, com verificação visual real do PDF gerado (renderizado com PyMuPDF pra conferir pixel a pixel, não só o status HTTP):

- **Modo customizado** (2× Sangue de Druida, 1× Pacto das Sombras, 0× Carta Zero): PDF gerado com exatamente essas cópias, na ordem esperada — confirmado visualmente.
- **Modo folha cheia** (1 carta selecionada, grade 2×2): PDF de 1 página, com 4 cópias da mesma carta preenchendo a grade inteira — confirmado visualmente.
- Persistência: quantidades submetidas em uma geração aparecem corretamente no arquivo `proxy_quantities.json` da coleção, e são recarregadas ao reabrir a tela.
- Exclusão total (`todas as quantidades em 0`): erro tratado com mensagem clara, sem gerar PDF vazio.

## 5. Campo identificador configurável — registro da segunda rodada

Na primeira rodada, a chave de identificação da linha (seção 3.1) estava fixa no campo `name`. Levantado pelo usuário: e se o dataset não tiver `name`? Duas opções foram discutidas — concatenar as duas primeiras colunas automaticamente, ou deixar a pessoa escolher explicitamente qual coluna usar.

### 5.1 Por que "concatenar as duas primeiras colunas" foi descartado

O schema de dataset do CardForge é deliberadamente customizável (ver seção sobre isso em `docs/02-dados.md`) — não há garantia nenhuma de que as duas primeiras colunas de um dataset qualquer sejam algo legível como identificador. É um acidente de ordem de coluna, não uma escolha real. Concatenar `power` + `toughness` (por exemplo) produziria algo como "3 - 3", que não identifica nada.

### 5.2 Desenho escolhido: campo configurável, com fallback automático sensato

`collections.resolve_identifier_field(slug, columns)` (novo, em `web/services/collections.py`) resolve nessa ordem:

1. Campo explicitamente configurado (`identifier_field` em `collection.json`), **se ainda existir** entre as colunas atuais do dataset (protege contra a pessoa escolher um campo e depois excluir essa coluna — cai pro próximo passo em vez de quebrar).
2. `name`, se existir — preserva o comportamento de antes pra quem já usa esse campo (a grande maioria dos casos, dado que `name` é uma das colunas padrão sugeridas).
3. A primeira coluna do dataset — mesmo fallback of "melhor esforço" que já existia implicitamente, agora como passo explícito e documentado, não mais hardcoded.
4. `None` — quem chama cai pro número da linha.

`CollectionMeta` ganhou o campo `identifier_field: str = ""` (string vazia = "automático", não um valor real de coluna — evita confundir "não configurado" com "configurado pra uma coluna chamada vazio"). Persistido via `update_meta()` (função genérica já existente, aceita `**fields` arbitrários — não precisou de nenhuma mudança nela).

### 5.3 Onde a pessoa configura

Um seletor novo no topo da tela de **Dados** (`GET/POST /data/identifier-field`) — não na tela de Proxy, porque é uma propriedade do *dataset/coleção*, não uma configuração de uma geração de proxy específica (mesmo raciocínio que já se aplica a "Campo do dataset" no editor de template, que também vive perto de onde as colunas são geridas, não espalhado pelas telas que consomem essas colunas).

`proxy_quantities.row_key()` e `quantities_for_rows()` passaram a receber `id_field` como parâmetro em vez de usar `"name"` fixo internamente — o módulo de persistência ficou agnóstico de qual campo é usado, quem decide isso é `proxy_bp.py`, resolvendo via `collections.resolve_identifier_field()`.

### 5.4 Validação realizada

- Dataset sem campo `name` (`codigo`, `poder`): confirmado que o sistema cai automaticamente pra `codigo` (primeira coluna) como identificador, tanto na exibição quanto na chave de persistência.
- Configuração explícita (trocar pra `poder`): confirmado que a tela de Proxy passa a exibir os valores de `poder` em vez de `codigo`.
- Caso de borda — campo configurado é removido do dataset depois: confirmado que não quebra (a tela de Dados continua carregando normalmente), graças à checagem `explicit in columns` em `resolve_identifier_field()`.
- Persistência: `identifier_field` confirmado gravado corretamente em `collection.json` após salvar pelo seletor.
