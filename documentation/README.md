# Documentation du projet

Index de la documentation technique, DevOps GCP, observabilité et guides opérationnels.

> Le [`README.md`](../README.md) à la racine reste le point d’entrée du dépôt (installation, usage, liens prod).

---

## Déploiement & CI/CD (GCP)

| Document | Description |
|----------|-------------|
| [GCP_DEPLOYMENT.md](GCP_DEPLOYMENT.md) | Rapport final déploiement (URLs, commandes, incidents) |
| [GCP_WIF_AND_CICD.md](GCP_WIF_AND_CICD.md) | Workload Identity Federation, IAM, GitHub Environments |
| [VALIDATION_CICD_WIF.md](VALIDATION_CICD_WIF.md) | Synthèse validation architecture CI/CD |
| [DEMO_CICD_10MIN.md](DEMO_CICD_10MIN.md) | Script de démo 10 min (Actions + console GCP) |
| [GCP_MIGRATION.md](GCP_MIGRATION.md) | Vue d’ensemble migration GCP |
| [GCP_MIGRATION_PHASE1.md](GCP_MIGRATION_PHASE1.md) | Phase 1 — Artifact Registry & Docker |
| [GCP_MIGRATION_PHASE2.md](GCP_MIGRATION_PHASE2.md) | Phase 2 — Cloud Run, SQL, secrets |
| [GCP_MIGRATION_FINAL.md](GCP_MIGRATION_FINAL.md) | Architecture production finale |
| [GCP_CLOUD_MONITORING.md](GCP_CLOUD_MONITORING.md) | Monitoring & alertes GCP |

Checklist opérationnelle : [`../scripts/DEPLOY_PHASE1.md`](../scripts/DEPLOY_PHASE1.md)

---

## Architecture & observabilité (local / stack complète)

| Document | Description |
|----------|-------------|
| [documentation.md](documentation.md) | Sommaire observabilité (Docker, Prometheus, Grafana, …) |
| [architecture-overview.md](architecture-overview.md) | Carte cognitive du système |
| [docker.md](docker.md) | Infrastructure Docker |
| [prometheus.md](prometheus.md) | Métriques |
| [grafana.md](grafana.md) | Dashboards |
| [loki.md](loki.md) | Logs |
| [langfuse.md](langfuse.md) | Tracing LLM |
| [ollama.md](ollama.md) | Inférence locale |
| [commands.md](commands.md) | Commandes CLI |
| [discord.md](discord.md) | Alerting Discord |
| [GAME_DAY.md](GAME_DAY.md) | Scénarios Game Day / chaos |

Runbooks : répertoire [`../runbooks/`](../runbooks/)

---

## Projet & contribution

| Document | Description |
|----------|-------------|
| [BRIEF.md](BRIEF.md) | Brief projet |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Guide de contribution |
| [CHANGELOG.md](CHANGELOG.md) | Historique des versions |

---

## Workflows GitHub

- [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) — Lint, tests, build Docker, Trivy (sans GCP)
- [`.github/workflows/cd.yml`](../.github/workflows/cd.yml) — Build, migration, déploiement Cloud Run (WIF)
