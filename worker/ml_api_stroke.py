# ml_api_stroke.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging
import math
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Stroke Prediction API",
    description="AI-powered stroke risk prediction system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ---------- Model / risk score function ----------
# Try to load the real model; if it fails, use the formula
model = None
features = []
use_fallback = False

try:
    import joblib
    import numpy as np
    model = joblib.load("stroke_model.pkl")
    model.n_jobs = 1  # avoid multiprocessing issues
    features = joblib.load("model_features.pkl")
    logger.info("✅ Model loaded successfully")
    logger.info(f"📊 Model features: {features}")
except Exception as e:
    logger.warning(f"⚠️ Could not load model: {e}")
    logger.info("Using fallback risk score formula")
    use_fallback = True

def calculate_risk_score(age: int, bmi: float, hypertension: int, diabetes: int,
                         smoking: int, cholesterol: float) -> float:
    """
    Compute a risk score using the same logic as your training script.
    Returns a raw score that will be converted to a probability.
    """
    score = 0.0
    # Age factor (higher risk above 40)
    score += max(0, age - 40) * 0.05
    # BMI factor (higher risk above 25)
    score += max(0, bmi - 25) * 0.1
    # Medical conditions
    score += hypertension * 0.8
    score += diabetes * 0.7
    score += smoking * 0.6
    # High cholesterol (>240)
    if cholesterol > 240:
        score += 0.5
    return score

def sigmoid(x: float) -> float:
    """Sigmoid function to convert raw score to probability."""
    return 1 / (1 + math.exp(-10 * (x - 0.5)))

# ---------- Request model ----------
class StrokePredictionRequest(BaseModel):
    age: int
    height: Optional[float] = None
    weight: Optional[float] = None
    bmi: Optional[float] = None
    hypertension: int
    diabetes: int
    smoking: int
    cholesterol: float

# ---------- Helper to get prediction ----------
def get_prediction_probability(age: int, bmi: float, hypertension: int,
                               diabetes: int, smoking: int, cholesterol: float) -> float:
    if use_fallback or model is None:
        raw = calculate_risk_score(age, bmi, hypertension, diabetes, smoking, cholesterol)
        # Scale raw score to roughly [0,1] – you can adjust the divisor
        prob = sigmoid(raw / 10)
        return prob
    else:
        # Use the real ML model
        input_features = [[age, bmi, hypertension, diabetes, smoking, cholesterol]]
        prob = model.predict_proba(input_features)[0][1]
        return float(prob)

# ---------- Endpoints ----------
@app.get("/")
async def root():
    return {
        "message": "Stroke Prediction API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": [
            {"path": "/predict", "method": "POST", "description": "Predict stroke risk"},
            {"path": "/predict_stroke", "method": "POST", "description": "Predict stroke risk (legacy)"},
            {"path": "/health", "method": "GET", "description": "API health check"}
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model_loaded": not use_fallback,
        "using_fallback": use_fallback
    }

@app.options("/predict_stroke")
async def options_predict_stroke():
    return {
        "message": "CORS preflight successful",
        "allowed_methods": ["POST", "OPTIONS"],
        "allowed_headers": ["Content-Type", "Authorization"],
        "allow_credentials": True
    }

@app.options("/predict")
async def options_predict():
    return {
        "message": "CORS preflight successful",
        "allowed_methods": ["POST", "OPTIONS"],
        "allowed_headers": ["Content-Type", "Authorization"],
        "allow_credentials": True
    }

@app.post("/predict")
async def predict_stroke(request: StrokePredictionRequest):
    return await predict_stroke_endpoint(request)

@app.post("/predict_stroke")
async def predict_stroke_legacy(request: StrokePredictionRequest):
    return await predict_stroke_endpoint(request)

async def predict_stroke_endpoint(request: StrokePredictionRequest):
    logger.info("📥 Received prediction request")
    try:
        # BMI calculation (same as before)
        bmi = request.bmi
        if bmi is None and request.height is not None and request.weight is not None:
            if request.height > 0:
                bmi = request.weight / ((request.height / 100) ** 2)
                bmi = round(bmi, 1)
            else:
                raise HTTPException(status_code=400, detail="Height must be greater than 0")
        if bmi is None:
            raise HTTPException(status_code=400, detail="BMI must be provided or calculated from height/weight")
        
        # Validation (same as before)
        if request.age < 18 or request.age > 120:
            raise HTTPException(status_code=400, detail="Age must be between 18 and 120")
        if bmi < 10 or bmi > 60:
            raise HTTPException(status_code=400, detail="BMI must be between 10 and 60")
        if request.cholesterol < 100 or request.cholesterol > 500:
            raise HTTPException(status_code=400, detail="Cholesterol must be between 100 and 500 mg/dL")
        if request.hypertension not in [0,1] or request.diabetes not in [0,1] or request.smoking not in [0,1]:
            raise HTTPException(status_code=400, detail="Medical conditions must be 0 or 1")
        
        # Get probability
        probability = get_prediction_probability(
            request.age, bmi, request.hypertension,
            request.diabetes, request.smoking, request.cholesterol
        )
        
        # Determine risk level (identical to before)
        if probability >= 0.7:
            risk_level = "Very High"
            color = "#dc2626"
        elif probability >= 0.5:
            risk_level = "High"
            color = "#ea580c"
        elif probability >= 0.3:
            risk_level = "Moderate"
            color = "#ca8a04"
        elif probability >= 0.15:
            risk_level = "Low"
            color = "#16a34a"
        else:
            risk_level = "Very Low"
            color = "#15803d"
        
        risk_score = int(probability * 100)
        
        # Recommendations (same)
        if risk_level in ["High", "Very High"]:
            recommendations = [
                "Immediate consultation with a healthcare provider is recommended",
                "Regular monitoring of blood pressure and cholesterol levels",
                "Consider lifestyle changes: healthy diet, regular exercise"
            ]
        elif risk_level == "Moderate":
            recommendations = [
                "Schedule a check-up with your primary care physician",
                "Monitor key health metrics regularly",
                "Consider preventive lifestyle changes"
            ]
        else:
            recommendations = [
                "Maintain current healthy lifestyle habits",
                "Regular health check-ups are still recommended",
                "Continue preventive care measures"
            ]
        
        # Contributing factors (same)
        factors = []
        if request.age > 60:
            factors.append("Age (higher risk above 60)")
        if bmi >= 30:
            factors.append("Obesity (BMI ≥ 30)")
        elif bmi >= 25:
            factors.append("Overweight (BMI ≥ 25)")
        if request.hypertension == 1:
            factors.append("Hypertension")
        if request.diabetes == 1:
            factors.append("Diabetes")
        if request.smoking == 1:
            factors.append("Smoking")
        if request.cholesterol > 240:
            factors.append("High Cholesterol (>240 mg/dL)")
        
        return {
            "success": True,
            "stroke_risk_probability": probability,
            "risk_level": risk_level,
            "risk_color": color,
            "risk_score": risk_score,
            "bmi": bmi,
            "factors": factors,
            "recommendations": recommendations,
            "interpretation": f"Based on the provided data, there is a {probability:.1%} probability of stroke risk, which is classified as {risk_level}.",
            "timestamp": datetime.now().isoformat(),
            "input_data": {
                "age": request.age,
                "bmi": bmi,
                "hypertension": "Yes" if request.hypertension == 1 else "No",
                "diabetes": "Yes" if request.diabetes == 1 else "No",
                "smoking": "Yes" if request.smoking == 1 else "No",
                "cholesterol": request.cholesterol
            }
        }
    except Exception as e:
        logger.error(f"❌ Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.get("/test")
async def test_endpoint():
    return {
        "status": "API is working!",
        "timestamp": datetime.now().isoformat(),
        "model_loaded": not use_fallback,
        "using_fallback": use_fallback
    }

@app.post("/test-prediction")
async def test_prediction():
    try:
        test_data = {
            "age": 55,
            "bmi": 28.5,
            "hypertension": 1,
            "diabetes": 0,
            "smoking": 1,
            "cholesterol": 220
        }
        prob = get_prediction_probability(
            test_data["age"], test_data["bmi"],
            test_data["hypertension"], test_data["diabetes"],
            test_data["smoking"], test_data["cholesterol"]
        )
        if prob >= 0.6:
            risk = "High"
        elif prob >= 0.3:
            risk = "Moderate"
        else:
            risk = "Low"
        return {
            "test_data": test_data,
            "stroke_risk_probability": prob,
            "risk_level": risk,
            "message": "Test prediction successful"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

# ---------- Cloudflare Worker entrypoint (only used when deployed) ----------
# This part is ignored when running locally with uvicorn.
# On Cloudflare, the environment sets a special variable, so we can conditionally include it.
if 'WORKERS_RS_VERSION' in sys.modules or 'PYODIDE' in sys.modules:
    try:
        from asgi import WsgiAsgi
        from worker import WorkerEntrypoint

        class Default(WorkerEntrypoint):
            async def fetch(self, request):
                asgi_app = WsgiAsgi(app)
                return await asgi_app(request.js_object, self.env)
    except ImportError:
        pass  # Not in Cloudflare environment, ignore

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)