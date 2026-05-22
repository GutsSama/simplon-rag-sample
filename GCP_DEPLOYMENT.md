# Déploiement GCP — Rapport final (Simplon RAG Sample)

**Projet GCP :** `simplon-rag-sample`  
**Région :** `europe-west1`  
**Date de validation :** 22 mai 2026  

---

## URLs de production (à transmettre)

| Service | URL |
|---------|-----|
| **Backend (API FastAPI)** | https://simplon-rag-api-hohepdhnvq-ew.a.run.app |
| **Frontend (Streamlit)** | https://simplon-rag-frontend-hohepdhnvq-ew.a.run.app |

**Endpoints utiles :**

- API docs : https://simplon-rag-api-hohepdhnvq-ew.a.run.app/docs
- Health live : https://simplon-rag-api-hohepdhnvq-ew.a.run.app/api/v1/health/live
- Health ready : https://simplon-rag-api-hohepdhnvq-ew.a.run.app/api/v1/health/ready

**Revisions validées :**

- API : `simplon-rag-api-00011-vd2` (ready : DB + Mistral OK)
- Frontend : `simplon-rag-frontend-00001-wdp`

---

## Synthèse

Le déploiement cloud-native sur GCP est **opérationnel** :

- Images Docker multi-stage (API + frontend) dans Artifact Registry
- Cloud Run managé avec Cloud SQL (PostgreSQL + pgvector)
- Secrets via Secret Manager (`MISTRAL_API_KEY`, `POSTGRES_PASSWORD`, `JWT_SECRET`)
- Health checks live/ready conformes aux bonnes pratiques Cloud Run
- Migrations Alembic exécutées hors conteneur (CI / script local)

Les blocages rencontrés étaient liés à l’**ordre de démarrage applicatif**, à l’**IAM**, et à la **configuration** (nom de base, secrets), pas à Docker ou Cloud Run en tant que tels.

---

## Architecture déployée

```text
Utilisateur
    → Cloud Run (simplon-rag-frontend, Streamlit :8501)
        → Cloud Run (simplon-rag-api, FastAPI :8000)
            → Cloud SQL (socket Unix /cloudsql/...)
            → Secret Manager (env injectées)
            → Mistral AI API (HTTPS)
            → GCS (corpus, si STORAGE_PROVIDER=gcs)
```

---

## Étapes d’implémentation

### Phase 0 — Prérequis

```bash
gcloud auth login
gcloud config set project simplon-rag-sample
gcloud config set run/region europe-west1
gcloud auth configure-docker europe-west1-docker.pkg.dev
```

### Phase 1 — Build et push de l’image API (linux/amd64)

```bash
cd api
docker build --platform linux/amd64 --target prod \
  -t europe-west1-docker.pkg.dev/simplon-rag-sample/simplon-rag-repo/api:latest .
docker push europe-west1-docker.pkg.dev/simplon-rag-sample/simplon-rag-repo/api:latest
```

### Phase 2 — Secrets Secret Manager

```bash
cd ..   # racine du repo
chmod +x scripts/bootstrap_secrets.sh
export POSTGRES_PASSWORD='...'   # mot de passe utilisateur Cloud SQL rag_user
export MISTRAL_API_KEY='...'
./scripts/bootstrap_secrets.sh
```

Vérification :

```bash
gcloud secrets list --project=simplon-rag-sample
gcloud secrets versions list POSTGRES_PASSWORD --project=simplon-rag-sample
```

### Phase 3 — IAM (service account Compute par défaut, phase rapide)

```bash
chmod +x scripts/grant_default_sa_secrets.sh
./scripts/grant_default_sa_secrets.sh
```

Accorde `roles/secretmanager.secretAccessor` sur chaque secret et `roles/cloudsql.client` au SA  
`841424350137-compute@developer.gserviceaccount.com`.

### Phase 4 — Base de données

**Important :** la base Cloud SQL s’appelle `rag_db`, pas `rag`.

```bash
chmod +x scripts/sync_cloudsql_password.sh scripts/migrate_cloudsql.sh
./scripts/sync_cloudsql_password.sh
./scripts/migrate_cloudsql.sh   # nécessite cloud-sql-proxy installé
```

### Phase 5 — Déploiement API Cloud Run

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

### Phase 6 — Synchroniser la clé Mistral (si mise à jour dans `.env` local)

Le fichier `.env` local **ne met pas à jour** Cloud Run. Utiliser :

```bash
chmod +x scripts/sync_mistral_secret_from_env.sh
./scripts/sync_mistral_secret_from_env.sh
gcloud run deploy simplon-rag-api ...   # même commande qu’en phase 5
```

### Phase 7 — Vérification API

```bash
chmod +x scripts/verify_cloudrun_api.sh
./scripts/verify_cloudrun_api.sh
```

Attendu : `/health/live` → 200, `/health/ready` → 200.

### Phase 8 — Déploiement frontend Streamlit

```bash
cd frontend
docker build --platform linux/amd64 --target prod \
  -t europe-west1-docker.pkg.dev/simplon-rag-sample/simplon-rag-repo/frontend:latest .
docker push europe-west1-docker.pkg.dev/simplon-rag-sample/simplon-rag-repo/frontend:latest

API_URL=$(gcloud run services describe simplon-rag-api --region=europe-west1 --format='value(status.url)')

gcloud run deploy simplon-rag-frontend \
  --image=europe-west1-docker.pkg.dev/simplon-rag-sample/simplon-rag-repo/frontend:latest \
  --region=europe-west1 \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars="API_BASE_URL=${API_URL}/api/v1" \
  --port=8501
```

---

## Problèmes rencontrés et corrections

| # | Symptôme | Cause | Solution |
|---|----------|-------|----------|
| 1 | Cloud Run : container failed to listen on PORT | `alembic upgrade head` dans l’entrypoint + `POSTGRES_PASSWORD` requis avant uvicorn | `RUN_DB_MIGRATIONS=false` (défaut prod), migrations via CI/script ; `postgres_password` optionnel au boot |
| 2 | `PERMISSION_DENIED` actAs sur `cloudrun-runtime` | SA custom non créé / pas de binding pour le compte utilisateur | Phase 1 : deploy sans `--service-account` (default compute) ; Phase 2 : `scripts/setup_gcp_service_accounts.sh` |
| 3 | Permission denied on secret (deploy) | Default compute SA sans `secretAccessor` | `scripts/grant_default_sa_secrets.sh` |
| 4 | Secrets introuvables au bootstrap IAM | Secrets pas encore créés dans GCP | `scripts/bootstrap_secrets.sh` avant IAM |
| 5 | `/health/ready` → database unreachable | `POSTGRES_DB=rag` alors que Cloud SQL a `rag_db` | `POSTGRES_DB=rag_db` + `migrate_cloudsql.sh` |
| 6 | `/health/ready` → Mistral 401 | Valeur invalide dans Secret Manager (pas le `.env` local) | `sync_mistral_secret_from_env.sh` + **redéployer** la revision API |
| 7 | Modifier `.env` sans effet sur prod | Cloud Run lit Secret Manager, pas le `.env` du Mac | Toujours : nouvelle version secret + redeploy |

---

## Modifications code / infra (repo)

| Fichier | Changement |
|---------|------------|
| `api/docker-entrypoint.sh` | Migrations conditionnelles (`RUN_DB_MIGRATIONS`, défaut `false`) |
| `api/Dockerfile` (prod) | `ENV APP_ENV=production`, `RUN_DB_MIGRATIONS=false`, `WEB_CONCURRENCY=1` |
| `api/src/rag/config/settings.py` | `postgres_password` optionnel au boot |
| `api/src/rag/api/app.py` | Dispose engine DB seulement si initialisé |
| `docker-compose.yml` | `RUN_DB_MIGRATIONS=true` pour le dev local |
| `.github/workflows/cd.yml` | `POSTGRES_DB=rag_db`, `RUN_DB_MIGRATIONS=false` |
| `scripts/deploy_gcp.sh` | SA `cloudrun-runtime`, `DB_NAME=rag_db` |
| `scripts/*.sh` | Bootstrap secrets, IAM, migrations, vérification, sync Mistral |

---

## Chargement de `MISTRAL_API_KEY` (audit)

1. Cloud Run injecte la variable d’environnement `MISTRAL_API_KEY` depuis Secret Manager (`:latest`).
2. `pydantic-settings` mappe vers `Settings.mistral_api_key` (`api/src/rag/config/settings.py`).
3. `get_settings()` (cache LRU) alimente health, `ChatMistralAI`, `MistralAIEmbeddings`.
4. Pas de clé hardcodée ; `.env` exclu de l’image Docker (`api/.dockerignore`).

Le `.env` local sert uniquement au développement et à `scripts/sync_mistral_secret_from_env.sh`.

---

## Scripts utilitaires (`scripts/`)

| Script | Rôle |
|--------|------|
| `bootstrap_secrets.sh` | Créer secrets + version 1 |
| `grant_default_sa_secrets.sh` | IAM default compute (phase 1) |
| `sync_cloudsql_password.sh` | Aligner mot de passe SQL ↔ secret |
| `migrate_cloudsql.sh` | Alembic via Cloud SQL Proxy |
| `sync_mistral_secret_from_env.sh` | Pousser `.env` → Secret Manager |
| `verify_cloudrun_api.sh` | Health live + ready + logs |
| `setup_gcp_service_accounts.sh` | `cloudrun-runtime` + `github-deploy` (phase 2 WIF) |
| `DEPLOY_PHASE1.md` | Checklist courte phase 1 |

---

## Phase 2 recommandée (après rendu)

- Créer `cloudrun-runtime` et `github-deploy` : `./scripts/setup_gcp_service_accounts.sh all`
- Activer Workload Identity Federation : voir [`GCP_WIF_AND_CICD.md`](GCP_WIF_AND_CICD.md)
- CD GitHub sur `main` : [`.github/workflows/cd.yml`](.github/workflows/cd.yml)
- Retirer les droits secrets du default compute SA

---

## Critères jury / validation

| Critère | Statut |
|---------|--------|
| Docker multi-stage + Artifact Registry | OK |
| Cloud Run API + Frontend | OK |
| Secret Manager | OK |
| Cloud SQL + socket Unix | OK |
| Health live / ready | OK |
| Migrations Alembic externalisées | OK |
| WIF / SA dédiés | Documenté, phase 2 |

---

## Références

- [GCP_WIF_AND_CICD.md](GCP_WIF_AND_CICD.md) — WIF, IAM, CD
- [GCP_MIGRATION_FINAL.md](GCP_MIGRATION_FINAL.md) — migration initiale
- [scripts/DEPLOY_PHASE1.md](scripts/DEPLOY_PHASE1.md) — checklist rapide
- [Cloud Run troubleshooting](https://cloud.google.com/run/docs/troubleshooting)
