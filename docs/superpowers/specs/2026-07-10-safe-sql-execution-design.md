# Safe SQL Execution Design

## Scope

This milestone adds the secure foundation for executing approved analytical SQL. It does not connect execution to the query orchestrator yet and does not implement summarization or chart recommendations.

## Architecture

Administrative application work continues to use `DATABASE_URL`. Analytical queries use a separate `QUERY_DATABASE_URL` engine whose PostgreSQL role has `SELECT` privileges only on the six public business tables.

`SqlExecutionService` accepts SQL, revalidates it immediately before opening the query connection, executes it with `sqlalchemy.text` inside an explicit read-only transaction, applies local statement and lock timeouts, and rolls the transaction back after reading the result. It returns a frozen Pydantic result containing columns, JSON-compatible rows, row count, and database execution time.

Docker initialization remains idempotent. After migrations and seed, an administrative bootstrap script creates or updates `datatalk_reader`, revokes broad privileges, and grants only `CONNECT`, schema `USAGE`, and table-level `SELECT` on the allowlist.

## Error Handling

Rejected SQL raises a domain validation error before any database connection is opened. Database failures are converted into a generic execution error that does not include driver messages, SQL text, credentials, or stack traces.

## Tests

Unit tests cover revalidation, result mapping, JSON serialization, timeout/read-only statements, rollback-only behavior, row limiting, and sanitized database errors. Static Docker validation confirms that both database URLs and the reader bootstrap are wired correctly. PostgreSQL privilege integration tests remain a later milestone.
