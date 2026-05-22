# Phase 1 — Cloud Run deploy (default compute SA)

Checklist ordonnée. Chaque étape dépend de la précédente.

## Prérequis

```bash
gcloud config set project simplon-rag-sample
gcloud config set run/region europe-west1
```

## 1. Secrets (obligatoire avant IAM)

Vérifier :

```bash
gcloud secrets list --project=simplon-rag-sample
```

Si la liste est vide ou `describe` renvoie `NOT_FOUND`, créer les secrets :

```bash
export POSTGRES_PASSWORD='...'   # mot de passe utilisateur Cloud SQL (rag_user)
export MISTRAL_API_KEY='...'
chmod +x scripts/bootstrap_secrets.sh
./scripts/bootstrap_secrets.sh
```

> Sans secrets, `--set-secrets=...:latest` échoue (IAM ou NOT_FOUND).

## 2. IAM default compute SA

```bash
chmod +x scripts/grant_default_sa_secrets.sh
./scripts/grant_default_sa_secrets.sh
```

Accorde `secretAccessor` sur les 3 secrets + `cloudsql.client`.

## 3. Image

```bash
cd api
docker build --platform linux/amd64 --target prod \
  -t europe-west1-docker.pkg.dev/simplon-rag-sample/simplon-rag-repo/api:latest .
docker push europe-west1-docker.pkg.dev/simplon-rag-sample/simplon-rag-repo/api:latest
```

## 4. Deploy

```bash
gcloud run deploy simplon-rag-api \
  --image=europe-west1-docker.pkg.dev/simplon-rag-sample/simplon-rag-repo/api:latest \
  --region=europe-west1 \
  --platform=managed \
  --allow-unauthenticated \
  --add-cloudsql-instances=simplon-rag-sample:europe-west1:simplon-rag-db-instance \
  --set-env-vars="APP_ENV=production,RUN_DB_MIGRATIONS=false,STORAGE_PROVIDER=gcs,POSTGRES_HOST=/cloudsql/simplon-rag-sample:europe-west1:simplon-rag-db-instance,POSTGRES_USER=rag_user,POSTGRES_DB=rag_db" \
  --set-secrets="POSTGRES_PASSWORD=POSTGRES_PASSWORD:latest,MISTRAL_API_KEY=MISTRAL_API_KEY:latest,JWT_SECRET=JWT_SECRET:latest" \
  --port=8000
```

## 5. Vérification

```bash
chmod +x scripts/verify_cloudrun_api.sh
./scripts/verify_cloudrun_api.sh
```

| Endpoint | Attendu |
|----------|---------|
| `/api/v1/health/live` | 200 |
| `/api/v1/health/ready` | 200 si DB + Mistral OK, sinon 503 |

## Phase 2

`./scripts/setup_gcp_service_accounts.sh` — `cloudrun-runtime` + WIF + retirer droits du default SA.
