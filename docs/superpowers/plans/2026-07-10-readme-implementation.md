# DataTalk AI README Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish a Portuguese README that accurately presents the implemented DataTalk AI MVP to recruiters and tech leads.

**Architecture:** The README is a single Markdown document at the repository root. Its claims are grounded in the FastAPI routes, Docker Compose configuration, frontend scripts, tests, and security service currently present in the repository.

**Tech Stack:** Markdown, FastAPI, React, PostgreSQL, Docker Compose, Pytest, Vitest.

## Global Constraints

- Write in Portuguese (Brazil) for recruiters and tech leads.
- Do not expose secrets or state that a live LLM provider is implemented.
- Document only commands and endpoints that exist in the repository.
- Publish only `README.md`; do not include unrelated pending changes.

---

### Task 1: Write the Portfolio README

**Files:**
- Create: `README.md`

**Interfaces:**
- Consumes: `docker-compose.yml`, `.env.example`, `frontend/package.json`, FastAPI route modules, and the validated test commands.
- Produces: A root README with project pitch, architecture, safety model, setup, users, endpoints, testing, and roadmap.

- [ ] **Step 1: Verify documented commands and contracts**

Run:

```powershell
docker compose config
python -m pytest -q
npm run test
```

Expected: Compose configuration is valid, backend tests pass, and frontend tests pass.

- [ ] **Step 2: Create README.md**

Include these sections in this order:

```markdown
# DataTalk AI

## Visão geral
## O que está implementado
## Arquitetura
## Segurança SQL
## Stack
## Execução com Docker
## Execução local
## Usuários demo
## API
## Testes
## Limites atuais e roadmap
```

- [ ] **Step 3: Validate documentation integrity**

Run:

```powershell
git diff --check
```

Expected: Exit code `0` with no whitespace errors.

### Task 2: Publish Only the README

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: The completed root README and the configured `origin` remote.
- Produces: One commit and push containing only `README.md`.

- [ ] **Step 1: Inspect scope before staging**

Run:

```powershell
git status --short
git diff -- README.md
```

Expected: `README.md` is the only file staged for this publication.

- [ ] **Step 2: Stage and commit the README**

Run:

```powershell
git add README.md
git commit -m "docs: add project README"
```

Expected: a commit containing only `README.md`.

- [ ] **Step 3: Push the current branch**

Run:

```powershell
git push origin main
```

Expected: the README is available in the configured GitHub repository.
