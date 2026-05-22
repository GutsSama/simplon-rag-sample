#!/usr/bin/env bash
# Run Alembic migrations against Cloud SQL (via Cloud SQL Auth Proxy).
#
# Prereqs:
#   - cloud-sql-proxy installed (brew install cloud-sql-proxy)
#   - POSTGRES_PASSWORD secret matches Cloud SQL user rag_user
#
# Usage:
#   ./scripts/migrate_cloudsql.sh

set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${GCP_REGION:-europe-west1}"
INSTANCE="${CLOUDSQL_INSTANCE:-simplon-rag-db-instance}"
CONN="${PROJECT_ID}:${REGION}:${INSTANCE}"
API_DIR="$(cd "$(dirname "$0")/../api" && pwd)"

export POSTGRES_HOST="${POSTGRES_HOST:-127.0.0.1}"
export POSTGRES_PORT="${POSTGRES_PORT:-5432}"
export POSTGRES_USER="${POSTGRES_USER:-rag_user}"
export POSTGRES_DB="${POSTGRES_DB:-rag_db}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-$(gcloud secrets versions access latest --secret=POSTGRES_PASSWORD --project="$PROJECT_ID")}"

if ! command -v cloud-sql-proxy >/dev/null 2>&1; then
  echo "ERROR: install cloud-sql-proxy (brew install cloud-sql-proxy)"
  exit 1
fi

echo "Instance: $CONN"
echo "Database: $POSTGRES_DB @ $POSTGRES_USER"
echo "Starting Cloud SQL Auth Proxy on 127.0.0.1:${POSTGRES_PORT}..."

cloud-sql-proxy "$CONN" --port "$POSTGRES_PORT" &
PROXY_PID=$!
trap 'kill "$PROXY_PID" 2>/dev/null || true' EXIT

for i in $(seq 1 30); do
  if (echo >/dev/tcp/127.0.0.1/"$POSTGRES_PORT") 2>/dev/null; then
    break
  fi
  sleep 1
done

cd "$API_DIR"
uv sync --frozen
uv run alembic upgrade head
echo "Migrations applied."
