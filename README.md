# CourseSphere

Aplicação React/Vite e API Flask para consultar catálogo de cursos, recomendar cursos e manter cursos próprios. Esta branch contém a entrega de análise AppSec e SRE. Comece pelo [relatório final](document/RELATORIO_FINAL.md), [decisões](document/DECISOES.md) e [guia de tarefas](document/GUIA_DESAFIO.md).

## Pré-requisitos e isolamento

- Docker Engine com Compose v2 para a demonstração local. Portas locais 8080, 9090 e 3001 disponíveis.
- Para execução sem Docker: Python 3.12, Node.js 24 e npm. Instale dependências em ambiente virtual e com `npm ci`.
- A stack padrão **não** usa credenciais locais de Firebase, OpenAI ou Pinecone. O catálogo público, saúde, logs, métricas e balanceamento funcionam sem elas. Login, CRUD remoto e recomendações reais exigem configuração externa autorizada; a seção de execução integrada descreve o ensaio realizado com contas descartáveis.
- `backend/.env` e `frontend/.env` são ignorados pelo Git. Nunca coloque chaves Admin em `VITE_*`: elas são incorporadas ao bundle público. Consulte `backend/analysis.env.example` e `frontend/analysis.env.example`. Não execute cargas `--apply` contra projetos não verificados.

## Subir a stack local

```bash
docker compose config --quiet
docker compose up -d --build
docker compose ps
curl -i http://127.0.0.1:8080/health
curl -i http://127.0.0.1:8080/ready
curl -i 'http://127.0.0.1:8080/courses?limit=1'
```

- Interface e API: `http://127.0.0.1:8080`
- Prometheus: `http://127.0.0.1:9090`
- Grafana, dashboard **CourseSphere — SRE**: `http://127.0.0.1:3001` (Viewer anônimo local)
- `GET /metrics` é coletado pela rede Docker, e devolve 404 no gateway público local.

Para usar serviços externos **somente com um projeto de teste confirmado**, crie `backend/.env.test` com os campos de `backend/analysis.env.example` e use:

```bash
docker compose -f compose.yaml -f compose.test-env.yaml up -d --build
```

Configure `VITE_FIREBASE_*` do mesmo projeto **antes do build**, por exemplo em um arquivo local `frontend/.env` passado por `docker compose --env-file frontend/.env -f compose.yaml -f compose.test-env.yaml up -d --build`, e confira o destino. O frontend recebe esses valores em tempo de compilação. O modelo FastEmbed `BAAI/bge-small-en-v1.5` precisa estar disponível no cache configurado por `EMBEDDING_CACHE_DIR` para recomendações; a imagem padrão não o contém. O Pinecone requer um índice de teste de 384 dimensões. A conexão com Firebase, OpenAI e Pinecone foi validada no ensaio local autorizado descrito abaixo; as regras Firebase ainda exigem revisão própria.

Para encerrar a demonstração, `docker compose down` preserva os volumes de métricas e Grafana. `docker compose down -v` também apaga esses volumes; use apenas se quiser descartar os dados locais da demonstração.

## Execução integrada local com credenciais autorizadas

O override versionado `compose.test-env.yaml` injeta `backend/.env.test` nas duas APIs. A configuração Web de `frontend/.env` entra no build pelo comando acima; o backend recebe somente as variáveis de `backend/.env.test`. Para recomendações com embeddings, forneça ao container um cache FastEmbed do modelo indicado acima como volume somente leitura em `/app/cache/fastembed`; esse volume depende do ambiente local e não acompanha o repositório. O ensaio autorizado em 27/10/2026 confirmou cadastro e login de duas contas descartáveis, perfil, CRUD de cursos e chat, além de consulta real a OpenAI/Pinecone. As contas e seus dados foram excluídos após o teste. Consulte `document/evidence/live-provider-smoke.txt` e `document/evidence/live-integration-smoke.txt`. Para testar a interface, abra `http://127.0.0.1:8080` e use uma conta sua ou crie uma conta de teste; os dados criados por você permanecem no Firebase até serem removidos.

## Executar separadamente

```bash
python -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
cd backend
../.venv/bin/python -m database.seed_sqlite_catalog
FLASK_APP=app:app ../.venv/bin/flask run --port 5050
```

No Windows, adapte a ativação do venv ao shell. Para frontend:

```bash
cd frontend
npm ci
npm run dev
```

O Vite usa `http://127.0.0.1:5000` por padrão para o proxy da API. Se Flask estiver na porta 5050, defina `BACKEND_PROXY_TARGET=http://127.0.0.1:5050` antes de `npm run dev` (ou inicie Flask na porta 5000). O catálogo local é gerado do CSV versionado; muitos registros têm apenas código, sem descrição/turma verificada.

## Rotas principais

| Operação | Método/rota | Autenticação |
| --- | --- | --- |
| Cadastro | `POST /users/create` | Não |
| Perfil | `GET/POST /users/info` | `Authorization: Bearer <Firebase ID token>` |
| Recomendação | `POST /users/query` | Opcional; Bearer se presente |
| Catálogo público | `GET /courses` e subrotas | Não |
| Cursos próprios | `GET/POST /my/courses`, `GET/PUT/DELETE /my/courses/<id>` | Bearer |
| Chats | `GET /chats`, `POST /chats/<id>/messages`, `DELETE /chats/<id>` | Bearer |
| Saúde | `GET /health`, `GET /ready` | Rede local no Compose |

O CRUD de cursos próprios salva em `users/{uid}/courses`; a API extrai `uid` do token verificado. O catálogo público SQLite permanece somente leitura. Exemplos detalhados, limites de campos e fronteiras estão no relatório.

## Testes, análise de dependências e reprodução

```bash
cd backend
PYTHONPATH=. ../.venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=. ../.venv/bin/python tests/security_probe.py

cd ../frontend
npm ci
npm run build
npm audit --omit=dev --audit-level=high
```

A sonda usa mocks de Firebase/OpenAI/Pinecone; não acessa contas externas. Para reproduzir os cinco achados na versão anterior às correções, use um checkout descartável fora deste diretório, a partir da raiz da branch entregue:

```bash
git worktree add --detach ../coursesphere-baseline 01bd2692d02aeee5bb008b08ebcb2e9c19785b9b
mkdir -p ../coursesphere-baseline/backend/tests
cp backend/tests/security_probe.py ../coursesphere-baseline/backend/tests/
cd ../coursesphere-baseline
python3.12 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
cd backend
PYTHONPATH=. ../.venv/bin/python tests/security_probe.py
```

Execute a mesma sonda na branch entregue com os comandos acima desta seção e compare as respostas com `document/evidence/security-baseline.json` e `document/evidence/security-after.json`. O relatório descreve cada entrada, resposta e pré-condição. A saída completa de regressões está em `document/evidence/regression-tests.log`. A auditoria online inicial e final está em `document/evidence/npm-audit*.json`; somente dependências de produção foram contadas nos totais do relatório.

Ferramentas empregadas: `unittest` do Python 3.12 e a sonda `backend/tests/security_probe.py` para regressões e reprodução; `npm audit` para análise de dependências; `npm run build` com Node.js 24 para verificar o frontend; Docker Compose v2 e `curl` para iniciar e exercitar a stack; Prometheus 3.5.0 e `promtool` para métricas e regras de alerta; Grafana 12.1.0 para o dashboard. Os comandos principais estão nesta página e no relatório; resultados sanitizados estão em `document/evidence/`.

A CI em `.github/workflows/security.yml` roda regressões, build e `npm audit --omit=dev --audit-level=high` em push e pull request. Um alerta alto ou crítico novo faz esse job falhar e precisa de triagem, não de aceitação automática.

Para conferir balanceamento sem autenticação:

```bash
for i in $(seq 1 12); do
  curl -fsS -o /dev/null -D - 'http://127.0.0.1:8080/courses?limit=1' | grep X-Instance-ID
done
```

Evidência capturada: `document/evidence/load-balancer.txt` e `document/evidence/observability-smoke.txt`. Para falha controlada, `docker compose stop backend_b`, repita GET, e `docker compose start backend_b`; resultado em `document/evidence/backend-failover-after.txt`. Não aplique esse ensaio em produção.

## Limites conhecidos

A regressão automática usa identidades e armazenamento simulados; um ensaio posterior confirmou login Firebase, CRUD e recomendação reais com duas contas descartáveis. A interface de login não foi automatizada no navegador, as regras Firebase não foram auditadas e não houve deploy em nuvem. O gateway/host Docker são pontos únicos de falha. Os SLOs são propostas, sem histórico suficiente para verificar cumprimento. Consulte [observabilidade](document/OBSERVABILIDADE.md) e [modelo de ameaças e resiliência](document/THREAT_MODEL_E_RESILIENCIA.md).
