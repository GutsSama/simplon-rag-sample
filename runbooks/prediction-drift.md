# Runbook: Prediction Drift Detected

## Symptoms
- Alert `ModelDriftDetected` is firing.
- `ml_model_drift_score` > 0.1.
- The distribution of predictions has changed significantly compared to the baseline.

## Diagnosis
1. Check the Grafana "ML Drift" panel to see which class is drifting.
2. Compare current prediction distribution with historical data.
3. Verify if there is a change in the input data (e.g., a new type of spam campaign).

## Mitigation
- Trigger a model retraining with the latest data.
- Re-evaluate the model's performance on a fresh test set.
- Check if the preprocessing logic was changed recently.
