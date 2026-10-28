# Observabilidade, SLIs e SLOs

## Contrato dos endpoints

- `GET /health`: liveness. Responde 200 quando o processo Flask/Gunicorn consegue atender uma requisição; não consulta dependências.
- `GET /ready`: readiness. Responde 200 apenas quando uma consulta simples à tabela `courses` no SQLite local funciona; caso contrário, 503. Não consulta Firebase, OpenAI ou Pinecone para evitar que uma falha externa retire todo o catálogo de serviço.
- `GET /metrics`: formato Prometheus, coletado internamente de `backend_a:5000` e `backend_b:5000`. O gateway público local devolve 404 nessa rota.

Os logs da aplicação são JSON por linha. Campos: timestamp, nível, evento, instância, request ID, método, padrão de rota, status, duração e tipo de erro quando houver. Não registrar corpo, query string, token, senha, UID ou texto de exceção. O mesmo request ID segue do gateway à API. Métricas usam somente método, padrão da rota e status; não usam identificadores de usuário, curso, mensagem ou URL dinâmica.

## SLI 1 — disponibilidade da API

**População:** requisições `GET /courses` nas duas instâncias. Excluem-se respostas 4xx causadas por parâmetros inválidos do cliente.

**Evento bom:** resposta 2xx ou 3xx. **Total:** respostas 2xx, 3xx e 5xx da população. A fórmula é `bons / total`. Exemplo PromQL para leitura do catálogo:

```promql
sum(increase(coursesphere_http_requests_total{method="GET",route="/courses",status=~"2..|3.."}[30d]))
/
sum(increase(coursesphere_http_requests_total{method="GET",route="/courses",status!~"4.."}[30d]))
```

**SLO proposto:** pelo menos **99,5%** em janela móvel de **30 dias**. É uma meta inicial, sem histórico de tráfego para calibrá-la.

## SLI 2 — latência da recomendação

**População:** respostas 2xx de `POST /users/query`, nas duas instâncias. **Evento bom:** duração até **10 s**. **Total:** todas as respostas 2xx da população. A fórmula é `requisições até 10 s / requisições bem-sucedidas`.

```promql
sum(increase(coursesphere_http_request_duration_seconds_bucket{method="POST",route="/users/query",status=~"2..",le="10.0"}[30d]))
/
sum(increase(coursesphere_http_request_duration_seconds_count{method="POST",route="/users/query",status=~"2.."}[30d]))
```

**SLO proposto:** pelo menos **95%** das recomendações bem-sucedidas em até 10 s, em janela móvel de **30 dias**. A meta inclui o tempo das chamadas a OpenAI, embeddings e Pinecone; precisa ser calibrada em um ambiente de teste com esses serviços.

**Sem tráfego:** denominador zero torna o SLI indefinido; não registrar 100% artificialmente. Monitorar `up` e volume de requisições separadamente.

## Dashboard e resposta operacional

O Grafana provisiona o painel **CourseSphere — SRE** com: requisições por segundo e por instância, proporção de 5xx, p95 de latência, falhas de autenticação e número de instâncias coletadas. O Prometheus coleta as duas APIs a cada 10 s.

| Sinal | Alerta inicial sugerido | Ação de quem atende |
| --- | --- | --- |
| `up` de uma instância = 0 por 2 min | Instância indisponível | Inspecionar `/ready`, logs por request ID e dependência SQLite; confirmar que o gateway ainda serve pela outra instância. |
| Taxa de 5xx > 1% por 5 min com tráfego suficiente | Erro em rota de usuário | Filtrar por padrão de rota e instância; verificar dependência externa e implantação recente. |
| p95 de `/users/query` > 10 s por 10 min | Lentidão | Verificar OpenAI, cache do modelo, Pinecone, volume e CPU. |
| Falhas de autenticação acima da linha de base | Possível abuso ou falha de configuração | Conferir taxa de 429, erros de token e status do Firebase sem registrar credenciais. |

Esses limiares são pontos de partida. As três primeiras regras estão em `infra/prometheus/alerts.yml`, validadas por `promtool check rules`; a regra de instância indisponível passou em `promtool test rules` com série sintética. Prometheus carregou três regras e o dashboard é funcional no Compose local. Alertas ainda precisam de calibração com tráfego real e um destino de notificação.
