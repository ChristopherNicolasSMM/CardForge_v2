# Proxy de impressão (PDF)

A tela **Proxy / PDF** monta uma folha pronta para impressão com vários cards por página, marcas de corte e (opcionalmente) o verso.

## Configurações

| Campo | O que faz |
|---|---|
| Template | Qual template usar para renderizar os cards |
| Formato da folha | A4, A3 ou Letter |
| Colunas / Linhas | Quantos cards cabem por página, lado a lado |
| Margem | Distância entre a borda da folha e o primeiro card |
| Espaço entre cards | Espaçamento (gap) entre um card e outro na mesma página |
| Marcas de corte | Pequenas linhas nos cantos de cada card, para guiar o corte com estilete/tesoura |
| Incluir folha de verso | Gera uma página extra por folha de frente, com o verso de cada card |
| Imagem de verso | Se o template já tem uma imagem de verso definida, ela é usada automaticamente; envie um arquivo aqui para usar outra imagem só nesta geração |

## Sobre o verso

O verso é definido **por template** (não por card individual) — normalmente todo o baralho de um mesmo template compartilha a mesma arte de verso, como acontece em jogos de cartas físicos. Defina-a uma vez no [editor de template](01-templates#fundo-e-verso) e ela é reaproveitada em toda geração de proxy, a menos que você envie uma imagem alternativa na hora.

Quando o verso é incluído, cada página de verso é **espelhada horizontalmente** em relação à disposição da frente — assim, ao imprimir frente e verso e dobrar a folha, os versos alinham corretamente com os cards da frente.

## Gerando o PDF

Clique em **▤ Gerar PDF de proxy**. O arquivo fica disponível na lista de PDFs gerados nesta sessão, com botões de download e exclusão. O nome do arquivo segue o padrão `<template>-proxy-ddmmaaaa_hhmmss.pdf` (data e hora da geração), pra facilitar identificar qual é qual quando há vários.

## Dicas de impressão

- Use papel mais grosso (180g+) se for jogar com os proxies direto, sem sleeve.
- As marcas de corte são posicionadas considerando uma pequena margem entre cards — confira se sua impressora está configurada para **impressão sem escala** (100%, "tamanho real"), senão as medidas em milímetros do card final ficam incorretas.
