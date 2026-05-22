#!/bin/sh
set -e

# Local/docker-compose: migrate on container start.
# Cloud Run / CD: migrations run in CI before deploy (see .github/workflows/cd.yml).
if [ "${RUN_DB_MIGRATIONS:-false}" = "true" ]; then
  alembic upgrade head
fi

exec "$@"
