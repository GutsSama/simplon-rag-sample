# Infrastructure & Docker

Le projet utilise **Docker Compose** pour orchestrer l'ensemble des services nécessaires au fonctionnement du RAG et de la stack d'observabilité.

## 📦 Services Orchestrés

| Service | Image | Rôle |
| :--- | :--- | :--- |
| **API** | Custom (FastAPI) | Coeur logique, LangGraph, Orchestration RAG. |
| **Frontend** | Custom (Streamlit) | Interface utilisateur pour le chat. |
| **Postgres** | `ankane/pgvector` | Base de données avec extension Vector pour le RAG. |
| **Prometheus** | `prom/prometheus` | Collecte et stockage des métriques. |
| **Grafana** | `grafana/grafana` | Visualisation des données et dashboards. |
| **Loki** | `grafana/loki` | Centralisation des logs. |
| **Promtail** | `grafana/promtail` | Agent de collecte des logs Docker. |
| **Langfuse** | `langfuse/langfuse` | Serveur de tracing pour les flux LLM. |

## 🔌 Connectivité avec l'Hôte (Ollama)

L'une des particularités du projet est l'utilisation d'Ollama sur la machine hôte (macOS) plutôt que dans un container. Cela permet d'accéder directement au GPU Metal d'Apple Silicon.

- **Configuration** : L'API communique via `http://host.docker.internal:11434`.
- **Réseau** : Le paramètre `extra_hosts` est utilisé dans le `docker-compose.yml` pour permettre cette résolution DNS interne.

## 💾 Persistance des Données

- **Postgres** : Volume `postgres_data` pour conserver les documents ingérés et l'historique des conversations.
- **Observabilité** : Les configurations (Prometheus YAML, Dashboards Grafana) sont montées en lecture seule pour garantir l'immutabilité de la stack de monitoring.

## 🚀 Lancement
```bash
docker compose up -d
```
