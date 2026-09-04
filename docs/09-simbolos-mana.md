# Símbolos inline (notação estilo MTG)

Campos de texto (`rules_text`, `mana_cost`, ou qualquer outro campo mapeado
numa camada de texto) podem conter notação entre chaves `{X}` para inserir
um ícone no meio do texto, em vez de escrever a palavra por extenso. A
notação é a mesma usada por ferramentas de MTG em geral.

> Os ícones usados aqui são compostos a partir dos glifos oficiais do
> projeto [Mana](https://mana.andrewgioia.com/) (licença SIL OFL 1.1),
> com a paleta de cores oficial do mesmo projeto. Ver
> `assets/mana-src/ATTRIBUTION.md` para os detalhes de licenciamento.

Se a notação dentro das chaves não for reconhecida, o texto aparece como
digitado (ex: `{ZZ}`) em vez de sumir ou quebrar a geração da carta.

## Cores

| Notação | Ícone |
|---|---|
| `{W}` | branco |
| `{U}` | azul |
| `{B}` | preto |
| `{R}` | vermelho |
| `{G}` | verde |
| `{C}` | incolor |
| `{S}` | neve |

## Genérico e especiais

| Notação | Ícone |
|---|---|
| `{0}` … `{20}`, `{100}` | custo genérico |
| `{X}` | símbolo X |
| `{T}` | ativar (tap) |
| `{Q}` | desativar (untap) |
| `{E}` | energia |

> Outros valores numéricos de 2+ dígitos fora de 0–20/100 ainda aparecem
> como texto (ex: `{37}`) — sem ícone dedicado.

## Híbrido

Combina duas cores — o mana pode ser pago com qualquer uma das duas.

`{W/U}` `{W/B}` `{W/R}` `{W/G}` `{U/B}` `{U/R}` `{U/G}` `{B/R}` `{B/G}` `{R/G}`
(e as combinações inversas, ex: `{U/W}`)

## Two-brid (genérico ou cor)

Pode ser pago com 2 de mana genérico ou 1 da cor indicada.

`{2/W}` `{2/U}` `{2/B}` `{2/R}` `{2/G}`

## Phyrexian

Pode ser pago com a cor indicada ou com 2 pontos de vida.

`{W/P}` `{U/P}` `{B/P}` `{R/P}` `{G/P}` `{C/P}`

## Phyrexian híbrido

Combina duas cores em phyrexian — qualquer uma das duas cores, ou vida.

`{W/B/P}` `{W/R/P}` `{W/G/P}` `{W/U/P}` `{B/R/P}` `{B/G/P}` `{B/U/P}`
`{R/G/P}` `{R/U/P}` `{G/U/P}` (e combinações inversas)

## Como inserir sem decorar a notação

Tanto a tela de **Dados** quanto o campo "Texto fixo" do editor de
template têm um botão **🔮 Símbolo** que abre uma paleta visual — clique
no ícone desejado pra inserir a notação automaticamente na posição do
cursor.

## Exemplo de uso no CSV

```
rules_text: "{T}: Add {W} or {U} to your mana pool.\nWhenever you cast a Red spell, draw a card. {2/R}: Debug program."
```

Isso renderiza os símbolos de tap, mana branco, mana azul e o custo
híbrido `2/vermelho` como ícones inline, mantendo o resto como texto
normal — inclusive quebrando linha corretamente quando o texto for maior
que a largura da camada.
