# Gerar cards em lote

A tela **Gerar** renderiza todos os cards do dataset atual de uma vez, usando o template escolhido.

## Como gerar

1. Escolha o **template**.
2. Marque os **formatos de saída** desejados: PNG, JPEG, WebP e/ou SVG. Pode marcar mais de um — todos são gerados na mesma execução.
3. Clique em **▶ Gerar todos os cards**.

A geração é síncrona: a página fica carregando até o lote terminar, e então mostra a grade de resultados.

## Cartas por template

Se a coleção usa a coluna [`_template`](02-dados#cartas-por-template-_template) (mais de um template, cada linha marcada com o seu dono), a tela mostra quantos cards estão associados ao template selecionado, atualizando ao trocar o template no seletor. Só essas linhas entram na geração.

Se houver linha sem `_template` definido, ou apontando pra um template que não existe, a geração é bloqueada com um aviso — marque **"gerar mesmo assim"** pra prosseguir ignorando essas linhas, ou volte aos [Dados](02-dados) e corrija.

## Lotes grandes

Para datasets com mais de ~100 cards, a geração pode levar alguns segundos a mais — a interface avisa quando isso acontece. Não há limite técnico rígido, mas se o navegador ou o servidor derem timeout em lotes muito grandes, uma alternativa é dividir o dataset em partes menores e gerar em execuções separadas.

## Resultado

Cada card gerado aparece como uma miniatura, com um selo por formato disponível (`PNG`, `SVG`, etc.) — clique num selo para baixar aquele arquivo individualmente.

Para baixar tudo de uma vez, use **⇩ Baixar tudo (.zip)** — o arquivo compactado organiza os cards em uma subpasta por formato.

### Uma particularidade do formato SVG

O SVG é um formato vetorial — ao contrário do PNG/JPEG/WebP (que já saem "prontos", pixel a pixel), o SVG guarda instruções de desenho que o programa que abrir o arquivo (navegador, Inkscape, etc.) interpreta na hora de exibir. Duas consequências práticas:

- **Texto longo sem símbolo no meio não quebra linha automaticamente** dentro do SVG — se uma camada de texto multilinha gerar uma linha muito comprida, ela pode ultrapassar a largura da camada no arquivo SVG (o PNG/preview não tem esse problema, já que a quebra de linha é calculada na hora de desenhar os pixels). Se isso acontecer, considere gerar em PNG pra esse template, ou ajustar o texto/tamanho da fonte.
- **Fontes customizadas** vão embutidas no próprio arquivo SVG — abra sempre num navegador atual (Chrome, Firefox, Edge) pra ter certeza que a fonte certa aparece; outras ferramentas mais simples de visualizar SVG às vezes não aplicam a fonte embutida corretamente e mostram uma fonte genérica no lugar (o desenho continua correto, só a tipografia muda).

## Lotes anteriores

A tela de Gerar mantém uma lista dos lotes já gerados na sessão atual, com acesso rápido ao resultado de cada um. Esse histórico é por sessão de navegador — fechar o navegador ou limpar cookies reinicia essa lista (os arquivos gerados continuam no disco em `collections/<coleção>/output/`, e podem ser encontrados manualmente lá se necessário).

## Excluindo lotes e cards

- **Excluir lote** — na lista de lotes (tela de Gerar) ou na tela de resultado de um lote, remove a pasta inteira daquele lote do disco (todos os formatos, todos os cards).
- **Excluir card** — dentro da tela de resultado de um lote, cada card tem seu próprio botão **Excluir card**, que remove só os arquivos daquele card específico (em todos os formatos gerados) e atualiza a contagem do lote — sem precisar refazer o lote inteiro.

Nenhuma das duas ações pode ser desfeita pela interface.
