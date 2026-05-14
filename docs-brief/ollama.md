# Configuration Ollama Optimisée - MacBook M4 (Metal GPU)

> [!IMPORTANT]
> **Architecture Hybride** : Nous avons adopté une architecture hybride pour optimiser les performances d’inférence sur Apple Silicon.
> La stack d’observabilité complète reste orchestrée via Docker Compose, tandis qu’Ollama est exécuté directement sur l’hôte macOS afin de bénéficier de l’accélération GPU Metal.
> Lors des tests, l’exécution d’Ollama dans Docker Desktop utilisait uniquement le CPU via la VM Linux, entraînant des latences incompatibles avec un usage RAG interactif.

Ce guide détaille la configuration recommandée pour faire tourner des modèles de RAG (comme **Qwen 2.5 Coder 7B**) de manière optimale sur une puce Apple M4 en utilisant l'accélération Metal.

## 1. Choix du Modèle : Qwen 2.5 Coder 7B vs legal-fast

### Qwen 2.5 Coder 7B (Recommandé pour la logique RAG)

- **Pourquoi ?** C'est actuellement l'un des meilleurs modèles 7B au monde. Sa capacité à suivre des instructions complexes et à générer du JSON structuré est cruciale pour un pipeline RAG (extraction d'entités, routing, évaluation).
- **Performance M4 :** Très fluide. Sur un M4, vous devriez obtenir entre 40 et 60 tokens/sec en 4-bit ou 8-bit.
- **Usage :** Idéal si votre RAG nécessite une étape de réflexion ou de transformation de données.

### legal-fast:latest (3.4 GB)

- **Analyse :** La taille (3.4 GB) indique une quantification **Q4_K_M** (4-bit). C'est le compromis standard vitesse/précision.
- **Usage :** Si ce modèle est spécifiquement fine-tuné sur du droit français (ce que suggère le nom), il sera meilleur pour le vocabulaire juridique, mais potentiellement moins "intelligent" que Qwen 2.5 pour la logique pure du RAG.

---

## 2. Création d'un Modelfile Optimisé

Pour tirer le maximum du M4, créez un fichier nommé `Modelfile.m4` :

```dockerfile
FROM qwen2.5-coder:7b

# Configuration de la fenêtre de contexte (Crucial pour le RAG)
# Le M4 gère très bien 16k ou 32k selon votre RAM unifiée.
PARAMETER num_ctx 16384

# Température basse pour le RAG (évite les hallucinations)
PARAMETER temperature 0.1
PARAMETER top_p 0.9

# Forcer l'utilisation du GPU Metal pour toutes les couches
PARAMETER num_gpu -1

# Optimisation des threads pour les cœurs de performance du M4
# (Ajuster selon si vous avez un M4, M4 Pro ou M4 Max)
PARAMETER num_thread 8

# Message Système optimisé pour le RAG
SYSTEM """
Tu es un assistant expert en analyse de documents. 
Ta mission est de répondre uniquement en te basant sur le contexte fourni. 
Si l'information n'est pas dans le contexte, dis-le clairement. 
Sois concis, précis et professionnel.
"""
```

### Créer le modèle personnalisé

```bash
ollama create qwen-rag-m4 -f Modelfile.m4
```

---

## 3. Paramètres Système et Environnement

Ollama sur macOS utilise Metal par défaut, mais vous pouvez optimiser la gestion de la mémoire.

### Variables d'environnement (dans votre .zshrc ou .bashrc)

```bash
# Augmenter le timeout pour éviter que le modèle ne se décharge trop vite
export OLLAMA_KEEP_ALIVE=24h

# Si vous utilisez Docker pour l'API, assurez-vous d'utiliser l'adresse hôte
export OLLAMA_HOST=0.0.0.0
```

---

## 4. Vérification de l'Accélération GPU

Pour vérifier que votre MacBook M4 utilise bien le GPU Metal pendant l'inférence :

1. Lancez un prompt : `ollama run qwen-rag-m4 "Bonjour"`
2. Ouvrez un second terminal et tapez :

```bash
/usr/bin/top -o cpu
```

- Cherchez le processus `ollama` ou `ollama runner`.
- Si `%CPU` dépasse 100%, c'est que les cœurs CPU travaillent.
- Le plus fiable : Utilisez **Activity Monitor** (Moniteur d'activité), onglet **GPU History** (Fenêtre > Historique du GPU). Vous devriez voir un pic d'activité lors de la génération.

## 5. Pourquoi Qwen 2.5 Coder est top pour ton projet

1. **Context Window :** Supporte nativement jusqu'à 128k (bien que 16k-32k suffisent pour la plupart des RAG).
2. **Raisonnement :** Il surclasse Llama 3 8B sur presque tous les benchmarks de logique.
3. **JSON :** Il suit parfaitement les schémas JSON, ce qui facilitera l'intégration avec ton backend FastAPI.

---

## 6. Commandes Utiles pour le Projet

Voici les commandes indispensables pour gérer Ollama au quotidien dans ton projet :

### Gestion des Modèles

```bash
# Lister les modèles téléchargés
ollama list

# Voir quel modèle est actuellement chargé en mémoire GPU
ollama ps

# Supprimer un modèle pour libérer de l'espace
ollama rm legal-fast:latest
```

### Tests et Debugging

```bash
# Tester le modèle en ligne de commande (interactif)
ollama run qwen-rag-m4

# Consulter les logs du serveur Ollama (utile si l'API ne répond pas)
tail -f ~/.ollama/logs/server.log
```

### Utilisation de l'API (Simuler le backend)

Si ton API FastAPI a du mal à communiquer avec Ollama, teste directement avec `curl` :

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "qwen-rag-m4",
  "prompt": "Explique-moi brièvement ce qu est le RAG.",
  "stream": false
}'
```

### Maintenance

Si Ollama semble bloqué ou ne libère pas la VRAM du M4 :

1. Clique sur l'icône Ollama dans la barre de menu (haut de l'écran).
2. Sélectionne **Quit Ollama**.
3. Relance l'application.
