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

## Cartas por template

Se a coleção usa a coluna [`_template`](02-dados#cartas-por-template-_template), a lista de quantidade abaixo já mostra só as cartas associadas ao template escolhido — as de outros templates não aparecem e não entram na folha. Um aviso indica quantas linhas ficaram de fora por estarem sem `_template` ou apontando pra um template inexistente; marque **"gerar mesmo assim"** pra montar a folha ignorando essas linhas, ou corrija nos [Dados](02-dados) antes.

## Quantidade por carta

Por padrão, cada carta do dataset entra com **1 cópia** — mas dá pra ajustar isso: logo abaixo das configurações da folha, uma lista mostra cada carta (identificada pelo [campo identificador](02-dados#campo-identificador) da coleção — `name` por padrão) com um campo de quantidade ao lado. Exemplo: pra montar um deck de verdade pra imprimir, ponha `2` em "Sangue de Druida" e `1` em "Pacto das Sombras" — o resto pode ficar em `0` pra não entrar na folha.

- **`0`** exclui a carta da folha inteiramente.
- Os botões **Marcar todas (1x)** e **Zerar todas** ajudam a preencher a lista rápido, principalmente em datasets grandes.
- Um contador abaixo da lista mostra quantas cartas estão selecionadas e quantas cópias no total, atualizando conforme você digita.
- **As quantidades ficam salvas** — da próxima vez que você abrir a tela de Proxy (mesma coleção), elas continuam preenchidas do jeito que você deixou.

> Se duas cartas diferentes do seu dataset tiverem o mesmo valor no campo identificador, elas vão compartilhar a mesma quantidade salva (o sistema identifica cada linha por esse campo). Na prática isso raramente é um problema — cartas diferentes normalmente têm identificadores diferentes — mas vale saber se o seu dataset tiver duplicatas de propósito. Trocar o [campo identificador](02-dados#campo-identificador) pra um que seja sempre único no seu dataset resolve.

### Modo "uma folha cheia de cada"

Além da quantidade manual, existe um modo alternativo: **uma folha cheia de cada carta selecionada**. Nesse modo, a quantidade digitada não importa pro número de cópias — cada carta com quantidade maior que `0` (ou seja, "selecionada") ganha uma página inteira só pra ela, repetida até preencher toda a grade de colunas×linhas. Útil pra tirar uma "folha de prova" de uma ou mais cartas específicas, sem misturar com as outras.

Cartas com quantidade `0` não entram em nenhum dos dois modos.

## Sobre o verso

O verso é definido **por template** (não por card individual) — normalmente todo o baralho de um mesmo template compartilha a mesma arte de verso, como acontece em jogos de cartas físicos. Defina-a uma vez no [editor de template](01-templates#fundo-e-verso) e ela é reaproveitada em toda geração de proxy, a menos que você envie uma imagem alternativa na hora.

Quando o verso é incluído, cada página de verso é **espelhada horizontalmente** em relação à disposição da frente — assim, ao imprimir frente e verso e dobrar a folha, os versos alinham corretamente com os cards da frente.

## Gerando o PDF

Clique em **▤ Gerar PDF de proxy**. O arquivo fica disponível na lista de PDFs gerados nesta sessão, com botões de download e exclusão. O nome do arquivo segue o padrão `<template>-proxy-ddmmaaaa_hhmmss.pdf` (data e hora da geração), pra facilitar identificar qual é qual quando há vários.

## Dicas de impressão

- Use papel mais grosso (180g+) se for jogar com os proxies direto, sem sleeve.
- As marcas de corte são posicionadas considerando uma pequena margem entre cards — confira se sua impressora está configurada para **impressão sem escala** (100%, "tamanho real"), senão as medidas em milímetros do card final ficam incorretas.
