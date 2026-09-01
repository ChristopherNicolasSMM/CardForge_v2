# Coleções

Uma **coleção** é a unidade organizadora do CardForge. Ela representa um jogo — ou uma atualização/expansão específica de um jogo — e é uma pasta própria e autocontida em disco:

```
collections/<coleção>/
  collection.json      ← nome, descrição, jogo
  templates/             ← os modelos de card dessa coleção
  assets/library/         ← imagens de arte enviadas nessa coleção
  assets/fonts_custom/     ← fontes enviadas nessa coleção
  data.json                ← o dataset de cards em edição
  output/                  ← lotes gerados + PDFs de proxy
```

Templates, dados, fontes e artes de uma coleção **nunca se misturam** com os de outra. Isso significa que você pode ter, por exemplo, "Meu TCG — Base" e "Meu TCG — Expansão 2" como coleções separadas, cada uma com seus próprios cards, sem risco de uma bagunçar a outra.

## Escolhendo uma coleção

Antes de usar Templates, Dados, Gerar ou Proxy, você precisa ter uma coleção **ativa**. A coleção ativa fica visível no topo da barra lateral, com um link pra trocar. Se você tentar acessar qualquer uma dessas telas sem coleção ativa, o CardForge te leva direto pra tela de Coleções.

A escolha da coleção ativa é por sessão de navegador (assim como no restante do sistema) — abas diferentes podem estar em coleções diferentes ao mesmo tempo.

## Criando uma coleção

Em **Coleções → + Nova coleção**, informe:

- **Nome** — obrigatório.
- **Jogo** (opcional) — útil quando várias coleções pertencem ao mesmo jogo (ex: "Base", "Expansão 1", "Expansão 2" todas do mesmo jogo).
- **Descrição** (opcional).

## Duplicando uma coleção (atualização de jogo)

Esse é o fluxo pensado especificamente para quando você lança uma atualização ou expansão de um jogo que já existe: em vez de recomeçar do zero, duplique a coleção base.

Ao duplicar, você escolhe **o que copiar**:

- **Templates** — geralmente sim, pra manter o mesmo layout visual.
- **Fontes e imagens da biblioteca** — geralmente sim, pelo mesmo motivo.
- **Dados** (os cards já cadastrados) — geralmente não, já que uma expansão costuma ter cards novos. Mas nada impede de trazer os dados também, se fizer sentido pro seu caso (ex: uma reimpressão com pequenos ajustes).

A nova coleção guarda uma referência de qual coleção original ela veio (`based_on`), só como informação — as duas continuam totalmente independentes depois de criadas.

## Importando um template de outra coleção

Se duas coleções diferentes (de jogos diferentes) devem compartilhar o mesmo layout de card, você não precisa recriar o template do zero: na tela de **Templates**, clique em **Importar de outra coleção**, escolha a coleção de origem e o template. Isso copia a pasta inteira do template (incluindo fundo, verso e fontes específicas dele) pra dentro da coleção atual — as duas cópias ficam independentes depois da importação; editar uma não afeta a outra.

## Excluindo uma coleção

Exclui a pasta inteira do disco — templates, dados, fontes, artes e tudo o que já foi gerado daquela coleção. Não pode ser desfeito pela interface.

## Migração de projetos antigos

Se você já vinha usando uma versão do CardForge anterior ao sistema de coleções (templates soltos na raiz do projeto), na primeira vez que o servidor sobe depois da atualização, tudo isso vira automaticamente uma coleção chamada **"Geral"** — nenhum template ou dado é perdido.
