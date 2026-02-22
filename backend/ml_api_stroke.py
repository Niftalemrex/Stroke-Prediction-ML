# ml_api_stroke.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import joblib
import numpy as np
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Stroke Prediction API",
    description="AI-powered stroke risk prediction system",
    version="1.0.0"
)

# Add CORS middleware for React app - VERY PERMISSIVE FOR TESTING
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow ALL origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicitly list methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
)

# Load model and features
try:
    model = joblib.load("stroke_model.pkl")
    features = joblib.load("model_features.pkl")
    logger.info("✅ Model loaded successfully")
    logger.info(f"📊 Model features: {features}")
except Exception as e:
    logger.error(f"❌ Failed to load model: {e}")
    model = None
    features = []

# Request model - with height and weight for BMI calculation
class StrokePredictionRequest(BaseModel):
    age: int
    height: Optional[float] = None
    weight: Optional[float] = None
    bmi: Optional[float] = None
    hypertension: int
    diabetes: int
    smoking: int
    cholesterol: float

@app.get("/")
async def root():
    return {
        "message": "Stroke Prediction API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": [
            {"path": "/predict", "method": "POST", "description": "Predict stroke risk"},
            {"path": "/predict_stroke", "method": "POST", "description": "Predict stroke risk (legacy endpoint)"},
            {"path": "/health", "method": "GET", "description": "API health check"}
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy" if model else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "model_loaded": model is not None
    }

# Handle OPTIONS requests for CORS preflight
@app.options("/predict_stroke")
async def options_predict_stroke():
    """Handle OPTIONS request for CORS preflight"""
    return {
        "message": "CORS preflight successful",
        "allowed_methods": ["POST", "OPTIONS"],
        "allowed_headers": ["Content-Type", "Authorization"],
        "allow_credentials": True
    }

@app.options("/predict")
async def options_predict():
    """Handle OPTIONS request for CORS preflight"""
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
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Calculate BMI if height and weight are provided
        bmi = request.bmi
        if bmi is None and request.height is not None and request.weight is not None:
            if request.height > 0:
                bmi = request.weight / ((request.height / 100) ** 2)
                bmi = round(bmi, 1)
            else:
                raise HTTPException(status_code=400, detail="Height must be greater than 0")
        
        if bmi is None:
            raise HTTPException(status_code=400, detail="BMI must be provided or calculated from height/weight")
        
        # Validate inputs
        if request.age < 18 or request.age > 120:
            raise HTTPException(status_code=400, detail="Age must be between 18 and 120")
        
        if bmi < 10 or bmi > 60:
            raise HTTPException(status_code=400, detail="BMI must be between 10 and 60")
        
        if request.cholesterol < 100 or request.cholesterol > 500:
            raise HTTPException(status_code=400, detail="Cholesterol must be between 100 and 500 mg/dL")
        
        if request.hypertension not in [0, 1] or request.diabetes not in [0, 1] or request.smoking not in [0, 1]:
            raise HTTPException(status_code=400, detail="Medical conditions must be 0 or 1")
        
        # Prepare features in correct order
        input_features = [request.age, bmi, request.hypertension, 
                         request.diabetes, request.smoking, request.cholesterol]
        
        # Make prediction
        probability = model.predict_proba([input_features])[0][1]
        
        # Determine risk level
        if probability >= 0.7:
            risk_level = "Very High"
            color = "#dc2626"  # red-600
        elif probability >= 0.5:
            risk_level = "High"
            color = "#ea580c"  # orange-600
        elif probability >= 0.3:
            risk_level = "Moderate"
            color = "#ca8a04"  # yellow-600
        elif probability >= 0.15:
            risk_level = "Low"
            color = "#16a34a"  # green-600
        else:
            risk_level = "Very Low"
            color = "#15803d"  # green-700
        
        # Calculate risk score (0-100)
        risk_score = int(probability * 100)
        
        # Generate recommendations
        recommendations = []
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
        
        # Identify contributing factors
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
            "stroke_risk_probability": float(probability),
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
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

# Simple test endpoint for quick verification
@app.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify API is working"""
    return {
        "status": "API is working!",
        "timestamp": datetime.now().isoformat(),
        "model_loaded": model is not None
    }

# Test prediction endpoint
@app.post("/test-prediction")
async def test_prediction():
    """Test prediction with sample data"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Sample test data
        test_data = {
            "age": 55,
            "bmi": 28.5,
            "hypertension": 1,
            "diabetes": 0,
            "smoking": 1,
            "cholesterol": 220
        }
        
        # Prepare features
        input_features = [
            test_data["age"],
            test_data["bmi"],
            test_data["hypertension"],
            test_data["diabetes"],
            test_data["smoking"],
            test_data["cholesterol"]
        ]
        
        # Make prediction
        probability = model.predict_proba([input_features])[0][1]
        
        # Determine risk level
        if probability >= 0.6:
            risk_level = "High"
        elif probability >= 0.3:
            risk_level = "Moderate"
        else:
            risk_level = "Low"
        
        return {
            "test_data": test_data,
            "stroke_risk_probability": float(probability),
            "risk_level": risk_level,
            "message": "Test prediction successful"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)