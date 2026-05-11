# Synthèse de l'Observabilité - Projet MailGuard

Ce document résume l'architecture et les composants d'observabilité mis en place pour l'API MailGuard, conformément aux exigences du brief.

## 🏗️ Architecture de la Stack
La stack d'observabilité est composée des éléments suivants, tous orchestrés via Docker Compose :
- **API (FastAPI)** : L'application principale instrumentée.
- **Prometheus** : Collecte et stockage des métriques (HTTP RED et métier ML).
- **Grafana** : Visualisation des métriques via des tableaux de bord.
- **Langfuse** : Tracing complet des appels LLM, gestion des coûts et des feedbacks.
- **Alertmanager** : Gestion et routage des alertes (ex: via Discord).

## 📊 Métriques Prometheus
L'API expose plusieurs types de métriques sur l'endpoint `/api/v1/metrics` :
- **HTTP RED** :
  - `http_requests_total` : Nombre total de requêtes par méthode, endpoint et statut.
  - `http_request_duration_seconds` : Latence des requêtes (Histogramme).
- **Métriques Métier ML** :
  - `prediction_distribution` : Répartition des prédictions (spam, non-spam, phishing).
  - `prediction_confidence` : Score de confiance moyen des prédictions.
  - `model_drift_score` : Score de dérive calculé sur une fenêtre glissante.
- **Coûts LLM** :
  - `llm_daily_cost_euros` : Coût quotidien cumulé exporté depuis Langfuse.

## 🕵️ Tracing LLM (Langfuse)
Chaque appel à `/explain` est tracé avec les spans suivants :
1. **retrieval** : Temps de recherche dans la base vectorielle Chroma.
2. **prompt_build** : Temps de construction du prompt avec le contexte récupéré.
3. **llm_call** : Appel au modèle (Mistral/OpenAI) avec capture automatique des tokens et du coût.

**Conformité RGPD** : 
- Les `user_id` sont systématiquement pseudonymisés via un hash SHA-256 avant d'être envoyés à Langfuse.
- Aucun contenu d'email brut n'est stocké dans les métadonnées des traces.

## 🚨 Alerting et Qualité
- **Feedback** : Un endpoint `/api/v1/feedback` permet de récolter les avis utilisateurs (👍/👎) et d'associer un score aux traces dans Langfuse.
- **Alertes configurées** :
  - Latence excessive (P95 > 2s sur `/predict`).
  - Taux d'erreur 5xx élevé (> 5% sur 5 min).
  - Détection de dérive (Drift) du modèle Scikit-Learn.
  - Dépassement du budget quotidien LLM.

## ✅ Conclusion
L'API est désormais totalement observable. Les incidents applicatifs peuvent être diagnostiqués via Grafana, tandis que les anomalies liées au LLM (hallucinations, coûts, latence RAG) sont identifiables précisément dans Langfuse.
