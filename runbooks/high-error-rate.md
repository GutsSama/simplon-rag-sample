# Runbook — APIErrorRate

**Alerte** : `APIErrorRate`  
**Condition** : `> 5% de réponses 5xx` pendant 1 minute  
**Canal Discord** : `#alerts-prod`

---

## Symptôme

Plus de 5% des requêtes reçoivent une réponse HTTP 5xx. Les utilisateurs voient des messages d'erreur dans l'interface Streamlit.

## Diagnostic (< 5 min)

### 1. Consulter les logs applicatifs

```bash
# Voir les erreurs récentes avec leur stack trace
docker logs simplon_rag_api --tail 100 | grep -E "ERROR|CRITICAL|500"

# Format JSON structuré (avec jq)
docker logs simplon_rag_api --tail 100 | jq 'select(.level == "ERROR")'
```

### 2. Identifier l'endpoint en erreur (Grafana)

```
Grafana → Simplon RAG Overview → Panel "Error Rate by Endpoint"
→ Identifier l'endpoint qui génère les 5xx
```

### 3. Tester manuellement

```bash
# Tester le healthcheck
curl http://localhost:8000/api/v1/health

# Tester la base de données
docker exec simplon_rag_postgres pg_isready -U rag

# Tester Ollama
curl http://localhost:11434/api/tags
```

### 4. Vérifier les dépendances

```bash
docker compose ps        # Tous les services sont-ils UP ?
docker compose logs postgres --tail 20
```

## Mitigation

| Cause | Action |
|-------|--------|
| PostgreSQL down | `docker compose restart postgres` + attendre le healthcheck |
| Ollama down | Relancer Ollama sur le Mac hôte |
| Bug applicatif | Consulter les logs → identifier le `request_id` → tracer dans Langfuse |
| Dépassement de mémoire | `docker stats` → augmenter la mémoire du container si possible |
| Erreur de migration | `docker exec simplon_rag_api uv run alembic upgrade head` |
| Chaos injecté | `curl -X POST http://localhost:8000/api/v1/chaos/error` (sans `code`) |

## Escalade

Si l'erreur est liée à une migration de données ou une corruption de base : **ne pas redémarrer** avant analyse.

---

*Propriétaire : équipe IA — Mise à jour : 2026-05*
