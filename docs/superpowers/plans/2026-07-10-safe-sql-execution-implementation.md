# Safe SQL Execution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a separately configured, PostgreSQL read-only SQL execution layer without wiring it into the query orchestrator yet.

**Architecture:** Keep administrative persistence on `DATABASE_URL` and create a distinct query engine from `QUERY_DATABASE_URL`. Revalidate every statement in `SqlExecutionService`, execute with PostgreSQL transaction-local protections, map results to JSON-safe values, and provision a least-privilege Docker role after migrations.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2, Pydantic 2, psycopg 3, PostgreSQL 16, Pytest, Docker Compose.

## Global Constraints

- Execute only SQL approved by `SqlSafetyService`.
- Never execute generated SQL through the administrative engine.
- Never commit a query transaction.
- Do not connect this service to the orchestrator in this milestone.
- Preserve all existing local changes and do not commit or push.

---

### Task 1: SQL execution contract and core behavior

**Files:**
- Create: `app/schemas/sql_execution.py`
- Create: `app/services/sql_execution_service.py`
- Create: `app/tests/test_sql_execution_service.py`

**Interfaces:**
- Consumes: `SqlSafetyService.validate(sql: str) -> SqlSafetyResult` and a SQLAlchemy `Engine`.
- Produces: `SqlExecutionService.execute(sql: str) -> SqlExecutionResult`.

- [ ] Write tests for rejected SQL, query result mapping, JSON-safe values, read-only transaction settings, rollback, row cap, and sanitized database errors.
- [ ] Run `python -m pytest app/tests/test_sql_execution_service.py -q` and confirm collection fails because the new modules do not exist.
- [ ] Implement the result schema, domain exceptions, and execution service with `sqlalchemy.text`.
- [ ] Re-run the focused test file and confirm it passes.

### Task 2: Dedicated analytical database configuration

**Files:**
- Modify: `app/core/config.py`
- Modify: `app/db/database.py`
- Modify: `.env.example`
- Test: `app/tests/test_sql_execution_service.py`

**Interfaces:**
- Consumes: `QUERY_DATABASE_URL`, `QUERY_STATEMENT_TIMEOUT_MS`, and `QUERY_LOCK_TIMEOUT_MS`.
- Produces: `query_engine` used only by `SqlExecutionService`.

- [ ] Add failing settings tests proving the query URL and positive timeout values are exposed.
- [ ] Run the focused tests and verify the expected failure.
- [ ] Add settings fields, validators, and the separate query engine.
- [ ] Re-run the focused tests and confirm they pass.

### Task 3: Idempotent PostgreSQL read-only role

**Files:**
- Create: `app/db/configure_query_role.py`
- Modify: `docker-entrypoint.sh`
- Modify: `docker-compose.yml`
- Test: `app/tests/test_query_role_config.py`

**Interfaces:**
- Consumes: the administrative `DATABASE_URL` and reader credentials supplied by environment variables.
- Produces: a `datatalk_reader` role restricted to the catalog allowlist.

- [ ] Write tests for the exact allowlist, internal-table revocations, and idempotent SQL generation.
- [ ] Run the role test and confirm it fails because the module does not exist.
- [ ] Implement role configuration with quoted identifiers and bound password input.
- [ ] Invoke it after migration and seed, then configure `QUERY_DATABASE_URL` for the API service.
- [ ] Run role tests and `docker compose config --quiet`.

### Task 4: Regression verification

**Files:**
- No production file changes expected.

**Interfaces:**
- Consumes: all deliverables from Tasks 1-3.
- Produces: verification evidence for the milestone.

- [ ] Run `python -m compileall app`.
- [ ] Run `python -m pytest -q`.
- [ ] Run `docker compose config --quiet`.
- [ ] Inspect `git diff --check` and `git status --short --branch` without staging, committing, or pushing.
