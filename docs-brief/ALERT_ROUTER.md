# Spécifications Techniques : Alert Router

L'**Alert Router** est un microservice personnalisé conçu pour orchestrer et distribuer les alertes système vers différents canaux de communication (Discord, Telegram) avec une logique de routage basée sur la sévérité.

## 🚀 Fonctionnalités Clés

*   **Multi-Canal** : Support simultané de Discord (Webhooks) et Telegram (Bot API).
*   **Routage Intelligent** : Sélection dynamique des canaux via paramètres de requête (Query Params).
*   **Résilience Industrielle** :
    *   **Auto-Retry** : 3 tentatives de rejeu automatique via `httpx.AsyncHTTPTransport`.
    *   **Timeouts** : Limitation à 10s par requête pour éviter les blocages de ressources.
*   **Observabilité Intégrée** :
    *   Logs structurés (Timestamp, Level, Component).
    *   Mesure de la latence de traitement pour chaque alerte.
    *   Healthcheck endpoint (`/health`).

## 🛠️ Stack Technique

*   **Langage** : Python 3.11
*   **Framework** : FastAPI (Asynchrone)
*   **Client HTTP** : httpx
*   **Validation** : Pydantic v2
*   **Serveur** : Uvicorn

## 📡 Interface API

### Webhook Principal
`POST /webhook?channels=telegram,discord`

#### Paramètres de requête
*   `channels` (optionnel) : Liste séparée par des virgules des canaux cibles. Défaut : `telegram,discord`.

#### Format du Payload (Alertmanager compatible)
```json
{
  "alerts": [
    {
      "status": "firing",
      "labels": { "alertname": "APIHighLatency", "severity": "critical" },
      "annotations": { "summary": "Latence élevée", "description": "p95 > 15s" },
      "startsAt": "2026-05-15T10:00:00Z",
      "generatorURL": "http://prometheus:9090"
    }
  ],
  "status": "firing",
  "receiver": "critical-alerts",
  "externalURL": "http://alertmanager:9093"
}
```

## ⚙️ Configuration (Environnement)

Le service s'appuie sur les variables d'environnement suivantes :

| Variable | Description | Requis |
| :--- | :--- | :--- |
| `DISCORD_WEBHOOK` | URL du webhook Discord | Optionnel |
| `TELEGRAM_BOT_TOKEN` | Token API du Bot Telegram | Optionnel |
| `TELEGRAM_CHAT_ID` | ID du chat cible Telegram | Optionnel |
| `LOG_LEVEL` | Niveau de log (INFO, DEBUG) | Non (Défaut: INFO) |

## 🛡️ Sécurité

1.  **Isolation Réseau** : Le service est exposé uniquement sur le réseau interne Docker (`default`).
2.  **Gestion des Secrets** : Aucune clé n'est stockée dans l'image Docker ou le code source. Tout passe par des variables d'environnement injectées au runtime.
3.  **Validation de Schéma** : Utilisation de Pydantic pour rejeter toute payload malformée.

## 📊 Maintenance

Consulter les logs du container pour le monitoring :
```bash
docker logs simplon_rag_alert_router
```
