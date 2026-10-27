# Relatório final — análise AppSec e SRE do CourseSphere

Data: 27/10/2026. Versão inicial: `01bd2692d02aeee5bb008b08ebcb2e9c19785b9b`. Branch de trabalho: `codex/appsec-sre`.

## Resumo para gestão

A API, a interface e a infraestrutura local foram analisadas contra o escopo do desafio. Cinco comportamentos de risco foram reproduzidos na versão inicial com requisições controladas e integrações externas simuladas. A análise abrange exposição de credenciais, divulgação de detalhes internos, configuração de navegador e consumo excessivo de recursos. Os cinco foram corrigidos; os mesmos testes após a mudança rejeitam as entradas indevidas. O fluxo de catálogo e a interface podem ser executados em Docker sem credenciais externas. O CRUD de cursos próprios foi acrescentado com separação por usuário verificado; sua integração real com Firebase ainda depende de um projeto de teste confirmado.

A operação local agora inclui duas instâncias de API, gateway Nginx, Prometheus e Grafana. Doze requisições de catálogo chegaram às duas instâncias (8 e 4). A retirada controlada de uma instância evidenciou uma falha inicial de timeout; após ajustar o proxy, seis novas requisições passaram pela instância restante. Isso demonstra recuperação no cenário testado, não alta disponibilidade de produção. O gateway, o host Docker e os serviços externos continuam pontos de risco.

Prioridades seguintes: validar autenticação e CRUD com duas contas em Firebase de teste; validar recomendação com OpenAI, Pinecone e cache de embeddings de teste; configurar limites e observabilidade em uma implantação real; calibrar os SLOs com tráfego. Nenhuma escrita foi feita nos projetos externos presentes nos arquivos `.env` locais porque os identificadores não confirmavam isolamento.

## Método e escopo

1. Conferência do PDF e inventário do repositório/commit inicial; preservar arquivos locais na branch de trabalho.
2. Leitura de rotas, serviços, modelos, frontend, configuração e fronteiras de confiança. Sondas HTTP com cliente Flask e `unittest.mock` para Firebase, OpenAI e Pinecone. Entradas fictícias e sentinelas, sem tokens reais.
3. Repetição das mesmas sondas após as correções, teste de regressão do fluxo legítimo, build de frontend, análise de dependências via `npm audit --omit=dev` e smoke tests da stack Docker.
4. Revisão de logs, métricas, distribuição e comportamento diante da parada de uma API.

A sonda prova o comportamento da camada Flask e das validações em cada versão. Os mocks impedem inferir a configuração das regras Firebase ou a disponibilidade real de OpenAI/Pinecone. O catálogo SQLite foi lido localmente. Não houve teste de intrusão contra contas ou dados de terceiros.

## Superfície e fronteiras

| Método e rota | Entrada e efeito | Identidade exigida |
| --- | --- | --- |
| `POST /users/create` | Email/senha; cria conta Firebase | Não; controle por limite no gateway |
| `GET/POST /users/info` | Lê/grava perfil | Firebase ID token no cabeçalho Bearer |
| `POST /users/query` | Pergunta/histórico; chama OpenAI e eventualmente Pinecone | Opcional; token Bearer se fornecido |
| `POST /hash` | Gera identificador de mensagem | Bearer |
| `GET /chats`, `POST /chats/<id>/messages`, `DELETE /chats/<id>` | Lista, grava e exclui chats sob `users/{uid}` | Bearer |
| `GET /courses` e filtros `bysection`, `bysemester`, `bydepartment`, `byinstructor` | Lê catálogo SQLite | Não |
| `GET /courses/<id>`, `GET /courses/description/<id>` | Lê curso e descrição estimada | Não |
| `GET/POST /my/courses`, `GET/PUT/DELETE /my/courses/<id>` | CRUD de cursos do próprio usuário em Firebase | Bearer; UID vem da verificação no servidor |
| `GET /health`, `GET /ready` | Liveness e readiness | Interno/gateway local |
| `GET /metrics` | Métricas Prometheus | Somente rede interna Docker; gateway devolve 404 |

Navegador controla campos JSON, IDs de URL e Origin. Firebase Auth verifica identidade; o backend deriva o caminho de dados do UID verificado. A conta Admin acessa Realtime Database. O catálogo SQLite vem do CSV versionado. A recomendação transmite pergunta e histórico à OpenAI e consulta Pinecone após gerar embeddings; por isso esses dados e dependências exigem revisão específica em ambiente de teste. A interface usa caminhos relativos para API na mesma origem via gateway.

## Achados reproduzidos e priorização

A evidência numérica está em `document/evidence/security-baseline.json` e `document/evidence/security-after.json`. Reproduza a sonda no commit inicial e no commit final com `cd backend && PYTHONPATH=. ../.venv/bin/python tests/security_probe.py`, usando a versão da sonda entregue na branch final. No commit inicial, copie apenas esse arquivo de teste para um checkout descartável; ele não existia no commit-base. Todos os métodos externos são substituídos por mocks. Os resultados iniciais foram salvos antes da edição do código.

| ID | Categoria | Severidade | Comportamento inicial e pré-condição | Impacto potencial | Depois |
| --- | --- | --- | --- | --- | --- |
| A1 | Dados sensíveis / sessão | Alta | `GET /users/info?id_token=TOKEN_SENTINEL` era aceito (200). Requer token de usuário já obtido. | ID token na URL pode ficar em histórico, logs, rastreamento ou cópia de links. | 400; Bearer aceito no fluxo legítimo. |
| A2 | Divulgação de informação | Média | Exceção fictícia `INTERNAL_SENTINEL` no serviço de perfil aparecia no corpo HTTP (400). Requer falha interna acionável. | Detalhes de serviço, configuração ou dados embutidos em exceções podem alcançar cliente. | Texto ausente; 503 com resposta estável. |
| A3 | Configuração de segurança | Média | Preflight de `https://untrusted.example` recebia `Access-Control-Allow-Origin` para a mesma origem. Requer navegador em origem adversária; leitura efetiva depende de credenciais/cabeçalhos disponíveis nesse contexto. | Uma origem arbitrária podia fazer chamadas cross-origin permitidas pelo navegador quando possuísse credencial válida. CORS sozinho não contorna autenticação. | Origem não confiável sem header de permissão; localhost de desenvolvimento permitido. |
| A4 | Consumo de recursos / validação | Média | `POST /chats/test/messages` aceitava 501 mensagens em uma chamada (200), com gravação simulada. Requer conta autenticada. | Amplificação de escritas no Firebase, latência e custo; não houve escrita real no teste. | 400; lote pequeno aceito. |
| A5 | Consumo de recursos / validação | Alta | `POST /users/query` aceitava histórico de 200.000 caracteres (200), com recomendação simulada. A rota permitia usuário anônimo. | Custo de tokens/latência e pressão de memória se encaminhado ao serviço externo. O teste não mediu custo real. | 413 pelo limite de corpo; consulta curta aceita. |

**Ordem:** A1 e A5 pela exposição da credencial e pela rota anônima com potencial de custo; A4 pelo volume de escritas autenticadas; A2 e A3 pela dependência de pré-condições para impacto. As classificações são qualitativas, sem CVSS calculado. Os cinco comportamentos são distintos; A4 e A5 compartilham o tema de consumo, mas atingem serviços, permissões e limites diferentes.

## Correções, causa raiz e prova

| Decisão | Causa raiz | Solução e alternativa considerada | Prova e limite |
| --- | --- | --- | --- |
| D04 / A1 | Token no parâmetro de URL e em alguns corpos. | Bearer no cabeçalho para perfil, chat e recomendação; opção de cookie exigiria controle de sessão/CSRF adicional. | 200→400 na URL; perfil simulado com cabeçalho retorna 200. Token ainda reside no cliente Firebase. |
| D05 / A2 | Blueprints enviavam `str(error)` ao cliente. | Respostas estáveis por classe de falha e log só do tipo, com request ID; preservar detalhe em resposta foi rejeitado pela exposição. | Sentinela presente→ausente; teste de sucesso simulado passa. Diagnóstico depende de métricas e correlação. |
| D06 / A3 | `CORS(application)` aceitava qualquer Origin. | Allowlist configurável e gateway de mesma origem; bloqueio universal de CORS atrapalharia desenvolvimento. | Preflight externo sem header; localhost permitido. CORS não substitui autenticação. |
| D07 / A4 e A5 | Ausência de limites de corpo e campos. | 64 KiB HTTP, até 50 mensagens por gravação, conteúdos até 4.000 caracteres; pergunta até 2.000 e histórico de até 8 itens curtos. Só um limite global não protegeria a semântica. | 501 mensagens 200→400; histórico 200.000 caracteres 200→413; casos curtos retornam 200 com mocks. Números precisam de telemetria de uso. |

Nove testes de regressão passaram, incluindo CRUD entre Alice e Bob fictícios, readiness com e sem tabela SQLite, rota legítima, headers, logs sem token e métricas. Saída: `document/evidence/regression-tests.log`. O CRUD demonstrou 404 para Bob nas operações de leitura, edição e exclusão de um curso de Alice e sucesso de Alice. Isso verifica a autorização da aplicação simulada, não as regras do banco remoto.

## Hardening adicional

1. Limite por IP no gateway para `POST /users/create` (5/min, rajada 2) e `POST /users/query` (30/min, rajada 5). Em dez cadastros inválidos rápidos, três respostas 400 foram seguidas por sete 429 (`document/evidence/rate-limit.txt`). A validação inicial retornou 400 sem acionar Firebase. Limite por IP pode afetar usuários atrás do mesmo NAT; múltiplos gateways exigiriam estado compartilhado.
2. Headers `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer` e CSP restritiva na API, além de request ID validado como UUID. Teste de `/health` conferiu header e correlação; o gateway também adiciona headers em respostas de erro. CSP da API não é a política do frontend; deve ser avaliada separadamente antes de impor ao HTML.

## Operação, SLIs e SLOs

`/health` mede processo vivo. `/ready` consulta a tabela `courses` em SQLite somente leitura e devolve 503 quando indisponível. Isso não atesta Firebase, OpenAI ou Pinecone. `/metrics` expõe contadores por método/rota padronizada/status, histograma de duração e eventos de autenticação; `/metrics` não está exposto pelo gateway. Logs JSON incluem request ID, instância, rota, status e duração, sem corpo, query string ou credencial. O teste confirma que um Bearer fictício não apareceu no log.

**SLI 1:** disponibilidade de `GET /courses`: respostas 2xx/3xx divididas por respostas 2xx/3xx/5xx em 30 dias, excluindo 4xx de entrada inválida. **SLO proposto:** ≥99,5% em janela móvel de 30 dias. **SLI 2:** latência de `POST /users/query` bem-sucedido: 2xx até 10 s divididos por todos os 2xx, em 30 dias. **SLO proposto:** ≥95% em até 10 s. Sem requisições, o indicador é indefinido, não 100%. Fórmulas PromQL e ações de alerta: `document/OBSERVABILIDADE.md`. Não há série histórica para dizer que as metas foram cumpridas.

No Compose, Prometheus observou `backend_a:5000` e `backend_b:5000` como `up`; contadores de catálogo foram 8 e 4 e o dashboard provisionado **CourseSphere — SRE** mostrou cinco painéis (`document/evidence/observability-smoke.txt`). O painel é funcional (`document/evidence/final-smoke.txt`). Três regras de alerta foram carregadas pelo Prometheus; `promtool` validou sintaxe e o disparo sintético da regra de instância indisponível. Faltam calibração e destino de notificação.

## Containers, balanceamento e falha

As imagens são Python/Gunicorn para API e Node apenas no build de frontend, servido por Nginx. O Compose inicia `backend_a`, `backend_b`, `frontend`, `gateway`, `prometheus`, `grafana`. Exposição local: `http://127.0.0.1:8080`, Prometheus em `:9090`, Grafana em `:3001`. A imagem backend gera SQLite a partir do CSV versionado e não copia o banco local ignorado. Configuração padrão usa identificadores fictícios para Firebase Web e não injeta `.env` do backend. Um override `compose.test-env.yaml` aceita credenciais de um projeto **confirmadamente de teste** em `backend/.env.test` ignorado.

Doze GETs válidos em `/courses?limit=1` retornaram 200; oito foram atendidos por backend-a e quatro por backend-b (`document/evidence/load-balancer.txt`). Com backend-b parado, a primeira configuração teve dois timeouts em seis tentativas (`document/evidence/backend-failover.txt`). Após `proxy_connect_timeout 1s`, `proxy_next_upstream` e duas tentativas, seis de seis GETs retornaram 200 via backend-a (`document/evidence/backend-failover-after.txt`). Isso vale para GET idempotente nesse ensaio; uma falha durante escrita não deve ser repetida automaticamente sem chave de idempotência. Nginx, host, rede e disco ainda são pontos únicos de falha.

## Dependências e riscos restantes

A auditoria online de dependências **de produção** do frontend começou com 24 alertas (2 críticos, 9 altos, 13 moderados), registrados em `document/evidence/npm-audit.json`. Atualizações compatíveis, Firebase 13, React Router 7, remoção do `uuid` não usado e override de `@grpc/grpc-js` 1.14.6 deixaram **zero alertas** no `npm audit --omit=dev --json` final (`document/evidence/npm-audit-after.json`). O build com Node 24 passou. A auditoria é fotografia do advisory database na data; não prova ausência de falhas. Alertas iniciais não foram contados entre os cinco achados, pois o alcance da funcionalidade vulnerável não foi demonstrado. A CI executa regressões, build e auditoria de produção em push/PR; mudanças futuras podem reintroduzir alertas.

| Risco de disponibilidade | Efeito | Próxima ação proporcional |
| --- | --- | --- |
| Firebase Auth/Realtime Database ou credencial Admin inválida | Login, perfil, chats e cursos próprios param; catálogo público continua. | Ambiente de teste, métricas por rota, regras de acesso revisadas e backup/restore testado. |
| OpenAI, Pinecone ou modelo FastEmbed ausente/lento | Recomendação falha ou fica lenta; catálogo continua. | Timeout de 12 s e zero retry automático já configurados para OpenAI; falta orçamento total, política de retry para Pinecone, cache do modelo no build/volume e teste de degradação. |
| SQLite gerado na imagem sem dados completos | Catálogo tem códigos, mas muitos detalhes ausentes; atualização requer rebuild. | Pipeline de dados versionado, verificação de qualidade e estratégia de atualização/backup. |
| Gateway ou host Docker único | Aplicação inteira fica indisponível. | Em produção, múltiplas réplicas em hosts distintos e balanceador gerenciado com probes. |
| Rate limit local ao Nginx | Limite perde consistência em múltiplos gateways. | Armazenamento compartilhado para quotas e política de IP confiável. |

A interface foi aberta no navegador; a pergunta fictícia chegou a `POST /users/query` (backend-a, 502 esperado sem OpenAI), exibindo erro estável (`document/evidence/browser-flow.txt`). O catálogo respondeu pelo gateway; login real, CRUD Firebase real e recomendação ponta a ponta **não foram validados** porque não havia garantia de projetos externos de teste. O cache FastEmbed necessário para recomendação não é empacotado na imagem padrão. Não há deploy em nuvem nem cluster Kubernetes. O desenho dessas opções está em `document/THREAT_MODEL_E_RESILIENCIA.md`.

## Comandos essenciais de reprodução

```bash
# Na raiz do repositório, com Docker/Compose:
docker compose config --quiet
docker compose up -d --build
curl -i http://127.0.0.1:8080/health
curl -i 'http://127.0.0.1:8080/courses?limit=1'
curl -i http://127.0.0.1:8080/metrics # 404 no gateway
curl -i http://127.0.0.1:9090/-/healthy

# Testes sem serviços externos, a partir de backend/:
PYTHONPATH=. python -m unittest discover -s tests -v
PYTHONPATH=. python tests/security_probe.py

# Dependências e build, a partir de frontend/ (Node 24):
npm ci
npm run build
npm audit --omit=dev --audit-level=high
```

Para distribuição, repita GET de catálogo e confira `X-Instance-ID`; para falha, pare apenas uma instância local e repita GET, depois restaure-a. Não use esses comandos de falha contra produção. Arquivos `document/evidence/` contêm resultados sanitizados. As decisões D01–D21, inclusive alternativas e pressupostos, estão em `document/DECISOES.md`.

## Histórico da entrega

- `233a115` — correções de segurança, CRUD, dependências e testes de regressão.
- `f31baa9` — Docker/Compose, duas instâncias, gateway, Prometheus, Grafana, alertas e CI.
- Commit de documentação e evidências: último commit da branch `codex/appsec-sre` após esta seção.

## Estado de publicação

Os três commits estão apenas na branch local `codex/appsec-sre`; o `git push` para `github.com/Alcristi/CourseSphere` foi rejeitado pela revisão automática por ser uma publicação pública de código e evidências sem autorização específica do payload/destino. O remoto já é público e `origin/main` coincide com o commit-base. Os arquivos `.env` não estão no índice; a comparação dos valores sensíveis locais com os arquivos preparados não encontrou correspondências. Após a revisão automática bloquear o envio, o usuário decidiu manter a branch apenas local. A atividade 50 e o requisito de entrega pública não foram concluídos por essa decisão. A análise local, os testes, o Docker e a documentação estão concluídos.
