#!/usr/bin/env bash
# deployment script to provision and deploy the Simplon RAG application to GCP.
#
# Usage:
#   ./scripts/deploy_gcp.sh
#
# Make sure to run 'gcloud auth login' and 'gcloud config set project [YOUR-PROJECT-ID]' first.

set -euo pipefail

# ---------------------------------------------------------
# 1. Configuration & Default Variables
# ---------------------------------------------------------
REGION="europe-west1"
GCP_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")

if [ -z "$GCP_PROJECT" ]; then
    echo "ERROR: No active Google Cloud project set. Please set it using:"
    echo "  gcloud config set project <PROJECT_ID>"
    exit 1
fi

echo "========================================================="
echo "Targeting GCP Project: $GCP_PROJECT"
echo "Targeting Region:      $REGION"
echo "========================================================="

# Resource Names
BUCKET_NAME="simplon-rag-corpus-$GCP_PROJECT"
DB_INSTANCE_NAME="simplon-rag-db-instance"
DB_NAME="rag_db"
DB_USER="rag_user"
REPO_NAME="simplon-rag-repo"
IMAGE_NAME="api"
SERVICE_NAME="simplon-rag-api"
SERVICE_ACCOUNT_NAME="cloudrun-runtime"
SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_NAME@$GCP_PROJECT.iam.gserviceaccount.com"

# Secure random password generation if not provided in environment
DB_ROOT_PASSWORD="${POSTGRES_ROOT_PASSWORD:-$(openssl rand -hex 16)}"
DB_PASSWORD="${POSTGRES_PASSWORD:-$(openssl rand -hex 16)}"
JWT_SECRET="${JWT_SECRET:-$(openssl rand -hex 32)}"
MISTRAL_API_KEY="${MISTRAL_API_KEY:-}"

if [ -z "$MISTRAL_API_KEY" ]; then
    echo "WARNING: MISTRAL_API_KEY environment variable is not set."
    echo "Make sure to set MISTRAL_API_KEY in your local environment or enter it now."
    read -rsp "Enter MISTRAL_API_KEY: " MISTRAL_API_KEY
    echo ""
fi

# ---------------------------------------------------------
# 2. Enable Required APIs
# ---------------------------------------------------------
echo "Step 1: Enabling necessary Google Cloud APIs..."
gcloud services enable \
    run.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com \
    storage.googleapis.com

# ---------------------------------------------------------
# 3. Provision Google Cloud Storage (GCS)
# ---------------------------------------------------------
echo "Step 2: Creating and configuring Google Cloud Storage..."
if ! gcloud storage buckets describe "gs://$BUCKET_NAME" &>/dev/null; then
    gcloud storage buckets create "gs://$BUCKET_NAME" \
        --location="$REGION" \
        --uniform-bucket-level-access
    echo "Bucket gs://$BUCKET_NAME created successfully."
else
    echo "Bucket gs://$BUCKET_NAME already exists."
fi

# Create GCS Lifecycle rule to delete temp/old files after 30 days
echo "Configuring bucket lifecycle policy (deleting items after 30 days)..."
LIFECYCLE_FILE=$(mktemp)
cat <<EOF > "$LIFECYCLE_FILE"
{
  "rule": [
    {
      "action": {"type": "Delete"},
      "condition": {
        "age": 30
      }
    }
  ]
}
EOF
gcloud storage buckets update "gs://$BUCKET_NAME" --lifecycle-file="$LIFECYCLE_FILE"
rm -f "$LIFECYCLE_FILE"

# ---------------------------------------------------------
# 4. Provision Google Cloud SQL
# ---------------------------------------------------------
echo "Step 3: Provisioning Google Cloud SQL (PostgreSQL 15)..."
if ! gcloud sql instances describe "$DB_INSTANCE_NAME" &>/dev/null; then
    echo "Creating Cloud SQL PostgreSQL instance (db-f1-micro, this may take a few minutes)..."
    gcloud sql instances create "$DB_INSTANCE_NAME" \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region="$REGION" \
        --storage-size=10GB \
        --root-password="$DB_ROOT_PASSWORD" \
        --database-flags=cloudsql.enable_pgaudit=on
else
    echo "Cloud SQL instance $DB_INSTANCE_NAME already exists."
fi

echo "Ensuring application database '$DB_NAME' exists..."
if ! gcloud sql databases describe "$DB_NAME" --instance="$DB_INSTANCE_NAME" &>/dev/null; then
    gcloud sql databases create "$DB_NAME" --instance="$DB_INSTANCE_NAME"
fi

echo "Ensuring database user '$DB_USER' exists..."
# Create or update user password
gcloud sql users create "$DB_USER" \
    --instance="$DB_INSTANCE_NAME" \
    --password="$DB_PASSWORD" || \
gcloud sql users set-password "$DB_USER" \
    --instance="$DB_INSTANCE_NAME" \
    --password="$DB_PASSWORD"

# Enable pgvector extension using admin credentials if possible.
# Note: On Cloud SQL PostgreSQL, the 'vector' extension is trusted, so it can be installed
# by users in the cloudsqlsuperuser role. Running CREATE EXTENSION IF NOT EXISTS vector;
# is done automatically via the Alembic migrations when the app starts, but we also ensure
# it's enabled here.
echo "NOTE: pgvector extension will be created automatically by the app's startup Alembic migrations."

# ---------------------------------------------------------
# 5. Configure Secret Manager
# ---------------------------------------------------------
echo "Step 4: Storing secrets in Secret Manager..."

upsert_secret() {
    local secret_name="$1"
    local secret_value="$2"
    if ! gcloud secrets describe "$secret_name" &>/dev/null; then
        gcloud secrets create "$secret_name" --replication-policy="automatic"
    fi
    echo -n "$secret_value" | gcloud secrets versions add "$secret_name" --data-file=- >/dev/null
    echo "Secret '$secret_name' updated with a new version."
}

upsert_secret "MISTRAL_API_KEY" "$MISTRAL_API_KEY"
upsert_secret "POSTGRES_PASSWORD" "$DB_PASSWORD"
upsert_secret "JWT_SECRET" "$JWT_SECRET"

# ---------------------------------------------------------
# 6. Service Account & IAM Permissions
# ---------------------------------------------------------
echo "Step 5: Creating and configuring Service Account..."
if ! gcloud iam service-accounts describe "$SERVICE_ACCOUNT_EMAIL" &>/dev/null; then
    gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
        --description="Service account for Simplon RAG API Cloud Run service" \
        --display-name="simplon-rag-sa"
fi

echo "Binding IAM permissions (least privilege)..."
# 1. Cloud SQL Client permission
gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/cloudsql.client" >/dev/null

# 2. Secret Manager Secret Accessor permission for the specific secrets
for secret in MISTRAL_API_KEY POSTGRES_PASSWORD JWT_SECRET; do
    gcloud secrets add-iam-policy-binding "$secret" \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/secretmanager.secretAccessor" >/dev/null
done

# 3. GCS Object User permission on the bucket (read, write, delete)
gcloud storage buckets add-iam-policy-binding "gs://$BUCKET_NAME" \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.objectUser" >/dev/null

# ---------------------------------------------------------
# 7. Artifact Registry & Docker Image
# ---------------------------------------------------------
echo "Step 6: Preparing Artifact Registry and Docker image..."
if ! gcloud artifacts repositories describe "$REPO_NAME" --location="$REGION" &>/dev/null; then
    gcloud artifacts repositories create "$REPO_NAME" \
        --repository-format=docker \
        --location="$REGION" \
        --description="Docker repository for Simplon RAG sample"
fi

# Configure docker auth
gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet

# Build and Tag Image
IMAGE_TAG="$REGION-docker.pkg.dev/$GCP_PROJECT/$REPO_NAME/$IMAGE_NAME"
GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")

echo "Building production Docker image..."
docker build --target prod -t "$IMAGE_TAG:latest" -t "$IMAGE_TAG:$GIT_SHA" ./api

echo "Pushing images to Artifact Registry..."
docker push "$IMAGE_TAG:latest"
docker push "$IMAGE_TAG:$GIT_SHA"

# ---------------------------------------------------------
# 8. Deploy to Cloud Run
# ---------------------------------------------------------
echo "Step 7: Deploying to Google Cloud Run..."
DB_CONN_STRING="$GCP_PROJECT:$REGION:$DB_INSTANCE_NAME"

gcloud run deploy "$SERVICE_NAME" \
    --image="$IMAGE_TAG:$GIT_SHA" \
    --region="$REGION" \
    --service-account="$SERVICE_ACCOUNT_EMAIL" \
    --add-cloudsql-instances="$DB_CONN_STRING" \
    --update-env-vars="APP_ENV=production,STORAGE_PROVIDER=gcs,RUN_DB_MIGRATIONS=false,GCS_BUCKET_NAME=$BUCKET_NAME,POSTGRES_HOST=/cloudsql/$DB_CONN_STRING,POSTGRES_USER=$DB_USER,POSTGRES_DB=$DB_NAME,MISTRAL_CHAT_MODEL=mistral-large-latest,MISTRAL_EMBED_MODEL=mistral-embed,CORS_ALLOWED_ORIGINS=*" \
    --update-secrets="MISTRAL_API_KEY=MISTRAL_API_KEY:latest,POSTGRES_PASSWORD=POSTGRES_PASSWORD:latest,JWT_SECRET=JWT_SECRET:latest" \
    --allow-unauthenticated \
    --port=8000 \
    --memory=1Gi \
    --cpu=1 \
    --timeout=300 \
    --concurrency=20 \
    --min-instances=1

echo "========================================================="
echo "Deployment successful!"
echo "Cloud Run Service URL: $(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format='value(status.url)')"
echo "========================================================="
