# Système de Routage Intelligent des Alertes

Le projet utilise un **Alert Router** personnalisé pour centraliser et diriger les notifications vers les bons canaux selon leur gravité.

## Architecture Globale

1.  **Collecte** : Prometheus surveille les métriques.
2.  **Évaluation** : Les règles d'alerte (`alert_rules.yml`) sont évaluées.
3.  **Routage Central** : Alertmanager reçoit les alertes et les envoie au `alert-router`.
4.  **Distribution** : Le `alert-router` (FastAPI) distribue les messages vers Discord et/ou Telegram.

## Stratégie de Routage par Sévérité

| Sévérité | Canaux | Justification |
| :--- | :--- | :--- |
| 🔴 **CRITICAL** | Discord + Telegram | Incident majeur nécessitant une attention immédiate sur tous les supports. |
| ⚠️ **WARNING** | Telegram uniquement | Notification informative pour suivi, sans polluer le canal d'équipe Discord. |

## Configuration des Canaux

Les secrets sont gérés via le fichier `.env` à la racine :

*   `DISCORD_WEBHOOK` : Webhook URL pour le canal d'alertes Discord.
*   `TELEGRAM_BOT_TOKEN` : Token API fourni par BotFather.
*   `TELEGRAM_CHAT_ID` : ID numérique de l'utilisateur ou du groupe Telegram.

## Tester le Système

### Simulation manuelle (Curl)

**Alerte Critique (Multi-canal) :**
```bash
curl -X POST "http://localhost:9095/webhook?channels=discord,telegram" -H "Content-Type: application/json" -d '{
  "alerts": [{
    "status": "firing",
    "labels": {"alertname": "CriticalTest", "severity": "critical"},
    "annotations": {"summary": "Alerte Critique", "description": "Test multi-canal"},
    "startsAt": "2026-05-15T16:00:00Z",
    "generatorURL": "http://prometheus"
  }],
  "status": "firing",
  "receiver": "critical-alerts",
  "externalURL": "http://alertmanager"
}'
```

### Logs et Maintenance

Pour surveiller le routage en temps réel :
```bash
docker logs -f simplon_rag_alert_router
```
