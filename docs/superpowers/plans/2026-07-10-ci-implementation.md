# DataTalk AI CI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a GitHub Actions workflow that validates the backend, frontend, and Docker Compose definition on every push and pull request.

**Architecture:** A single workflow contains three independent jobs so each project boundary reports failures separately and jobs can run in parallel. The workflow has read-only permissions, uses dependency caching, cancels stale branch runs, and never deploys or accesses secrets.

**Tech Stack:** GitHub Actions, Python 3.12, Node.js 20, Pytest, Vitest, TypeScript, Vite, Docker Compose.

## Global Constraints

- Continuous integration only; no deployment steps.
- Run on every `push` and `pull_request`.
- Use only `contents: read` permissions.
- Do not reference repository secrets or external LLM API keys.
- Preserve all unrelated staged and working-tree changes.

---

### Task 1: Add the CI Workflow

**Files:**
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: `requirements.txt`, `frontend/package-lock.json`, backend tests, frontend scripts, and `docker-compose.yml`.
- Produces: GitHub Actions workflow `CI` with jobs `backend`, `frontend`, and `docker`.

- [ ] **Step 1: Confirm the workflow does not exist**

Run:

```powershell
Test-Path .github/workflows/ci.yml
```

Expected: `False`.

- [ ] **Step 2: Create the workflow**

Create `.github/workflows/ci.yml` with this exact content:

```yaml
name: CI

on:
  push:
  pull_request:

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

jobs:
  backend:
    name: Backend
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6
      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: requirements.txt
      - name: Install backend dependencies
        run: python -m pip install -r requirements.txt
      - name: Compile backend
        run: python -m compileall app alembic
      - name: Run backend tests
        run: python -m pytest -q

  frontend:
    name: Frontend
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6
      - name: Set up Node.js
        uses: actions/setup-node@v6
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - name: Install frontend dependencies
        run: npm ci
      - name: Check frontend types
        run: npm run typecheck
      - name: Run frontend tests
        run: npm run test
      - name: Build frontend
        run: npm run build

  docker:
    name: Docker Compose
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6
      - name: Validate Docker Compose configuration
        run: docker compose config
```

- [ ] **Step 3: Validate workflow structure locally**

Run:

```powershell
docker compose config
python -m compileall app alembic
python -m pytest -q
```

Expected: Compose validation succeeds, compilation succeeds, and all backend tests pass.

- [ ] **Step 4: Validate frontend commands locally**

Run from `frontend`:

```powershell
npm ci
npm run typecheck
npm run test
npm run build
```

Expected: dependency installation, type checking, all frontend tests, and the production build succeed.

### Task 2: Update the README CI Status

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: workflow name `CI` and repository path `marcoaurelioleal-AI/DataTalk-AI`.
- Produces: visible CI badge and accurate documentation of automated validation.

- [ ] **Step 1: Add the workflow badge below the title**

Add this line below `# DataTalk AI`:

```markdown
[![CI](https://github.com/marcoaurelioleal-AI/DataTalk-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/marcoaurelioleal-AI/DataTalk-AI/actions/workflows/ci.yml)
```

- [ ] **Step 2: Document the automated checks**

After the local infrastructure validation command, add:

```markdown
O GitHub Actions executa essas verificacoes automaticamente em cada push e pull request, com jobs independentes para backend, frontend e Docker Compose.
```

- [ ] **Step 3: Update the roadmap**

Replace the current roadmap item:

```markdown
5. CI/CD no GitHub Actions e preparacao para deploy cloud.
```

with:

```markdown
5. Preparacao para deploy cloud com ambientes e secrets gerenciados.
```

- [ ] **Step 4: Validate the complete change set**

Run:

```powershell
git diff --check
```

Expected: exit code `0` with no whitespace errors.

- [ ] **Step 5: Inspect only CI-related files**

Run:

```powershell
git diff -- .github/workflows/ci.yml README.md
```

Expected: one new workflow and only the planned README edits.
