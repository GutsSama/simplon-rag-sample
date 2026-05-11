# Plan d'Implémentation et Récapitulatif - MailGuard Observability

Ce document récapitule les étapes d'implémentation réalisées pour répondre au brief **MailGuard Observability**, ainsi que les commandes utiles pour la gestion du projet.

## 🚀 Étapes d'Implémentation (Brief)

### Phase 1 : Logs structurés et Métriques de base

- [x] **Logging JSON structuré** : Implémenté via `python-json-logger`.
- [x] **Middleware Request ID** : Création d'un `request_id` unique par requête, propagé dans les logs et le tracing.
- [x] **Métriques Prometheus (RED)** : Compteurs et histogrammes pour les requêtes HTTP sur `/predict` et `/explain`.
- [x] **Endpoint `/metrics`** : Exposé pour le scraping par Prometheus.

### Phase 2 : Métriques Métier et Dashboard

- [x] **Métriques /predict** : Distribution des prédictions et scores de confiance.
- [x] **Détection de Drift** : Algorithme de calcul de dérive (KS/PSI) intégré.
- [x] **Docker Compose** : Orchestration de l'API, Prometheus, Grafana, Langfuse et Postgres.
- [x] **Dashboard Grafana** : (En cours) Provisioning automatique du dashboard "MailGuard Overview".

### Phase 3 : Observabilité LLM (Langfuse)

- [x] **Instrumentation `/explain`** : Ajout de spans (retrieval, prompt_build, llm_call) via le wrapper `LangfuseTracing`.
- [x] **Détails des Traces** : Inclusion du `user_id_hash`, `model` et `request_id`.
- [x] **Correction Critique** : Suppression des imports obsolètes de `langfuse.model` qui empêchaient le démarrage.
- [x] **Suivi des Coûts** : (Prévu) Job d'export des coûts Langfuse vers Prometheus.

### Phase 4 : Alerting et Runbooks

- [x] **Règles d'Alerte** : Définition des seuils de latence, taux d'erreur et budget LLM dans `prometheus/rules.yml`.
- [x] **Alertmanager** : Configuration du routage des alertes.

---

## 🛠️ Commandes Utiles

### Python & FastAPI (via `uv`)

- **Lancer l'API en local** :
  ```bash
  cd api
  uv run python main.py
  ```

- **Installer les dépendances** :
  ```bash
  uv sync --extra dev
  ```

- **Lancer les tests** :
  ```bash
  cd api
  uv run pytest
  ```

### Docker

- **Lancer toute la stack** :
  ```bash
  docker compose up -d
  ```

- **Reconstruire l'image API après modification** :
  ```bash
  docker compose build api
  ```

- **Voir les logs de l'API** :
  ```bash
  docker logs -f mailguard-api
  ```

- **Arrêter les services** :
  ```bash
  docker compose down
  ```

### PostgreSQL

- **Accéder à la DB via Docker** :
  ```bash
  docker exec -it mailguard-db psql -U rag_user -d rag_db
  ```

- **Appliquer les migrations Alembic** :
  ```bash
  cd api
  uv run alembic upgrade head
  ```

---

## 📂 Fichiers Créés / Modifiés

| Fichier | Statut | Description |
| :--- | :--- | :--- |
| `.env` | **Nouveau** | Configuration des clés API (Mistral) et accès DB (Ignoré par Git). |
| `api/Dockerfile` | **Nouveau** | Image Docker optimisée (multi-stage) pour l'API. |
| `api/.dockerignore` | **Nouveau** | Optimisation du contexte de build Docker. |
| `api/src/rag/api/llm_observability.py` | **Modifié** | Correction des imports Langfuse et ajout du tracing. |
| `api/tests/integration/test_postgresql.py` | **Nouveau** | Test d'intégration pour vérifier la connexion réelle à Postgres. |
| `RECAP_IMPLEMENTATION.md` | **Nouveau** | Ce document de suivi. |

---

## ✅ Validation de la Base de Données

Les tables ont été créées avec succès via les migrations Alembic :

- `documents` et `document_chunks` (pour le RAG)
- `conversations` et `messages` (pour l'historique du chat)
- `alembic_version` (suivi des migrations)

Un test d'intégration dédié a été ajouté pour valider la connexion à PostgreSQL et la présence de l'extension `pgvector`.

---

## 🐳 Optimisation de l'Image Docker

L'image Docker créée est **optimisée et allégée** pour plusieurs raisons :

1. **Base "Slim"** : Utilisation de `python:3.14-slim-bookworm`, qui pèse environ 100MB contre ~900MB pour l'image standard.
2. **Multi-stage Build** :
   - L'étape `builder` installe les outils de compilation (`build-essential`) nécessaires pour certaines libs ML.
   - L'étape `final` ne contient que l'environnement virtuel et le code source, éliminant les outils de build lourds et inutiles en production.
3. **Utilisation de `uv`** : Installation extrêmement rapide et gestion propre des dépendances via un environnement virtuel isolé.
4. **.dockerignore** : Empêche l'inclusion de fichiers inutiles (logs, .venv local, cache), réduisant la taille du contexte envoyé au démon Docker.
