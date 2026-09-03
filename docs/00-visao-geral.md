# Visão geral

CardForge é um motor de criação de cards para jogos de carta customizados. Você define um **template** (o layout visual do card), alimenta com **dados** (uma linha por card) e o sistema gera as artes finais — prontas para uso digital ou impressão.

## O fluxo em quatro passos

1. **Templates** — monte o layout: fundo, posição do nome, custo, texto de regras, arte, etc.
2. **Dados** — uma linha por card, com os valores que preenchem os campos do template.
3. **Gerar** — renderiza todos os cards do dataset atual, no formato que você escolher (PNG, JPEG, WebP, SVG).
4. **Proxy / PDF** — monta uma folha pronta para impressão, com marcas de corte e verso.

## Conceitos-chave

**Template** é o molde do card. Ele descreve, em milímetros, onde cada elemento fica: o fundo, o nome, o custo, a arte, o texto de regras. Um template pode **herdar** de outro — o filho reaproveita tudo do pai e só sobrescreve o que for diferente. Isso é útil quando você tem uma família de cards com o mesmo layout base, mas cores ou fontes distintas por facção.

**Camada** (*layer*) é cada elemento dentro de um template: um retângulo de fundo, um bloco de texto, uma arte. Toda camada tem posição (`x`, `y`), tamanho (`largura`, `altura`) e uma ordem de empilhamento (`z-index` — quanto maior, mais na frente).

**Dado** é uma linha da sua planilha ou tabela: os valores reais que entram em cada camada de texto/imagem. Um dataset com 30 linhas gera 30 cards.

**Campo** conecta uma camada a uma coluna do dataset. Por exemplo, uma camada de texto com campo `name` mostra o valor da coluna `name` daquela linha. Se o campo ficar vazio, a camada usa conteúdo fixo em vez de puxar do dataset — **texto fixo** pra camadas de texto, **imagem fixa** pra camadas de imagem/fundo — útil pra conteúdo que não muda entre cards (um rodapé, um ícone, uma marca d'água).

## Coleções

Todo o resto deste manual assume que você já tem uma **coleção** ativa. Uma coleção representa um jogo (ou uma atualização/expansão de um jogo) e organiza templates, dados, fontes e cards gerados numa pasta própria — veja o manual de [Coleções](08-colecoes) antes de continuar, se ainda não criou a sua.

## Onde os dados ficam

CardForge não usa banco de dados — tudo é arquivo, organizado por coleção:

```
collections/<coleção>/
  templates/        ← modelos de card dessa coleção
  assets/library/     ← imagens de arte enviadas
  assets/fonts_custom/ ← fontes .ttf enviadas
  data.json             ← dataset em edição
  output/                 ← lotes gerados + PDFs de proxy
```

Cada coleção é isolada das demais — nada se mistura entre coleções, a menos que você [importe um template explicitamente](08-colecoes#importando-um-template-de-outra-coleção) de uma para outra.

## Próximos passos

Comece pelo manual de [Coleções](08-colecoes) pra criar seu primeiro projeto, depois siga para [Templates](01-templates) para montar seu primeiro modelo, ou vá direto para [Dados](02-dados) se já tem um template pronto.
