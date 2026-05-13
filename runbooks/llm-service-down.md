# Runbook — LLMServiceDown

**Alerte** : `LLMServiceDown`  
**Condition** : `up{job="api"} == 0` ou `up{job="ollama"} == 0` pendant 1 minute  
**Canal Discord** : `#alerts-prod`

---

## Symptôme

L'API RAG ou Ollama n'est plus joignable. Toutes les nouvelles conversations échouent immédiatement. L'interface Streamlit affiche une erreur de connexion.

## Diagnostic (< 5 min)

### 1. Identifier le service en cause (Prometheus)

```
Prometheus → Status → Targets
→ Vérifier quels targets sont DOWN
```

### 2. Si l'API FastAPI est down

```bash
# Vérifier l'état du container
docker compose ps api

# Voir les logs de crash
docker logs simplon_rag_api --tail 50

# Tentative de redémarrage
docker compose restart api
```

### 3. Si Ollama est down (hôte macOS)

```bash
# Vérifier si Ollama tourne
curl http://localhost:11434/api/tags  # Timeout = Ollama down

# Vérifier depuis le container
docker exec simplon_rag_api curl http://host.docker.internal:11434/api/tags

# Redémarrer Ollama
# → Via l'icône dans la barre de menu macOS : Quit → Relaunch
# Ou via terminal :
killall ollama && open -a Ollama
```

### 4. Vérifier la connectivité réseau Docker

```bash
# Vérifier que host.docker.internal est résolu
docker exec simplon_rag_api ping -c 1 host.docker.internal

# Vérifier la variable d'env
docker exec simplon_rag_api env | grep OLLAMA
```

## Mitigation

| Cause | Action |
|-------|--------|
| API crashée (OOM) | Augmenter la mémoire Docker + `docker compose restart api` |
| Ollama crash | Relancer Ollama sur le Mac hôte |
| Modèle non chargé | `ollama pull qwen2.5-coder:7b && ollama pull mxbai-embed-large` |
| Réseau Docker cassé | `docker compose down && docker compose up -d` |
| Variable OLLAMA_BASE_URL incorrecte | Vérifier `api/.env` : `OLLAMA_BASE_URL=http://host.docker.internal:11434` |

## Scénarios Game Day

Pour simuler cet incident en démo :

```bash
# Simuler un Ollama inaccessible (corrompre l'URL dans l'env, pas besoin d'arrêter Ollama)
docker exec simplon_rag_api curl -X POST http://localhost:8000/api/v1/chaos/ollama-break?broken=true

# Envoyer un message dans l'UI → observer l'erreur dans Streamlit + l'alerte Discord
# Résolution :
docker exec simplon_rag_api curl -X POST http://localhost:8000/api/v1/chaos/ollama-break?broken=false
```

---

*Propriétaire : équipe IA — Mise à jour : 2026-05*
