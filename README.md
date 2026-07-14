# DataTalk AI

[![CI](https://github.com/marcoaurelioleal-AI/DataTalk-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/marcoaurelioleal-AI/DataTalk-AI/actions/workflows/ci.yml)

Plataforma de AI Engineering para consultar dados de negocio em linguagem natural com uma camada obrigatoria de seguranca SQL.

O usuario faz uma pergunta, o sistema gera uma consulta, valida as regras antes de qualquer execucao e devolve uma resposta com SQL rastreavel, tabela, sugestao de grafico, historico, feedback e metricas. O dominio demo representa um e-commerce com dados de vendas e marketing.

## Por que este projeto existe

Equipes de negocio precisam responder perguntas como "quais produtos venderam mais?", mas nem sempre contam com alguem para escrever SQL. Permitir que uma IA execute SQL livremente, por outro lado, cria um risco operacional serio.

O DataTalk AI foi construido para demonstrar esse equilibrio: experiencia de linguagem natural sem abrir mao de validacao, rastreabilidade e execucao controlada.

## O que esta implementado

- Backend FastAPI com PostgreSQL, SQLAlchemy e migrations Alembic.
- Autenticacao JWT, cadastro, login e rotas protegidas.
- Seed idempotente com usuarios demo e dados de e-commerce.
- Catalogo de tabelas e schemas que respeita a allowlist de consulta.
- Providers `mock` e Gemini selecionaveis por ambiente, com timeout, retry controlado e telemetria segura no provider real.
- Cadeia LangChain LCEL com etapas nomeadas para contexto, geracao e validacao de SQL.
- Orquestracao de perguntas, validacao SQL, execucao controlada, resumo, tabela e recomendacao de grafico.
- Historico de consultas, feedback e metricas por usuario.
- Frontend React com dashboard, consulta, catalogo, historico e metricas.
- Visualizacao responsiva dos resultados em barras, linha, pizza, metrica ou tabela, conforme a recomendacao do backend.
- Ambiente Docker com banco, API e frontend.
- 188 testes automatizados para backend e frontend.

## Arquitetura

```text
Usuario
  |
  v
React + Vite (frontend)
  |
  v
FastAPI (API REST + JWT)
  |
  v
Query Orchestrator
  |
  +--> LangChain SQL Agent (LCEL)
  |       contexto -> provider -> validator
  |                              |
  +------------------------------+
                   |
                   v
             PostgreSQL (dados demo)
                   |
                   v
       Result Summarizer + Chart Recommender
                   |
                   v
  Resposta, grafico, tabela, historico, feedback e metricas
```

O backend separa rotas, schemas, repositories, services, providers, agentes e modelos. Essa divisao reduz o acoplamento entre a camada HTTP, as regras de seguranca e o acesso aos dados.

## Seguranca SQL

O SQL nunca e executado sem passar pelo `SqlSafetyService`. A validacao aplica regras explicitas:

- aceita somente consultas iniciadas por `SELECT`;
- bloqueia `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, `REPLACE`, `GRANT`, `REVOKE`, `MERGE`, `CALL` e `EXEC`;
- bloqueia comentarios e multiplas statements;
- bloqueia `SELECT *`;
- exige exatamente um `LIMIT` inteiro e limita o resultado a `QUERY_MAX_ROWS`;
- aceita somente as tabelas `customers`, `products`, `orders`, `order_items`, `campaigns` e `sales_channels`;
- bloqueia tabelas internas, incluindo `users`, `query_logs` e `query_feedback`;
- registra consultas aprovadas e bloqueadas para formar o historico e as metricas.

Essas regras sao uma segunda camada de defesa: mesmo que um provider gere uma consulta inadequada, ela nao deve chegar ao banco.

## Stack

| Camada | Tecnologias |
| --- | --- |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy, Alembic, Psycopg |
| Banco | PostgreSQL 16 |
| Autenticacao | JWT e hash PBKDF2 |
| IA no MVP | LangChain Core (LCEL), providers `mock` e Gemini com saida estruturada |
| Frontend | React, TypeScript, Vite, Tailwind CSS, Axios, Recharts, Lucide |
| Qualidade | Pytest, Vitest, React Testing Library |
| Infraestrutura | Docker e Docker Compose |

## Execucao com Docker

### Pre-requisitos

- Docker Desktop com Docker Compose ativo.

### Subir o ambiente

```powershell
docker compose up --build
```

O ambiente disponibiliza:

| Servico | URL |
| --- | --- |
| Frontend | http://localhost:5173 |
| API | http://localhost:8000 |
| Documentacao OpenAPI | http://localhost:8000/docs |
| PostgreSQL | `localhost:5432` |

Na inicializacao da API, as migrations sao aplicadas e o banco recebe os dados demo de forma idempotente.

Para encerrar os containers:

```powershell
docker compose down
```

## Execucao local

### Backend

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload
```

Em um ambiente local, ajuste `DATABASE_URL` no `.env` para apontar para uma instancia PostgreSQL disponivel.

### Ativar o Gemini

O provider `mock` permanece como padrao. Para usar sua chave do Google Gemini, configure somente o arquivo local `.env`:

```dotenv
LLM_PROVIDER=gemini
GEMINI_API_KEY=sua_chave_aqui
GEMINI_CHAT_MODEL=gemini-2.5-flash
LLM_REQUEST_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=2
LLM_RETRY_BACKOFF_SECONDS=0.25
```

O mesmo `.env` e interpolado pelo Docker Compose. A chave e usada apenas pela API, nunca e enviada ao frontend e nao deve ser adicionada ao Git. O arquivo `.gitignore` bloqueia `.env` e suas variacoes locais.

O provider tenta novamente apenas falhas transitorias, como timeout, limite de requisicoes (`429`) e indisponibilidade (`5xx`). Erros permanentes de autenticacao ou requisicao nao sao repetidos. Cada chamada emite um evento JSON com provider, modelo, status, tentativas, latencia e categoria do erro, sem registrar a pergunta, o prompt, o SQL ou a chave.

### Frontend

Em outro terminal:

```powershell
Set-Location frontend
npm install
npm run dev
```

Por padrao, o frontend consulta a API em `http://localhost:8000`. Para outro endereco, configure `VITE_API_URL` em `frontend/.env` a partir de `frontend/.env.example`.

## Usuarios demo

| Perfil | E-mail | Senha |
| --- | --- | --- |
| Admin | `admin@datatalk.ai` | `admin123` |
| Analista | `analyst@datatalk.ai` | `analyst123` |
| Visualizador | `viewer@datatalk.ai` | `viewer123` |

Essas credenciais existem apenas para a base demo. Nunca use senhas de exemplo em ambientes publicos.

## API

As rotas protegidas exigem `Authorization: Bearer <token>` obtido em `POST /auth/login`.

| Grupo | Endpoints |
| --- | --- |
| Health | `GET /`, `GET /health` |
| Autenticacao | `POST /auth/register`, `POST /auth/login`, `GET /users/me` |
| Catalogo | `GET /catalog/tables`, `GET /catalog/tables/{table_name}/schema` |
| Consultas | `POST /queries/ask`, `GET /queries/history`, `GET /queries/{query_id}` |
| Feedback | `POST /queries/{query_id}/feedback`, `GET /queries/{query_id}/feedback` |
| Metricas | `GET /metrics/overview`, `GET /metrics/queries`, `GET /metrics/tables` |

Exemplos de perguntas para a tela de consulta:

- `Quais produtos venderam mais este mes?`
- `Qual canal trouxe mais receita?`
- `Quais clientes compraram mais?`

## Testes e verificacao

Backend:

```powershell
python -m pytest -q
```

Frontend:

```powershell
Set-Location frontend
npm run test
npm run typecheck
npm run build
```

Infraestrutura:

```powershell
docker compose config
```

O GitHub Actions executa essas verificacoes automaticamente em cada push e pull request, com jobs independentes para backend, frontend e Docker Compose.

A suite atual possui 188 testes: 163 no backend e 25 no frontend. Ela cobre health check, autenticacao, catalogo, validator SQL, providers mock e Gemini, resiliencia e telemetria do provider, cadeia LangChain, agente, execucao controlada, orquestracao, historico, feedback e metricas no backend. No frontend, cobre restauracao e invalidacao de sessao, login, navegacao protegida, estados de carregamento, consultas aprovadas, bloqueadas e ambiguas, falhas de API, feedback, formatacao e visualizacoes em barras, linha, pizza, metrica e tabela.

## Limites atuais e roadmap

O projeto implementa uma cadeia LangChain LCEL e os providers `mock` e Gemini. A cadeia prepara o schema permitido, monta o prompt seguro, chama o provider e encerra no `SqlSafetyService`. A execucao permanece fora da cadeia e passa por uma segunda validacao no `SqlExecutionService`. OpenAI, LangGraph e LlamaIndex ainda nao estao integrados.

Proximas evolucoes planejadas:

1. Integracao do provider OpenAI com configuracao por ambiente.
2. Fluxo LangGraph para classificar, gerar, validar, executar e resumir consultas como etapas observaveis.
3. Recuperacao de conhecimento nao estruturado com LlamaIndex.
4. Observabilidade avancada, tracing e monitoramento de erros.
5. Preparacao para deploy cloud com ambientes e secrets gerenciados.

## Valor para portfolio

O DataTalk AI demonstra um caso pratico de AI Engineering: uso de IA em dados estruturados com seguranca de saida, controle de acesso, APIs REST, banco relacional, experiencia web, testes e infraestrutura containerizada.

O diferencial central nao e apenas transformar texto em SQL. E garantir que a consulta passe por uma politica explicita de seguranca antes de atingir o banco e que seu resultado permaneça rastreavel.
