# Observabilité : Traçage LLM avec Langfuse

## Aperçu
La Phase 3 se concentre sur la "boîte noire" des appels LLM dans l'endpoint `/explain`. Nous utilisons Langfuse pour tracer les étapes internes du pipeline RAG.

## Détails de l'Implémentation

### 1. Architecture de Traçage
Nous utilisons une instrumentation manuelle pour capturer des traces haute résolution de notre processus RAG. Chaque requête vers `/explain` génère une trace contenant plusieurs "Spans".

- **Helper** : [llm_observability.py](file:///Users/amaury/simplon-rag-sample/api/src/rag/api/llm_observability.py)

### 2. Spans Instrumentés
Conformément au brief, nous capturons :
- **`retrieval`** : Temps pris pour interroger la base vectorielle et nombre de fragments trouvés.
- **`prompt_build`** : Capture le prompt final envoyé au LLM.
- **`llm_call`** : Un span de type "Generation" capturant le nom du modèle, les tokens d'entrée et le contenu de sortie.

### 3. Confidentialité et Conformité (RGPD)
Pour protéger les données utilisateur :
1. **Pseudonymisation** : Le `user_id` fourni dans la requête est haché via SHA-256 avant d'être envoyé à Langfuse.
2. **Masquage de contenu** : Seul un extrait du contenu de l'email est stocké dans l'entrée du span de récupération pour permettre le débogage sans exposer de données personnelles (PII).

### 4. Suivi des coûts
Langfuse calcule automatiquement le coût de chaque requête en fonction du modèle et du nombre de tokens. Ces coûts sont exportés quotidiennement vers Prometheus via un job dédié : [export_langfuse_cost.py](file:///Users/amaury/simplon-rag-sample/api/src/rag/jobs/export_langfuse_cost.py).

## Vérification
1. Appelez l'endpoint `/explain`.
2. Connectez-vous à Langfuse sur `http://localhost:3000`.
3. Recherchez la trace `explain_email`. Vous devriez voir la hiérarchie des spans et le coût associé.
