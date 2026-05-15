# Configuration de l'Alerting Telegram

Ce document détaille l'intégration d'Alertmanager avec Telegram via un pont FastAPI personnalisé.

## Architecture de l'alerte

1. **Source** : Prometheus analyse les métriques toutes les 15s.
2. **Evaluation** : Prometheus envoie l'alerte à **Alertmanager**.
3. **Pont** : Alertmanager envoie un webhook à `telegram-bridge` (FastAPI).
4. **Notification** : Le pont formate le message et l'envoie via l'API Bot Telegram.

## Configuration BotFather

1. **Bot** : [@Simplo_rag_bot](https://t.me/Simplo_rag_bot)
2. **Token** : Configuré dans le fichier `.env` (`TELEGRAM_BOT_TOKEN`).
3. **Chat ID** : Identifiant numérique de l'utilisateur ou du groupe (`TELEGRAM_CHAT_ID`).

## Composants du Pont

- **Fichier** : `monitoring/telegram-bridge/main.py`
- **Techno** : FastAPI + httpx
- **Formatage** : Supporte le Markdown pour un affichage clair (Emojis, Sévérité en gras, etc.).

## Tester les alertes

Pour vérifier le bon fonctionnement du pont :

1. **Test manuel (Curl)** :
   ```bash
   curl -X POST http://localhost:9095/webhook -H "Content-Type: application/json" -d '{
     "alerts": [{
       "status": "firing",
       "labels": {"alertname": "TestAlert", "severity": "critical"},
       "annotations": {"summary": "Test", "description": "Ceci est un test"},
       "startsAt": "2026-05-15T10:00:00Z",
       "generatorURL": "http://prometheus"
     }],
     "status": "firing",
     "receiver": "telegram",
     "externalURL": "http://alertmanager"
   }'
   ```

2. **Test réel** :
   Arrêter un service : `docker stop simplon_rag_api`.

## Maintenance

Les logs du pont sont consultables via :
```bash
docker logs -f simplon_rag_telegram_bridge
```
