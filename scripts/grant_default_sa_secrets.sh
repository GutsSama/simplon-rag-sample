#!/usr/bin/env bash
# Phase 1: grant default Compute SA access to secrets + Cloud SQL (manual Cloud Run deploy).
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
PROJECT_NUMBER="${GCP_PROJECT_NUMBER:-$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')}"
DEFAULT_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
REGION="${GCP_REGION:-europe-west1}"
SERVICE_NAME="${CLOUD_RUN_SERVICE:-simplon-rag-api}"
REQUIRED_SECRETS=(POSTGRES_PASSWORD MISTRAL_API_KEY JWT_SECRET)
GRANT_CLOUDSQL="${GRANT_CLOUDSQL:-true}"

if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "(unset)" ]; then
  echo "ERROR: set GCP project — gcloud config set project simplon-rag-sample"
  exit 1
fi

echo "Project:          $PROJECT_ID"
echo "Default Compute:  $DEFAULT_SA"
echo ""

echo "=== 1. Verify secrets exist and have at least one version ==="
missing=0
for secret in "${REQUIRED_SECRETS[@]}"; do
  if ! gcloud secrets describe "$secret" --project="$PROJECT_ID" &>/dev/null; then
    echo "MISSING secret: $secret"
    echo "  Create: echo -n 'value' | gcloud secrets create $secret --data-file=- --project=$PROJECT_ID"
    missing=1
    continue
  fi
  version_count=$(gcloud secrets versions list "$secret" --project="$PROJECT_ID" \
    --filter="state=ENABLED" --format="value(name)" 2>/dev/null | wc -l | tr -d ' ')
  if [ "${version_count:-0}" -eq 0 ]; then
    echo "NO ENABLED VERSION: $secret"
    echo "  Add: echo -n 'value' | gcloud secrets versions add $secret --data-file=- --project=$PROJECT_ID"
    missing=1
  else
    latest=$(gcloud secrets versions list "$secret" --project="$PROJECT_ID" \
      --filter="state=ENABLED" --limit=1 --format="value(name)")
    echo "OK: $secret (enabled version: $latest — :latest in Cloud Run is valid)"
  fi
done

if [ "$missing" -ne 0 ]; then
  echo ""
  echo "Fix missing secrets/versions before IAM bindings."
  exit 1
fi

echo ""
echo "=== 2. Grant Secret Manager Secret Accessor on each secret ==="
for secret in "${REQUIRED_SECRETS[@]}"; do
  gcloud secrets add-iam-policy-binding "$secret" \
    --project="$PROJECT_ID" \
    --member="serviceAccount:${DEFAULT_SA}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet >/dev/null
  echo "IAM OK: $secret -> $DEFAULT_SA"
done

if [ "$GRANT_CLOUDSQL" = "true" ]; then
  echo ""
  echo "=== 3. Grant Cloud SQL Client (project level) ==="
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${DEFAULT_SA}" \
    --role="roles/cloudsql.client" \
    --condition=None \
    --quiet >/dev/null
  echo "IAM OK: roles/cloudsql.client -> $DEFAULT_SA"
fi

echo ""
echo "=== Done. Redeploy then verify: ==="
echo "  gcloud run deploy $SERVICE_NAME --region=$REGION ... (your deploy command)"
echo ""
echo "  gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)'"
echo "  curl -sS \"\$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')/api/v1/health/live\""
echo "  gcloud run services logs read $SERVICE_NAME --region=$REGION --limit=30"
