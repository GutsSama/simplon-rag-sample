# Guide de Migration GCP - Phase 2 : Cloud SQL & Connectivité Locale

Ce document décrit l'implémentation, les commandes exécutées et la configuration pour la mise en place de la base de données **Google Cloud SQL (PostgreSQL)** ainsi que les étapes pour s'y connecter de manière sécurisée depuis un environnement local.

---

## 1. Création de la Base de Données sur GCP

Toutes les ressources de base de données ont été provisionnées dans la région `europe-west1` sous le projet `simplon-rag-sample`.

### Commandes exécutées pour la création :

```bash
# 1. Création de l'instance PostgreSQL (version 15, taille minimale db-f1-micro pour optimiser les coûts)
gcloud sql instances create simplon-rag-db-instance \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=europe-west1 \
    --storage-size=10GB \
    --root-password="rag_root_password_prod" \
    --project=simplon-rag-sample

# 2. Création de la base de données RAG dédiée
gcloud sql databases create rag_db \
    --instance=simplon-rag-db-instance \
    --project=simplon-rag-sample

# 3. Création de l'utilisateur applicatif dédié avec ses identifiants de production
gcloud sql users create rag_user \
    --instance=simplon-rag-db-instance \
    --password="rag_password" \
    --project=simplon-rag-sample
```

---

## 2. Accès Sécurisé via Cloud SQL Auth Proxy

Pour que votre code local (ou votre conteneur local en développement) puisse communiquer avec la base Cloud SQL de production sans exposer cette dernière à l'ensemble d'Internet via des adresses IP publiques autorisées, l'utilisation du **Cloud SQL Auth Proxy** de Google est requise.

### Étape 1 : Téléchargement et installation du proxy (macOS)
```bash
# Télécharger le binaire du proxy pour macOS (architecture Intel/Apple Silicon)
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/v2.11.0/bin/darwin/amd64/cloud-sql-proxy

# Rendre le binaire exécutable
chmod +x cloud-sql-proxy
```

### Étape 2 : Lancement du tunnel sécurisé
Lancez le proxy dans une fenêtre de terminal dédiée. Ce tunnel redirigera le port local `5432` vers votre base Cloud SQL GCP :
```bash
./cloud-sql-proxy simplon-rag-sample:europe-west1:simplon-rag-db-instance --port 5432
```
*Le terminal affichera que le proxy est à l'écoute sur le port `127.0.0.1:5432`.*

---

## 3. Configuration de l'environnement Local (`.env`)

Lorsque le tunnel proxy est actif, configurez votre fichier `.env` à la racine pour cibler le tunnel local :

```ini
# PostgreSQL (Redirection locale via Cloud SQL Auth Proxy)
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DB=rag_db
POSTGRES_USER=rag_user
POSTGRES_PASSWORD=rag_password
POSTGRES_SCHEMA=rag
```

---

## 4. Exécution des Migrations de Base de Données

Une fois le proxy lancé et le fichier `.env` mis à jour, vous devez créer les tables et installer l'extension `pgvector` sur Cloud SQL.

```bash
# Activer l'environnement virtuel local
source .venv/bin/activate

# Lancer les migrations Alembic pour générer le schéma de base de données
uv run alembic upgrade head
```

> [!IMPORTANT]
> Le script de migration initial d'Alembic exécute la directive `CREATE EXTENSION IF NOT EXISTS vector;`. Sur GCP Cloud SQL, cette extension est entièrement supportée et sera automatiquement installée dans la base `rag_db`.
