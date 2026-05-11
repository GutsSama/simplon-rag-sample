import numpy as np
from scipy.stats import ks_2samp
from rag.api.metrics import MODEL_DRIFT_SCORE

# Reference distribution (example)
# spam: 0.3, non-spam: 0.6, phishing: 0.1
REFERENCE_DISTRIBUTION = [0.3, 0.6, 0.1]

def calculate_drift(current_predictions: list):
    """Calculate drift score using Kolmogorov-Smirnov test or similar."""
    if len(current_predictions) < 50:
        return 0.0
    
    # Simulating drift detection
    # In a real case, we would compare the frequency of each class
    # with the reference distribution.
    counts = np.bincount(current_predictions, minlength=3)
    current_dist = counts / len(current_predictions)
    
    # Simple drift score: sum of absolute differences
    drift_score = np.sum(np.abs(current_dist - REFERENCE_DISTRIBUTION))
    
    MODEL_DRIFT_SCORE.labels(model_version="1.0.0").set(drift_score)
    return drift_score
