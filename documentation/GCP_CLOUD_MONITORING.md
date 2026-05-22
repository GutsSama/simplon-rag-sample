# Guide — Intégration Native GCP (Cloud Monitoring & Logging)

Ce document décrit comment basculer d'une stack OSS locale (Prometheus/Loki/Grafana) vers les outils managés natifs de Google Cloud (Cloud Monitoring et Cloud Logging) sur Cloud Run, afin d'optimiser l'opérationnel.

## 1. Cloud Logging (Automatique)

Cloud Run ingère automatiquement tous les logs envoyés sur `stdout`/`stderr`.
Grâce à la bibliothèque `python-json-logger` (configurée dans `api/src/rag/api/logging.py`), nos logs sont **déjà en JSON structuré**.

**Résultat dans GCP (Logs Explorer)** :
Chaque champ JSON (ex: `correlation_id`, `trace_id`) devient indexable et filtrable nativement, remplaçant ainsi **Loki**.
Pour filtrer tous les logs d'une session :
```text
jsonPayload.correlation_id="<uuid>"
```

## 2. Cloud Monitoring (Métriques & Alertes)

Cloud Run exporte nativement des métriques (CPU, Mémoire, Container instances, Latence HTTP). Pour les métriques applicatives (RAG custom) :
- Les métriques Prometheus de l'API peuvent être scrapées par un sidecar OpenTelemetry ou via le service managé GCP pour Prometheus.
- Pour simplifier l'approche "serverless", nous créons des Alerting Policies sur les métriques Cloud Run natives.

### Commandes pour répliquer nos alertes locales vers GCP (Alerting Policies)

#### Alerte 1 : High 5xx Error Rate
Création d'une politique d'alerte si le taux d'erreur dépasse 5% :
```bash
gcloud alpha monitoring policies create \
  --policy-from-file=gcp_alert_errors.json
```
*(Le fichier JSON contenant la condition MQL est fourni dans le dossier `scripts/`)*

#### Alerte 2 : High P95 Latency
Alerte sur la métrique native de latence Cloud Run :
```bash
gcloud alpha monitoring policies create \
  --policy-from-file=gcp_alert_latency.json
```

## 3. Coût LLM & Tracing (Langfuse)

Pour l'observabilité détaillée des agents LangGraph, nous continuons d'utiliser **Langfuse** (soit managé `cloud.langfuse.com`, soit auto-hébergé sur GCP via Cloud Run). 
La corrélation avec GCP se fait via le `correlation_id` (injecté dans le middleware FastAPI) qui apparaît :
1. Dans Cloud Logging (Logs Explorer)
2. En tant que `tags` ou `metadata` dans les traces Langfuse.

## Conclusion

Le passage à GCP permet de retirer :
- Le conteneur Loki
- Le conteneur Promtail
- (Optionnellement) Prometheus / Alertmanager si on utilise 100% GCP Managed Prometheus

La branche de code applicatif **reste identique**, c'est tout l'avantage d'une architecture découplée (JSON logs + endpoint `/metrics` standard).
