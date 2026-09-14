# Dados: importar e editar cards

A tela **Dados** guarda o dataset atual — a lista de cards que será usada na geração em lote e no proxy de impressão. Cada linha vira um card.

A área da tabela ocupa o espaço restante da tela e rola por conta própria (o cabeçalho de coluna fica fixo no topo enquanto você desce) — não é preciso rolar a página inteira pra chegar na última linha de um dataset grande.

## Duas formas de alimentar o dataset

### 1. Importar um arquivo

Formatos aceitos: `.csv`, `.xlsx`, `.yml`/`.yaml`, `.json`. Clique em **Importar** e escolha o arquivo — isso **substitui** a tabela atual inteira.

Os nomes de coluna aceitam tanto o nome interno (`name`, `mana_cost`, `type_line`...) quanto o equivalente em português (`nome`, `custo_mana`, `tipo`...). O sistema normaliza automaticamente.

### 2. Editar direto na tabela

Clique em qualquer célula para editar o texto. Use **+ Card** para adicionar uma linha vazia, e o **✕** no final da linha para remover uma. Use **+ Coluna** para adicionar um campo novo que ainda não existe.

Pra inserir um símbolo de mana (ex: em `rules_text`) sem decorar a notação: clique na célula onde quer inserir, posicione o cursor onde o ícone deve entrar, clique no botão **🔮 Símbolo** na barra de ferramentas, e escolha o ícone na paleta — a notação certa (`{W}`, `{T}` etc.) é inserida automaticamente na posição do cursor. Veja a lista completa de símbolos e a notação correspondente em [Símbolos de mana](09-simbolos-mana).

As alterações são salvas automaticamente cerca de 1 segundo depois de parar de editar — um indicador ao lado dos botões mostra o status ("Alterações não salvas…" → "Salvo às HH:MM"). O botão **Salvar alterações** continua disponível pra salvar na hora, se preferir.

## Filtro e paginação

Acima da tabela, o campo **Filtrar em todas as colunas…** busca um texto em qualquer campo de qualquer linha (não diferencia maiúsculas/minúsculas) — útil pra achar um card específico num dataset com centenas de linhas sem precisar rolar.

O seletor **Por página** (20 / 50 / 100 / Todas) controla quantas linhas aparecem de uma vez; os botões abaixo da tabela navegam entre páginas. Filtro e paginação são só de visualização — **editar uma célula sempre grava na linha certa**, mesmo filtrada ou numa página diferente da primeira.

## Cartas por template (`_template`)

Se a coleção tem **mais de um template** (por exemplo, um pra cartas de combate e outro pra cartas de personagem), use o botão **+ Coluna _template** pra adicionar essa coluna reservada. Ela aparece como uma lista suspensa — escolha, em cada linha, qual template é o dono daquela carta.

Isso é o que permite [Gerar](03-gerar#cartas-por-template) e [Proxy](04-proxy#cartas-por-template) filtrarem automaticamente: ao gerar com um template, só as linhas marcadas com aquele template entram no lote — sem isso, escolher um template aplicava a **todas** as linhas do dataset de uma vez, mesmo as que pertenciam a outro tipo de carta.

Uma linha com `_template` vazio, ou apontando pra um nome de template que não existe (mostrado com ⚠ e borda destacada), fica de fora até ser corrigida.

> Coleção com um único template não precisa dessa coluna — sem ela, Gerar e Proxy continuam aplicando o template escolhido ao dataset inteiro, como sempre.

## Campo identificador

O CardForge precisa reconhecer cada carta em alguns lugares fora da tabela — por exemplo, na lista de quantidade da tela de [Proxy](04-proxy#quantidade-por-carta). Por padrão, ele usa o campo `name`; se o seu dataset não tiver esse campo, usa a primeira coluna.

Se isso não fizer sentido pro seu esquema (ex: seu identificador natural é `codigo` ou `sku`, não a primeira coluna por acidente de ordem), escolha explicitamente no seletor **Campo identificador**, no topo da tela de Dados. Fica salvo por coleção.

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
