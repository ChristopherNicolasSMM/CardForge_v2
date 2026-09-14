# Solução de problemas

## O texto ficou maior do que antes depois de atualizar

Isso é esperado, e é uma correção, não um bug novo: até essa atualização, o tamanho da fonte era calculado com uma resolução fixa (96 DPI) independente da resolução real da imagem sendo gerada — o efeito prático era um texto sistematicamente **menor do que o configurado**, principalmente na geração final (que roda a 300 DPI por padrão). Agora o tamanho bate com o que está configurado em cada camada.

Se você já tinha ajustado o tamanho de fonte "no olho" pra compensar esse encolhimento, pode precisar diminuir o `Tamanho (pt)` de algumas camadas depois dessa atualização. Use **◎ Ver renderização real** pra conferir.

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

## As quantidades de impressão do Proxy não batem com o que eu esperava

- Confirme que não marcou o modo **"uma folha cheia de cada"** sem querer — nesse modo, a quantidade digitada é ignorada (cada carta selecionada sempre enche a página inteira).
- Se duas cartas do seu dataset têm o mesmo valor no **campo identificador** (por padrão `name`), elas compartilham a mesma quantidade salva. Veja/ajuste em [Dados → Campo identificador](02-dados#campo-identificador).
- As quantidades ficam salvas por coleção — se você trocou de coleção, a lista reflete a quantidade salva (ou `1` por padrão) daquela coleção específica, não da anterior.

## Erro ao excluir um lote, card, template ou PDF de proxy (Windows)

- O CardForge já tenta algumas vezes automaticamente antes de desistir (arquivos recém-gerados às vezes ficam brevemente "em uso" no Windows — antivírus fazendo varredura, indexação do Explorer). Se o erro persistir mesmo assim:
  - Feche qualquer visualizador de imagem/PDF que tenha aberto o arquivo em questão.
  - Espere alguns segundos e tente excluir de novo.
  - Se for um antivírus específico fazendo a varredura demorar demais, considere adicionar a pasta `collections/` às exceções dele.

## A coleção "Geral" não aparece mais / não é recriada sozinha

Isso é proposital. Anos atrás, antes do sistema de coleções existir, templates e dados ficavam soltos em `templates/`, `assets/library/` e `assets/fonts_custom/` na raiz do projeto. Pra não perder esse conteúdo quando o sistema de coleções foi introduzido, o CardForge tinha uma migração automática: se nenhuma coleção existisse ainda e sobrasse algo nessas pastas legadas, ele criava sozinho uma coleção chamada "Geral" com esse conteúdo, toda vez que o app iniciava.

Essa migração automática foi desativada — o CardForge não cria mais pastas na raiz (`templates/`, `assets/library/`, `assets/fonts_custom/`) nem a coleção "Geral" sozinho. Se você ainda precisar migrar conteúdo legado daquelas pastas manualmente, a função continua disponível no código (`web/services/collections.py:migrate_legacy_if_needed()`), só não roda mais automaticamente no início.

## Usando o executável (.exe)

### O Windows avisou "o Windows protegeu seu PC" ou o antivírus acusou algo

É esperado, na primeira execução, com um executável sem assinatura de código digital (um certificado pago que o CardForge ainda não tem). Não significa que o arquivo está infectado — é o comportamento padrão do Windows/antivírus com qualquer executável não assinado, mesmo de projetos legítimos. Clique em **Mais informações → Executar assim mesmo** (SmartScreen) ou libere manualmente no seu antivírus.

### Onde ficam meus dados (coleções, cards gerados) quando uso o executável?

Numa pasta **ao lado do próprio `CardForge.exe`** — não em `%APPDATA%` nem em nenhum lugar escondido do sistema. Se você descompactou o `.zip` em `C:\CardForge\`, seus dados estão em `C:\CardForge\collections\`. Isso é proposital: mover a pasta inteira (backup, pendrive, outra máquina) leva os dados junto, sem precisar procurar em outro lugar.

### Fechei a janela preta (console) sem querer e o CardForge parou

É esperado — aquela janela é o próprio servidor rodando; fechá-la encerra o CardForge (os dados já salvos continuam intactos). Pra usar de novo, abra `CardForge.exe` outra vez.

### O navegador não abriu sozinho

Acontece raramente (por exemplo, se o navegador padrão do sistema não estiver configurado). A janela de console mostra o endereço a usar — algo como `http://127.0.0.1:5000/` — copie e cole manualmente na barra de endereço do navegador.
