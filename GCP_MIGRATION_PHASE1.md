# Guide de Migration GCP - Phase 1 : Artifact Registry & Docker

Ce document décrit l'implémentation, les commandes exécutées et les réponses détaillées aux questions guidantes de la **Phase 1** du déploiement de l'API RAG Simplon sur Google Cloud Platform (GCP).

---

## 1. Initialisation du Projet GCP & Configuration

Avant de manipuler Docker et Artifact Registry, l'environnement gcloud a été configuré avec le projet GCP cible.

### Commandes de configuration :
```bash
# 1. Authentification au compte GCP
gcloud auth login

# 2. Définir le projet actif
gcloud config set project simplon-rag-sample

# 3. Ajouter le binome / collaborateur au projet GCP (Rôle Owner ou Editor)
gcloud projects add-iam-policy-binding simplon-rag-sample \
    --member="user:collaborateur-binome@gmail.com" \
    --role="roles/owner"

# 4. Activer les API Google Cloud requises (Artifact Registry et Cloud Run)
gcloud services enable artifactregistry.googleapis.com run.googleapis.com
```

---

## 2. Réponses aux Questions Guidantes

### Question A : Quels fichiers NE doivent PAS entrer dans l'image Docker ?
Pour assurer la sécurité, la légèreté et la conformité de l'image de production, les fichiers suivants doivent être explicitement ignorés (via le fichier [api/.dockerignore](file:///Users/amaury/simplon-rag-sample/api/.dockerignore)) :
1. **Secrets et Clés d'API (`.env`, `.env.example`)** : Les jetons secrets (tels que `MISTRAL_API_KEY`, `POSTGRES_PASSWORD`, `JWT_SECRET`) ne doivent **jamais** être écrits en dur dans l'image. Ils seront injectés dynamiquement au runtime de Cloud Run via **Google Secret Manager**.
2. **Environnements Virtuels et Modules (`.venv/`, `node_modules/`)** : Ces dossiers contiennent des dépendances compilées pour l'hôte local (macOS) qui provoqueraient des conflits d'architecture (Linux slim) et alourdiraient l'image de plusieurs centaines de Mo.
3. **Caches de développement (`__pycache__/`, `.pytest_cache/`, `.ruff_cache/`)** : Fichiers temporaires générés lors des tests et des vérifications locales, superflus en production.
4. **Corpus de données documentaire (`data/docs/`, `data/`)** : Le corpus de PDF ne doit pas être figé dans l'image Docker. L'application en production lira directement le corpus depuis un compartiment centralisé **Google Cloud Storage (GCS)**, assurant le découplage total entre le code applicatif et les documents.
5. **Dossier de versioning (`.git/`, `.gitignore`)** : Historique Git inutile pour le fonctionnement de l'application.

---

### Question B : Comment tagger l'image Docker ?
Les images Docker destinées à GCP Artifact Registry doivent respecter le format d'URL standard suivant :
```
[LOCATION]-docker.pkg.dev/[PROJECT-ID]/[REPOSITORY-NAME]/[IMAGE-NAME]:[TAG]
```

Pour notre projet :
- **Location (Région)** : `europe-west1` (Belgique)
- **GCP Project ID** : `simplon-rag-sample`
- **Nom du dépôt** : `simplon-rag-repo`
- **Nom de l'image** : `api`

#### Stratégie de Taggage en Production :
1. **Tag d'environnement (`:latest`, `:prod`)** : Permet le déploiement continu et cible la dernière build stable.
2. **Tag de version (SemVer - ex: `:1.0.0`)** : Marque les versions majeures et mineures correspondant aux releases Git.
3. **Tag de commit (SHA - ex: `:a1b2c3d`)** : Généré automatiquement par la CI/CD (`git rev-parse --short HEAD`). Assure la traçabilité complète entre le code source et le conteneur en production.

---

### Question C : Comment vérifier la taille de l'image et pourquoi est-ce important pour le "Cold Start" ?

#### Commande pour inspecter la taille locale :
```bash
docker image inspect europe-west1-docker.pkg.dev/simplon-rag-sample/simplon-rag-repo/api:latest --format='{{div .Size 1024 1024}} MB'
```

#### Importance pour le Cold Start (Démarrage à froid) :
Dans une architecture serverless telle que Google Cloud Run, les conteneurs sont instanciés à la demande (autoscaling horizontal de `0` à `N` instances). 
- Lorsqu'il n'y a pas de trafic, Cloud Run met à l'échelle le service à 0 pour économiser les coûts.
- Lors de l'arrivée d'une nouvelle requête, si aucune instance n'est active, GCP effectue un **Cold Start** : il télécharge l'image Docker depuis Artifact Registry, l'extrait en mémoire, et lance l'application.
- Si l'image pèse plusieurs Go, le temps de latence réseau et d'extraction peut prendre plus de 30 secondes.
- Grâce au **build multi-stage** configuré dans notre [Dockerfile](file:///Users/amaury/simplon-rag-sample/api/Dockerfile) (extraction des dépendances dans un stage `builder` puis copie sélective uniquement du binaire/virtuallenv final sur une base de runtime `slim`), la taille finale compressée de l'image est réduite à **269 Mo**, limitant la latence de démarrage à **moins d'une seconde**.

---

## 3. Étapes d'Exécution & Commandes Utilisées

Toutes les étapes de la Phase 1 ont été réalisées avec succès :

### Étape 1 : Création du dépôt Docker sur Artifact Registry
Le dépôt docker sécurisé a été initialisé dans la région `europe-west1` :
```bash
gcloud artifacts repositories create simplon-rag-repo \
    --repository-format=docker \
    --location=europe-west1 \
    --description="Docker repository for Simplon RAG sample"
```

### Étape 2 : Configuration de l'authentification Docker
Liaison sécurisée entre Docker local et les serveurs d'Artifact Registry GCP :
```bash
gcloud auth configure-docker europe-west1-docker.pkg.dev --quiet
```

### Étape 3 : Build de l'image Docker avec la cible de production
Construction optimisée en ciblant uniquement le stage `prod` du Dockerfile (dépendances Ollama exclues) :
```bash
docker build --target prod -t europe-west1-docker.pkg.dev/simplon-rag-sample/simplon-rag-repo/api:latest ./api
```
*Taille de l'image finale générée : **269 Mo** (taille compressée).*

### Étape 4 : Push de l'image vers GCP
Envoi de l'image compilée sur le cloud de Artifact Registry :
```bash
docker push europe-west1-docker.pkg.dev/simplon-rag-sample/simplon-rag-repo/api:latest
```

### Étape 5 : Vérification de la présence de l'image sur GCP
```bash
gcloud artifacts docker images list europe-west1-docker.pkg.dev/simplon-rag-sample/simplon-rag-repo/api
```
*L'image a été correctement stockée sous le digest `sha256:98e2a7354224ec27a383120b16d3d72ce4f63f41b413db49e731f697d41c76b1`.*
