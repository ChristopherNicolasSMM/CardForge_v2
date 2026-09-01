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

### Propriedades de uma camada

| Campo | O que faz |
|---|---|
| Rótulo | Nome de exibição na lista de camadas (não afeta a renderização) |
| Campo do dataset | Nome da coluna que alimenta essa camada (ex: `name`, `power`). Deixe vazio para usar texto fixo. |
| Texto fixo | Usado quando o campo está vazio — um texto que não muda entre cards |
| X, Y, Largura, Altura | Posição e tamanho em milímetros |
| Camada (z-index) | Ordem de empilhamento — maior fica na frente |
| Encaixe | Para camadas de imagem/fundo: `cover` (preenche e corta), `contain` (encaixa sem cortar) ou `stretch` (estica) |
| Visível | Desmarque para ocultar a camada sem excluí-la |
| Multilinha | Quebra o texto automaticamente dentro da largura da camada |
| Fonte, tamanho, peso, estilo, cor, alinhamento | Estilo tipográfico (só se aplica a camadas de texto) |

### Adicionando uma nova camada

Escolha o tipo (**texto**, **imagem**, **fundo** ou **custo/ícone**) no seletor abaixo da lista de camadas e clique em **+ Adicionar camada**. Ela entra com valores padrão — ajuste a posição e o campo depois.

### Fundo e verso

- **Imagem de fundo** — a arte de moldura do card. Fica atrás de todas as outras camadas.
- **Imagem de verso** — usada apenas na folha de [proxy de impressão](04-proxy), como o verso comum de todos os cards desse template.

### Fontes customizadas

Envie um arquivo `.ttf` no painel **Fontes**. Ela fica disponível especificamente para esse template (outros templates não são afetados, a menos que enviem a mesma fonte também). Depois de enviada, selecione-a no campo **Fonte** de qualquer camada de texto.

### Visualizando o resultado real

O canvas do editor é uma representação rápida, mas não é pixel-perfeito com o resultado final. Clique em **◎ Ver renderização real** a qualquer momento para ver exatamente como o card sairá, renderizado pelo mesmo motor usado na geração em lote — usando dados de exemplo.

### Salvando

Clique em **Salvar template**. Uploads de fundo, verso e fonte já salvam automaticamente ao serem enviados; só as edições de camada (posição, texto, estilo) precisam do clique em Salvar.

## Duplicando e excluindo

Na galeria, cada template tem os botões **Editar**, **Duplicar** e **Excluir**. Duplicar copia a pasta inteira (incluindo imagens e fontes específicas) com um novo nome — útil para criar uma variação sem afetar o original. Excluir remove a pasta inteira do disco e não pode ser desfeito.
