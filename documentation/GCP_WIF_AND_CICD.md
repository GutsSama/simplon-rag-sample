# Configuration DevOps : Workload Identity Federation (WIF) et CI/CD

Ce guide décrit l'architecture de déploiement sécurisée (CI/CD) sur GCP via GitHub Actions.
Il applique les meilleures pratiques DevOps : **Aucune clé de compte de service (JSON) stockée de manière permanente**, déploiement continu, isolation des privilèges, et prévention des "Cold Starts".

---

## 1. Workload Identity Federation (WIF)

Workload Identity Federation permet aux workflows GitHub Actions de s'authentifier auprès de Google Cloud Platform de façon éphémère et sécurisée en échangeant un token OIDC (OpenID Connect).

### A. Création du Workload Identity Pool et Provider

Ouvrez un Cloud Shell dans votre projet GCP (`$PROJECT_ID`) et exécutez les commandes suivantes :

```bash
PROJECT_ID="simplon-rag-sample" # Remplacez par l'ID réel
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
GITHUB_REPO="votre-organisation/simplon-rag-sample" # ex: Simplon/rag-project

# 1. Créer le Pool d'identités
gcloud iam workload-identity-pools create "github-actions-pool" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --display-name="GitHub Actions Pool"

# 2. Créer le Provider GitHub OIDC au sein du pool
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="github-actions-pool" \
  --display-name="GitHub provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
  --attribute-condition="assertion.repository == '${GITHUB_REPO}'" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

### B. Création et séparation des Service Accounts (SA)

Dans une architecture Zero-Trust, on sépare les privilèges au minimum requis :

1. **`cloudrun-runtime`** : Ce SA est attaché au service Cloud Run *pendant son exécution*. Il n'a aucun droit de déploiement, seulement le droit de lire Secret Manager, Cloud SQL, et Cloud Storage.
2. **`github-deploy`** : Ce SA est utilisé par *GitHub Actions*. Il a le droit de pousser des images sur Artifact Registry, de déployer sur Cloud Run, et d'exécuter l'image temporairement pour les migrations de DB.

```bash
# 1. Création du SA Runtime
gcloud iam service-accounts create cloudrun-runtime \
    --display-name="Cloud Run Runtime SA"

# Autorisations Runtime (Exemples)
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:cloudrun-runtime@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"
# (Répéter pour roles/secretmanager.secretAccessor et roles/storage.objectAdmin)

# 2. Création du SA Deploy
gcloud iam service-accounts create github-deploy \
    --display-name="GitHub Actions Deploy SA"

# Autorisations Deploy
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:github-deploy@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/run.admin"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:github-deploy@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/artifactregistry.writer"
# Autoriser le Deploy SA à "incarner" (ActAs) le Runtime SA lors du déploiement
gcloud iam service-accounts add-iam-policy-binding \
    cloudrun-runtime@${PROJECT_ID}.iam.gserviceaccount.com \
    --member="serviceAccount:github-deploy@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"

# 3. Lier le WIF au SA Deploy (Pour que GitHub puisse emprunter l'identité "github-deploy")
gcloud iam service-accounts add-iam-policy-binding \
  "github-deploy@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-actions-pool/attribute.repository/${GITHUB_REPO}"
```

> [!IMPORTANT]
> Récupérez l'identifiant du Provider WIF généré via :
> `gcloud iam workload-identity-pools providers describe github-provider --workload-identity-pool="github-actions-pool" --location="global" --format="value(name)"`
> Ce chemin servera dans les Variables GitHub (`GCP_WORKLOAD_IDENTITY_PROVIDER`).

---

## 2. Configuration des GitHub Environments et Secrets

Pour éviter les déploiements accidentels et structurer la gestion de production, activez les **GitHub Environments** :

1. Allez dans GitHub > **Settings** > **Environments**.
2. Créez un environnement nommé `production`.
3. Activez **Required reviewers** (Approbation manuelle recommandée).
4. Ajoutez des variables d'environnement (Variables de Dépôt ou d'Environnement) :
   - `GCP_PROJECT_ID` : `simplon-rag-sample`
   - `GCP_REGION` : `europe-west9` (Recommandé pour la France / RGPD et faible latence).
   - `GCP_WORKLOAD_IDENTITY_PROVIDER` : L'identifiant complet du provider WIF (ex: `projects/123456789/locations/global/workloadIdentityPools/github-actions-pool/providers/github-provider`).
   - `GCP_DEPLOY_SERVICE_ACCOUNT` : `github-deploy@...`

---

## 3. Configuration Optimale de Cloud Run pour le RAG

Le déploiement d'une application d'IA (Embeddings / LangChain / VectorDB) requiert une configuration spécifique pour éviter les "Cold Starts" catastrophiques (plusieurs secondes d'attente pour que le conteneur démarre et charge les poids en mémoire).

Lors de votre déploiement ou via `cd.yml`, appliquez :
- **Min Instances (`--min-instances=1`)** : Garantit qu'au moins un conteneur est toujours allumé.
- **CPU Always Allocated (`--no-cpu-throttling`)** : Sans cela, le CPU est bridé à presque 0 entre les requêtes, empêchant toute tâche de fond ou un réveil rapide.

*Rappel concernant le runtime applicatif :*
MISTRAL_API_KEY, DATABASE_URL et autres données sensibles sont récupérés **dynamiquement via Secret Manager** par le conteneur lui-même ou l'intégration Cloud Run (`--update-secrets`), JAMAIS via la CI/CD pour des raisons de sécurité de l'environnement GitHub.

---

## 4. Annuler un Déploiement (Rollback)

Si le Workflow GitHub Actions effectue un déploiement défectueux, Cloud Run permet un retour en arrière (Rollback) immédiat et sans temps d'arrêt.

1. **Lister les révisions existantes :**
   ```bash
   gcloud run revisions list --service=simplon-rag-api --region=europe-west9
   ```

2. **Rediriger 100% du trafic vers la révision saine :**
   ```bash
   gcloud run services update-traffic simplon-rag-api \
       --region=europe-west9 \
       --to-revisions=simplon-rag-api-00001-xyz=100
   ```
