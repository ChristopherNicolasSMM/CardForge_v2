# Fontes e biblioteca de imagens

## Fontes

CardForge procura uma fonte nesta ordem, parando na primeira que encontrar:

1. `templates/<nome-do-template>/fonts/` — fonte específica daquele template.
2. `assets/fonts_custom/` da **coleção ativa** — fontes enviadas nessa coleção, disponíveis para qualquer template dela.
3. `assets/fonts/` — fontes embutidas no CardForge (sempre globais, disponíveis em qualquer coleção).

Na prática, isso significa que:

- Enviar uma fonte pelo **editor de template** (painel "Fontes") a torna exclusiva daquele template.
- Fontes ficam isoladas por coleção — uma fonte enviada numa coleção não aparece em outra. Se duas coleções diferentes precisam da mesma fonte customizada, envie-a em cada uma.

Depois de enviada, a fonte aparece no seletor **Fonte** de qualquer camada de texto daquele template, usando o nome do arquivo (sem a extensão `.ttf`) como nome da família.

### Formatos aceitos

Apenas `.ttf`. Se você tem uma fonte em `.otf` ou `.woff`, converta para `.ttf` antes de enviar (há conversores gratuitos online).

## Biblioteca de imagens

As imagens de arte enviadas pela tela de **Dados** (pelo seletor **Escolher** na coluna `art`) ficam em `collections/<coleção>/assets/library/` — compartilhadas entre todos os templates e todos os cards **dessa coleção**. Envie uma vez, reutilize em quantas linhas do dataset quiser. Coleções diferentes têm bibliotecas separadas.

### Formatos aceitos

`.png`, `.jpg`, `.jpeg`, `.webp`.

### Onde as imagens fixas de um template ficam

Diferente da biblioteca de arte, a **imagem de fundo**, a **imagem de verso** e qualquer **imagem fixa** de camada (ver [Templates](01-templates#propriedades-de-uma-camada)) ficam salvas dentro da própria pasta daquele template (`collections/<coleção>/templates/<nome>/`), não na biblioteca compartilhada — cada template guarda suas próprias imagens fixas.

### Ordem de busca de imagens (dinâmicas e fixas)

Tanto uma camada de imagem **dinâmica** (puxando do dataset) quanto uma **fixa** procuram o arquivo nessa ordem:

1. Dentro da pasta do próprio template.
2. Na biblioteca de imagens (`assets/library/`) da coleção ativa.
3. No diretório de trabalho onde o servidor foi iniciado (evite depender disso — é o menos confiável dos três).
