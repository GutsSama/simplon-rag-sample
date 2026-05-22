# Simplon RAG - Architecture & Observability Documentation

> Index général du dossier : [README.md](README.md)

Bienvenue dans la documentation technique du projet **Simplon RAG**. Ce projet implémente un chatbot de support intelligent basé sur une architecture RAG (Retrieval Augmented Generation), conçu pour être déployé localement avec une observabilité de niveau production.

## 🏗️ Architecture Globale
Le système repose sur un flux agentique piloté par **LangGraph**, permettant une prise de décision granulaire (Guardrails, Retrieval, Evaluation). L'inférence est déportée sur **Ollama** (via l'hôte macOS) pour bénéficier de l'accélération GPU Metal.

## 📚 Sommaire de la Documentation

1.  **[Infrastructure Docker](docker.md)** : Gestion des containers, réseaux et volumes.
2.  **[Métriques & Prometheus](prometheus.md)** : Implémentation des KPIs techniques et métiers.
3.  **[Visualisation & Grafana](grafana.md)** : Dashboards RED et RAG Insights.
4.  **[Logs & Loki](loki.md)** : Centralisation des logs structurés avec Promtail.
5.  **[Tracing & Langfuse](langfuse.md)** : Observabilité profonde des flux LLM.
6.  **[Guide des Commandes CLI](commands.md)** : Cheat sheet pour le lancement, les tests et le debug.
7.  **[Alerting Discord](discord.md)** : Configuration Alertmanager → Discord, liste des alertes et procédure de test.
8.  **[Runbook — Haute Latence](../runbooks/high-latency-messages.md)** : Diagnostic et mitigation du p95 élevé.
9.  **[Runbook — Taux d'Erreur](../runbooks/high-error-rate.md)** : Diagnostic et mitigation des erreurs 5xx.
10. **[Runbook — LLM Indisponible](../runbooks/llm-service-down.md)** : Diagnostic et mitigation d'un service LLM down.

---

## 🎯 Objectifs de l'Observabilité
L'observabilité dans ce projet n'est pas seulement technique (CPU/RAM), elle est orientée **Métier IA** :
- **Réactivité** : Monitoring de la latence p95 par noeud du graphe.
- **Fiabilité** : Guardrails pour rejeter les questions hors-sujet.
- **Qualité** : Auto-évaluation par un LLM "juge" avec score de 0 à 10.
- **Transparence** : Traces complètes de chaque étape de réflexion de l'agent.

## 🔥 Chaos Engineering — Scénarios Game Day

Des endpoints de simulation de panne sont disponibles pour démontrer la résilience de la stack :

| Scénario | Commande |
|----------|---------|
| Injecter 5s de latence | `curl -X POST http://localhost:8000/api/v1/chaos/latency?ms=5000` |
| Forcer des erreurs 500 | `curl -X POST http://localhost:8000/api/v1/chaos/error?code=500` |
| Simuler Ollama down | `curl -X POST "http://localhost:8000/api/v1/chaos/ollama-break?broken=true"` |
| Rétablir la normale | `curl -X POST http://localhost:8000/api/v1/chaos/latency?ms=0` |

## 🚀 Game Day Readiness
Pour préparer la soutenance technique, un guide spécifique est disponible :
👉 **[GAME_DAY.md](GAME_DAY.md)**
