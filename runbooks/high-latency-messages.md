# Runbook — APIHighLatency

**Alerte** : `APIHighLatency`  
**Condition** : `histogram_quantile(0.95, ...) > 10s` pendant 1 minute  
**Canal Discord** : `#alerts-prod`

---

## Symptôme

Le p95 de latence sur le endpoint `/api/v1/conversations/{id}/messages` dépasse 10 secondes.
Les utilisateurs voient le spinner tourner sans réponse.

## Diagnostic (< 5 min)

### 1. Identifier le nœud lent (Langfuse)

```
Langfuse → Traces → Trier par durée DESC
→ Identifier le span le plus long : retrieve, generate, ou evaluate ?
```

### 2. Vérifier Ollama

```bash
# Sur l'hôte macOS
ollama ps    # Voir si le modèle est chargé
curl http://localhost:11434/api/tags  # Réponse rapide ?

# Depuis un container
docker exec simplon_rag_api curl http://host.docker.internal:11434/api/tags
```

### 3. Vérifier PostgreSQL / pgvector

```bash
docker exec simplon_rag_postgres psql -U rag -c "SELECT count(*) FROM chunks;"
docker stats simplon_rag_postgres
```

### 4. Vérifier la charge du container API

```bash
docker stats simplon_rag_api
docker logs simplon_rag_api --tail 50
```

## Mitigation

| Cause | Action |
|-------|--------|
| Ollama saturé | Réduire `num_predict` dans les settings |
| pgvector lent | Vérifier l'index HNSW — `REINDEX` si nécessaire |
| Rewrite-loop infinie | Voir les traces Langfuse — reset des conversations bloquées |
| Container sous pression | `docker compose restart api` |
| Chaos injecté | `curl -X POST http://localhost:8000/api/v1/chaos/latency?ms=0` |

## Escalade

Si l'alerte persiste > 15 min : prévenir l'équipe.

---

*Propriétaire : équipe IA — Mise à jour : 2026-05*
