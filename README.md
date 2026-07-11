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
- Geracao deterministica com provider `mock`, adequada para desenvolvimento e testes sem chave de API.
- Orquestracao de perguntas, validacao SQL, execucao controlada, resumo, tabela e recomendacao de grafico.
- Historico de consultas, feedback e metricas por usuario.
- Frontend React com dashboard, consulta, catalogo, historico e metricas.
- Visualizacao responsiva dos resultados em barras, linha, pizza, metrica ou tabela, conforme a recomendacao do backend.
- Ambiente Docker com banco, API e frontend.
- 172 testes automatizados para backend e frontend.

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
  +--> Data Analyst SQL Agent + Mock Provider
  |              |
  |              v
  +------> SQL Safety Validator
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
| IA no MVP | Provider `mock` e contrato de agente SQL |
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

A suite atual possui 172 testes: 147 no backend e 25 no frontend. O backend cobre health check, autenticacao, catalogo, validator SQL, provider mock, agente, execucao controlada, orquestracao, historico, feedback e metricas. O frontend cobre restauracao e invalidacao de sessao, login, navegacao protegida, estados de carregamento, consultas aprovadas, bloqueadas e ambiguas, falhas de API, feedback, formatacao e visualizacoes em barras, linha, pizza, metrica e tabela.

## Limites atuais e roadmap

O MVP implementa o provider `mock`. O contrato do agente foi preparado para evoluir sem alterar as barreiras de seguranca, mas Gemini, OpenAI, uma cadeia LangChain completa, LangGraph e LlamaIndex ainda nao estao integrados.

Proximas evolucoes planejadas:

1. Integracao de providers Gemini e OpenAI com configuracao por ambiente.
2. Fluxo LangGraph para classificar, gerar, validar, executar e resumir consultas como etapas observaveis.
3. Recuperacao de conhecimento nao estruturado com LlamaIndex.
4. Observabilidade avancada, tracing e monitoramento de erros.
5. Preparacao para deploy cloud com ambientes e secrets gerenciados.

## Valor para portfolio

O DataTalk AI demonstra um caso pratico de AI Engineering: uso de IA em dados estruturados com seguranca de saida, controle de acesso, APIs REST, banco relacional, experiencia web, testes e infraestrutura containerizada.

O diferencial central nao e apenas transformar texto em SQL. E garantir que a consulta passe por uma politica explicita de seguranca antes de atingir o banco e que seu resultado permaneça rastreavel.
