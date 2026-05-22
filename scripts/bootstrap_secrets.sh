#!/usr/bin/env bash
# Create required Secret Manager secrets (if missing) and enable :latest for Cloud Run.
#
# Usage:
#   export MISTRAL_API_KEY="your-key"
#   export POSTGRES_PASSWORD="your-db-password"
#   export JWT_SECRET="$(openssl rand -hex 32)"   # optional, auto-generated if unset
#   ./scripts/bootstrap_secrets.sh
#
# Then:
#   ./scripts/grant_default_sa_secrets.sh
#   gcloud run deploy ...

set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"

upsert_secret() {
  local name="$1"
  local value="$2"
  if [ -z "$value" ]; then
    echo "ERROR: empty value for $name"
    return 1
  fi
  if gcloud secrets describe "$name" --project="$PROJECT_ID" &>/dev/null; then
    echo -n "$value" | gcloud secrets versions add "$name" \
      --project="$PROJECT_ID" --data-file=-
    echo "Added new version: $name"
  else
    echo -n "$value" | gcloud secrets create "$name" \
      --project="$PROJECT_ID" --replication-policy="automatic" --data-file=-
    echo "Created secret: $name"
  fi
}

if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "(unset)" ]; then
  echo "ERROR: gcloud project not set"
  exit 1
fi

POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"
MISTRAL_API_KEY="${MISTRAL_API_KEY:-}"
JWT_SECRET="${JWT_SECRET:-$(openssl rand -hex 32)}"

if [ -z "$POSTGRES_PASSWORD" ]; then
  read -rsp "POSTGRES_PASSWORD (Cloud SQL user password): " POSTGRES_PASSWORD
  echo ""
fi
if [ -z "$MISTRAL_API_KEY" ]; then
  read -rsp "MISTRAL_API_KEY: " MISTRAL_API_KEY
  echo ""
fi

echo "Project: $PROJECT_ID"
upsert_secret "POSTGRES_PASSWORD" "$POSTGRES_PASSWORD"
upsert_secret "MISTRAL_API_KEY" "$MISTRAL_API_KEY"
upsert_secret "JWT_SECRET" "$JWT_SECRET"

echo ""
echo "Next:"
echo "  ./scripts/grant_default_sa_secrets.sh"
echo "  # redeploy Cloud Run"
