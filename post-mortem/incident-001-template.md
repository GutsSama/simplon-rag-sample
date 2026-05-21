# Post-Mortem : [Titre de l'incident]

**Date** : YYYY-MM-DD
**Auteur(s)** : [Vos noms]
**Statut** : [Draft / En revue / Clôturé]

## 1. Résumé
**Description** : Bref résumé de ce qui s'est passé (ex: "Le chatbot est parti dans une boucle infinie de réécritures, consommant 50€ de budget Mistral en 1 heure").
**Impact** : Temps d'indisponibilité, coût engendré, expérience utilisateur (ex: "Les utilisateurs recevaient des erreurs 504").
**Root Cause** : Cause profonde en 1 phrase.

## 2. Timeline (Chronologie)
*(Tous les temps en UTC ou heure locale précisée)*
- **10:00** : Déploiement de la version X (ajout du nœud 'evaluate').
- **10:15** : Première alerte `HighP95Latency` reçue sur Discord.
- **10:20** : Investigation sur Grafana confirme une augmentation de la durée des requêtes à >15s.
- **10:25** : Alerte `LLMDailyCostExceeded` déclenchée.
- **10:30** : Identification du problème via Langfuse (boucle infinie sur la trace #ABC).
- **10:45** : Rollback vers la version X-1 / Bascule sur modèle local Ollama.
- **10:50** : Fin de l'incident, les métriques reviennent à la normale.

## 3. Détection
- **Comment l'incident a-t-il été détecté ?** (Alertes Prometheus, plainte utilisateur, etc.)
- **Temps de détection** (TDD) : [X] minutes.
- Aurions-nous pu le détecter plus tôt ? Comment ?

## 4. Root Cause (Cause racine)
*(Technique des 5 Pourquoi)*
- Le chatbot a consommé tout le budget. **Pourquoi ?**
- L'agent a fait 50 appels au LLM pour une seule question. **Pourquoi ?**
- Le nœud `evaluate` a retourné systématiquement "non pertinent", forçant une réécriture. **Pourquoi ?**
- Le prompt d'évaluation était trop strict et n'acceptait que des réponses structurées en JSON alors que l'agent renvoyait du Markdown.

## 5. Ce qui a bien fonctionné / Ce qui n'a pas fonctionné
**Bien fonctionné** :
- L'alerte budget a empêché une facture de plusieurs centaines d'euros.
- Langfuse a permis d'identifier immédiatement la boucle infinie dans le graphe.

**Pas bien fonctionné** :
- Le rollback a pris trop de temps (pas de procédure claire).
- L'alerte de latence n'a pas été jugée critique assez vite.

## 6. Actions Correctives (Action Items)
| Action | Priorité | Owner | Statut |
|---|---|---|---|
| Mettre une limite logicielle `max_retries = 3` dans le graphe LangGraph. | P1 | [Nom] | To Do |
| Ajouter un test unitaire qui simule un évaluateur très strict. | P2 | [Nom] | To Do |
| Optimiser le prompt de `evaluate` pour accepter le format Markdown. | P2 | [Nom] | To Do |
