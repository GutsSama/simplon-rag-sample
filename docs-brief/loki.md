# Logs & Observabilité (Loki)

Loki permet de centraliser et de requêter les logs de tous les containers de manière efficace.

## 🪵 Flux de Logging

1.  **Génération** : L'API utilise `structlog` pour produire des logs au format **JSON**.
2.  **Collecte** : **Promtail** surveille la socket Docker (`/var/run/docker.sock`) et récupère les logs des containers.
3.  **Stockage** : Loki indexe les métadonnées (labels comme `container`, `level`) mais pas le contenu complet, ce qui le rend très léger.

## 🏷️ Labels & Recherche

Grâce à la configuration de Promtail, chaque log est tagué avec le nom du container. Dans Grafana, vous pouvez filtrer les logs avec la requête LogQL :
```logql
{container="simplon_rag_api"} |= "error"
```

## 🎯 Intérêt pour le RAG
Les logs structurés permettent de tracer précisément les métadonnées des réponses :
- `duration` du noeud.
- `source_count` (nombre de chunks récupérés).
- `category` détectée par le guardrail.
- `score` d'évaluation.

Ces données sont visibles directement dans le dashboard Grafana sous forme de tableau de logs chronologique.
