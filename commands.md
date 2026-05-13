# Guide des Commandes CLI

Ce fichier répertorie toutes les commandes nécessaires pour piloter le projet Simplon RAG.

## 🚀 Lancement du Projet

### 1. Démarrer toute la stack (Docker)
```bash
docker compose up -d
```

### 2. Vérifier l'état des containers
```bash
docker compose ps
```

### 3. Redémarrer l'API (après une modif de code)
```bash
docker compose restart api
```

---

## 🏗️ Ingestion des Données
Pour peupler la base de données avec les documents PDF/Markdown :
```bash
docker exec -it simplon_rag_api python -m rag.ingest
```

---

## 📈 Tests & Observabilité

### 1. Générer du trafic simulé (Metrics/Logs)
Cette commande lance une série de questions-réponses pour remplir les dashboards Grafana et Langfuse :
```bash
docker exec -it simplon_rag_api python -m rag.populate_metrics
```

### 2. Tester la connectivité Ollama depuis le container
```bash
docker exec -it simplon_rag_api curl http://host.docker.internal:11434/api/tags
```

### 3. Consulter les logs en temps réel
```bash
docker compose logs -f api
```

---

## 🧪 Tests de Qualité
Pour lancer la suite de tests automatisés validant la pertinence des réponses :
```bash
docker exec -it simplon_rag_api pytest src/tests/test_rag_quality.py
```

---

## 🧹 Nettoyage
### Arrêter les services
```bash
docker compose down
```

### Tout supprimer (volumes inclus - ATTENTION perte de données)
```bash
docker compose down -v
```
