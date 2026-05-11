# Observabilité : Logging Structuré et Traçage de Requête

## Aperçu
La Phase 1 de l'implémentation de l'observabilité se concentre sur la mise en place d'un format de log cohérent et interrogeable à travers tous les services, et sur l'établissement d'un moyen de corréler les logs appartenant à une même requête utilisateur.

## Détails de l'Implémentation

### 1. Logging Structuré JSON
Nous avons remplacé le logging standard par un format JSON utilisant `python-json-logger`. Cela permet aux systèmes d'agrégation de logs (comme ELK ou Grafana Loki) d'analyser les logs comme des données structurées.

- **Configuration** : [logging_config.py](file:///Users/amaury/simplon-rag-sample/api/src/rag/api/logging_config.py)
- **Champs inclus** :
  - `timestamp` : Format ISO8601 UTC.
  - `level` : Niveau de log (INFO, ERROR, etc.).
  - `name` : Nom du logger (généralement le nom du module).
  - `message` : Le message de log réel.
  - `request_id` : L'identifiant de corrélation pour la requête en cours.

### 2. Middleware Request ID
Un middleware FastAPI a été ajouté dans `app.py` pour garantir que chaque requête se voit attribuer un identifiant unique.

- **Logique** :
  1. Vérification de la présence de `X-Request-ID` dans les headers entrants.
  2. Si absent, génération d'un nouveau UUID.
  3. Stockage de l'ID dans une `ContextVar` pour un accès direct par le logger.
  4. Injection de l'ID dans les headers de la réponse sortante.
  5. Logging de la fin de requête avec sa durée et son code de statut.

### 3. Conformité RGPD
Le logger est configuré pour ne **jamais** enregistrer le contenu brut des emails. Seules les métadonnées (longueur de l'email, présence de pièces jointes, etc.) et les identifiants pseudonymisés sont autorisés dans les logs de production.

## Vérification
Pour vérifier le logging :
1. Lancez l'API.
2. Faites une requête sur `/api/v1/health`.
3. Vérifiez la sortie console. Vous devriez voir un objet JSON similaire à :
   ```json
   {"timestamp": "2026-05-11T14:00:00.000Z", "level": "INFO", "name": "rag.api.app", "message": "Request processed", "request_id": "550e8400-e29b-41d4-a716-446655440000", "method": "GET", "path": "/api/v1/health", "status_code": 200, "duration": 0.0012}
   ```
