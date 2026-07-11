# AGENTS.md — DataTalk AI

## Instrução obrigatória

Antes de implementar qualquer código, leia integralmente:

- `docs/SDD.md`

O arquivo `docs/SDD.md` é a fonte principal de verdade do projeto DataTalk AI.

## Objetivo do projeto

Construir o DataTalk AI, uma plataforma de AI Engineering que permite consultar dados de negócio usando linguagem natural, com geração de SQL segura, validação contra comandos destrutivos, execução apenas de consultas permitidas, resposta em linguagem natural, tabela, gráfico, histórico, feedback e métricas.

## Prioridades de implementação

Siga esta ordem:

1. Estrutura inicial do projeto
2. Backend FastAPI
3. Configuração e health check
4. Banco PostgreSQL
5. Models e migrations
6. Seed de dados
7. Auth JWT
8. Catálogo de dados
9. SQL Safety Validator
10. Mock Provider
11. LangChain SQL Agent
12. Query Orchestrator
13. Histórico de queries
14. Feedback
15. Métricas
16. Frontend React
17. Docker
18. Testes
19. README
20. CI/CD

## Regras técnicas obrigatórias

- Nunca implemente execução de SQL sem validação prévia.
- O sistema deve executar apenas queries `SELECT`.
- Bloqueie comandos destrutivos como `DELETE`, `UPDATE`, `INSERT`, `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, `GRANT`, `REVOKE`.
- Use allowlist de tabelas consultáveis.
- Não permita consulta às tabelas internas como `users`, `query_logs` e `query_feedback`.
- Toda query executada ou bloqueada deve ser registrada.
- Use variáveis de ambiente para segredos.
- Não versionar `.env`.
- Separar rotas, services, repositories, schemas, agents e validators.
- Criar testes para as regras críticas de segurança.
- O projeto deve rodar com `docker compose up --build`.

## Padrão de resposta esperado

Antes de modificar código, explique rapidamente:

1. O que será alterado
2. Quais arquivos serão criados/editados
3. Como testar

Após modificar código, informe:

1. O que foi implementado
2. Comandos executados
3. Testes realizados
4. Próximo passo recomendado

## Critério de aceite

O projeto só deve ser considerado pronto quando:

- O backend rodar
- O banco estiver populado com dados demo
- O usuário conseguir fazer pergunta em linguagem natural
- O sistema gerar SQL
- O SQL Safety Validator validar ou bloquear a query
- Queries perigosas forem bloqueadas
- Queries seguras retornarem tabela, resumo e sugestão de gráfico
- Histórico, feedback e métricas funcionarem
- Testes passarem
- README explicar arquitetura, segurança e execução

## Controle de escopo e milestones

O projeto deve ser desenvolvido em milestones pequenos e independentes.

Regras obrigatórias:

* Implemente somente o milestone solicitado no prompt atual.
* Não inicie o próximo milestone automaticamente.
* Não implemente funcionalidades fora do escopo solicitado.
* Não faça refatorações amplas sem necessidade direta.
* Não adicione dependências de produção fora das exigidas pelo milestone.
* Antes de modificar arquivos, informe brevemente o plano e os arquivos envolvidos.
* Execute primeiro os testes diretamente relacionados ao milestone.
* Execute a suíte completa somente ao final do milestone.
* Não faça commit nem push automaticamente.
* Ao terminar, pare e aguarde aprovação.

Ao concluir cada milestone, retorne somente:

1. diagnóstico;
2. arquivos criados;
3. arquivos alterados;
4. implementação realizada;
5. testes executados;
6. resultados;
7. limitações restantes;
8. próximo milestone recomendado.

O próximo milestone deve ser apenas recomendado, nunca iniciado automaticamente.
