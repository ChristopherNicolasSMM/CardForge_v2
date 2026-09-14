## CardForge v2.1.0

### ✨ Novidades

**Coleções com mais de um template agora geram certo.** 
Até aqui, Gerar e Proxy aplicavam sempre um único template escolhido a **todas** as linhas do dataset — se sua coleção mistura, por exemplo, cartas de combate e cartas de personagem na mesma tabela, gerar com o template errado tentava renderizar tudo nele. 
Agora existe a coluna reservada `_template`: marque nos Dados qual template é dono de cada linha (aparece como um dropdown, já populado com os templates da coleção ativa) e Gerar/Proxy filtram sozinhos. 
Se alguma linha ficar sem `_template` definido, ou apontando pra um template que não existe, a geração avisa e deixa você escolher: corrigir antes, ou marcar "gerar mesmo assim" e seguir ignorando essas linhas. Coleção com um único template não precisa mexer em nada — continua funcionando como sempre.

**Tabela de Dados com filtro, paginação e scroll próprio.** 
Datasets grandes (100+ linhas) ganharam three coisas:
- Campo de busca que filtra em todas as colunas de uma vez;
- Paginação (20/50/100/Todas por página);
- A área da tabela agora ocupa o espaço restante da tela e rola por conta própria, com cabeçalho de coluna fixo — não é mais preciso rolar a página inteira pra chegar na última linha.

**Menu lateral recolhível.** Clique na setinha na borda do menu pra deixar só os ícones e ganhar espaço de tela. O estado fica salvo no navegador e persiste entre páginas.

### 🐛 Correções

**A coleção "Geral" não é mais recriada sozinha.** Uma migração automática legada recriava a coleção "Geral" (e as pastas `templates/`, `assets/library/`, `assets/fonts_custom/` na raiz do projeto) toda vez que o app iniciava, mesmo depois de excluída manualmente. Essa migração foi desativada — o CardForge não cria mais nada na raiz sozinho.

### 📚 Documentação

Manual embutido (`/wiki`) atualizado: seção nova sobre filtro/paginação e a coluna `_template` em Dados, notas equivalentes em Gerar e Proxy, e uma entrada em Solução de Problemas explicando a desativação da migração da coleção Geral.
