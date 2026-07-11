#!/bin/sh
set -e

alembic upgrade head
python -m app.db.seed
python -m app.db.configure_query_role

exec "$@"
