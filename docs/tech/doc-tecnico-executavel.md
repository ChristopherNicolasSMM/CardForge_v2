# Documento Técnico — Executável (PyInstaller)

**Projeto:** CardForge 2.0
**Escopo:** Empacotamento da aplicação Flask como executável standalone, pra uso por pessoas não-desenvolvedoras, sem precisar instalar Python/dependências manualmente.
**Status:** Implementado e validado localmente (build Linux, ver seção 7). Build Windows real ainda não gerado — ver seção 8 (pendências).

---

## 1. Contexto e motivação

O CardForge 2.0 é uma aplicação Flask — pra rodar hoje, é preciso ter Python instalado, criar um ambiente virtual, instalar `requirements.txt` e rodar `python run.py`. Isso é uma barreira real pra parte do público-alvo do projeto (comunidade de fãs, nem todos desenvolvedores).

Objetivo desta feature: gerar um executável que a pessoa baixa, abre, e o CardForge simplesmente funciona — sem instalar Python, sem linha de comando, com o navegador abrindo sozinho.

---

## 2. Decisões de arquitetura (confirmadas com o usuário antes de implementar)

| Decisão | Escolha | Motivo |
|---|---|---|
| Sistema operacional | Windows, por enquanto | Público majoritário; Mac/Linux ficam como extensão futura de baixo custo incremental (ver seção 6.1) |
| Local dos dados do usuário | Pasta ao lado do executável (portátil) | Simplicidade pra quem não é dev: mover a pasta inteira (backup, pendrive, outra máquina) continua funcionando, sem precisar saber onde o SO esconde `%APPDATA%` |
| Modo de empacotamento | `--onedir` (pasta), não `--onefile` | Inicialização mais rápida (`--onefile` descompacta tudo numa pasta temporária a cada execução); mais fácil de raciocinar sobre onde ficam os dados |
| CI de build automático | GitHub Actions, só Windows por ora | Sem custo incremental relevante adicionar Mac/Linux depois — é literalmente duplicar um job trocando o `runs-on` (ver seção 6.1) |

---

## 3. O problema central: dois tipos de "raiz" diferentes

Antes desta feature, todo módulo que precisava de um caminho de arquivo calculava sua própria "raiz do projeto" via `Path(__file__).resolve().parent...parent`. Isso funciona bem rodando a partir do código-fonte, mas quebra de duas formas diferentes sob um executável empacotado:

1. **Para recurso read-only** (fontes embutidas, ícones de mana, templates/estáticos do Flask, manuais da wiki): o `__file__` de um módulo empacotado pelo PyInstaller pode resolver pra dentro de uma pasta interna do bundle (`_internal/` no layout atual do PyInstaller 6.x) — ainda funciona, mas não é robusto contra mudanças de versão do PyInstaller nem contra o modo `--onefile` (onde `__file__` aponta pra uma pasta temporária *diferente a cada execução*).

2. **Para dado do usuário** (coleções, cards gerados, uploads): esse é o problema real. Se o código continuasse resolvendo esses caminhos do mesmo jeito, os dados do usuário iriam parar **dentro da pasta temporária de extração do PyInstaller** em modo `--onefile` — que é apagada/recriada a cada execução. Ou seja: o usuário perderia todas as coleções toda vez que fechasse o CardForge. Mesmo em `--onedir`, esses dados ficariam escondidos dentro de `_internal/`, junto com arquivos internos do bundle — nada portátil, e arriscado (um update do executável poderia sobrescrever `_internal/` inteiro).

### Solução: `core/paths.py`

Módulo novo, único ponto de verdade sobre as duas raízes:

```python
def resource_root() -> Path:
    """Recursos read-only empacotados. Em execução normal: raiz do repo.
    Empacotado: sys._MEIPASS (funciona em --onefile E --onedir)."""

def data_root() -> Path:
    """Dados do usuário, sempre graváveis. Em execução normal: raiz do
    repo (comportamento de sempre). Empacotado: SEMPRE a pasta que contém
    o executável — nunca a pasta temporária de extração."""
```

A distinção crítica: `data_root()` usa `Path(sys.executable).resolve().parent` (a pasta real onde o `.exe` está, estável entre execuções), enquanto `resource_root()` usa `sys._MEIPASS` (a pasta interna do bundle, correta pra recurso read-only, mas não confiável como local de gravação persistente).

### Arquivos refatorados pra usar isso

| Arquivo | O que mudou | Tipo de raiz |
|---|---|---|
| `web/config.py` | `BASE_DIR` → `data_root()`; `DOCS_DIR` → `resource_root() / "docs"` | Ambas (documentado inline por quê cada um é o que é) |
| `web/__init__.py` | `template_folder`/`static_folder` do Flask → `resource_root() / "web"` | Resource |
| `core/render/font_paths.py` | `BUILTIN_FONTS` → `resource_root()`; `_DEFAULT_CUSTOM_FONTS` (legado) → `data_root()` | Ambas |
| `core/render/svg_builder.py` | `FONTS_DIR` → `resource_root()` | Resource |
| `core/render/mana_symbols.py` | `ICONS_PNG_DIR` → `resource_root()` | Resource |
| `core/template/loader.py` | `ROOT` (raiz legada de templates, pré-coleções) → `data_root()` | Data |
| `core/render/preview_renderer.py` | `ROOT` removido (dead code — nunca era usado) | — |

Todos os outros lugares que lidam com caminho (`web/services/collections.py`, `session_data.py`, `assets.py`) já importavam de `web.config`, então herdaram a correção automaticamente, sem precisar editar esses arquivos.

---

## 4. `desktop_launcher.py` — ponto de entrada do executável

Não reaproveita `run.py` diretamente porque as necessidades são diferentes:

- **Nunca liga debug/reloader do Flask.** O reloader do Flask re-executa o processo via `sys.argv` pra vigiar mudança de arquivo — dentro de um binário congelado do PyInstaller isso não faz sentido nenhum (não há arquivo `.py` sendo "editado") e pode falhar de formas estranhas.
- **Escolhe porta livre automaticamente**, tentando 5000 primeiro (comportamento familiar de quem já roda a partir do código-fonte) e caindo pra outras se estiver ocupada — evita a experiência ruim de "não abre porque a porta já está em uso" sem explicação.
- **Abre o navegador padrão sozinho** (`webbrowser.open`, com um pequeno delay via `threading.Timer` pra dar tempo do servidor subir primeiro) — a pessoa não-dev não precisa saber que existe um endereço `http://127.0.0.1:...` pra digitar.
- **Imprime onde os dados estão** no console, na inicialização — útil pra quem for fazer backup ou mover a instalação.

---

## 5. `cardforge.spec`

Além do entry point, o spec declara explicitamente (`datas`) os recursos que precisam ir dentro do bundle preservando a estrutura de pasta relativa (é isso que `resource_root()` espera encontrar):

- `web/templates/`, `web/static/` — a interface inteira
- `assets/fonts/` — fontes embutidas
- `assets/icons_png/` — ícones de símbolo de mana (já pré-gerados, versionados no repo — ver `docs/tech/doc-tecnico-mtg-symbols-frames.md`)
- `docs/` — manuais da wiki

Não inclui `assets/mana-src/` (glifos vendorizados) nem `scripts/generate_mana_icons.py` — são artefatos de *desenvolvimento* (geram os PNGs que já vêm prontos), não são lidos em tempo de execução pela aplicação.

---

## 6. GitHub Actions (`.github/workflows/build-executable.yml`)

Builda automaticamente num runner `windows-latest` de verdade (não é cross-compilation — é uma máquina Windows real, gerenciada pela GitHub) sempre que:
- uma tag `v*` é publicada (ex: `v2.1.0`) → gera o `.zip` e anexa automaticamente ao Release correspondente
- disparado manualmente pela aba Actions → gera só o artifact, útil pra testar o build sem precisar cortar uma versão

### 6.1 Como estender pra macOS/Linux depois

Duplicar o job `build-windows`, trocando `runs-on: windows-latest` por `macos-latest`/`ubuntu-latest`, e o passo de empacotamento (`Compress-Archive`, específico do PowerShell) por um equivalente (`zip -r`, disponível nativamente nos runners Mac/Linux). O `cardforge.spec` não precisa de nenhuma mudança — é o mesmo arquivo pros três sistemas. A única ressalva real é a assinatura/notarização do macOS (ver seção 8).

---

## 7. Validação realizada

Não tenho acesso a uma máquina Windows a partir deste ambiente (sandbox Linux) — mas o mecanismo de "congelamento" do PyInstaller é o mesmo entre sistemas operacionais, só o formato final do binário muda. Pra validar a lógica de resolução de caminho de verdade (não só ler o código e confiar), buildei e rodei a versão **Linux** deste mesmo spec, dentro deste ambiente:

1. **Build:** `pyinstaller cardforge.spec` completou sem erro, gerando `dist/CardForge/` (executável + pasta `_internal/` com os recursos empacotados).
2. **Teste de portabilidade:** copiei `dist/CardForge/` pra uma pasta completamente diferente (`/tmp/CardForge_portable_test`), simulando o usuário movendo a instalação — e rodei o executável de lá.
3. **Confirmação do local dos dados:** o console imprimiu `Dados desta instalação: /tmp/CardForge_portable_test` — exatamente a pasta pra onde copiei, não um caminho temporário interno. Depois de usar o app, `collections/`, `templates/`, `assets/fonts_custom/`, `assets/library/`, `instance/` foram criados **ao lado do executável**, como esperado.
4. **Confirmação dos recursos empacotados:** `web/`, `assets/fonts/`, `assets/icons_png/`, `docs/` foram encontrados corretamente dentro de `_internal/` (não fiz suposição sobre essa estrutura — descobri checando o disco depois do build, porque o layout exato de pastas internas do PyInstaller varia entre versões).
5. **Teste funcional via HTTP real** (não só leitura de arquivo): com o executável rodando, usei `curl` pra:
   - Carregar a página inicial, CSS estático, o manual da wiki (`/wiki/` → 200, título correto vindo do markdown empacotado)
   - Consultar `/symbols/manifest` → 64 símbolos retornados corretamente
   - Criar uma coleção, criar um template, abrir o editor (confirmando que o botão da paleta de símbolos está presente no HTML servido)
   - **Gerar uma renderização de card de verdade** (`/templates/T1/preview`, o mesmo endpoint que a UI usa) — recebi de volta um PNG de ~12KB, que abri e conferi visualmente: nome, custo de mana com ícones (tap + mana azul), tipo e texto de regras todos corretos, usando a fonte Beleren-Bold embutida.

Esse último ponto é o mais importante: confirma que PIL, a fonte customizada, e o pipeline de renderização inteiro funcionam de dentro do executável empacotado — não só que o servidor Flask sobe.

---

## 8. Limitações conhecidas e pendências

- **Build Windows real ainda não foi gerado.** Tudo o que foi validado (seção 7) foi num binário Linux equivalente — a lógica de caminho é a mesma, mas nunca substitui testar o artefato real que o usuário vai baixar. Recomendação: rodar o workflow do GitHub Actions (disparo manual) assim que isso for mesclado, baixar o `.zip` gerado, e testar numa máquina Windows de verdade antes do primeiro release.
- **Ícone do executável:** o build Linux ignorou o `.ico` (esperado — `.ico`/`.icns` só são aplicados em Windows/Mac pelo PyInstaller). Não dá pra confirmar visualmente que o ícone aparece certo no `.exe` sem testar no Windows.
- **Console sempre visível:** o spec usa `console=True` — a pessoa vê uma janela de terminal atrás do navegador (com a URL e onde os dados estão, que pode ser útil, mas também "não parece um app profissional"). Alternativa (`console=False` + ícone de bandeja do sistema via alguma lib tipo `pystray`) é mais polida mas adiciona complexidade e uma dependência nova — decisão consciente de deixar assim por ora, mais simples e mais fácil de depurar se algo der errado na primeira versão.
- **macOS (quando for a vez):** sem uma conta de desenvolvedor Apple paga, o Gatekeeper vai mostrar aviso de "desenvolvedor não identificado" no primeiro uso — não impede de rodar (botão direito → Abrir resolve), mas não é plug-and-play. Registrado aqui pra não pegar ninguém de surpresa quando essa extensão acontecer.
- **Antivírus/SmartScreen do Windows:** executáveis gerados por PyInstoller sem assinatura de código (`code signing certificate`, também pago) frequentemente disparam avisos de "Windows protegeu seu PC" ou até falsos positivos de antivírus — comportamento comum e conhecido do ecossistema PyInstaller, não específico deste projeto, mas vale documentar no README/wiki pra usuários não ficarem alarmados.

---

## 9. Como gerar o executável localmente

```bash
pip install -r requirements.txt -r requirements-build.txt
pyinstaller cardforge.spec --noconfirm
```

Resultado em `dist/CardForge/` — essa pasta inteira é o "app" a distribuir (zipar e compartilhar, ou copiar direto).

## 10. Como cortar um release com build automático

1. `git tag v2.1.0 && git push --tags` (ajustar o número da versão)
2. O workflow builda automaticamente e anexa `CardForge-windows.zip` ao Release correspondente no GitHub
3. Ou, pra testar sem cortar uma tag: aba **Actions** → **Build do executável** → **Run workflow** — gera só o artifact, pra baixar e testar manualmente
