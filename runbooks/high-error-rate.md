# Runbook: High 5xx Error Rate

## Symptoms
- Alert `HighErrorRate` is firing.
- Users report failures and 500 Internal Server Errors.
- Taux d'erreur > 5%.

## Diagnosis
1. Check the `mailguard-api` logs for tracebacks: `docker-compose logs api`.
2. Verify connectivity to Postgres: `docker-compose exec api pg_isready -h postgres`.
3. Check for external API failures (Mistral/OpenAI).
4. Verify if the database is out of disk space or connections.

## Mitigation
- Restart the API and database: `docker-compose restart api postgres`.
- Check and fix the specific error identified in the logs.
- If it's a Mistral/OpenAI outage, notify the status to the CTO.
