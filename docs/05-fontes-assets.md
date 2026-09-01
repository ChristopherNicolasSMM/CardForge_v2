# Fontes e biblioteca de imagens

## Fontes

CardForge procura uma fonte nesta ordem, parando na primeira que encontrar:

1. `templates/<nome-do-template>/fonts/` — fonte específica daquele template.
2. `assets/fonts_custom/` — fontes enviadas globalmente (disponíveis para qualquer template).
3. `assets/fonts/` — fontes embutidas no CardForge.

Na prática, isso significa que:

- Enviar uma fonte pelo **editor de template** (painel "Fontes") a torna exclusiva daquele template.
- Se dois templates diferentes precisam da mesma fonte customizada, você pode enviá-la nos dois, ou colocá-la diretamente em `assets/fonts_custom/` no disco (fora da interface) para que fique disponível a todos de uma vez.

Depois de enviada, a fonte aparece no seletor **Fonte** de qualquer camada de texto daquele template, usando o nome do arquivo (sem a extensão `.ttf`) como nome da família.

### Formatos aceitos

Apenas `.ttf`. Se você tem uma fonte em `.otf` ou `.woff`, converta para `.ttf` antes de enviar (há conversores gratuitos online).

## Biblioteca de imagens

As imagens de arte enviadas pela tela de **Dados** ficam em `assets/library/` e são compartilhadas entre todos os templates e todos os cards — envie uma vez, reutilize em quantas linhas do dataset quiser.

### Formatos aceitos

`.png`, `.jpg`, `.jpeg`, `.webp`.

### Onde as imagens de fundo dos templates ficam

Diferente da biblioteca de arte, a **imagem de fundo** e a **imagem de verso** de um template ficam salvas dentro da própria pasta daquele template (`templates/<nome>/`), não na biblioteca compartilhada — cada template tem seu próprio fundo.
