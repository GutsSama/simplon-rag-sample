#!/bin/bash
set -e

echo "  Configuration de Cloud Monitoring pour Simplon RAG"

# 1. Activation des APIs
gcloud services enable monitoring.googleapis.com logging.googleapis.com
echo " APIs Monitoring et Logging activées"

# 2. Création de l'Alerte : Latence élevée (P95 > 10s)
cat <<EOF > /tmp/gcp_alert_latency.json
{
  "displayName": "Simplon RAG - Latence Elevée",
  "combiner": "OR",
  "conditions": [
    {
      "displayName": "Latence requêtes Cloud Run > 10s",
      "conditionThreshold": {
        "filter": "resource.type = \"cloud_run_revision\" AND metric.type = \"run.googleapis.com/request_latencies\"",
        "aggregations": [
          {
            "alignmentPeriod": "300s",
            "crossSeriesReducer": "REDUCE_PERCENTILE_95",
            "perSeriesAligner": "ALIGN_DELTA"
          }
        ],
        "comparison": "COMPARISON_GT",
        "duration": "60s",
        "trigger": {
          "count": 1
        },
        "thresholdValue": 10000
      }
    }
  ]
}
EOF

gcloud alpha monitoring policies create --policy-from-file=/tmp/gcp_alert_latency.json
echo " Politique d'alerte latence créée"

# 3. Création de l'Alerte : Erreurs 5xx (> 5%)
cat <<EOF > /tmp/gcp_alert_errors.json
{
  "displayName": "Simplon RAG - Taux Erreurs 5xx",
  "combiner": "OR",
  "conditions": [
    {
      "displayName": "Taux erreurs > 5%",
      "conditionThreshold": {
        "filter": "resource.type = \"cloud_run_revision\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.labels.response_code_class = \"5xx\"",
        "aggregations": [
          {
            "alignmentPeriod": "300s",
            "crossSeriesReducer": "REDUCE_SUM",
            "perSeriesAligner": "ALIGN_RATE"
          }
        ],
        "comparison": "COMPARISON_GT",
        "duration": "60s",
        "trigger": {
          "count": 1
        },
        "thresholdValue": 0.05
      }
    }
  ]
}
EOF

gcloud alpha monitoring policies create --policy-from-file=/tmp/gcp_alert_errors.json
echo " Politique d'alerte erreurs 5xx créée"

echo " Configuration GCP Monitoring terminée !"
