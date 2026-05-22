# Démo CI/CD + WIF — 10 minutes

**Projet :** `simplon-rag-sample`  
**Région :** `europe-west1`  
**Repo GitHub :** https://github.com/GutsSama/simplon-rag-sample  

Guide opérationnel : storytelling, navigation UI, commandes de secours et fallbacks anti-risque live.

---

## Avant la démo (J-1 ou H-1)

### Onglets à ouvrir

| Onglet | URL / cible |
|--------|-------------|
| CI vert | GitHub → Actions → **CI Pipeline** → dernier run ✅ |
| CD vert | GitHub → Actions → **CD Pipeline (Deploy to GCP)** → dernier run sur `main` ✅ |
| Console GCP | https://console.cloud.google.com/?project=simplon-rag-sample |
| Fallback live | Capture d’écran `/docs` + `/health/ready` (ou terminal avec `curl` prêt) |

### Préparer le terminal (fallback réseau)

```bash
# Contexte GCP
export PROJECT_ID="simplon-rag-sample"
export REGION="europe-west1"

gcloud config set project "${PROJECT_ID}"
gcloud config set run/region "${REGION}"

# URLs Cloud Run (récupération dynamique — préférable au hardcode)
export API_URL="$(gcloud run services describe simplon-rag-api \
  --region="${REGION}" --format='value(status.url)')"
export FRONTEND_URL="$(gcloud run services describe simplon-rag-frontend \
  --region="${REGION}" --format='value(status.url)')"

echo "API:       ${API_URL}"
echo "Frontend:  ${FRONTEND_URL}"
```

### Healthcheck prêt (copier-coller si le navigateur lag)

```bash
# Live (utilisé par le CD)
curl -fsS "${API_URL}/api/v1/health" && echo " OK health"

# Ready (DB + dépendances — plus parlant en démo)
curl -fsS "${API_URL}/api/v1/health/live" && echo " OK live"
curl -fsS "${API_URL}/api/v1/health/ready" && echo " OK ready"

# Docs (JSON OpenAPI — rapide, pas de rendu HTML)
curl -fsS -o /dev/null -w "HTTP %{http_code}\n" "${API_URL}/openapi.json"
```

### URLs de secours (si `gcloud` indisponible)

| Ressource | URL |
|-----------|-----|
| API docs (navigateur) | https://simplon-rag-api-hohepdhnvq-ew.a.run.app/docs |
| Health live | https://simplon-rag-api-hohepdhnvq-ew.a.run.app/api/v1/health/live |
| Health ready | https://simplon-rag-api-hohepdhnvq-ew.a.run.app/api/v1/health/ready |
| Frontend | https://simplon-rag-frontend-hohepdhnvq-ew.a.run.app |

> **Règle live :** navigateur en priorité ; si latence / cold start → `curl` ou capture d’écran.

---

## Script oral + timing (10 min)

### 0:00–0:30 — Hook

**À dire :**

> « GitHub → GCP **sans clé JSON**. Auth éphémère via **Workload Identity Federation**. **CI sans cloud**. **CD automatique** sur `main`. »

---

### 0:30–3:30 — CI (3 min) — GitHub Actions

**Navigation :** Actions → **CI Pipeline** → run récent (PR ou push hors `main`).

| Bloc UI | À montrer | Phrase |
|---------|-----------|--------|
| **Lint & Test** | `ruff` + `pytest` | « Validation locale, **aucun accès GCP**. » |
| **Docker Build & Security Scan** | build + **Trivy** | « **Fail fast** avant la prod — CVE CRITICAL/HIGH bloquent. » |

**Message clé :** « CI = qualité + sécurité, **zéro dépendance GCP**. »

**Commandes équivalentes (si on vous demande “comment c’est fait localement”) :**

```bash
cd api
uv sync --frozen --all-extras
uv run ruff check .
uv run ruff format --check .
POSTGRES_PASSWORD="dummy_password" uv run pytest tests/ -v

# Build dry-run (comme la CI)
docker build -t simplon-rag/api:test ./api
docker build -t simplon-rag/frontend:test ./frontend

# Scan Trivy (comme la CI — nécessite Trivy installé)
trivy image --severity CRITICAL,HIGH --exit-code 1 simplon-rag/api:test
```

---

### 3:30–7:30 — CD (4 min) — GitHub Actions

**Navigation :** Actions → **CD Pipeline (Deploy to GCP)** → run `main` ✅.

Regrouper mentalement en **3 blocs** (pas 8 étapes une par une) :

#### Bloc 1 — Auth GCP (WIF) ~1 min

**Étapes UI :** `Authenticate to Google Cloud` → `Setup Google Cloud SDK`

**À dire :**

> « GitHub émet un jeton **OIDC** → GCP via le **Workload Identity Pool** → impersonation du SA **`github-deploy`**. Auth **temporaire, scoped, jetable** — pas de JSON dans les secrets. »

**Vérification console (optionnel, hors timing) :**

```bash
# Provider WIF (identifiant pour GitHub var GCP_WORKLOAD_IDENTITY_PROVIDER)
gcloud iam workload-identity-pools providers describe github-provider \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="github-actions-pool" \
  --format="value(name)"

# Lister le pool
gcloud iam workload-identity-pools describe github-actions-pool \
  --project="${PROJECT_ID}" \
  --location="global"
```

#### Bloc 2 — Build + Push + Migration ~1 min 30

**Étapes UI :** `Build and Push API/Frontend` → `Setup Cloud SQL Proxy` → `Run DB Migration (Alembic)`

**À dire :**

> « Images **versionnées** (SHA + `latest`) dans **Artifact Registry**. La base est **toujours alignée avant le déploiement** : proxy Cloud SQL + `alembic upgrade head`, mot de passe lu depuis **Secret Manager**. »

**Commandes de vérification post-CD :**

```bash
# Dernier SHA déployé (depuis GitHub ou local)
SHA_SHORT="$(git rev-parse --short HEAD)"   # ou le SHA affiché dans le run CD

# Images dans Artifact Registry (chemin du workflow cd.yml)
gcloud artifacts docker images list \
  "europe-west1-docker.pkg.dev/${PROJECT_ID}/rag/api" --include-tags --limit=5

gcloud artifacts docker images list \
  "europe-west1-docker.pkg.dev/${PROJECT_ID}/rag/frontend" --include-tags --limit=5

# Instance Cloud SQL
gcloud sql instances describe simplon-rag-db-instance --format="yaml(name,state,region)"
```

#### Bloc 3 — Deploy + Healthcheck ~1 min 30

**Étapes UI :** `Deploy API to Cloud Run` → `Deploy Frontend` → `Post-Deploy Healthcheck`

**À dire :**

> « Nouvelle **révision** Cloud Run, secrets via **Secret Manager**, `min-instances=1` pour le RAG. Le pipeline **valide automatiquement** avec `/api/v1/health`. »

**Live — priorité curl (plus fiable qu’un navigateur en 10 min) :**

```bash
curl -fsS "${API_URL}/api/v1/health"
curl -fsS "${API_URL}/api/v1/health/ready"
```

**Live navigateur (fallback = capture ou curl ci-dessus) :**

- `${API_URL}/docs`
- `${API_URL}/api/v1/health/ready`

**Commandes équivalentes au deploy CD :**

```bash
SHA_SHORT="$(git rev-parse --short HEAD)"
REGISTRY="europe-west1-docker.pkg.dev/${PROJECT_ID}"
DB_INSTANCE="${PROJECT_ID}:${REGION}:simplon-rag-db-instance"

# Décrire le service (révision active, image, SA)
gcloud run services describe simplon-rag-api \
  --region="${REGION}" \
  --format="yaml(status.url,status.latestReadyRevisionName,spec.template.spec.serviceAccountName)"

gcloud run revisions list --service=simplon-rag-api --region="${REGION}" --limit=3

# Frontend + URL API injectée
gcloud run services describe simplon-rag-frontend \
  --region="${REGION}" \
  --format="yaml(status.url,spec.template.spec.containers[0].env)"
```

---

### 7:30–9:30 — Console GCP (2 min) — 3 écrans MAX

#### Écran 1 — IAM / WIF (~40 s)

**Navigation :** IAM & Admin → **Workload Identity Federation** → `github-actions-pool` → provider `github-provider`

**Puis :** IAM → **Comptes de service** → comparer :

| SA | Rôle en démo |
|----|----------------|
| `github-deploy@...` | CI/CD — deploy, push images |
| `cloudrun-runtime@...` | Runtime Cloud Run — secrets, SQL, GCS |

```bash
gcloud iam service-accounts list --filter="email~simplon-rag OR email~github-deploy OR email~cloudrun-runtime"

gcloud iam service-accounts get-iam-policy \
  "github-deploy@${PROJECT_ID}.iam.gserviceaccount.com"
```

#### Écran 2 — Artifact Registry (~40 s)

**Navigation :** Artifact Registry → repo **`rag`** → images `api` / `frontend`

**Montrer :** tags **`latest`** + **SHA commit**

```bash
gcloud artifacts repositories list --location="${REGION}"
gcloud artifacts docker tags list \
  "europe-west1-docker.pkg.dev/${PROJECT_ID}/rag/api" --limit=10
```

#### Écran 3 — Cloud Run (~40 s)

**Navigation :** Cloud Run → **`simplon-rag-api`** → onglet **Révisions**

**Montrer :** révision active, **min instances = 1**, connexion **Cloud SQL**, variables/secrets

```bash
gcloud run services describe simplon-rag-api --region="${REGION}" \
  --format="table(status.url,status.latestReadyRevisionName)"

# Détail scaling RAG
gcloud run services describe simplon-rag-api --region="${REGION}" \
  --format="yaml(spec.template.metadata.annotations,spec.template.spec.containers[0].resources)"
```

---

### 9:30–10:00 — Conclusion

**À dire :**

> « La **CI** garantit qualité et sécurité sans cloud. Le **CD** utilise **WIF** pour une auth éphémère. Chaque commit sur **`main`** produit une image **versionnée**, une base **migrée**, un déploiement **Cloud Run** et une **vérification automatique**. »

---

## Commandes utiles (hors démo — questions jury)

### Secrets (sans afficher les valeurs)

```bash
gcloud secrets list --project="${PROJECT_ID}"
gcloud secrets versions list POSTGRES_PASSWORD --project="${PROJECT_ID}" --limit=3
```

### Rollback Cloud Run (30 s si question incident)

```bash
# Lister les révisions
gcloud run revisions list --service=simplon-rag-api --region="${REGION}"

# Router 100% du trafic vers une révision précédente (remplacer REVISION_NAME)
gcloud run services update-traffic simplon-rag-api \
  --region="${REGION}" \
  --to-revisions=REVISION_NAME=100
```

### Variables GitHub requises (environnement `production`)

| Variable | Exemple |
|----------|---------|
| `GCP_PROJECT_ID` | `simplon-rag-sample` |
| `GCP_REGION` | `europe-west1` |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | `projects/…/locations/global/workloadIdentityPools/github-actions-pool/providers/github-provider` |
| `GCP_DEPLOY_SERVICE_ACCOUNT` | `github-deploy@simplon-rag-sample.iam.gserviceaccount.com` |

---

## Anti-risques live (checklist rapide)

| Risque | Mitigation |
|--------|------------|
| `/docs` ou health lents | `curl` préparé + capture d’écran |
| CD qui tourne pendant la démo | Utiliser un **run enregistré**, pas de push sur `main` |
| Trivy / CI rouge | Avoir un **run CI vert** en backup |
| Confusion région | Toujours dire **`europe-west1`** (aligné prod) |
| Secrets exposés | Ne jamais `gcloud secrets versions access` à l’écran |

---

## Références repo

| Fichier | Contenu |
|---------|---------|
| [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) | Lint, tests, Docker dry-run, Trivy |
| [`.github/workflows/cd.yml`](../.github/workflows/cd.yml) | WIF, AR, migration, deploy, health |
| [`GCP_WIF_AND_CICD.md`](GCP_WIF_AND_CICD.md) | Setup WIF + IAM |
| [`VALIDATION_CICD_WIF.md`](VALIDATION_CICD_WIF.md) | Synthèse architecture |
| [`GCP_DEPLOYMENT.md`](GCP_DEPLOYMENT.md) | Rapport déploiement + URLs |

---

## Schéma (slide ou tableau blanc — 15 s)

```text
PR / branche ──► CI (ruff, pytest, Trivy)     [sans GCP]
main         ──► CD (WIF → build → migrate → deploy → health)
                      │
                      ▼
              Artifact Registry + Cloud SQL + Cloud Run
```
