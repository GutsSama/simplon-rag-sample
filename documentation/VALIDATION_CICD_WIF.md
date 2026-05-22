# Validation de l'architecture CI/CD avec Workload Identity Federation (WIF)

Le chantier d'automatisation des déploiements (DevOps) sur GitHub Actions a été implémenté avec succès, répondant aux exigences modernes de sécurité cloud-native sur GCP.

## Synthèse des Réalisations

1. **Sécurité Zero-Trust (Workload Identity Federation)**
   - Abandon total des clés JSON persistantes pour l'authentification GitHub -> GCP.
   - Création d'un pool d'identité OIDC permettant l'échange de jetons temporaires.
   - Séparation stricte des privilèges IAM via deux Service Accounts (`cloudrun-runtime` pour l'exécution, `github-deploy` pour le déploiement CI/CD).

2. **Intégration Continue (CI)**
   - Workflow `.github/workflows/ci.yml` configuré pour valider la qualité du code à chaque Pull Request.
   - Exécution du linter (`ruff`) et des tests unitaires (`pytest`).
   - Build Docker (dry-run) avec scan de sécurité de l'image via **Trivy** pour bloquer tout déploiement en cas de vulnérabilité OS ou dépendance critique (CVE).
   - Ce pipeline s'exécute sans aucun droit d'accès GCP.

3. **Déploiement Continu (CD)**
   - Workflow `.github/workflows/cd.yml` déclenché uniquement sur `main`.
   - Utilisation du *cache Docker Buildx* distant pour accélérer les itérations de build.
   - Multi-tagging sur Artifact Registry (`europe-west9` recommandé) avec le SHA du commit et `:latest`.
   - **Migration asynchrone de la base de données** : Le CD instancie le proxy d'authentification Cloud SQL dans le runner (action `cloud-sql-proxy-action`), récupère le mot de passe via Secret Manager et applique `alembic upgrade head` avant d'initier le déploiement des conteneurs.
   - **Optimisation Cloud Run (RAG)** : Activation de `--min-instances=1` et `--no-cpu-throttling` (CPU Always Allocated) pour supprimer les "Cold Starts" particulièrement néfastes sur les flux d'IA/embeddings.
   - **Healthcheck post-déploiement** intégré pour s'assurer que le point d'entrée HTTP répond (`/api/v1/health`).

## Prérequis de Production

Pour valider l'exécution en conditions réelles, le dépôt GitHub doit contenir les variables d'environnement suivantes dans **Settings > Environments > production** :
- `GCP_PROJECT_ID`
- `GCP_REGION` (ex: `europe-west9`)
- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_DEPLOY_SERVICE_ACCOUNT`

Ces avancées garantissent une mise en production professionnelle, sécurisée et reproductible, apte à supporter des itérations rapides.
