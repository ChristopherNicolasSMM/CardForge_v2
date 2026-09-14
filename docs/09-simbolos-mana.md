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

## Símbolos customizados por coleção

As tabelas acima são o catálogo **embutido**, sempre disponível
globalmente em qualquer coleção (estilo MTG: cores, genérico, tap...) — e
continuam funcionando exatamente assim, sem nenhuma mudança de
comportamento.

Se o seu jogo tem seus próprios conceitos (ex: "fogo", "água", "escudo"),
não é preciso mexer no catálogo embutido nem despejar arquivos na pasta
global do CardForge. Cada coleção pode ter seu próprio conjunto de
símbolos, isolado das demais:

```
collections/<coleção>/assets/icons_png/
  manifest.json      ← notações customizadas dessa coleção
  <arquivos .png>      ← os ícones referenciados no manifest
```

`manifest.json` é uma lista de objetos:

```json
[
  { "notation": "fogo",  "file": "fogo.png",  "category": "Duelo das Tavernas", "label": "Fogo" },
  { "notation": "agua",  "file": "agua.png",  "category": "Duelo das Tavernas", "label": "Água" }
]
```

Com isso, `{fogo}` e `{agua}` passam a funcionar em qualquer campo de
texto dessa coleção, do mesmo jeito que `{W}` funciona pra Magic — inclusive
aparecendo na paleta visual do botão **🔮 Símbolo**, junto com o catálogo
embutido. Outras coleções não são afetadas: uma notação customizada só
existe dentro da coleção que a define.

Também é possível **sobrescrever** um ícone embutido só numa coleção
específica, sem tocar no global: basta colocar um arquivo com o mesmo
caminho relativo do catálogo embutido dentro da pasta `assets/icons_png/`
dessa coleção (ex: um `W.png` próprio) — ele passa a ter prioridade sobre
o ícone global, só nessa coleção.

Coleções sem `manifest.json` e sem arquivos próprios em `assets/icons_png/`
comportam-se exatamente como antes dessa funcionalidade existir.
