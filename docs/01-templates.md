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

- **Arraste o corpo da camada** para mover — a camada **selecionada** sempre tem prioridade no arraste, mesmo que outra camada esteja visualmente por cima dela nesse ponto do canvas. Assim, depois de selecionar pela lista uma camada que está "escondida" atrás de outra, você consegue arrastá-la normalmente.
- **Arraste a alça no canto inferior direito** (o quadradinho laranja) para redimensionar.
- **Setas do teclado** movem a camada selecionada em passos pequenos (0,5mm); segure **Shift** pra passos maiores (2mm) — útil pra ajustes finos difíceis de acertar só com o mouse.
- **Alt+clique** no canvas "fura" a pilha de camadas: cada Alt+clique no mesmo ponto seleciona a próxima camada abaixo daquela, ciclando pela pilha inteira ali. Use isso quando quiser selecionar uma camada só clicando no canvas, mesmo com várias sobrepostas no mesmo lugar.

Todas as posições são salvas em milímetros, então o card se comporta do mesmo jeito em qualquer resolução de tela.

### Travando uma camada

Clique no ícone 🔓 ao lado do nome de uma camada, na lista à esquerda, pra travá-la (vira 🔒). Uma camada travada:

- **Não é mais selecionável por clique no canvas** — o clique atravessa ela e pega o que estiver embaixo (ou nada, se não houver mais nada ali).
- Ainda pode ser selecionada pela **lista de camadas**, e editada normalmente pelo painel de propriedades (os campos numéricos continuam funcionando).
- Não pode ser arrastada nem redimensionada pelo canvas enquanto estiver travada.

É útil pra proteger uma camada grande (como o fundo) de atrapalhar cliques nas camadas menores por cima dela. Também dá pra travar/destravar pelo checkbox **Bloqueada** no painel de propriedades.

### Selecionando várias camadas ao mesmo tempo

Segure **Ctrl** (ou **Cmd** no Mac) e clique numa camada — na lista à esquerda ou no próprio canvas — pra adicioná-la à seleção sem perder a(s) que já estavam selecionadas. Clicar de novo numa camada já selecionada (ainda segurando Ctrl/Cmd) a remove da seleção.

Com várias camadas selecionadas:

- **Arrastar** qualquer uma delas no canvas move o grupo inteiro junto, mantendo a posição relativa entre elas.
- **Setas do teclado** deslocam todas as selecionadas ao mesmo tempo.
- O painel de propriedades mostra um aviso ("N camadas selecionadas") e passa a **aplicar qualquer alteração a todas de uma vez** — mude a fonte, o alinhamento, a cor, o que for, e todas as camadas selecionadas recebem o novo valor.
- Quando um campo tem valores **diferentes** entre as camadas selecionadas, ele aparece em branco (com a dica "valores diferentes") em vez de mostrar um valor de uma camada só, arbitrariamente — assim que você digita algo nele, esse valor passa a valer pra todas.
- **Alinhar na carta** alinha cada camada selecionada à borda da carta, independentemente — não umas em relação às outras.
- **Trazer para frente / enviar para trás** aplica ao grupo inteiro, preservando a ordem relativa entre as camadas selecionadas. **Subir uma camada / descer uma camada** (troca com a vizinha) continua valendo só pra última camada clicada, já que não faz sentido bem definido pra um grupo.
- **Excluir camada** exclui todas as selecionadas de uma vez (com confirmação mostrando quantas).

Clicar numa camada **sem** segurar Ctrl/Cmd sempre volta a selecionar só ela, limpando a seleção anterior.

### Alinhando camadas

No painel de propriedades, a seção **Alinhar na carta** tem seis botões que posicionam a camada selecionada relativa às bordas do card: esquerda, centro horizontal, direita, topo, centro vertical, base. É a forma rápida de deixar várias camadas alinhadas entre si (ex: encostar duas camadas na mesma margem esquerda) sem precisar acertar o `X`/`Y` manualmente.

### Zoom no canvas

Os controles **−** / **+** / **100%** acima do canvas ajustam o zoom (25% a 400%), pra ajustar posições com mais precisão em camadas pequenas ou em detalhes finos. **Ctrl+roda do mouse** sobre o canvas também funciona como atalho de zoom. O canvas ganha barra de rolagem automaticamente quando o zoom deixa o card maior que a área visível.

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
| Fonte, tamanho, peso, estilo, cor | Estilo tipográfico (só se aplica a camadas de texto) |
| Alinhamento | Alinhamento horizontal do texto dentro da caixa: esquerda, centro ou direita |
| Alinhamento vertical | Posição do bloco de texto dentro da altura da caixa: topo (padrão), centro ou base — útil quando a caixa é mais alta que o texto |
| Espaçamento entre letras | Distância extra entre cada caractere, em pt. `0` usa o espaçamento normal da fonte; valores maiores afastam as letras |

### Adicionando uma nova camada

Escolha o tipo (**texto**, **imagem**, **fundo** ou **custo/ícone**) no seletor abaixo da lista de camadas e clique em **+ Adicionar camada**. Ela entra com valores padrão — ajuste a posição e o campo depois.

### Fundo e verso

- **Imagem de fundo** — a arte de moldura do card. Fica atrás de todas as outras camadas.
- **Imagem de verso** — usada apenas na folha de [proxy de impressão](04-proxy), como o verso comum de todos os cards desse template.

Abaixo de cada campo, uma bolinha indica se já existe uma imagem definida: 🟢 verde com o nome do arquivo quando tem, 🔴 vermelha com "nenhuma imagem definida" quando não tem. Esse indicador reflete o que está realmente salvo no template — diferente do campo de arquivo em si, que o navegador sempre mostra como "nenhum arquivo escolhido" depois de recarregar a página, mesmo com uma imagem já definida.

Esses dois campos, no painel esquerdo, são atalhos pra situações específicas (o fundo principal e o verso de impressão). Para qualquer **outra** camada de imagem ou fundo com conteúdo fixo — um ícone de canto, um selo de edição, uma marca d'água — use o campo **Imagem fixa** nas propriedades daquela camada (veja a tabela acima), deixando o **Campo do dataset** vazio.

### Fontes customizadas

Envie um arquivo `.ttf` no painel **Fontes**. Ela fica disponível especificamente para esse template (outros templates não são afetados, a menos que enviem a mesma fonte também). Depois de enviada, selecione-a no campo **Fonte** de qualquer camada de texto.

### Visualizando o resultado real

O canvas do editor é uma representação rápida, mas não é pixel-perfeito com o resultado final. Clique em **◎ Ver renderização real** a qualquer momento para ver exatamente como o card sairá, renderizado pelo mesmo motor usado na geração em lote — usando dados de exemplo.

### Salvando

O editor salva sozinho: cerca de 1 segundo depois da última alteração (arrastar, digitar, alinhar, etc.), a edição é salva automaticamente — um indicador ao lado dos botões mostra **"Alterações não salvas…"** durante esse intervalo e **"Salvo às HH:MM"** depois que salva. O botão **Salvar template** continua disponível pra salvar na hora, se preferir não esperar.

Se você tentar sair da página (fechar a aba, recarregar, ou clicar em outro item do menu) enquanto ainda houver uma alteração não salva, o navegador mostra um aviso de confirmação antes de sair — proteção extra pra aquele intervalo curto antes do auto-save disparar.

### Organizando o painel de propriedades

O painel da direita é dividido em grupos colapsáveis — **Conteúdo**, **Posição e tamanho**, **Camada**, **Tipografia** — clique no título de um grupo pra abrir ou fechar. O painel também tem rolagem própria (fica fixo enquanto você rola o resto da página), então não precisa mais descer a tela inteira pra alcançar uma opção mais abaixo.

## Duplicando e excluindo

Na galeria, cada template tem os botões **Editar**, **Duplicar** e **Excluir**. Duplicar copia a pasta inteira (incluindo imagens e fontes específicas) com um novo nome — útil para criar uma variação sem afetar o original. Excluir remove a pasta inteira do disco e não pode ser desfeito.
