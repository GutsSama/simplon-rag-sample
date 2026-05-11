# Aide-mémoire : Commandes Utiles pour l'Observabilité

Ce document regroupe les commandes essentielles pour manipuler, tester et vérifier la stack d'observabilité de MailGuard.

## 🚀 Gestion de la Stack Infrastructure

### Démarrer toute la stack (API + Infra)
```bash
docker-compose up -d
```

### Arrêter la stack et supprimer les volumes (nettoyage complet)
```bash
docker-compose down -v
```

### Voir les logs de l'API en temps réel (format JSON)
```bash
docker-compose logs -f api
```

## 🧪 Tests des Endpoints

### Tester le classifieur de Spam (/predict)
```bash
curl -X POST http://localhost:8000/api/v1/predict \
     -H "Content-Type: application/json" \
     -d '{"email_content": "Gagnez 1000 euros maintenant !", "user_id": "user123"}'
```

### Tester l'explication RAG (/explain)
```bash
curl -X POST http://localhost:8000/api/v1/explain \
     -H "Content-Type: application/json" \
     -d '{"email_content": "Cher client, votre facture est disponible.", "user_id": "user456"}'
```

### Consulter les métriques brutes (Prometheus)
```bash
curl http://localhost:8000/api/v1/metrics
```

## 🛠️ Simulation d'Incidents (Game Day)

### Simuler une panne de base de données (déclenche l'alerte ErrorRate)
```bash
docker-compose stop postgres
# Attendre 2 minutes pour l'alerte critique
```

### Simuler une latence élevée (via l'API ou un outil de stress)
```bash
# Exemple avec 'ab' (Apache Benchmark) pour générer du trafic
ab -n 1000 -c 10 http://localhost:8000/api/v1/predict
```

## 🌐 Accès aux Interfaces

| Service | URL | Identifiants par défaut |
|---------|-----|-------------------------|
| **MailGuard API** | `http://localhost:8000` | - |
| **Prometheus** | `http://localhost:9090` | - |
| **Grafana** | `http://localhost:3001` | `admin` / `admin` |
| **Langfuse** | `http://localhost:3000` | (À créer au 1er lancement) |
| **Alertmanager** | `http://localhost:9093` | - |

## 🧹 Maintenance des Données

### Réinitialiser uniquement la base de données vectorielle
```bash
docker-compose stop postgres
docker-compose rm -f postgres
docker volume rm simplon-rag-sample_pgdata
docker-compose up -d postgres
```
