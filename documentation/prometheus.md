# Métriques & Alerting (Prometheus)

Prometheus est responsable de la collecte des métriques par "scraping" de l'API.

## 📈 Implémentation des Métriques

Nous utilisons deux types d'instrumentation :

### 1. Instrumentation Automatique (RED)
Via `prometheus-fastapi-instrumentator`, nous collectons les métriques HTTP standards :
- `http_requests_total`
- `http_request_duration_seconds`

### 2. Métriques Personnalisées (RAG)
Définies dans `api/src/rag/monitoring/metrics.py`, elles ciblent spécifiquement le comportement de l'IA :
- `rag_guard_route_total` : Compte les appels au guardrail avec labels `in_scope`, `category`.
- `rag_node_duration_seconds` : Histogramme de latence par noeud LangGraph (`retrieve`, `generate`, etc.).
- `rag_eval_score` : Score de qualité attribué à la génération.

## 🚨 Alertes (Alertmanager)

Les règles d'alerting sont définies dans `monitoring/prometheus/alert_rules.yml` :

- **HighP95Latency** : Déclenchée si la latence p95 d'un noeud RAG dépasse **10 secondes**.
- **HighErrorRate** : Déclenchée si le taux d'erreurs 5xx dépasse **5%**.

## 🛑 Cardinalité
Pour préserver les performances de Prometheus, les labels utilisés sont de **basse cardinalité** (énumérations fixes, booléens). Aucun identifiant unique (user_id, conversation_id) n'est envoyé vers Prometheus.
