#!/usr/bin/env bash
# Post-deploy checks for simplon-rag-api on Cloud Run.
set -euo pipefail

REGION="${GCP_REGION:-europe-west1}"
SERVICE_NAME="${CLOUD_RUN_SERVICE:-simplon-rag-api}"

URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" \
  --format='value(status.url)' 2>/dev/null || true)

if [ -z "$URL" ]; then
  echo "ERROR: service $SERVICE_NAME not found in $REGION"
  exit 1
fi

echo "Service URL: $URL"
echo ""
echo "=== Revision / traffic ==="
gcloud run services describe "$SERVICE_NAME" --region="$REGION" \
  --format='table(status.latestReadyRevisionName,status.conditions.type,status.conditions.status)'

echo ""
echo "=== Liveness (no DB) ==="
curl -sfS "${URL}/api/v1/health/live" | python3 -m json.tool || {
  echo "FAIL: /health/live"
  exit 1
}

echo ""
echo "=== Readiness (DB + Mistral) ==="
code=$(curl -sS -o /tmp/ready.json -w "%{http_code}" "${URL}/api/v1/health/ready" || echo "000")
cat /tmp/ready.json | python3 -m json.tool 2>/dev/null || cat /tmp/ready.json
echo "HTTP $code (200 = ready, 503 = expected if DB/Mistral not configured)"

echo ""
echo "=== Recent logs ==="
gcloud run services logs read "$SERVICE_NAME" --region="$REGION" --limit=20
