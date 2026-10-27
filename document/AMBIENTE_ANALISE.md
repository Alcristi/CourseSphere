# Ambiente de análise — CourseSphere

Registro da atividade 03 em 27/10/2026. Este mapa foi feito a partir do README, dos exemplos de configuração e dos pontos de inicialização/integração do código. Nenhuma credencial local foi lida e nenhum serviço externo foi acessado.

## Preparação segura

1. Use um checkout descartável ou uma cópia isolada para executar testes. Os arquivos `backend/.env` e `frontend/.env` já existem neste checkout; **não os sobrescreva nem execute a aplicação com eles antes de confirmar que apontam apenas para recursos de teste**.
2. Os modelos sem segredos estão em `backend/analysis.env.example` e `frontend/analysis.env.example`. Eles não são carregados automaticamente. No checkout isolado, copie-os respectivamente para `backend/.env` e `frontend/.env`, preencha com credenciais e IDs de um projeto de teste e mantenha esses `.env` fora do Git.
3. Configure Firebase Authentication e Realtime Database em um **projeto de teste**; crie contas e dados descartáveis. Use a configuração web desse mesmo projeto no frontend e uma conta de serviço Admin desse projeto no backend. Valores `VITE_*` entram no bundle do navegador; a chave privada Admin fica somente no backend.
4. Se testar recomendações, use chave OpenAI de teste e índice Pinecone separado (`courses-analysis` no modelo), denso e com **384 dimensões**. Confirme o alvo antes de executar `python -m database.seed_courses --apply`; sem `--apply`, o comando apenas inspeciona a carga.
5. Registre nas evidências somente nomes de variáveis, IDs não sensíveis, respostas sanitizadas e dados fictícios. Não copie tokens, chaves privadas, senhas ou dados pessoais para logs, prints ou commits.

A regra `.gitignore` ignora `backend/.env` e `frontend/.env`. Os dois modelos `analysis.env.example` contêm valores vazios ou nomes de teste, sem segredo.

## Mapa de dependências

| Componente/fluxo | Dependências e configuração | Pode ser exercitado localmente? | Limitação |
| --- | --- | --- | --- |
| Frontend React/Vite | Node/npm, `frontend/package.json` e `package-lock.json`; SDK Firebase Web; oito variáveis `VITE_FIREBASE_*`. | Código, lint/build e parte da interface podem ser examinados com dependências instaladas. | Cadastro, login e dados do usuário dependem do projeto Firebase configurado. A API está endereçada no código como `http://127.0.0.1:5000`, o que restringe testes fora da máquina local sem ajuste. |
| API Flask | Python, `backend/requirements.txt`: Flask, Flask-CORS, firebase-admin, openai, pandas, fastembed, pinecone e python-dotenv. | Revisão estática e testes isolados são possíveis. | `backend/app.py` importa blueprints que carregam Firebase Admin na importação; para iniciar a API atual é necessária uma conta de serviço válida. Não se deve usar a credencial local existente sem confirmar que é de teste. |
| Identidade e dados do usuário | Firebase Authentication, Realtime Database; `FIREBASE_TYPE`, `FIREBASE_PROJECT_ID`, `FIREBASE_PRIVATE_KEY_ID`, `FIREBASE_PRIVATE_KEY`, `FIREBASE_CLIENT_EMAIL`, `FIREBASE_CLIENT_ID`, URLs de auth/token/certificados/universe e `FIREBASE_DATABASE_URL` no backend. | Casos com mocks podem ser isolados. | Fluxos completos exigem projeto Firebase de teste, regras adequadas, conta Admin e duas contas fictícias para testes de autorização. |
| Catálogo de cursos | SQLite local em `backend/database/roster_reviews.sqlite.db`; CSV versionado em `backend/data/course-roster-kaggle/cornell_courses.csv`. | Sim. `python -m database.seed_sqlite_catalog` (a partir de `backend/`) cria a base local se ela não existir. | A base não está presente neste checkout. A carga contém essencialmente códigos; títulos, seções, semestres e instrutores podem faltar. Não substitui dados completos de produção. |
| Interpretação da pergunta | API OpenAI; `OPENAI_API_KEY` e `OPENAI_QUERY_MODEL`. | A lógica pode ser testada com cliente simulado. | O fluxo real de recomendação consulta serviço externo e pode gerar custo. |
| Busca semântica | Pinecone; `PINECONE_API_KEY` e `PINECONE_INDEX`; modelo FastEmbed `BAAI/bge-small-en-v1.5`. | Embeddings podem ser testados localmente se o modelo estiver íntegro no cache; consultas podem ser simuladas. | Busca real requer índice Pinecone de teste. O código usa `local_files_only=True`, portanto não baixa o modelo sob demanda. O diretório de cache existe, mas o modelo não foi validado. |
| Containers | Dockerfiles/Compose. | Não verificado nesta atividade. | O executável Docker não foi detectado no PowerShell atual; a disponibilidade em outro ambiente não foi verificada. |

`HF_TOKEN` aparece em `backend/.env.example`, mas não foi encontrada referência a ele no código de execução examinado. Trate-o como potencialmente opcional até um teste comprovar necessidade.

## O que testar sem serviços externos

- Ler e revisar código, configuração, fluxo de chamadas e dependências.
- Executar lint/build do frontend com dependências locais, sem concluir que login ou dados funcionam.
- Gerar e consultar o catálogo SQLite a partir do CSV versionado em um ambiente isolado; o arquivo de saída é ignorado pelo Git.
- Testar serviços com clientes Firebase/OpenAI/Pinecone simulados e dados fictícios.

## O que depende de serviços de teste

- Cadastro, login, verificação de tokens, perfis e chats: Firebase Authentication/Realtime Database.
- Interpretação real de perguntas: OpenAI.
- Busca vetorial e carga de índice: Pinecone; embeddings também exigem o modelo já armazenado no cache local.
- Fluxo completo pelo navegador: frontend, API, Firebase e, para recomendações, OpenAI/Pinecone.

## Estado verificado e próximos limites

- `backend/.env` e `frontend/.env` existem, mas seu conteúdo não foi inspecionado; **não há garantia de isolamento**.
- `frontend/node_modules` e `.venv/fastembed-cache` existem; integridade e compatibilidade não foram testadas.
- O SQLite local esperado não existe. Não foi criado nesta atividade para evitar alterar o estado de dados antes de definir um checkout isolado.
- Nenhuma aplicação foi iniciada e nenhuma rota foi chamada. A inicialização e os testes de comportamento pertencem às atividades seguintes.

## Estado após as atividades 04–58

A análise posterior confirmou Docker/Compose no WSL, Node 24 em imagem de build e Python no `.venv`. O backend foi iniciado localmente na porta 5050 e `GET /courses?limit=1` respondeu 200. A stack Compose iniciou duas APIs, frontend, gateway, Prometheus e Grafana. Um SQLite local ignorado já existia no checkout e foi apenas lido; a imagem gera seu próprio banco a partir do CSV. Firebase Admin agora é inicializado sob demanda, então rotas locais de catálogo e saúde não exigem conta de serviço. As chamadas frontend agora usam URLs relativas. A versão Docker padrão usa IDs Web fictícios e não recebe `backend/.env`; o override `compose.test-env.yaml` só deve ser usado após confirmar projeto de teste. Testes externos ponta a ponta continuam pendentes pelo isolamento não comprovado dos IDs locais. Consulte `document/RELATORIO_FINAL.md` para evidências.
