# Configuration de l'Alerting Discord

Ce document détaille l'intégration d'Alertmanager avec Discord pour le projet Simplon RAG.

## Architecture de l'alerte

1. **Source** : Prometheus analyse les métriques (`/metrics`) toutes les 15s.
2. **Evaluation** : Si une règle (`rules.yml`) est enfreinte pendant la durée définie (ex: 2 min), Prometheus envoie l'alerte à **Alertmanager**.
3. **Notification** : Alertmanager regroupe les alertes et les envoie au Webhook Discord.

## Webhook Configuré

**URL** : Configurée dans le fichier `.env` (`DISCORD_WEBHOOK`).

## Alertes Actives

| Alerte | Condition | Sévérité | Description |
|--------|-----------|----------|-------------|
| `APIHighLatency` | p95 > 15s | Critical | Latence excessive sur le chat (impact utilisateur immédiat). |
| `APIErrorRate` | > 5% de 5xx | Critical | Erreurs serveur détectées sur les endpoints. |
| `LLMServiceDown` | Target Down | Critical | Ollama ne répond plus depuis l'hôte Mac. |
| `LowEvaluationScore` | Moyenne < 5/10 | Warning | La qualité des réponses RAG se dégrade. |

## Tester les alertes

Pour simuler un incident et déclencher une alerte Discord :

1. **Latence** : Utiliser l'endpoint de chaos (si implémenté) ou saturer le CPU.
2. **Erreurs** : Arrêter le container Postgres : `docker compose stop postgres`.
3. **Service Down** : Arrêter Ollama sur le Mac.

## Runbooks

Chaque alerte Discord contient un lien vers le runbook correspondant dans le dossier `/runbooks/` pour aider à la résolution rapide.
