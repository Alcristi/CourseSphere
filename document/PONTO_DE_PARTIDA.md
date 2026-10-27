# Ponto de partida da análise

Registro feito em **27/10/2026** (America/Sao_Paulo), antes de iniciar mudanças de código para o desafio.

## Versão reproduzível

- Repositório: `git@github.com:Alcristi/CourseSphere.git`
- Branch encontrada: `main` (acompanhava `origin/main`).
- Commit-base completo: `01bd2692d02aeee5bb008b08ebcb2e9c19785b9b`
- Data do commit: `2026-10-26 23:43:29 -0300`
- Mensagem: `refactor(frontend): consolidate initial analysis version`
- Arquivos rastreados e índice: nenhuma alteração indicada por `git status --porcelain=v1 -uall`, `git diff --name-status` ou `git diff --cached --name-status`.

O commit-base identifica o código versionado de forma exata. Uma pessoa com acesso ao repositório pode fazer um clone limpo e selecionar esse hash para reproduzir a versão inicial. Os documentos locais não versionados abaixo não fazem parte desse commit.

## Estado local anterior a esta atividade

`git status --porcelain=v1 -uall` mostrou:

```text
?? document/CHECKLIST_ENTREGA.md
?? document/GUIA_DESAFIO.md
```

Esses dois arquivos foram preservados. Os arquivos `backend/.env` e `frontend/.env` existem localmente e estão ignorados pela regra `.gitignore:14:.env`. O conteúdo deles não foi lido nem copiado para este registro. A presença de outros arquivos ignorados não foi auditada exaustivamente.

Este próprio registro, `document/PONTO_DE_PARTIDA.md`, é um terceiro arquivo novo não versionado após a atividade 02. A atividade 01 já havia alterado o conteúdo de `document/GUIA_DESAFIO.md`, que ainda é não versionado; por isso o Git não mostra essa mudança como diff de arquivo rastreado.

## Forma escolhida para preservar o trabalho

Continuar **no mesmo checkout**, sem `git clean`, `git reset --hard` ou troca de branch, e manter os três documentos locais intactos. Antes de qualquer operação Git que possa descartar arquivos, conferir novamente `git status --porcelain=v1 -uall` e salvar os documentos no histórico de uma branch apropriada. Não colocar os arquivos `.env` no Git.

Foi tentado `git switch -c codex/appsec-sre-baseline`, mas o comando falhou ao criar a referência em `.git/refs/heads`; a branch permaneceu `main`. O Git para Windows, acessando este checkout por `\\wsl.localhost`, também informa `unable to open '.git/sequencer/todo': Function not implemented` em comandos de status, embora `.git/sequencer` não exista e o status tenha saído com código 0. Não houve limpeza, reset, commit nem alteração de branch.

**Limite de reprodução:** o hash reproduz o código versionado inicial, mas o guia, o checklist e este registro só serão recuperáveis por outra pessoa depois que forem versionados ou compartilhados. Até lá, não usar um novo worktree como única cópia: arquivos não versionados não são copiados automaticamente.

## Continuação da atividade 02

Foi criada a branch `codex/appsec-sre` com Git dentro do WSL, sem limpar ou sobrescrever os arquivos locais. A preservação dos arquivos iniciais será confirmada no histórico final. O commit-base acima permanece a referência da versão vulnerável.

## Histórico preservado

A branch local `codex/appsec-sre` contém três commits: `233a115` (correções), `f31baa9` (infraestrutura) e o commit final de documentação. `git status --porcelain=v1` ficou vazio após o commit, e `origin/main` continuou em `01bd2692d02aeee5bb008b08ebcb2e9c19785b9b`. A revisão automática bloqueou a publicação; o usuário decidiu manter a branch somente local.
