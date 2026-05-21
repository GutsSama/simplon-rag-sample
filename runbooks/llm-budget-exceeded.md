# Runbook: LLM Budget Exceeded

## 🚨 Alerte : LLMDailyCostExceeded

**Sévérité** : Warning
**Canal** : `#alerts-info` / Telegram
**Métrique** : `llm_daily_cost_euros > 20`

## 📋 Contexte
Cette alerte se déclenche lorsque le coût quotidien estimé (ou remonté par Langfuse) dépasse le plafond autorisé (ici 20 €/jour par défaut). Une surconsommation peut être légitime (pic de trafic anormal) ou résulter d'un incident (boucle infinie de l'agent LangGraph, erreur de parsing entraînant un re-prompt infini).

## 🔍 Investigation (Détection de la Root Cause)

1. **Identifier la conversation fautive via Grafana / Langfuse** :
   - Ouvrir **Langfuse** (http://localhost:3002).
   - Aller dans **Traces**.
   - Trier les traces par **Tokens** ou **Cost** (décroissant).
   - Chercher les traces anormalement lourdes (> 10 000 tokens pour une simple réponse).

2. **Comprendre l'anomalie** :
   - Est-ce que le nœud `retrieve` ramène trop de chunks inutiles ?
   - Est-ce que le nœud `evaluate` rejette systématiquement la réponse, provoquant une boucle `guard_route -> retrieve -> generate -> evaluate` ?
   - Regarder le détail du graphe dans Langfuse pour la trace concernée.

3. **Vérifier le volume d'ingestion** :
   - Quelqu'un a-t-il ingéré un livre entier de 2000 pages ? (Voir Grafana / métriques `/documents/ingest-*`).

## 🛠️ Mitigation

1. **Stop immédiat (Optionnel / Extrême)** :
   Si le coût augmente de 1 € par minute de manière incontrôlable et que la root cause n'est pas claire, basculez l'application sur le modèle local Ollama pour bloquer la facturation :
   ```bash
   # Dans le fichier .env, remplacer le modèle Mistral par Ollama
   LLM_MODEL=qwen2.5-coder:7b
   ```
   *Note : cela nécessite de relancer / redéployer l'API.*

2. **Correction du prompt / Graph** :
   - Si la boucle vient de l'évaluation : adoucir le prompt de `evaluate` ou limiter le `max_retries` de l'agent.
   - Si la consommation vient d'un utilisateur spécifique (spammeur) : bannir l'IP ou l'utilisateur temporatiquement.

3. **Mise à l'échelle du budget** :
   Si le trafic est légitime, discuter avec la direction pour augmenter le plafond dans l'alerte Prometheus.

## 📝 Actions Post-Incident
- Réviser le nombre de `max_retries` de la boucle d'agent.
- Implémenter un rate-limiting applicatif par IP/Utilisateur si ce n'est pas déjà fait.
- (Si applicable) Rédiger un post-mortem si le dépassement est supérieur à X €.
