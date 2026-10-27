# Registro de decisões — CourseSphere AppSec & SRE

Este registro explica as escolhas, as alternativas consideradas, a evidência usada e o limite da conclusão. O relatório final aponta os resultados observados. Data de referência: 27/10/2026.

## D01 — Isolar os testes de segurança

**Observação:** os arquivos locais de configuração estão preenchidos, mas os identificadores de Firebase e Pinecone não indicam claramente um ambiente de teste. A API original inicializava Firebase Admin no import.

**Alternativas:** (a) criar usuários e dados reais no projeto configurado; (b) usar mocks para as provas de comportamento da aplicação; (c) montar emuladores completos. **Escolha:** usar o cliente de teste Flask e substituir somente as chamadas externas, com dados fictícios. A inicialização e uma leitura do catálogo local foram verificadas separadamente.

**Por quê:** permite reproduzir o comportamento de rota, validação e autorização sem escrever em recursos cujo isolamento não foi confirmado. **Limite:** os testes não provam as regras do Firebase ou a integração real com OpenAI/Pinecone; essas verificações exigem projeto de teste.

## D02 — Preservar a linha de base

**Observação:** commit-base `01bd2692d02aeee5bb008b08ebcb2e9c19785b9b`; guia e checklist eram não versionados. O Git para Windows falhou ao criar uma branch no caminho UNC. **Escolha:** criar `codex/appsec-sre` pelo Git no WSL, que preservou os arquivos locais. Não executar limpeza/reset. O estado histórico está em `document/PONTO_DE_PARTIDA.md`.

## D03 — Selecionar achados demonstráveis

**Observação:** a sonda com serviços simulados registrou token na URL aceito, texto arbitrário de exceção na resposta, origem externa autorizada por CORS, lote de 501 mensagens aceito e histórico de 200 mil caracteres aceito. **Escolha:** tratar esses cinco comportamentos como candidatos distintos, com pré-condições e limites explícitos no relatório. Alertas de dependências ficam separados até avaliação de alcance.

**Por quê:** cada resultado tem requisição, resposta e ponto de código reproduzíveis; evita contar uma recomendação genérica como prova de exploração.

## D04 — Transportar identidade no cabeçalho

**Observação:** o frontend enviava Firebase ID token em `GET /users/info?id_token=...`; URLs podem aparecer em histórico e logs. **Alternativas:** corpo de POST, cookie de sessão ou cabeçalho Bearer. **Escolha:** `Authorization: Bearer` para perfis, recomendações e chats, recusando o formato antigo na rota GET.

**Verificação:** sonda original aceitou a URL (200); regressão devolve 400 para URL e 200 para cabeçalho simulado. **Limite:** o token ainda existe no navegador, como exige o Firebase Auth; o gateway evita registrar query strings.

## D05 — Reduzir detalhes de erro expostos

**Observação:** blueprints interpolavam `str(error)` em respostas; uma exceção fictícia apareceu integralmente no corpo. **Alternativas:** manter texto para facilitar depuração ou devolver mensagem estável e registrar só a classe internamente. **Escolha:** mensagem estável, código HTTP por categoria e log estruturado com tipo de erro, sem conteúdo da exceção.

**Verificação:** a string sentinela deixou de aparecer na resposta; casos válidos continuam funcionando com mocks. **Limite:** diagnósticos de produção dependem de correlação por request ID e métricas, sem mensagem interna detalhada.

## D06 — Restringir CORS

**Observação:** `CORS(application)` refletia uma origem arbitrária. **Escolha:** allowlist configurável de origens de desenvolvimento, com frontend de produção acessando a API pela mesma origem via Nginx. **Verificação:** preflight de origem não confiável não recebe `Access-Control-Allow-Origin`; localhost de desenvolvimento recebe. **Limite:** CORS é proteção do navegador, não autenticação; chamadas diretas ainda exigem controles na API.

## D07 — Limitar custo por requisição

**Observação:** 501 mensagens eram aceitas em um único POST e o modelo Firebase faria um `push` por mensagem; histórico de 200 mil caracteres também era aceito na consulta a OpenAI. **Escolha:** corpo HTTP máximo de 64 KiB; até 50 mensagens de chat por requisição, cada conteúdo até 4 mil caracteres; pergunta e histórico com limites menores (2 mil caracteres por texto, 8 mensagens).

**Alternativas:** somente limite global de corpo ou somente limites por campo. A combinação protege memória/transporte e a operação de negócio. **Verificação:** sondas abusivas passam de 200 para 400/413; casos pequenos continuam 200. **Limite:** os números são limites iniciais e devem ser ajustados com telemetria de uso legítimo.

## D08 — Rate limiting no ponto de entrada

**Observação:** cadastro e recomendação podiam ser acionados repetidamente, inclusive sem login no caso da recomendação. **Escolha:** `limit_req` no Nginx para essas duas rotas, antes do pool de APIs, com 429 e pequenas rajadas. Isso aplica um limite comum às duas instâncias sem armazenar estado em cada processo.

**Limite:** com vários gateways, cada um tem seu próprio contador; uma produção distribuída precisaria de limite compartilhado e política para IPs atrás de proxy. Dez cadastros inválidos rápidos produziram 3 respostas 400 e 7 respostas 429 no Compose; o resultado está em `document/evidence/rate-limit.txt`.

## D09 — CRUD de cursos vinculado ao UID verificado

**Observação:** o catálogo SQLite tinha apenas leitura, enquanto o edital exige CRUD de cursos/aulas. **Alternativas:** permitir edição da base importada, criar uma tabela compartilhada ou guardar cursos próprios no Firebase sob o usuário. **Escolha:** API e página para cursos criados pelo usuário em `users/{uid}/courses`. O UID vem do token verificado pelo servidor, nunca do corpo da requisição.

**Por quê:** preserva o catálogo importado e torna o isolamento por usuário explícito. **Verificação:** teste com Alice e Bob fictícios: Bob recebe 404 ao ler, alterar ou excluir o curso de Alice; Alice completa criar, ler, editar e excluir. **Limite:** integração real e regras Firebase ainda requerem projeto de teste.

## D10 — Inicializar Firebase sob demanda

**Observação:** o import da API exigia conta Admin mesmo para `/courses` e saúde. **Escolha:** inicializar Firebase apenas quando uma operação autenticada precisa dele. **Verificação:** a aplicação importa e expõe rotas de saúde/catálogo sem inicializar o cliente externo; operações Firebase continuam exigindo credenciais válidas. **Limite:** a primeira operação autenticada pode ter latência maior e erro de configuração; o dashboard deve monitorá-la.

## D11 — Gerar catálogo próprio na imagem

**Observação:** havia um SQLite local não versionado; copiá-lo para a imagem tornou o primeiro build ambíguo e a carga recusou sobrescrevê-lo. **Escolha:** copiar só código Python e o CSV versionado para a imagem e gerar SQLite no build. O esquema da carga foi alinhado às colunas consultadas pelo código.

**Verificação:** o build criou 19.229 códigos de curso sem usar o banco local. **Limite:** o CSV não fornece títulos, turmas, semestres ou docentes para todos os registros; o relatório não os inventa.

## D12 — Logs e métricas sem dados sensíveis

**Escolha:** logs JSON para requisições, erros e autenticação, com request ID, rota padronizada, status, duração e instância. Não registrar URL completa, corpo, token, senha ou UID. Métricas Prometheus usam método, padrão de rota e status, evitando rótulos por usuário ou ID de recurso.

**Verificação:** teste analisou cada linha de log como JSON, confirmou ausência de token fictício e consultou `/metrics`. **Limite:** logs do proxy e serviços gerenciados precisam de política de retenção e acesso em produção.

## D13 — Separar liveness e readiness

**Escolha:** `/health` informa que o processo responde; `/ready` consulta o catálogo SQLite antes de aceitar tráfego. Prometheus coleta `/metrics` diretamente nas duas APIs internas; o gateway não expõe essa rota.

**Por quê:** um processo vivo pode estar incapaz de atender o catálogo. **Verificação:** teste retorna 200 com tabela de cursos e 503 com banco ausente. **Limite:** readiness não testa Firebase, OpenAI ou Pinecone, para não depender de chamadas externas a cada probe.

## D14 — Dois indicadores com metas propostas

**Escolha:** disponibilidade de `GET /courses` e latência de recomendações bem-sucedidas em `POST /users/query`. O relatório define numerador, denominador, exclusões, janela e metas. **Por quê:** são diretamente mensuráveis pelos contadores e histograma implementados. **Limite:** ainda não existe série histórica suficiente para afirmar cumprimento dos SLOs; metas são propostas iniciais.

## D15 — Containerização e balanceamento

**Escolha:** imagem Python com Gunicorn, imagem Node apenas para build do frontend, Nginx para arquivos estáticos, Nginx de entrada e duas instâncias da mesma imagem de API. Prometheus e Grafana ficam acessíveis só no loopback local. O Compose padrão não injeta credenciais externas; `compose.test-env.yaml` é um override para ambiente isolado.

**Alternativas:** publicar cada API, acoplar frontend e backend no mesmo processo ou usar Kubernetes desde o início. A solução escolhida facilita demonstrar duas instâncias e inspecionar cada uma. **Limite:** o gateway e o host Docker ainda são pontos únicos de falha; o Compose não representa alta disponibilidade de produção.

## D16 — API na mesma origem do frontend

**Observação:** várias chamadas do frontend apontavam diretamente para `127.0.0.1:5000`, endereço do navegador do usuário. **Escolha:** caminhos relativos, proxy de desenvolvimento no Vite e roteamento no gateway em Docker. **Verificação:** build TypeScript/Vite concluiu; a entrada HTTP única respondeu via Compose. **Limite:** o login depende da configuração Firebase Web do ambiente de teste.

## D17 — Tratar alertas de dependência com contexto

**Observação:** `npm audit --omit=dev` encontrou 24 alertas (2 críticos, 9 altos) na árvore inicial. **Escolha:** aplicar primeiro correções compatíveis sem `--force`, repetir build e auditoria e registrar alertas restantes. Um aviso na árvore instalada não prova por si só que a funcionalidade vulnerável é alcançável. **Resultado:** atualizações compatíveis, Firebase 13, React Router 7, remoção de `uuid` não utilizado e override de `@grpc/grpc-js` 1.14.6 reduziram o `npm audit --omit=dev` online a zero alertas. O build exigiu Node 24 e passou. **Limite:** resultado é uma fotografia do banco de advisories; o `npm ci` ainda mostra avisos em dependências de desenvolvimento, fora do escopo de produção desta contagem.

## D18 — Corrigir o failover observado

**Observação:** com backend-b parado, o primeiro ensaio de seis GETs teve dois timeouts. **Alternativas:** aceitar a indisponibilidade breve, consultar health dinamicamente por serviço externo ou ajustar timeout/retry do proxy. **Escolha:** `proxy_connect_timeout 1s`, `proxy_next_upstream` para erro/timeout e códigos 502/503/504, no máximo duas tentativas. **Verificação:** após validar e recarregar Nginx, seis de seis GETs responderam 200 via backend-a (`document/evidence/backend-failover-after.txt`). **Limite:** ensaio só vale para GET de catálogo; não repetir escritas automaticamente sem idempotência.

## D19 — Alinhar runtime do frontend e auditar dependências

**Observação:** Firebase 13 exige Node >=24.12, enquanto o build usava Node 22. **Escolha:** Node 24 na imagem de build e na CI; executar `npm ci` e build limpo no Docker. **Verificação:** build TypeScript/Vite passou, frontend reiniciado saudável, auditoria de produção final zero alertas. **Limite:** a biblioteca e as regras Firebase ainda precisam de teste ponta a ponta no projeto de teste; o pacote gerado tem aviso de chunk grande (aprox. 982 kB sem compressão), recomendando divisão futura.

## D20 — Não usar serviços externos sem isolamento comprovado

**Observação:** `.env` locais existem, mas nomes de projeto/índice não indicam ambiente de teste. **Escolha:** Compose padrão sem `backend/.env` e com Firebase Web fictício; override explícito `compose.test-env.yaml` para `.env.test`. **Por quê:** executar os testes de segurança ou criar usuários no projeto errado alteraria dados e poderia gerar custo. **Verificação:** sondas e testes usam mocks; builds ignoram `.env` no contexto Docker. **Limite:** login real, regras Realtime Database e recomendação real não foram demonstrados.

## D21 — Limitar a chamada externa de interpretação

**Observação:** a requisição à OpenAI não tinha orçamento de timeout definido no código da aplicação; o gateway espera até 30 s pelo backend. **Escolha:** timeout de 12 s e zero retry automático pelo cliente OpenAI. **Alternativas:** confiar no default do SDK ou repetir indefinidamente. O limite reduz espera e evita repetir a chamada que pode gerar custo; deve ser calibrado com latência real. **Verificação:** a suíte de regressão continua passando; a chamada real não foi exercitada porque não havia ambiente externo de teste confirmado. **Limite:** o tempo total ainda inclui outras etapas, inclusive Pinecone; ainda falta um orçamento total de recomendação e circuito de falhas.

## D22 — Validar integrações reais após autorização explícita

**Observação:** antes da autorização, o Compose padrão mantinha IDs fictícios e testes com mocks para evitar dados/custos externos. O usuário autorizou especificamente usar `backend/.env` e `frontend/.env`, incluindo Firebase, OpenAI e Pinecone e possíveis custos. **Escolha:** override `.env.compose.local.yaml`, ignorado pelo Git, injeta as credenciais somente nas duas APIs e monta o cache FastEmbed local em leitura; `--env-file frontend/.env` define apenas valores Web no build. A stack padrão continua sem credenciais.

**Verificação:** frontend, saúde, catálogo, Prometheus e Grafana responderam 200; as duas APIs estavam saudáveis. Firebase Admin realizou leitura de conectividade. Uma pergunta por código e outra de recomendação responderam 200; a segunda retornou três cursos com OpenAI, embeddings locais e Pinecone. Duas contas descartáveis foram criadas, autenticadas e usadas para perfil, CRUD e chat; acesso cruzado ao curso retornou 404 em leitura, alteração e exclusão. Contas e dados foram removidos. Evidências sanitizadas em `document/evidence/live-provider-smoke.txt` e `document/evidence/live-integration-smoke.txt`.

**Limite:** login visual não foi automatizado no navegador; o teste usou o endpoint oficial Firebase Auth REST. A prova não audita todas as regras Firebase nem estabelece disponibilidade contínua. O projeto configurado é o escolhido pelo usuário, e qualquer novo teste com contas criadas pelo usuário deve tratar a limpeza dos dados separadamente.
