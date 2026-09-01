# Referência: formato do template (base.json)

Este é um manual técnico para quem quer editar um template diretamente no arquivo, ou entender o que o editor visual está salvando por baixo dos panos. Não é necessário lê-lo para usar o CardForge normalmente.

## Estrutura geral

Cada template vive em `templates/<nome>/base.json`:

```json
{
  "meta": { "name": "meu-template", "inherits": null },
  "card": { "width_mm": 63.0, "height_mm": 88.0, "dpi": 300 },
  "gradients": {
    "red": { "id": "red", "stops": [
      { "offset": "0%", "color": "#E34234" },
      { "offset": "100%", "color": "#B22222" }
    ] }
  },
  "layers": [ ... ],
  "back_image": ""
}
```

| Chave | Descrição |
|---|---|
| `meta.name` | Nome do template (deve bater com o nome da pasta) |
| `meta.inherits` | Nome de outro template a herdar, ou `null` |
| `card.width_mm` / `card.height_mm` | Dimensões físicas do card |
| `card.dpi` | Resolução usada na renderização final (padrão 300) |
| `gradients` | Gradientes de cor usados como *fallback* quando uma camada `background` não tem imagem |
| `layers` | Lista de camadas (ver abaixo) |
| `back_image` | Nome do arquivo de imagem do verso, dentro da mesma pasta do template |

## Camadas (`layers`)

```json
{
  "id": "card_name",
  "type": "text",
  "label": "Nome",
  "field": "name",
  "static_text": "",
  "condition": "",
  "x_mm": 3.5, "y_mm": 3.5, "width_mm": 46, "height_mm": 5.5,
  "z_index": 10,
  "visible": true,
  "multiline": false,
  "fit": "cover",
  "source_image": "",
  "source_gradient": "",
  "style": {
    "font_family": "Beleren-Bold",
    "font_size_pt": 10.0,
    "font_weight": "bold",
    "font_style": "normal",
    "color": "#111111",
    "align": "left",
    "line_height_pt": 0.0
  }
}
```

### Tipos de camada (`type`)

| Tipo | Descrição |
|---|---|
| `background` | Imagem de fundo ou gradiente (usa `gradients` quando não há `source_image`) |
| `image` | Arte do card — o valor de `field` aponta para uma coluna do dataset com o caminho da imagem |
| `text` | Texto dinâmico (via `field`) ou fixo (via `static_text`) |
| `mana` | Igual a `text`, semanticamente reservado para custo/símbolos |

### Campos importantes

- **`field`** — nome da coluna do dataset. Se vazio (ou `"static"`), a camada usa `static_text` em vez de puxar do dataset.
- **`condition`** — controla se a camada aparece: `""` (sempre), `"has_pt"` (só se `power` e `toughness` estiverem preenchidos) ou `"has_flavor"` (só se `flavor_text` estiver preenchido).
- **`fit`** — só relevante para `background`/`image`: `cover` (preenche e corta o excesso), `contain` (encaixa sem cortar, pode sobrar espaço) ou `stretch` (distorce para caber exatamente).
- **`line_height_pt`** — `0` significa automático (`font_size_pt × 1.35`).

## Herança entre templates

Um template filho referencia o pai via `meta.inherits`. O filho só precisa declarar o que é **diferente** do pai:

```json
{
  "meta": { "name": "meu-filho", "inherits": "fang" },
  "layers": {
    "card_name": { "style": { "color": "#FFFFFF", "font_size_pt": 12 } }
  }
}
```

Note que no filho, `layers` pode ser um **objeto** (`{id: propriedades}`) em vez de lista — o sistema faz o *merge* de cada camada citada com a camada de mesmo `id` no pai, mantendo tudo que não foi sobrescrito. Camadas novas (com `id` que não existe no pai) são adicionadas ao final. Para remover uma camada herdada, use `{"delete": true}` no lugar das propriedades.

## Formato legado

Templates muito antigos (formato anterior à 1.0, com uma chave `elements` na raiz do JSON) são detectados e convertidos automaticamente ao carregar — coordenadas em pixels viram milímetros, `font_size` em pixels vira `font_size_pt`. A conversão só é salva em disco quando você salva o template pela interface; até lá, o arquivo original permanece intacto.
