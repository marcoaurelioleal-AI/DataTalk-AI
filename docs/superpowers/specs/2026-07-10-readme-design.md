# README Design: DataTalk AI

## Objective

Create a Portuguese README for recruiters and tech leads that presents the
implemented DataTalk AI MVP accurately and makes local evaluation simple.

## Audience and Tone

- Primary audience: recruiters and tech leads who evaluate AI Engineering work.
- Language: Portuguese (Brazil).
- Tone: concise, technical, and evidence-based.

## Content Structure

1. Project pitch and the safe natural-language-to-SQL problem it solves.
2. Implemented capabilities, separated from roadmap items.
3. Architecture diagram showing React, FastAPI, orchestrator, agent, safety
   validator, and PostgreSQL.
4. Security model: SELECT-only execution, destructive-command blocking,
   allowlist, internal-table protection, SELECT-star prohibition, required
   LIMIT, and query logging.
5. Technology stack and repository structure.
6. Quick start with Docker Compose, local backend/frontend commands, and URLs.
7. Demo users, API endpoint overview, and example questions.
8. Verification commands and the current automated-test coverage.
9. Scope notes and roadmap, explicitly identifying LangGraph, LlamaIndex, live
   Gemini/OpenAI provider integration, cloud deployment, and CI/CD as future
   work where applicable.

## Constraints

- Do not include secrets or a real API key.
- Do not claim a live LLM provider or a complete LangChain chain is available.
- Keep commands aligned with the current Docker Compose and package scripts.
- Avoid screenshots that can drift; use a text architecture diagram instead.

## Validation

- Check every command and URL against the repository configuration.
- Check that every referenced endpoint exists in the FastAPI routes.
- Confirm Markdown whitespace with `git diff --check`.
