#!/usr/bin/env bash
# Push MISTRAL_API_KEY from local .env into Secret Manager (new version :latest).
# Does NOT print the key. Then redeploy Cloud Run to load it.
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
ENV_FILE="${ENV_FILE:-$(cd "$(dirname "$0")/.." && pwd)/.env}"

if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: .env not found at $ENV_FILE"
  exit 1
fi

# shellcheck disable=SC1090
set -a
source "$ENV_FILE"
set +a

if [ -z "${MISTRAL_API_KEY:-}" ] || [ "$MISTRAL_API_KEY" = "your_mistral_api_key_here" ]; then
  echo "ERROR: set a real MISTRAL_API_KEY in $ENV_FILE"
  exit 1
fi

printf '%s' "$MISTRAL_API_KEY" | gcloud secrets versions add MISTRAL_API_KEY \
  --project="$PROJECT_ID" --data-file=-

echo "Secret MISTRAL_API_KEY: new version added (latest)."
echo ""
echo "Redeploy so Cloud Run picks it up:"
echo "  gcloud run deploy simplon-rag-api --region=europe-west1 \\"
echo "    --image=europe-west1-docker.pkg.dev/simplon-rag-sample/simplon-rag-repo/api:latest"
