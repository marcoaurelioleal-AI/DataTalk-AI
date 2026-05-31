# DataTalk AI — Software Design Document

## 1. Visão Geral

### 1.1 Nome do Projeto

DataTalk AI

1.2 Descrição

O DataTalk AI é uma plataforma de AI Engineering que permite consultar dados de negócio usando linguagem natural.

O usuário faz uma pergunta em português, o sistema interpreta a intenção, gera uma query SQL segura, valida a consulta, executa apenas comandos permitidos e retorna uma resposta com:

explicação em linguagem natural;
SQL gerado;
tabela de resultados;
sugestão de gráfico;
histórico;
métricas;
feedback do usuário.
1.3 Objetivo

Criar um projeto profissional de portfólio para demonstrar conhecimentos em:

Python;
FastAPI;
LangChain;
LlamaIndex;
agentes de IA;
SQL seguro;
PostgreSQL;
APIs REST;
Docker;
CI/CD;
testes;
frontend React;
arquitetura de sistemas de IA.
## 2. Problema

Em muitas empresas, times de negócio precisam consultar dados, mas dependem de analistas ou desenvolvedores para escrever SQL.

Exemplos de perguntas comuns:

“Quais produtos mais venderam este mês?”
“Qual campanha teve maior conversão?”
“Qual canal trouxe mais receita?”
“Quais clientes compraram mais nos últimos 30 dias?”
“Quais produtos tiveram queda de vendas?”

O problema é que nem todo usuário sabe SQL. Ao mesmo tempo, permitir que uma IA gere e execute SQL livremente é perigoso.

Uma IA mal controlada poderia tentar gerar comandos destrutivos, como:

DELETE
UPDATE
DROP
ALTER
TRUNCATE

Por isso, o sistema precisa permitir consulta aos dados com linguagem natural, mas com uma camada forte de segurança.

## 3. Solução Proposta

O DataTalk AI será um agente de dados com IA que:

recebe uma pergunta em linguagem natural;
identifica quais tabelas podem ser usadas;
consulta o schema permitido;
gera uma query SQL;
valida a query com regras de segurança;
bloqueia comandos perigosos;
executa apenas consultas SELECT;
limita a quantidade de linhas retornadas;
gera uma resposta em linguagem natural;
sugere o melhor tipo de gráfico;
salva histórico, métricas e feedback.

## 4. Público-Alvo

### 4.1 Usuário de Negócio

Pessoa que quer consultar dados sem escrever SQL.

Exemplo:

“Quais produtos venderam mais no último mês?”

4.2 Analista de Dados

Pessoa que quer acelerar análises exploratórias.

Exemplo:

“Compare a receita por canal nos últimos 90 dias.”

### 4.3 Gestor

Pessoa que quer obter insights rápidos.

Exemplo:

“Qual campanha teve melhor desempenho?”

### 4.4 Recrutador/Tech Lead

Pessoa que avaliará:

arquitetura;
segurança;
qualidade do código;
uso de IA;
testes;
organização;
clareza do projeto.

## 5. Escopo do MVP

### 5.1 Dentro do Escopo

O MVP deve conter:

backend FastAPI;
autenticação JWT;
banco PostgreSQL;
dados fictícios de negócio;
LangChain SQL Agent;
SQL Safety Validator;
execução apenas de SELECT;
allowlist de tabelas consultáveis;
histórico de queries;
feedback do usuário;
métricas;
frontend React;
Docker Compose;
testes;
README profissional.
### 5.2 Fora do Escopo Inicial

Não implementar no MVP:

deploy real em cloud;
Kubernetes;
autenticação OAuth;
permissão avançada por linha/coluna;
fine-tuning;
edição de dados via IA;
streaming;
multi-tenant real.

Esses pontos entram no roadmap.

## 6. Stack Técnica

### 6.1 Backend
Python 3.12+
FastAPI
Uvicorn
Pydantic v2
SQLAlchemy 2.0
Alembic
PostgreSQL
Pytest
python-dotenv
JWT

### 6.2 IA / Agentes
LangChain
LangGraph
LlamaIndex
Gemini API
OpenAI API opcional
Mock Provider para testes

### 6.3 Frontend
React
Vite
TypeScript
Tailwind CSS
Axios
Recharts
Lucide React

### 6.4 Infraestrutura
Docker
Docker Compose
GitHub Actions
Git

## 7. Mapeamento com Vagas de AI Engineer
Requisito da vaga	Como o projeto demonstra
Python	Backend com FastAPI
APIs REST	Endpoints para perguntas, histórico, métricas e feedback
LangChain	SQL Agent e tools
LlamaIndex	Roadmap para dados estruturados + documentos
LangGraph	Roadmap para fluxo agente controlado
LLMs	Gemini/OpenAI/Mock Provider
SQL	PostgreSQL com dados de negócio
Segurança	SQL Safety Validator
Docker	Execução containerizada
CI/CD	GitHub Actions
Testes	Pytest
Frontend	React + TypeScript
MLOps básico	Métricas, logs e feedback

## 8. Arquitetura Geral

Fluxo principal:

Usuário
  ↓
Frontend React
  ↓
FastAPI Backend
  ↓
Query Orchestrator Service
  ↓
LangChain SQL Agent
  ↓
SQL Safety Validator
  ↓
PostgreSQL
  ↓
Result Summarizer
  ↓
Chart Recommendation Service
  ↓
Resposta + Tabela + Gráfico

## 9. Arquitetura de Agentes

### 9.1 MVP com LangChain

Na primeira versão, o sistema terá um agente principal:

Data Analyst Agent
  ├── list_tables_tool
  ├── get_schema_tool
  ├── generate_sql_tool
  ├── validate_sql_tool
  ├── execute_sql_tool
  └── summarize_result_tool

### 9.2 Evolução com LangGraph

Na versão avançada, o fluxo será dividido em nós:

START
  ↓
Question Classifier
  ↓
Schema Selector
  ↓
SQL Generator
  ↓
SQL Validator
  ↓
Se inválida → Blocked Response
  ↓
Se válida → Query Executor
  ↓
Result Summarizer
  ↓
Chart Recommender
  ↓
END

## 10. Domínio de Dados

O MVP usará um domínio fictício de e-commerce e marketing analytics.

Esse domínio foi escolhido porque é fácil de entender e gera perguntas úteis, como:

produtos mais vendidos;
receita por canal;
campanhas com maior conversão;
clientes mais ativos;
vendas por período;
ticket médio;
categorias mais rentáveis.

## 11. Modelo de Dados

### 11.1 users

Armazena usuários do sistema.

Campos:

id
name
email
hashed_password
role
is_active
created_at

Roles:

admin
analyst
viewer
11.2 customers

Armazena clientes fictícios.

Campos:

id
name
email
city
state
created_at

### 11.3 products

Armazena produtos.

Campos:

id
name
category
price
created_at

### 11.4 sales_channels

Armazena canais de venda.

Campos:

id
name
type
created_at

Exemplos:

Website
App Mobile
Marketplace
Loja Física
WhatsApp

### 11.5 campaigns

Armazena campanhas de marketing.

Campos:

id
name
channel
start_date
end_date
budget
target_audience
created_at

### 11.6 orders

Armazena pedidos.

Campos:

id
customer_id
sales_channel_id
campaign_id
order_date
status
total_amount
created_at

Status possíveis:

paid
cancelled
pending
refunded

### 11.7 order_items

Armazena itens dos pedidos.

Campos:

id
order_id
product_id
quantity
unit_price
subtotal

### 11.8 query_logs

Armazena histórico das perguntas feitas ao agente.

Campos:

id
user_id
question
generated_sql
status
blocked_reason
answer_summary
execution_time_ms
provider_used
model_used
created_at

Status possíveis:

success
blocked
error
needs_clarification

### 11.9 query_feedback

Armazena feedback humano sobre as respostas.

Campos:

id
query_log_id
user_id
rating
is_helpful
comment
created_at

## 12. Tabelas Permitidas e Bloqueadas

### 12.1 Tabelas Permitidas para Consulta

O agente poderá consultar apenas:

customers
products
orders
order_items
campaigns
sales_channels

### 12.2 Tabelas Bloqueadas

O agente nunca poderá consultar:

users
query_logs
query_feedback

Essas tabelas são internas e não devem ser expostas ao agente de análise.

## 13. Requisitos Funcionais
RF01 — Autenticação

O sistema deve permitir:

registrar usuário;
fazer login;
receber token JWT;
acessar rotas protegidas.

Endpoints:

POST /auth/register
POST /auth/login
GET /users/me
RF02 — Catálogo de Dados

O sistema deve listar tabelas permitidas e schemas disponíveis.

Endpoints:

GET /catalog/tables
GET /catalog/tables/{table_name}/schema
RF03 — Pergunta em Linguagem Natural

O usuário deve poder fazer uma pergunta sobre os dados.

Endpoint:

POST /queries/ask

Request:

{
  "question": "Quais foram os 5 produtos mais vendidos no último mês?"
}
RF04 — Geração de SQL

O sistema deve gerar SQL usando LangChain com base em:

pergunta do usuário;
schema permitido;
descrição das tabelas;
regras de segurança.
RF05 — Validação de SQL

Antes de executar qualquer SQL, o sistema deve validar:

a query começa com SELECT;
não contém comandos proibidos;
não contém múltiplas statements;
só acessa tabelas permitidas;
possui LIMIT;
não usa SELECT *.
RF06 — Execução Controlada

O sistema só deve executar queries aprovadas pelo SQL Safety Validator.

RF07 — Resposta em Linguagem Natural

Após executar a query, o sistema deve gerar uma resposta clara.

Exemplo:

Os produtos mais vendidos no período foram Notebook Pro, Smartwatch X e Mouse Gamer. O Notebook Pro liderou com 128 unidades vendidas.
RF08 — Sugestão de Gráfico

O sistema deve sugerir um tipo de gráfico:

bar
line
pie
table
metric

Regras:

comparação entre categorias → bar
evolução temporal → line
participação percentual → pie
valor único → metric
resultado tabular → table
RF09 — Histórico de Consultas

O sistema deve salvar:

pergunta;
SQL gerado;
status;
motivo do bloqueio, se houver;
resposta;
tempo de execução;
usuário;
data.
RF10 — Feedback

O usuário deve poder avaliar a resposta:

útil/não útil;
nota de 1 a 5;
comentário opcional.

Endpoint:

POST /queries/{query_id}/feedback
RF11 — Métricas

O sistema deve exibir:

total de perguntas;
queries aprovadas;
queries bloqueadas;
taxa de sucesso;
tempo médio de resposta;
feedback positivo;
tabelas mais consultadas;
motivos de bloqueio mais comuns.

## 14. Requisitos Não Funcionais
RNF01 — Segurança

O sistema deve:

executar apenas SELECT;
bloquear comandos destrutivos;
usar allowlist de tabelas;
exigir LIMIT;
proteger endpoints com JWT;
armazenar segredos em .env;
não versionar .env.
RNF02 — Observabilidade

O sistema deve registrar:

latência;
status da query;
erro, quando houver;
usuário;
modelo usado;
provider usado;
SQL gerado;
motivo de bloqueio.
RNF03 — Manutenibilidade

O código deve separar:

rotas;
schemas;
models;
repositories;
services;
agents;
validators;
tools.
RNF04 — Testabilidade

O projeto deve conter testes para:

health check;
autenticação;
SQL Safety Validator;
bloqueio de comandos perigosos;
queries seguras;
histórico;
feedback;
métricas.
RNF05 — Portabilidade

O projeto deve rodar com:

docker compose up --build

## 15. SQL Safety Validator

### 15.1 Serviço

Criar arquivo:

app/services/sql_safety_service.py

### 15.2 Responsabilidades

O serviço deve:

normalizar SQL;
impedir múltiplas statements;
permitir apenas SELECT;
bloquear palavras proibidas;
validar tabelas permitidas;
exigir LIMIT;
limitar quantidade máxima de linhas.
15.3 Palavras Proibidas
INSERT
UPDATE
DELETE
DROP
ALTER
TRUNCATE
CREATE
REPLACE
GRANT
REVOKE
MERGE
CALL
EXEC

### 15.4 Regras Obrigatórias

A query deve:

começar com SELECT;
não conter comandos proibidos;
não conter ; com múltiplas statements;
não usar SELECT *;
possuir LIMIT;
usar apenas tabelas permitidas.

## 16. Prompt do Agente SQL

Prompt base:

Você é o DataTalk AI, um agente especializado em análise de dados empresariais.

Seu trabalho é transformar perguntas em linguagem natural em consultas SQL seguras.

Regras obrigatórias:

1. Gere apenas consultas SELECT.
2. Nunca gere INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, REPLACE, GRANT ou REVOKE.
3. Use apenas tabelas permitidas.
4. Nunca consulte tabelas internas como users, query_logs ou query_feedback.
5. Sempre use LIMIT, no máximo {max_rows}.
6. Nunca use SELECT *.
7. Use nomes explícitos de colunas.
8. Se a pergunta for ambígua, peça esclarecimento.
9. Se não for possível responder com os dados disponíveis, diga isso claramente.
10. Antes de executar, a query será validada por uma camada de segurança.

Pergunta do usuário:
{question}

Schema permitido:
{schema}

## 17. API Design

### 17.1 Health
GET /
GET /health

Resposta esperada:

{
  "status": "ok",
  "database": "connected",
  "llm_provider": "mock"
}

### 17.2 Auth
POST /auth/register
POST /auth/login
GET /users/me
17.3 Catalog
GET /catalog/tables
GET /catalog/tables/{table_name}/schema

### 17.4 Queries
POST /queries/ask
GET /queries/history
GET /queries/{query_id}

### 17.5 Feedback
POST /queries/{query_id}/feedback
GET /queries/{query_id}/feedback

### 17.6 Metrics
GET /metrics/overview
GET /metrics/queries
GET /metrics/tables

## 18. Contratos de API

### 18.1 POST /queries/ask — Sucesso

Request:

{
  "question": "Quais foram os 5 produtos mais vendidos no último mês?"
}

Response:

{
  "query_id": 1,
  "status": "success",
  "answer": "Os produtos mais vendidos no último mês foram Notebook Pro, Smartwatch X, Mouse Gamer, Headset Ultra e Monitor 27.",
  "generated_sql": "SELECT p.name, SUM(oi.quantity) AS total_sold FROM products p JOIN order_items oi ON p.id = oi.product_id JOIN orders o ON o.id = oi.order_id WHERE o.order_date >= CURRENT_DATE - INTERVAL '30 days' GROUP BY p.name ORDER BY total_sold DESC LIMIT 5;",
  "columns": ["product_name", "total_sold"],
  "rows": [
    {
      "product_name": "Notebook Pro",
      "total_sold": 128
    }
  ],
  "chart": {
    "type": "bar",
    "x": "product_name",
    "y": "total_sold"
  },
  "metadata": {
    "model_used": "gemini-2.5-flash",
    "provider_used": "gemini",
    "execution_time_ms": 1340
  }
}

### 18.2 POST /queries/ask — Bloqueado

Response:

{
  "query_id": 2,
  "status": "blocked",
  "answer": "Não posso executar essa operação. O sistema permite apenas consultas de leitura.",
  "blocked_reason": "Comando DELETE detectado.",
  "generated_sql": "DELETE FROM orders WHERE status = 'cancelled';"
}

### 18.3 POST /queries/ask — Pergunta Ambígua

Response:

{
  "query_id": 3,
  "status": "needs_clarification",
  "answer": "Sua pergunta está ampla. Você deseja analisar vendas por período, produto, canal ou região?",
  "generated_sql": null,
  "rows": [],
  "chart": {
    "type": "table"
  }
}

## 19. Camada de LLM Providers

O projeto deve suportar:

LLM_PROVIDER=mock
LLM_PROVIDER=gemini
LLM_PROVIDER=openai

### 19.1 Mock Provider

Deve funcionar sem API key.

Responsabilidades:

retornar SQL simulado para perguntas conhecidas;
retornar resposta simulada;
permitir testes e CI sem custo.

### 19.2 Gemini Provider

Provider principal para uso real.

### 19.3 OpenAI Provider

Provider opcional.

## 20. Estrutura do Projeto
datatalk-ai/
├── AGENTS.md
├── docs/
│   └── SDD.md
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── deps.py
│   │   └── routes/
│   │       ├── auth.py
│   │       ├── health.py
│   │       ├── catalog.py
│   │       ├── queries.py
│   │       ├── feedback.py
│   │       └── metrics.py
│   ├── agents/
│   │   ├── sql_agent.py
│   │   ├── langgraph_workflow.py
│   │   └── prompts.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── logging.py
│   ├── db/
│   │   ├── database.py
│   │   ├── base.py
│   │   └── seed.py
│   ├── models/
│   │   ├── user.py
│   │   ├── customer.py
│   │   ├── product.py
│   │   ├── order.py
│   │   ├── order_item.py
│   │   ├── campaign.py
│   │   ├── sales_channel.py
│   │   ├── query_log.py
│   │   └── query_feedback.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── catalog.py
│   │   ├── query.py
│   │   ├── feedback.py
│   │   └── metric.py
│   ├── repositories/
│   │   ├── catalog_repository.py
│   │   ├── query_repository.py
│   │   ├── feedback_repository.py
│   │   └── metric_repository.py
│   ├── services/
│   │   ├── query_orchestrator_service.py
│   │   ├── sql_safety_service.py
│   │   ├── sql_execution_service.py
│   │   ├── chart_service.py
│   │   ├── summarizer_service.py
│   │   └── metric_service.py
│   └── tests/
│       ├── test_health.py
│       ├── test_sql_safety.py
│       ├── test_query_orchestrator.py
│       ├── test_feedback.py
│       └── test_metrics.py
├── frontend/
├── alembic/
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md

## 21. Frontend
21.1 Stack
React
Vite
TypeScript
Tailwind CSS
Axios
Recharts
Lucide React
21.2 Telas
Login
email;
senha;
botão de entrar.
Dashboard

Cards:

total de perguntas;
queries aprovadas;
queries bloqueadas;
tempo médio;
feedback positivo.
Data Catalog

Exibe:

tabelas permitidas;
colunas;
tipos;
descrição de cada tabela.
Ask Data

Tela principal:

campo de pergunta;
resposta natural;
SQL gerado;
status da validação;
tabela de resultado;
gráfico sugerido.
History

Exibe histórico:

pergunta;
SQL;
status;
data;
tempo de execução.
Metrics

Gráficos:

perguntas por dia;
queries bloqueadas por motivo;
tabelas mais consultadas;
feedback por nota.

### 22. Docker

Criar docker-compose.yml com:

db
api
frontend

### 22.1 Banco

Usar PostgreSQL.

Porta padrão:

5432

### 22.2 API

Porta padrão:

8000

### 22.3 Frontend

Porta padrão:

5173

Comando esperado:

docker compose up --build

## 23. Variáveis de Ambiente

Criar .env.example:

DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/datatalk

SECRET_KEY=change_this_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

LLM_PROVIDER=mock

GEMINI_API_KEY=your_gemini_key_here
GEMINI_CHAT_MODEL=gemini-2.5-flash

OPENAI_API_KEY=your_openai_key_here
OPENAI_CHAT_MODEL=gpt-4o-mini

QUERY_MAX_ROWS=100
DEFAULT_QUERY_LIMIT=20

ENVIRONMENT=development
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

## 24. Seed de Dados

O seed deve criar:

Usuários demo
admin@datatalk.ai / admin123
analyst@datatalk.ai / analyst123
viewer@datatalk.ai / viewer123
Dados fictícios

Criar dados para:

clientes;
produtos;
canais de venda;
campanhas;
pedidos;
itens de pedidos.

O banco deve ter dados suficientes para perguntas interessantes.

Exemplos:

50 clientes;
20 produtos;
5 canais de venda;
10 campanhas;
200 pedidos;
500 itens de pedidos.

## 25. Testes

### 25.1 Testes Obrigatórios

Criar testes para:

test_health_returns_200
test_blocks_delete_query
test_blocks_update_query
test_blocks_drop_query
test_blocks_multiple_statements
test_blocks_select_star
test_blocks_unknown_table
test_allows_safe_select_with_limit
test_query_history_is_saved
test_feedback_is_saved
test_metrics_are_calculated
25.2 Exemplo de Teste Crítico
def test_blocks_destructive_sql():
    sql = "DELETE FROM orders WHERE status = 'cancelled'"
    result = validator.validate(sql)

    assert result.is_valid is False
    assert "DELETE" in result.reason

## 26. CI/CD

Criar GitHub Actions para:

Backend
instalar dependências;
compilar código;
rodar testes.
Frontend
instalar dependências;
rodar build.
Docker
validar docker compose config.

Fluxo:

push/pull request
  ↓
backend tests
  ↓
frontend build
  ↓
docker compose config

## 27. Métricas
Métricas de Uso
total de queries;
queries com sucesso;
queries bloqueadas;
tempo médio de resposta;
feedback positivo.
Métricas de Segurança
bloqueios por comando destrutivo;
bloqueios por tabela proibida;
bloqueios por ausência de LIMIT;
bloqueios por múltiplas statements.
Métricas de Produto
tabelas mais consultadas;
perguntas mais comuns;
taxa de sucesso;
taxa de bloqueio.

## 28. Roadmap
Fase 1 — MVP Seguro
FastAPI;
PostgreSQL;
dados fictícios;
LangChain SQL Agent;
SQL Safety Validator;
frontend com resposta, tabela e gráfico.
Fase 2 — LangGraph

Transformar fluxo em grafo:

classificar → gerar SQL → validar → executar → resumir → visualizar
Fase 3 — LlamaIndex

Combinar dados estruturados com documentos não estruturados.

Exemplo:

SQL responde números.
LlamaIndex recupera descrição textual/documentação.
Fase 4 — Observabilidade
logs estruturados;
métricas avançadas;
tracing;
monitoramento de erro.
Fase 5 — Cloud-ready
arquitetura AWS/GCP;
deploy containerizado;
secrets manager;
usuário de banco read-only.

## 29. Critérios de Aceite

O projeto será considerado pronto quando:

[ ] Rodar com docker compose up --build
[ ] Backend abrir em http://localhost:8000/docs
[ ] Frontend abrir em http://localhost:5173
[ ] Login funcionar
[ ] Banco vier populado com dados demo
[ ] Usuário conseguir fazer pergunta em linguagem natural
[ ] Sistema gerar SQL
[ ] Sistema validar SQL
[ ] Sistema bloquear comandos perigosos
[ ] Sistema executar SELECT seguro
[ ] Sistema retornar resposta natural
[ ] Sistema retornar tabela
[ ] Sistema sugerir gráfico
[ ] Histórico salvar pergunta e SQL
[ ] Feedback funcionar
[ ] Métricas aparecerem no dashboard
[ ] Testes passarem
[ ] README explicar arquitetura, segurança e uso

## 30. Prioridade de Implementação

Implementar nesta ordem:

estrutura inicial do projeto;
backend FastAPI;
configuração e health check;
banco PostgreSQL;
models e migrations;
seed de dados;
auth JWT;
catálogo de dados;
SQL Safety Validator;
Mock Provider;
LangChain SQL Agent;
Query Orchestrator;
histórico de queries;
feedback;
métricas;
frontend React;
Docker;
testes;
README;
CI/CD.

## 31. Como Apresentar o Projeto
Pitch Curto

O DataTalk AI é um agente de dados que permite consultar um banco PostgreSQL usando linguagem natural.

Ele usa IA para gerar SQL, mas possui uma camada de segurança que bloqueia comandos destrutivos, limita resultados e registra tudo em histórico, métricas e feedback.

Pitch para Entrevista

Desenvolvi o DataTalk AI para simular um problema real de empresas: permitir que pessoas de negócio consultem dados sem depender sempre de alguém escrevendo SQL. Usei FastAPI, PostgreSQL e LangChain para transformar perguntas em SQL, mas implementei uma camada de validação para bloquear comandos perigosos e permitir apenas consultas SELECT. O sistema retorna resposta em linguagem natural, tabela, sugestão de gráfico, histórico, feedback e métricas.

## 32. Valor para Portfólio

Este projeto demonstra:

GenAI aplicada a dados;
LangChain;
agentes com tools;
FastAPI;
SQL;
segurança;
validação de saída de LLM;
backend profissional;
frontend React;
Docker;
testes;
CI/CD;
pensamento de produto;
mentalidade de AI Engineer.

O ponto mais importante do projeto não é apenas gerar SQL.

O diferencial é:

IA + banco de dados + segurança + rastreabilidade + experiência de usuário