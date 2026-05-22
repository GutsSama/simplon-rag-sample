#!/usr/bin/env bash
# Provision Cloud Run runtime + GitHub deploy service accounts (WIF-ready).
#
# Run after: gcloud auth login && gcloud config set project simplon-rag-sample
#
# Phases:
#   ./scripts/setup_gcp_service_accounts.sh runtime   # cloudrun-runtime only
#   ./scripts/setup_gcp_service_accounts.sh deploy    # github-deploy + actAs
#   ./scripts/setup_gcp_service_accounts.sh developer   # grant actAs to your user (manual deploy)
#   ./scripts/setup_gcp_service_accounts.sh all

set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${GCP_REGION:-europe-west1}"
GITHUB_REPO="${GITHUB_REPO:-}" # e.g. org/simplon-rag-sample (required for deploy phase)

RUNTIME_SA="cloudrun-runtime"
DEPLOY_SA="github-deploy"
RUNTIME_EMAIL="${RUNTIME_SA}@${PROJECT_ID}.iam.gserviceaccount.com"
DEPLOY_EMAIL="${DEPLOY_SA}@${PROJECT_ID}.iam.gserviceaccount.com"
BUCKET_NAME="${GCS_BUCKET_NAME:-simplon-rag-corpus-${PROJECT_ID}}"
DEVELOPER_EMAIL="${DEVELOPER_EMAIL:-$(gcloud config get-value account 2>/dev/null)}"

usage() {
  echo "Usage: $0 {runtime|deploy|developer|all}"
  exit 1
}

create_sa() {
  local name="$1"
  local display="$2"
  local email="${name}@${PROJECT_ID}.iam.gserviceaccount.com"
  if gcloud iam service-accounts describe "$email" --project="$PROJECT_ID" &>/dev/null; then
    echo "Service account already exists: $email"
  else
    gcloud iam service-accounts create "$name" \
      --project="$PROJECT_ID" \
      --display-name="$display"
    echo "Created: $email"
  fi
}

setup_runtime() {
  echo "=== Runtime SA: $RUNTIME_EMAIL ==="
  create_sa "$RUNTIME_SA" "Cloud Run Runtime SA"

  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${RUNTIME_EMAIL}" \
    --role="roles/cloudsql.client" \
    --condition=None >/dev/null

  for secret in MISTRAL_API_KEY POSTGRES_PASSWORD JWT_SECRET; do
    if gcloud secrets describe "$secret" --project="$PROJECT_ID" &>/dev/null; then
      gcloud secrets add-iam-policy-binding "$secret" \
        --project="$PROJECT_ID" \
        --member="serviceAccount:${RUNTIME_EMAIL}" \
        --role="roles/secretmanager.secretAccessor" >/dev/null
      echo "Secret accessor: $secret"
    else
      echo "SKIP secret (not found): $secret"
    fi
  done

  if gcloud storage buckets describe "gs://${BUCKET_NAME}" &>/dev/null; then
    gcloud storage buckets add-iam-policy-binding "gs://${BUCKET_NAME}" \
      --member="serviceAccount:${RUNTIME_EMAIL}" \
      --role="roles/storage.objectUser" >/dev/null
    echo "GCS binding: gs://${BUCKET_NAME}"
  else
    echo "SKIP GCS bucket (not found): gs://${BUCKET_NAME}"
  fi
}

setup_deploy() {
  echo "=== Deploy SA: $DEPLOY_EMAIL ==="
  create_sa "$DEPLOY_SA" "GitHub Actions Deploy SA"

  for role in run.admin artifactregistry.writer cloudsql.client secretmanager.secretAccessor; do
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
      --member="serviceAccount:${DEPLOY_EMAIL}" \
      --role="roles/${role}" \
      --condition=None >/dev/null
    echo "Project role: ${role}"
  done

  # github-deploy must attach cloudrun-runtime when deploying Cloud Run
  gcloud iam service-accounts add-iam-policy-binding "$RUNTIME_EMAIL" \
    --project="$PROJECT_ID" \
    --member="serviceAccount:${DEPLOY_EMAIL}" \
    --role="roles/iam.serviceAccountUser" >/dev/null
  echo "actAs: ${DEPLOY_EMAIL} -> ${RUNTIME_EMAIL}"

  if [ -n "$GITHUB_REPO" ]; then
    PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
    gcloud iam service-accounts add-iam-policy-binding "$DEPLOY_EMAIL" \
      --project="$PROJECT_ID" \
      --role="roles/iam.workloadIdentityUser" \
      --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-actions-pool/attribute.repository/${GITHUB_REPO}" >/dev/null
    echo "WIF binding for repo: ${GITHUB_REPO}"
  else
    echo "SKIP WIF binding (set GITHUB_REPO=org/repo to enable)"
  fi
}

setup_developer() {
  if [ -z "$DEVELOPER_EMAIL" ]; then
    echo "ERROR: could not detect gcloud account. Set DEVELOPER_EMAIL=user@example.com"
    exit 1
  fi
  echo "=== Developer actAs: ${DEVELOPER_EMAIL} -> ${RUNTIME_EMAIL} ==="
  setup_runtime
  gcloud iam service-accounts add-iam-policy-binding "$RUNTIME_EMAIL" \
    --project="$PROJECT_ID" \
    --member="user:${DEVELOPER_EMAIL}" \
    --role="roles/iam.serviceAccountUser" >/dev/null
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="user:${DEVELOPER_EMAIL}" \
    --role="roles/run.admin" \
    --condition=None >/dev/null
  echo "Granted roles/iam.serviceAccountUser + roles/run.admin to ${DEVELOPER_EMAIL}"
}

[ -z "$PROJECT_ID" ] && echo "ERROR: no GCP project configured" && exit 1

case "${1:-}" in
  runtime) setup_runtime ;;
  deploy) setup_runtime; setup_deploy ;;
  developer) setup_developer ;;
  all) setup_runtime; setup_deploy; setup_developer ;;
  *) usage ;;
esac

echo ""
echo "Deploy with runtime SA:"
echo "  gcloud run deploy simplon-rag-api --region=${REGION} \\"
echo "    --service-account=${RUNTIME_EMAIL} \\"
echo "    ... (see README / cd.yml)"
