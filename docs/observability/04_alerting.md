# Observabilité : Alerting et Réponse aux Incidents

## Aperçu
La Phase 4 garantit que l'équipe est notifiée proactivement en cas de dégradation du système. Nous utilisons Prometheus Alertmanager pour router les alertes vers Discord.

## Stratégie d'Alerte

### 1. Alertes Définies
Nous avons configuré 4 alertes prioritaires dans [rules.yml](file:///Users/amaury/simplon-rag-sample/prometheus/rules.yml) :

| Nom de l'Alerte | Condition | Sévérité |
|-----------------|-----------|----------|
| `HighPredictLatency` | latence p95 sur /predict > 0.5s | Warning |
| `HighErrorRate` | erreurs 5xx > 5% du trafic | Critical |
| `ModelDriftDetected` | score de dérive > 0.1 | Warning |
| `LLMBudgetExceeded` | coût quotidien > 15€ | Critical |

### 2. Routage des Notifications
Alertmanager est configuré pour :
1. Grouper les alertes similaires.
2. Attendre 10 secondes avant l'envoi pour éviter le "flapping".
3. Envoyer les notifications vers un webhook Discord.

## Réponse aux Incidents (Runbooks)
Chaque alerte est liée à un runbook dédié qui fournit un guide étape par étape pour le diagnostic et la remédiation :

- [Runbook Latence Élevée](file:///Users/amaury/simplon-rag-sample/runbooks/high-latency-predict.md)
- [Runbook Taux d'Erreur Élevé](file:///Users/amaury/simplon-rag-sample/runbooks/high-error-rate.md)
- [Runbook Dérive Modèle](file:///Users/amaury/simplon-rag-sample/runbooks/prediction-drift.md)
- [Runbook Budget LLM Dépassé](file:///Users/amaury/simplon-rag-sample/runbooks/llm-budget-exceeded.md)

## Vérification
Pour tester le pipeline d'alerting :
1. Simulez un taux d'erreur élevé en arrêtant la base de données : `docker-compose stop postgres`.
2. Attendez 2 minutes.
3. Vérifiez l'interface des alertes Prometheus sur `http://localhost:9090/alerts`.
4. Vérifiez la notification dans le canal Discord désigné.
