#!/usr/bin/env bash
# Align Cloud SQL rag_user password with Secret Manager POSTGRES_PASSWORD (latest version).
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
INSTANCE="${CLOUDSQL_INSTANCE:-simplon-rag-db-instance}"
PASSWORD="${POSTGRES_PASSWORD:-$(gcloud secrets versions access latest --secret=POSTGRES_PASSWORD --project="$PROJECT_ID")}"

gcloud sql users set-password rag_user \
  --instance="$INSTANCE" \
  --project="$PROJECT_ID" \
  --password="$PASSWORD"

echo "Cloud SQL user rag_user password synced with POSTGRES_PASSWORD secret."
