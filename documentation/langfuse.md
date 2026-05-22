# Tracing & LLM Ops (Langfuse)

Langfuse est l'outil spécialisé pour l'observabilité profonde des applications basées sur des LLM.

## 🔍 Pourquoi Langfuse ?

Contrairement à Prometheus qui donne des agrégats (moyennes, taux), Langfuse permet de voir le **détail exact** de chaque interaction :
- Quel était le prompt exact envoyé ?
- Quels documents ont été récupérés par le retriever ?
- Quelle était la réponse brute du modèle ?
- Combien de tokens ont été consommés ?

## 🛠️ Implémentation

L'intégration se fait via le `CallbackHandler` de Langfuse au niveau du service de chat (`chat_service.py`).
- **Traces hiérarchiques** : Chaque exécution du graphe crée une trace racine, et chaque noeud (`guard`, `retrieve`, `generate`, `evaluate`) crée un "span" enfant.
- **Pseudonymisation** : Pour respecter la RGPD, les IDs utilisateurs sont hashés avant d'être envoyés vers Langfuse.

## 🚀 Utilisation lors de la Soutenance
Langfuse est l'outil parfait pour montrer au jury :
1.  **La complexité du graphe** : Visualisation du passage d'un noeud à l'autre.
2.  **La qualité du Retrieval** : Voir les morceaux de texte (chunks) que l'algorithme a choisi de lire.
3.  **L'auto-correction** : Si un noeud d'évaluation demande une réécriture, on voit les deux tentatives de génération.
