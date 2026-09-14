# Documento Técnico — Exclusão Resiliente a Bloqueios do Windows

**Projeto:** CardForge 2.0
**Escopo:** Corrigir `PermissionError: [WinError 5] Acesso negado` ao excluir lotes gerados, cards individuais, templates e PDFs de proxy no Windows.
**Status:** Implementado e validado (retry testado isoladamente + fluxo completo via Flask, sem regressão).

---

## 1. O bug reportado

Em produção (Windows), excluir um lote de cards gerado (`POST /generate/delete/<batch_id>`) derrubava com:

```
PermissionError: [WinError 5] Acesso negado: '...\output\<lote>\png'
  File "generate_bp.py", line 172, in delete_batch
    shutil.rmtree(batch_dir)
```

Causa: no Windows, um arquivo pode continuar "em uso" do ponto de vista do SO por um instante depois que a aplicação parou de precisar dele — um handle de fonte (PIL/FreeType) ou de imagem ainda em cache, antivírus fazendo varredura no arquivo recém-criado, ou indexação do Explorer. `shutil.rmtree` sem proteção nenhuma falha na hora, mesmo quando o bloqueio se resolveria sozinho um instante depois.

## 2. Não era a primeira vez

`web/services/collections.py` já tinha resolvido exatamente esse problema, só que **apenas para exclusão de coleção inteira** (`_rmtree_retry`, função privada): tenta de novo algumas vezes, liberando cache de fontes e forçando garbage collection entre as tentativas, antes de desistir e propagar o erro real. Levantamento no restante do código mostrou o mesmo padrão de risco, sem proteção, em mais 5 lugares:

| Local | Operação | Risco |
|---|---|---|
| `generate_bp.py::delete_batch` | `shutil.rmtree` | **Confirmado em produção** (traceback acima) |
| `generate_bp.py::delete_card` | `Path.unlink` | Mesma classe de bloqueio, arquivo de imagem individual |
| `core/template/loader.py::delete_template` | `shutil.rmtree` | Mesma classe — pasta de template inclui fontes customizadas, exatamente o tipo de handle que `collections.py` já sabia ser problemático |
| `proxy_bp.py` (excluir PDF de proxy) | `Path.unlink` | Mesma classe |
| `proxy_bp.py` (limpar upload de verso temporário) | `Path.unlink` | Mesma classe |
| `data_bp.py` (limpar arquivo temporário de importação) | `Path.unlink` | Mesma classe, risco menor (arquivo recém-criado pela própria aplicação) |

## 3. Solução: extrair e generalizar

`core/fsutil.py` (novo) — `rmtree_retry()` e `unlink_retry()`, extraídos da implementação já existente em `collections.py` (mesmo algoritmo: retry com backoff fixo, libera cache de fontes via `clear_font_cache()`, força `gc.collect()`, e — importante — **propaga o erro real se a falha persistir** depois de esgotar as tentativas, em vez de engolir silenciosamente um problema genuíno de permissão).

`collections.py` foi atualizado pra usar a versão compartilhada, removendo a duplicata privada (`_rmtree_retry` não existe mais nesse arquivo). Todos os outros pontos da tabela acima foram migrados pra chamar `rmtree_retry`/`unlink_retry` em vez de `shutil.rmtree`/`Path.unlink` direto.

**Deliberadamente não alterado:** os `shutil.rmtree(..., ignore_errors=True)` já existentes em `collections.py` (usados na duplicação de coleção, pra limpar o que não foi escolhido copiar) — esses já suprimem erro por design, é um comportamento diferente (silencioso, não crítico se falhar) que não faz parte do bug reportado.

## 4. Validação realizada

- **Retry isolado**, sem depender de reproduzir um lock real do Windows (não é possível neste ambiente Linux): simulei via monkeypatch do `shutil.rmtree` três cenários —
  - Sem falha: completa na primeira tentativa, sem overhead.
  - Falha transitória (2 falhas, sucesso na 3ª): confirma que o retry realmente tenta de novo e conclui.
  - Falha persistente: confirma que o erro real é propagado depois de esgotar as tentativas — não fica engolindo silenciosamente um problema de verdade.
- **Fluxo completo via Flask** (sem regressão no caminho feliz): gerar lote → excluir card individual → excluir lote inteiro; excluir template; gerar PDF de proxy → excluir PDF de proxy. Todos confirmados funcionando.
- **Não validado:** reprodução do lock real do Windows em si (por não ter acesso a uma máquina Windows neste ambiente) — a correção ataca a causa já diagnosticada e documentada em `collections.py` (que resolveu o mesmo tipo de problema na prática), mas a confirmação definitiva de que o `PermissionError` específico do usuário para de acontecer só vem do próximo uso real no Windows dele.
