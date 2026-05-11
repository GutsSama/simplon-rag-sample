from fastapi import APIRouter
from pydantic import BaseModel, Field
import random
from rag.api.metrics import PREDICTION_DISTRIBUTION, PREDICTION_CONFIDENCE

router = APIRouter(prefix="/predict", tags=["ml"])

class PredictRequest(BaseModel):
    email_content: str = Field(..., description="The content of the email to classify")

class PredictResponse(BaseModel):
    prediction: str = Field(..., description="Classification result: spam, non-spam, or phishing")
    confidence: float = Field(..., description="Confidence score between 0 and 1")
    model_version: str = Field("1.0.0", description="Version of the model used")

@router.post("", response_model=PredictResponse)
async def predict(request: PredictRequest):
    # Simulating a scikit-learn model prediction
    # In a real scenario, we would load a joblib/pkl model here
    classes = ["spam", "non-spam", "phishing"]
    prediction = random.choice(classes)
    confidence = random.uniform(0.7, 0.99)
    model_version = "1.0.0"

    # Record ML metrics
    PREDICTION_DISTRIBUTION.labels(
        prediction_class=prediction, 
        model_version=model_version
    ).inc()
    PREDICTION_CONFIDENCE.labels(
        model_version=model_version
    ).observe(confidence)
    
    return PredictResponse(
        prediction=prediction,
        confidence=confidence,
        model_version=model_version
    )
