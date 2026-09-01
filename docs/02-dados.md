# Dados: importar e editar cards

A tela **Dados** guarda o dataset atual — a lista de cards que será usada na geração em lote e no proxy de impressão. Cada linha vira um card.

## Duas formas de alimentar o dataset

### 1. Importar um arquivo

Formatos aceitos: `.csv`, `.xlsx`, `.yml`/`.yaml`, `.json`. Clique em **Importar** e escolha o arquivo — isso **substitui** a tabela atual inteira.

Os nomes de coluna aceitam tanto o nome interno (`name`, `mana_cost`, `type_line`...) quanto o equivalente em português (`nome`, `custo_mana`, `tipo`...). O sistema normaliza automaticamente.

### 2. Editar direto na tabela

Clique em qualquer célula para editar o texto. Use **+ Card** para adicionar uma linha vazia, e o **✕** no final da linha para remover uma. Use **+ Coluna** para adicionar um campo novo que ainda não existe.

Depois de editar, clique em **Salvar alterações** — a edição na tabela não é salva automaticamente.

## Colunas padrão

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

## Exportando

O botão **Exportar CSV** baixa o dataset atual como `.csv` — útil para editar em outra ferramenta ou guardar uma cópia fora do CardForge.

## Preview ao vivo

No fim da tela, escolha um **template** e um **card** e clique em **Visualizar card** para ver a renderização real daquela linha específica com aquele template — sem precisar gerar o lote inteiro.
