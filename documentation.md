# Simplon RAG - Architecture & Observability Documentation

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

---

## 🎯 Objectifs de l'Observabilité
L'observabilité dans ce projet n'est pas seulement technique (CPU/RAM), elle est orientée **Métier IA** :
- **Réactivité** : Monitoring de la latence p95 par noeud du graphe.
- **Fiabilité** : Guardrails pour rejeter les questions hors-sujet.
- **Qualité** : Auto-évaluation par un LLM "juge" avec score de 0 à 10.
- **Transparence** : Traces complètes de chaque étape de réflexion de l'agent.

## 🚀 Game Day Readiness
Pour préparer la soutenance technique, un guide spécifique est disponible :
👉 **[GAME_DAY.md](GAME_DAY.md)**
