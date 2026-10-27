# Arquitetura do backend CourseSphere

O backend segue **Blueprint → Service → Model**, com conexões e cargas de dados em `database/`. O ponto de entrada Flask é `backend/app.py`.

```text
backend/
├── app.py
├── .env.example
├── config/           # Tipos de pergunta usados na interpretação
├── blueprints/       # Rotas HTTP e respostas
├── services/         # Regras de negócio e integração OpenAI
├── models/           # Operações de dados Firebase, Pinecone e SQLite
├── database/         # Configuração, conexões e scripts de carga
├── data/             # Fontes locais para as cargas
└── requirements.txt
```

## Configuração

`database/config.py` carrega `backend/.env` sem sobrescrever variáveis do processo. `firebase_connection.py` monta a credencial Admin a partir de campos privados do ambiente; o frontend lê apenas os valores públicos `VITE_FIREBASE_*` de `frontend/.env`. Os arquivos `.env` não entram no Git.

Os endpoints de perfil recebem o Firebase ID token no corpo da requisição ou na URL; os endpoints de chat usam `Authorization: Bearer ...`. O Firebase Admin verifica o token, e os modelos usam o `uid` verificado para acessar `users/{uid}`. A recomendação aceita usuários anônimos e recebe um token opcional no corpo da requisição.

A configuração do Firebase no navegador continua visível após o build; a proteção de dados depende das regras do Firebase e da verificação de tokens no backend. O endpoint anônimo de recomendação ainda precisa de limite de requisições antes de exposição pública.

## API de cursos

`backend/blueprints/courses.py` expõe consultas ao catálogo SQLite por meio de `CourseCatalogService` e `CourseCatalogModel`. `GET /courses` retorna até 100 registros por padrão; `limit` aceita de 1 a 500 e `offset` inicia em 0. Também aceita os filtros `section_id`, `semester`, `department` e `instructor` como parâmetros de consulta.

`GET /courses/<id>` consulta a chave numérica do banco. `GET /courses/description/<id>` retorna `estimated_description` e `description_basis` quando o enriquecimento local foi aplicado. Os caminhos `bysection`, `bysemester`, `bydepartment` e `byinstructor` oferecem os mesmos filtros de forma explícita; o antigo formato genérico `/courses/<texto>` era ambíguo. Uma lista vazia é retornada quando não há correspondências, e a API responde 503 quando o banco ainda não foi criado.

As fontes locais contêm apenas códigos para muitos cursos. Títulos, descrições estimadas, seções, semestres e instrutores podem estar ausentes; a API não inventa esses dados.

## Tipos de pergunta

`backend/config/query_types.json` define os tipos de pergunta e os parâmetros esperados. `RecommendationService` usa esse catálogo no prompt e valida o tipo retornado. Recomendações de cursos seguem para a busca semântica; perguntas por código consultam o catálogo SQLite. Perguntas sobre major, minor e professor recebem uma resposta de indisponibilidade enquanto não há catálogos verificados para essas categorias.

## Fluxo da recomendação

1. `POST /users/query` recebe `query`, `history` e opcionalmente um token no corpo da requisição.
2. `RecommendationService` consulta o perfil autenticado e usa OpenAI para interpretar a pergunta.
3. `EmbeddingService` transforma as frases de busca em vetores.
4. `CourseModel` consulta o Pinecone e busca detalhes de cursos no SQLite.
5. `RecommendationService` seleciona até três cursos distintos e monta a resposta.

## Execução e cargas

A partir de `backend/`, instale `requirements.txt` e execute `python app.py`. Os comandos de carga são independentes da API:

- `python -m database.seed_sqlite_catalog` cria a base SQLite a partir dos dados locais.
- `python -m database.seed_sqlite_enrichment` inspeciona títulos e avaliações; `--apply` grava os enriquecimentos após fazer backup.
- `python -m database.seed_courses` inspeciona os cursos para o índice Pinecone; `--apply` grava os vetores.

O SQLite fica em `backend/database/roster_reviews.sqlite.db`. O modelo de embeddings precisa estar no cache local porque as consultas usam `local_files_only=True`.
