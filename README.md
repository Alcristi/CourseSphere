# CourseSphere

Aplicação React/Vite e API Flask para consultar catálogo de cursos, recomendar cursos e manter cursos próprios. Esta branch contém a entrega de análise AppSec e SRE. Comece pelo [relatório final](document/RELATORIO_FINAL.md), [decisões](document/DECISOES.md) e [guia de tarefas](document/GUIA_DESAFIO.md).

## Pré-requisitos e isolamento

- Docker Engine com Compose v2 para a demonstração local. Portas locais 8080, 9090 e 3001 disponíveis.
- Para execução sem Docker: Python 3.12, Node.js 24 e npm. Instale dependências em ambiente virtual e com `npm ci`.
- A stack padrão **não** usa credenciais locais de Firebase, OpenAI ou Pinecone. O catálogo público, saúde, logs, métricas e balanceamento funcionam sem elas. Login, CRUD remoto e recomendações reais precisam de projetos e contas de **teste** confirmados.
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

Configure `VITE_FIREBASE_*` do mesmo projeto **antes do build**, por exemplo via ambiente do shell, e confira o destino. O frontend recebe esses valores em tempo de compilação. O modelo FastEmbed `BAAI/bge-small-en-v1.5` precisa estar disponível no cache configurado por `EMBEDDING_CACHE_DIR` para recomendações; a imagem padrão não o contém. O Pinecone requer um índice de teste de 384 dimensões. Os serviços externos e regras Firebase não foram validados nesta entrega.

Para encerrar a demonstração, `docker compose down` preserva os volumes de métricas e Grafana. `docker compose down -v` também apaga esses volumes; use apenas se quiser descartar os dados locais da demonstração.

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

A sonda usa mocks de Firebase/OpenAI/Pinecone; não acessa contas externas. No commit-base `01bd2692d02aeee5bb008b08ebcb2e9c19785b9b`, copie `backend/tests/security_probe.py` da versão final para um checkout descartável, instale as dependências do backend e execute-a. Compare `document/evidence/security-baseline.json` com `document/evidence/security-after.json`. O relatório descreve cada entrada, resposta e pré-condição. A saída completa de regressões está em `document/evidence/regression-tests.log`. A auditoria online inicial e final está em `document/evidence/npm-audit*.json`; somente dependências de produção foram contadas nos totais do relatório.

A CI em `.github/workflows/security.yml` roda regressões, build e `npm audit --omit=dev --audit-level=high` em push e pull request. Um alerta alto ou crítico novo faz esse job falhar e precisa de triagem, não de aceitação automática.

Para conferir balanceamento sem autenticação:

```bash
for i in $(seq 1 12); do
  curl -fsS -o /dev/null -D - 'http://127.0.0.1:8080/courses?limit=1' | grep X-Instance-ID
done
```

Evidência capturada: `document/evidence/load-balancer.txt` e `document/evidence/observability-smoke.txt`. Para falha controlada, `docker compose stop backend_b`, repita GET, e `docker compose start backend_b`; resultado em `document/evidence/backend-failover-after.txt`. Não aplique esse ensaio em produção.

## Limites conhecidos

A verificação automática de CRUD usa duas identidades fictícias e armazenamento simulado. Login real, regras Firebase, recomendação real e deploy em nuvem aguardam ambiente externo isolado confirmado. O gateway/host Docker são pontos únicos de falha. Os SLOs são propostas, sem histórico suficiente para verificar cumprimento. Consulte [observabilidade](document/OBSERVABILIDADE.md) e [modelo de ameaças e resiliência](document/THREAT_MODEL_E_RESILIENCIA.md).
