# Dados: importar e editar cards

A tela **Dados** guarda o dataset atual — a lista de cards que será usada na geração em lote e no proxy de impressão. Cada linha vira um card.

## Duas formas de alimentar o dataset

### 1. Importar um arquivo

Formatos aceitos: `.csv`, `.xlsx`, `.yml`/`.yaml`, `.json`. Clique em **Importar** e escolha o arquivo — isso **substitui** a tabela atual inteira.

Os nomes de coluna aceitam tanto o nome interno (`name`, `mana_cost`, `type_line`...) quanto o equivalente em português (`nome`, `custo_mana`, `tipo`...). O sistema normaliza automaticamente.

### 2. Editar direto na tabela

Clique em qualquer célula para editar o texto. Use **+ Card** para adicionar uma linha vazia, e o **✕** no final da linha para remover uma. Use **+ Coluna** para adicionar um campo novo que ainda não existe.

As alterações são salvas automaticamente cerca de 1 segundo depois de parar de editar — um indicador ao lado dos botões mostra o status ("Alterações não salvas…" → "Salvo às HH:MM"). O botão **Salvar alterações** continua disponível pra salvar na hora, se preferir.

## Campos totalmente customizados (jogos com esquema diferente)

Os "Colunas padrão" acima são só um **ponto de partida sugerido**, no estilo Magic — nada nelas é obrigatório. Se o seu jogo usa conceitos completamente diferentes (ex: "Ataque", "Defesa", "Elemento", "Nível de Energia"), você tem duas formas de trabalhar só com os seus próprios campos:

1. **Ao criar a coleção**, escolha a opção **"Começar em branco"** — o dataset dessa coleção nasce sem nenhum campo padrão, e você monta a lista do zero com **+ Coluna**.
2. **Numa coleção já existente**, use os ícones no cabeçalho de cada coluna da tabela:
   - **✎ (renomear)** — muda o nome do campo em todos os cards de uma vez (ex: transformar `power` em `ataque`).
   - **✕ (remover)** — apaga o campo de todos os cards.

Importar um arquivo (CSV/XLSX/YAML/JSON) também respeita isso: as colunas do dataset passam a ser exatamente as colunas que o seu arquivo trouxe — nenhum campo padrão de MTG é adicionado à força se o seu arquivo não os tiver.

### Mapeando campos no template

No editor de template, o campo **"Campo do dataset"** de cada camada (veja o manual de [Templates](01-templates)) sugere automaticamente, num autocomplete, os nomes de campo que já existem no dataset da coleção ativa — assim fica fácil conectar visualmente cada camada do card ao dado certo, mesmo com um esquema totalmente próprio.

### Cuidado com vírgulas dentro de campos, ao importar CSV

Se algum campo de texto livre (descrição, sabor, texto de regras) puder conter vírgula, **coloque esse campo entre aspas duplas** no seu `.csv` — senão a vírgula interna quebra a coluna em dois pedaços e desloca tudo que vem depois, silenciosamente, sem erro na importação.

Errado (a vírgula dentro do texto quebra a coluna seguinte):
```csv
Rotulo,Informacoes
Sangue de Druida,Uma cerveja de cor avermelhada, com aroma maltado.
```

Certo:
```csv
Rotulo,Informacoes
Sangue de Druida,"Uma cerveja de cor avermelhada, com aroma maltado."
```

O repositório tem um exemplo completo e correto em `modelo_import/teste-rotulo.csv` — um dataset de rótulos de cerveja com campos 100% customizados (`Cervejaria`, `ABV`, `IBU`, `Harmon1`...), pronto pra importar e usar como referência. Se preferir não se preocupar com aspas, importe via `.xlsx` em vez de `.csv` — cada célula já é isolada naturalmente.

## Colunas padrão (ponto de partida sugerido, estilo MTG)

| Coluna | Uso |
|---|---|
| `name` | Nome do card |
| `mana_cost` | Custo (texto livre) |
| `type_line` | Linha de tipo |
| `rules_text` | Texto de regras |
| `flavor_text` | Texto de sabor |
| `power` / `toughness` | Força / Resistência |
| `artist` | Crédito do artista |
| `rarity` | Raridade |
| `art` | Caminho da imagem de arte (veja abaixo) |
| `color` | Cor — usada como *fallback* de gradiente quando o template não tem imagem de fundo fixa |

Você não está limitado a essas colunas — adicione qualquer campo customizado e referencie-o no **Campo do dataset** de uma camada no editor de template.

## Imagens de arte

Em vez de digitar um caminho de arquivo, clique em **Escolher** na célula da coluna `art`. Isso abre a biblioteca de imagens, de onde você pode:

- Selecionar uma imagem já enviada anteriormente.
- Enviar uma nova imagem (fica disponível para qualquer card, não só o atual).

> O seletor visual de imagem aparece especificamente na coluna chamada `art`. Se você remover ou renomear esse campo, a célula volta a ser um texto comum (ainda funciona, só sem o seletor) — para ter o seletor de volta, crie novamente uma coluna com esse nome exato.

## Exportando

O botão **Exportar CSV** baixa o dataset atual como `.csv` — útil para editar em outra ferramenta ou guardar uma cópia fora do CardForge.

## Preview ao vivo

No fim da tela, escolha um **template** e um **card** e clique em **Visualizar card** para ver a renderização real daquela linha específica com aquele template — sem precisar gerar o lote inteiro.
