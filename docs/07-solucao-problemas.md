# Solução de problemas

## O texto de uma camada não aparece no card gerado

- Confira se o **Campo do dataset** da camada bate exatamente com o nome de uma coluna no dataset (sem acento, minúsculo, `snake_case` — ex: `mana_cost`, não `Custo Mana`).
- Se a camada usa `condition` (`has_pt` ou `has_flavor`), ela só aparece quando os campos exigidos estiverem preenchidos naquela linha específica.
- Verifique se a camada está marcada como **Visível**.

## A fonte não aparece como esperado

- Fontes precisam estar em `.ttf`. Outros formatos (`.otf`, `.woff`) não são reconhecidos.
- Confirme que você selecionou a fonte certa no campo **Fonte** da camada — enviar a fonte não a aplica automaticamente a nenhuma camada existente.
- No **canvas do editor**, o texto pode parecer discretamente diferente da renderização final (é um preview rápido). Use **◎ Ver renderização real** para conferir o resultado exato.

## A imagem de fundo ou arte não aparece

- Confirme que o arquivo é `.png`, `.jpg`, `.jpeg` ou `.webp`.
- Para arte de card (camada `image`), o valor da coluna do dataset precisa ser exatamente o nome do arquivo como aparece na biblioteca (a forma mais segura é sempre usar o seletor **Escolher** na tabela de Dados, em vez de digitar o caminho manualmente).

## A geração em lote trava ou demora muito

- Datasets grandes (bem acima de 100 cards) podem levar mais tempo, já que a geração é síncrona (a página espera o lote inteiro terminar). Considere dividir o dataset em partes menores.
- Verifique se alguma imagem de arte referenciada no dataset é muito pesada (dezenas de MB) — isso pode deixar cada card mais lento de renderizar.

## O PDF de proxy saiu com o tamanho errado ao imprimir

- Ao imprimir, use a opção **tamanho real / sem escala / 100%** no diálogo de impressão. Se a impressora "ajustar à página" automaticamente, as medidas em milímetros dos cards ficam incorretas.

## Perdi o link de um lote gerado antigo

- A lista de lotes na tela de **Gerar** é por sessão de navegador. Se você limpou os cookies ou trocou de navegador, a lista visual se perde — mas os arquivos continuam em `instance/<sessão-antiga>/output/` no disco, e podem ser recuperados manualmente lá se necessário.

## Excluí um template por engano

Não há como desfazer pela interface — a pasta inteira (`templates/<nome>/`) é removida do disco. Se você usa controle de versão (git) no projeto, é possível recuperar a pasta do histórico de commits.
