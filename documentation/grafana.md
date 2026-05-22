# Visualisation & Dashboards (Grafana)

Grafana est le point central de visualisation du projet. Il agrège les données de Prometheus (métriques) et de Loki (logs).

## 📊 Dashboards Provisionnés

Le projet inclut deux dashboards pré-configurés (automatiquement importés au démarrage) :

### 1. RAG Performance & Quality
Ce dashboard est orienté **Métier** et **IA**.
- **Avg Eval Score** : Moyenne des scores de qualité (0-10) attribués par le LLM juge.
- **RAG Node Latency (p95)** : Temps de réponse pour chaque étape (Retrieval, Generation, etc.).
- **Guard Route Traffic** : Répartition des questions (In-Scope vs Out-of-Scope).
- **Score Distribution** : Histogramme de la qualité des réponses.
- **Loki Logs** : Flux de logs en temps réel filtré pour l'API.

### 2. API RED
Ce dashboard suit la méthode standard **RED** (Rate, Errors, Duration) :
- **RPS** : Requêtes par seconde.
- **Error Rate** : Taux d'erreurs 5xx.
- **Latency** : Distribution de la latence HTTP globale.

## 🔗 Intégration des Datasources
Les sources de données sont configurées via le fichier `monitoring/grafana/provisioning/datasources/datasource.yml` :
- **Prometheus** : `http://prometheus:9090`
- **Loki** : `http://loki:3100`

## 🎨 Design & Esthétique
Les dashboards utilisent le thème **Dark Mode** de Grafana avec des dégradés de couleurs (Gradients) et des seuils (Thresholds) visuels pour une lecture immédiate des anomalies (Passage au rouge si latence > 10s).
