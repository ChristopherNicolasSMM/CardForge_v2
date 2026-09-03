# Solução de problemas

## O texto de uma camada não aparece no card gerado

- Confira se o **Campo do dataset** da camada bate exatamente com o nome de uma coluna no dataset (sem acento, minúsculo — o sistema tenta ignorar maiúscula/minúscula, mas não corrige acentos ou espaços). Use o autocomplete do campo pra ver os nomes reais disponíveis na coleção ativa.
- Se a camada usa `condition` (`has_pt` ou `has_flavor`), ela só aparece quando os campos exigidos estiverem preenchidos naquela linha específica.
- Verifique se a camada está marcada como **Visível**.

## A fonte não aparece como esperado

- Fontes precisam estar em `.ttf`. Outros formatos (`.otf`, `.woff`) não são reconhecidos.
- Confirme que você selecionou a fonte certa no campo **Fonte** da camada — enviar a fonte não a aplica automaticamente a nenhuma camada existente.
- No **canvas do editor**, o texto pode parecer discretamente diferente da renderização final (é um preview rápido). Use **◎ Ver renderização real** para conferir o resultado exato.

## A imagem de fundo, logo ou arte não aparece

- Confirme que o arquivo é `.png`, `.jpg`, `.jpeg` ou `.webp`.
- Para uma camada de imagem **dinâmica** (puxando do dataset via `Campo do dataset`), o valor da coluna precisa ser exatamente o nome do arquivo como aparece na biblioteca — use sempre o seletor **Escolher** na tabela de Dados, em vez de digitar o caminho manualmente.
- Para uma camada de imagem **fixa** (a mesma em todo card, tipo um ícone ou selo), deixe o **Campo do dataset** vazio e envie a imagem pelo campo **Imagem fixa**, nas propriedades da camada.
- O sistema procura o arquivo na pasta do template, depois na biblioteca de imagens da coleção ativa (`assets/library/`), depois no diretório de trabalho — nessa ordem.

## Não consigo clicar/arrastar a camada que eu quero — outra camada sobreposta "rouba" o clique

- Selecione a camada certa pela **lista de camadas** (à esquerda) primeiro — depois disso, arrastar dentro da área dela no canvas sempre move ela, mesmo com outra camada visualmente por cima.
- Ou use **Alt+clique** repetidas vezes no mesmo ponto — cada clique passa pra próxima camada abaixo daquele ponto.
- Ou trave (🔒) a camada que está atrapalhando, na lista de camadas — enquanto travada, o clique no canvas atravessa ela direto pra próxima.
- Veja o manual de [Templates](01-templates#movendo-e-redimensionando-camadas) pra mais detalhes.

## Importei um CSV e os dados vieram bagunçados/trocados de coluna

Isso quase sempre é vírgula sem aspas dentro de um campo de texto livre (descrição, sabor, texto de regras). Como CSV usa vírgula como separador de coluna, uma vírgula *dentro* do texto quebra o campo em dois pedaços e desloca todas as colunas seguintes — silenciosamente, sem erro.

- Coloque entre aspas duplas (`"..."`) qualquer campo que possa conter vírgula.
- Evite vírgula solta no fim da linha (cria uma coluna extra sem nome).
- Ou importe via `.xlsx` em vez de `.csv` — cada célula já é isolada, sem esse risco.

Veja um exemplo comentado de um CSV com esse problema (e a correção) no manual de [Dados](02-dados#campos-totalmente-customizados-jogos-com-esquema-diferente).

## A geração em lote trava ou demora muito

- Datasets grandes (bem acima de 100 cards) podem levar mais tempo, já que a geração é síncrona (a página espera o lote inteiro terminar). Considere dividir o dataset em partes menores.
- Verifique se alguma imagem de arte referenciada no dataset é muito pesada (dezenas de MB) — isso pode deixar cada card mais lento de renderizar.

## O PDF de proxy saiu com o tamanho errado ao imprimir

- Ao imprimir, use a opção **tamanho real / sem escala / 100%** no diálogo de impressão. Se a impressora "ajustar à página" automaticamente, as medidas em milímetros dos cards ficam incorretas.

## Perdi o link de um lote gerado antigo

- A lista de lotes na tela de **Gerar** é por sessão de navegador. Se você limpou os cookies ou trocou de navegador, a lista visual se perde — mas os arquivos continuam em `collections/<coleção>/output/` no disco, e podem ser recuperados manualmente lá se necessário.

## Excluí um template ou uma coleção por engano

Não há como desfazer pela interface:
- Excluir um **template** remove a pasta `collections/<coleção>/templates/<nome>/` inteira.
- Excluir uma **coleção** remove `collections/<coleção>/` inteira — templates, dados, fontes, artes e tudo que já foi gerado dela.

Se você usa controle de versão (git) no projeto, é possível recuperar a pasta do histórico de commits.
