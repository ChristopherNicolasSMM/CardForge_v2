# Templates: criar e editar

## Criando um template

Na galeria de **Templates**, clique em **+ Novo template**. Você escolhe:

- **Nome** — usado como identificador (vira o nome da pasta em disco). Evite espaços e acentos aqui; use hífen (`dragoes-vermelhos`, por exemplo).
- **Herdar de** (opcional) — escolha um template existente para reaproveitar todas as camadas dele. Você só precisa ajustar o que for diferente.
- **Imagem de fundo** (opcional) — pode ser enviada agora ou depois, direto no editor.

Ao salvar, você já entra no editor visual do template recém-criado.

## O editor visual

O editor tem três painéis:

- **Esquerda** — lista de camadas, upload de fundo/verso, upload de fontes.
- **Centro** — o canvas: o card em escala, com cada camada desenhada na posição real.
- **Direita** — propriedades da camada selecionada.

### Movendo e redimensionando camadas

Clique numa camada no canvas (ou na lista à esquerda) para selecioná-la. Depois:

- **Arraste o corpo da camada** para mover.
- **Arraste a alça no canto inferior direito** (o quadradinho laranja) para redimensionar.

Todas as posições são salvas em milímetros, então o card se comporta do mesmo jeito em qualquer resolução de tela.

### Alinhando camadas

No painel de propriedades, a seção **Alinhar na carta** tem seis botões que posicionam a camada selecionada relativa às bordas do card: esquerda, centro horizontal, direita, topo, centro vertical, base. É a forma rápida de deixar várias camadas alinhadas entre si (ex: encostar duas camadas na mesma margem esquerda) sem precisar acertar o `X`/`Y` manualmente.

### Organizando a ordem das camadas (o que fica na frente)

Quando duas camadas se sobrepõem, quem aparece por cima é definida pelo **z-index** — maior valor fica na frente. Em vez de adivinhar números, use os botões da seção **Ordem de empilhamento**:

| Botão | O que faz |
|---|---|
| ⇤ trás | Manda a camada selecionada pro fundo de tudo |
| ↓ | Troca de posição com a camada logo abaixo dela na pilha |
| ↑ | Troca de posição com a camada logo acima dela na pilha |
| frente ⇥ | Traz a camada selecionada pra frente de tudo |

O campo numérico abaixo dos botões continua disponível pra quem preferir digitar o z-index exato. A lista de camadas à esquerda mostra o z-index de cada uma, pra facilitar de enxergar a ordem atual.

### Propriedades de uma camada

| Campo | O que faz |
|---|---|
| Rótulo | Nome de exibição na lista de camadas (não afeta a renderização) |
| Campo do dataset | Nome da coluna que alimenta essa camada (ex: `name`, `power`). Deixe vazio para usar conteúdo fixo. Sugere automaticamente os campos que já existem no dataset da coleção ativa. |
| Texto fixo | Usado em camadas de **texto** quando o campo está vazio — um texto que não muda entre cards |
| Imagem fixa | Usado em camadas de **imagem** ou **fundo** quando o campo está vazio — uma imagem que não muda entre cards (ícone, selo, marca d'água, moldura fixa) |
| X, Y, Largura, Altura | Posição e tamanho em milímetros |
| Ordem de empilhamento / z-index | Ver seção acima |
| Encaixe | Para camadas de imagem/fundo: `cover` (preenche e corta), `contain` (encaixa sem cortar) ou `stretch` (estica) |
| Visível | Desmarque para ocultar a camada sem excluí-la |
| Multilinha | Quebra o texto automaticamente dentro da largura da camada |
| Fonte, tamanho, peso, estilo, cor, alinhamento | Estilo tipográfico (só se aplica a camadas de texto) |

### Adicionando uma nova camada

Escolha o tipo (**texto**, **imagem**, **fundo** ou **custo/ícone**) no seletor abaixo da lista de camadas e clique em **+ Adicionar camada**. Ela entra com valores padrão — ajuste a posição e o campo depois.

### Fundo e verso

- **Imagem de fundo** — a arte de moldura do card. Fica atrás de todas as outras camadas.
- **Imagem de verso** — usada apenas na folha de [proxy de impressão](04-proxy), como o verso comum de todos os cards desse template.

Esses dois campos, no painel esquerdo, são atalhos pra situações específicas (o fundo principal e o verso de impressão). Para qualquer **outra** camada de imagem ou fundo com conteúdo fixo — um ícone de canto, um selo de edição, uma marca d'água — use o campo **Imagem fixa** nas propriedades daquela camada (veja a tabela acima), deixando o **Campo do dataset** vazio.

### Fontes customizadas

Envie um arquivo `.ttf` no painel **Fontes**. Ela fica disponível especificamente para esse template (outros templates não são afetados, a menos que enviem a mesma fonte também). Depois de enviada, selecione-a no campo **Fonte** de qualquer camada de texto.

### Visualizando o resultado real

O canvas do editor é uma representação rápida, mas não é pixel-perfeito com o resultado final. Clique em **◎ Ver renderização real** a qualquer momento para ver exatamente como o card sairá, renderizado pelo mesmo motor usado na geração em lote — usando dados de exemplo.

### Salvando

Clique em **Salvar template**. Uploads de fundo, verso e fonte já salvam automaticamente ao serem enviados; só as edições de camada (posição, texto, estilo) precisam do clique em Salvar.

## Duplicando e excluindo

Na galeria, cada template tem os botões **Editar**, **Duplicar** e **Excluir**. Duplicar copia a pasta inteira (incluindo imagens e fontes específicas) com um novo nome — útil para criar uma variação sem afetar o original. Excluir remove a pasta inteira do disco e não pode ser desfeito.
