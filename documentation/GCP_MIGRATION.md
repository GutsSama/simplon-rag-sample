# Guide de Migration GCP : Cloud Storage, Cloud SQL & Artifact Registry (Mistral AI)

Ce document détaille l'architecture cible simplifiée, les réponses aux questions fondamentales de déploiement et la stratégie de migration de la stack RAG locale vers Google Cloud Platform (GCP) utilisant l'API Mistral AI.

---

## 1. Artifact Registry & Docker (Gestion des Images)

### Fichiers à exclure de l'image Docker (`.dockerignore`)
Pour garantir la sécurité et la légèreté de l'image, les éléments suivants **ne doivent absolument pas** être inclus :
*   **Fichiers de configuration sensibles** : Fichiers `.env` contenant les clés d'API privées (`MISTRAL_API_KEY`, `POSTGRES_PASSWORD`, etc.). Ces variables doivent être injectées au runtime (via Cloud Run / Secret Manager).
*   **Environnements virtuels et dépendances locales** : Dossiers `.venv/` et `node_modules/`.
*   **Caches de développement et de test** : Dossiers `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.coverage`.
*   **Corpus documentaire local** : Le dossier `data/docs/` contenant les documents PDF à ingérer. Le corpus sera stocké de façon centralisée sur **Cloud Storage**.
*   **Base de données locale et historique Git** : Le dossier `.git/` et les bases de données SQLite/PostgreSQL de développement local.

### Tagger les images Docker pour Artifact Registry
Le format d'URL requis par GCP Artifact Registry est :
```
[LOCATION]-docker.pkg.dev/[PROJECT-ID]/[REPOSITORY-NAME]/[IMAGE-NAME]:[TAG]
```

Pour assurer un suivi et un déploiement fluide en production, nous utilisons trois types de tags :
1.  **Tag d'environnement** : `latest` (pour le développement) et `prod` (pour la production stable).
2.  **Tag de version (SemVer)** : `1.0.0` correspondant aux releases Git.
3.  **Tag de commit (SHA)** : `git rev-parse --short HEAD` (ex: `a1b2c3d`) généré automatiquement dans la CI/CD pour assurer une traçabilité parfaite entre l'image déployée et le code source.

#### Commandes de taggage :
```bash
docker tag simplon-rag-api:latest europe-west1-docker.pkg.dev/my-gcp-project/rag-repo/api:latest
docker tag simplon-rag-api:latest europe-west1-docker.pkg.dev/my-gcp-project/rag-repo/api:1.0.0
docker tag simplon-rag-api:latest europe-west1-docker.pkg.dev/my-gcp-project/rag-repo/api:a1b2c3d
```

### Taille de l'image, Démarrage Multi-stage & Impact sur le Cold Start
*   **Vérification de la taille** :
    ```bash
    docker images | grep simplon-rag-api
    # Ou pour obtenir une taille précise en Mo :
    docker image inspect simplon-rag-api --format='{{div .Size 1024 1024}} MB'
    ```
*   **Importance pour le Cold Start (Démarrage à froid)** :
    Dans une architecture serverless comme Cloud Run, les instances de conteneurs démarrent dynamiquement selon le trafic. Lors d'un cold start, GCP doit télécharger l'image depuis l'Artifact Registry puis l'extraire avant de lancer l'application. 
    Pour minimiser la taille de l'image (visant < 200 Mo vs 2 Go), nous utilisons un **build multi-stage** (stage `builder` pour installer les dépendances et compiler les wheels, puis stage final `slim` minimal sans outils de build superflus). Cela réduit drastiquement les temps de latence réseau et d'initialisation, permettant de répondre aux requêtes en moins d'une seconde.

---

## 2. Intégration Cloud Storage & Cloud SQL

### Pourquoi ne pas embarquer le corpus dans l'image Docker ?
1.  **Taille et Performance** : Un corpus de plusieurs dizaines ou centaines de Mo alourdirait inutilement l'image, dégradant les performances du cold start.
2.  **Découplage Code/Données** : L'ajout, la modification ou la suppression d'un document ne doivent pas exiger de re-builder, re-tagger et re-déployer l'intégralité du code de l'application.
3.  **Scalabilité Horizontale** : Plusieurs instances de l'API s'exécutant simultanément doivent accéder à un espace de stockage partagé unique et cohérent (Google Cloud Storage).

### Migration de base de données sans interruption (Zero-Downtime)
Pour modifier ou migrer le schéma de la base de données sur Cloud SQL sans couper le service en production :
*   **Migrations incrémentales avec Alembic** : Génération systématique de scripts de migration versionnés (`alembic upgrade head`) exécutés automatiquement lors de chaque livraison de code.
*   **Pattern Expand & Contract (Élargir & Rétrécir)** :
    *   **Expand** : Ajouter la nouvelle colonne ou table (en acceptant les valeurs nulles). L'ancienne version du code continue de tourner sans erreur.
    *   **Double-Write** : Déployer le nouveau code qui écrit les données à la fois dans l'ancienne et dans la nouvelle colonne, tout en lisant les données de l'ancienne colonne.
    *   **Backfill** : Exécuter un script asynchrone en arrière-plan pour migrer l'historique des anciennes lignes vers le nouveau format.
    *   **Read Switch** : Mettre à jour le code de l'API pour qu'il lise uniquement depuis la nouvelle colonne.
    *   **Contract** : Supprimer définitivement l'ancienne colonne de la base de données via une nouvelle migration Alembic propre.
*   **Indexation Concurrente** : Les index Postgres (notamment sur les embeddings avec `pgvector`) verrouillent les tables en écriture. Pour éviter cela, nous créons les index avec la clause `CONCURRENTLY` dans Alembic (`postgresql_concurrently=True` hors bloc de transaction).
*   **pgvector en Production** : Le script de migration initiale d'Alembic exécute explicitement `CREATE EXTENSION IF NOT EXISTS vector;` avant la création de toute colonne de type `Vector`.

---

## 3. Architecture Production Hardened (Améliorations Industrielles)

### Architecture Simplifiée : 100% API Mistral AI
Pour réduire la RAM requise, le temps de démarrage à froid, et éviter les coûts de GPU GCP, nous passons exclusivement sur l'API Mistral AI :
*   Le code de l'API RAG utilise l'API Mistral AI pour l'inférence LLM (`ChatMistralAI`) et la génération d'embeddings (`MistralAIEmbeddings`).
*   Pour assurer la flexibilité à long terme, ces modèles sont instanciés via des fonctions d'abstraction (`get_llm()` et `get_embeddings()`), ce qui permettra un changement futur de provider sans réécriture majeure de l'application.

### Sécurisation via Google Secret Manager
Pour éviter d'exposer des secrets en clair dans les configurations Cloud Run :
*   Les secrets (`MISTRAL_API_KEY`, `POSTGRES_PASSWORD`, `JWT_SECRET`) sont stockés de manière sécurisée dans **Google Secret Manager**.
*   Ils sont montés sous forme de variables d'environnement directement lors du déploiement de Cloud Run.

### Pooling des Connexions Cloud SQL
L'API FastAPI s'exécutant sur Cloud Run peut rapidement scaler horizontalement.
*   **SQLAlchemy Connection Pool** : Configuration du pool SQLAlchemy dans l'API (`pool_size=5`, `max_overflow=10`, `pool_recycle=1800`) pour limiter et réutiliser les connexions.

### Optimisation des coûts d'Embeddings (SHA-256 Hashing)
*   Lors du chargement d'un document, l'API calcule le hash SHA-256 du contenu du fichier PDF (`file_hash`).
*   Si le hash existe déjà en base de données, l'ingestion de ce fichier est ignorée, évitant ainsi la regénération d'embeddings identiques payants.

### Système de Fichiers Éphémère & Nettoyage
Cloud Run utilise un système de fichiers éphémère limité au dossier `/tmp`.
*   Le processus d'ingestion télécharge temporairement le PDF depuis GCS dans `/tmp/rag_ingest/`.
*   Un bloc Python `finally` garantit la suppression de tous les fichiers locaux temporaires immédiatement après leur traitement.

---

## 4. Pipeline CI/CD Cible

La CI/CD automatisée (GitHub Actions ou Cloud Build) effectuera les étapes suivantes :
1.  **Tests** : Lancement de la suite de tests avec mock des providers.
2.  **Build** : Compilation de l'image Docker avec un build multi-stage optimisé (sans dépendances Ollama).
3.  **Push** : Envoi de l'image vers GCP Artifact Registry avec double marquage (`:latest` et `:[COMMIT_SHA]`).
4.  **Deploy** : Mise à jour du service Cloud Run avec injection des secrets depuis Secret Manager.

---

## 5. Script de Validation de la Migration

Pour valider le bon fonctionnement de la stack migrée de bout en bout, nous disposons d'un script de validation automatique situé dans `scripts/validate_rag.py`.

### Ce que valide le script :
1. **Initialisation et Configuration** : Lecture correcte des nouveaux paramètres Mistral et stockage.
2. **Stockage Hybride** : Téléversement d'un PDF local vers le client de stockage (MinIO local / GCS), suivi de son rapatriement dans `/tmp/rag_ingest/` pour simuler le comportement cloud.
3. **Ingestion & Déduplication** : Ingestion dans la base de données PostgreSQL (pgvector configuré en dimension 1024), avec détection automatique de doublons par hash SHA-256.
4. **Requêtage de l'Agent** : Interrogation de l'agent RAG et réception d'une réponse de l'API Mistral AI.
5. **Évaluation Ragas** : Lancement d'une évaluation Ragas minimale pour s'assurer que les modèles de jugement Mistral AI fonctionnent correctement.

### Lancement de la validation :
```bash
uv run python scripts/validate_rag.py
```
