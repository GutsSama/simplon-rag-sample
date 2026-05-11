# Observabilité : Métriques Prometheus et Monitoring

## Aperçu
La Phase 2 implémente le monitoring quantitatif en utilisant Prometheus pour suivre la santé, les performances et la logique métier de l'API MailGuard.

## Détails de l'Implémentation

### 1. La Méthode RED
Nous suivons la méthode **RED** (Rate, Errors, Duration) pour le monitoring HTTP :
- **Rate** (Débit) : `http_requests_total` (Counter) - Nombre de requêtes par seconde.
- **Errors** (Erreurs) : `http_requests_total{status=~"5.."}` - Nombre de requêtes échouées.
- **Duration** (Durée) : `http_request_duration_seconds` (Histogram) - Distribution de la latence des requêtes.

### 2. Métriques spécifiques au ML
Pour le classifieur de spam (`/predict`), nous suivons :
- **Distribution des prédictions** : `ml_prediction_total` (Counter) - Décompte des spam vs non-spam vs phishing.
- **Scores de confiance** : `ml_prediction_confidence` (Histogram) - Aide à identifier quand le modèle devient incertain.
- **Dérive du modèle (Drift)** : `ml_model_drift_score` (Gauge) - Quantifie le changement dans la distribution des prédictions sur une fenêtre glissante.

### 3. Exposition des métriques
L'API expose un endpoint `/api/v1/metrics` que Prometheus scrape toutes les 15 secondes.

- **Source** : [metrics.py](file:///Users/amaury/simplon-rag-sample/api/src/rag/api/metrics.py)

## Infrastructure (Prometheus & Grafana)
Le fichier `docker-compose.yml` inclut :
- **Prometheus** : Récupère les métriques de l'API et stocke l'historique.
- **Grafana** : Visualise les métriques. Un tableau de bord "MailGuard Overview" est provisionné pour afficher :
  - Le QPS global et le taux d'erreur.
  - La latence p50/p95 par endpoint.
  - Le mix de prédictions ML.
  - Le score de dérive au cours du temps.

## Vérification
1. Accédez à `http://localhost:8000/api/v1/metrics` pour voir les métriques brutes.
2. Accédez à Grafana sur `http://localhost:3001` (user : `admin`, pass : `admin`).
