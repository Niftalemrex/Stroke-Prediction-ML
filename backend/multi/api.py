from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Optional
import pandas as pd
import numpy as np
import io
import tempfile
import json
from datetime import datetime
import logging
import traceback
from pathlib import Path

from .schemas import (
    PatientData, SinglePredictionResponse, BatchPredictionResponse,
    BatchResult, ErrorResponse
)
from .models import StrokeRiskPredictor
from .preprocessing import DataPreprocessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize components
predictor = StrokeRiskPredictor.get_instance()
preprocessor = DataPreprocessor()

def get_predictor() -> StrokeRiskPredictor:
    """Dependency injection for predictor"""
    return predictor

def get_preprocessor() -> DataPreprocessor:
    """Dependency injection for preprocessor"""
    return preprocessor

@router.post("/predict", response_model=SinglePredictionResponse)
async def predict_single(
    patient_data: PatientData,
    predictor: StrokeRiskPredictor = Depends(get_predictor)
):
    """
    Predict stroke risk for a single patient
    """
    try:
        start_time = datetime.now()
        
        # Convert Pydantic model to dict
        patient_dict = patient_data.dict()
        
        # Make prediction
        prediction = predictor.predict_single(patient_dict)
        
        # Calculate BMI
        bmi = patient_dict['weight_kg'] / ((patient_dict['height_cm'] / 100) ** 2)
        
        # Create interpretation
        interpretation = create_interpretation(patient_dict, prediction)
        
        response = SinglePredictionResponse(
            patient_id=f"PAT{int(datetime.now().timestamp())}",
            **patient_dict,
            stroke_risk=prediction["stroke_risk"],
            probability=prediction["probability"],
            bmi=round(bmi, 2),
            interpretation=interpretation,
            timestamp=datetime.now()
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Single prediction completed in {processing_time:.3f}s")
        
        return response
        
    except Exception as e:
        logger.error(f"Single prediction error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )

@router.post("/predict-batch", response_model=BatchPredictionResponse)
async def predict_batch(
    file: UploadFile = File(...),
    predictor: StrokeRiskPredictor = Depends(get_predictor),
    preprocessor: DataPreprocessor = Depends(get_preprocessor)
):
    """
    Predict stroke risk for multiple patients from an Excel/CSV file
    """
    start_time = datetime.now()
    
    try:
        # Read file content
        content = await file.read()
        
        # Determine file type
        file_extension = file.filename.split('.')[-1].lower()
        file_type = 'excel' if file_extension in ['xlsx', 'xls'] else 'csv'
        
        # Validate file
        is_valid, errors = preprocessor.validate_file(content, file_type)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail={"errors": errors}
            )
        
        # Read and preprocess data
        if file_type == 'excel':
            df = pd.read_excel(io.BytesIO(content))
        else:
            df = pd.read_csv(io.BytesIO(content))
        
        # Clean and preprocess
        df_clean = preprocessor.preprocess_dataframe(df)
        
        if df_clean.empty:
            raise HTTPException(
                status_code=400,
                detail="No valid data found in file"
            )
        
        # Make predictions
        results = predictor.predict_batch(df_clean)
        
        # Create summary statistics
        summary = create_summary_statistics(results)
        
        # Create response
        response = BatchPredictionResponse(
            filename=file.filename,
            total_patients=len(df),
            processed_patients=len(results),
            failed_patients=len(df) - len(results),
            results=results,
            summary=summary,
            processing_time=(datetime.now() - start_time).total_seconds(),
            timestamp=datetime.now()
        )
        
        logger.info(f"Batch prediction completed: {len(results)} patients processed")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch processing failed: {str(e)}"
        )

@router.get("/download-template")
async def download_template():
    """
    Download a sample Excel template for batch predictions
    """
    try:
        # Create sample DataFrame
        df = preprocessor.create_sample_template()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            df.to_excel(tmp.name, index=False)
            tmp_path = tmp.name
        
        # Return file
        return FileResponse(
            tmp_path,
            filename="stroke_prediction_template.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        logger.error(f"Template download error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create template: {str(e)}"
        )

@router.post("/download-results")
async def download_results(
    results: List[BatchResult],
    background_tasks: BackgroundTasks
):
    """
    Download prediction results as Excel file
    """
    try:
        # Convert to DataFrame
        df = pd.DataFrame([r.dict() for r in results])
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            # Write to Excel with formatting
            with pd.ExcelWriter(tmp.name, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Predictions', index=False)
                
                # Get workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['Predictions']
                
                # Add some basic formatting
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 30)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            tmp_path = tmp.name
        
        # Schedule cleanup
        background_tasks.add_task(lambda: Path(tmp_path).unlink(missing_ok=True))
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"stroke_predictions_{timestamp}.xlsx"
        
        return FileResponse(
            tmp_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        logger.error(f"Results download error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create results file: {str(e)}"
        )

@router.get("/model-info")
async def get_model_info(predictor: StrokeRiskPredictor = Depends(get_predictor)):
    """
    Get information about the trained model
    """
    try:
        info = predictor.get_model_info()
        return {
            "model": info,
            "timestamp": datetime.now().isoformat(),
            "status": "ready"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get model info: {str(e)}"
        )

@router.get("/validate-format")
async def validate_format():
    """
    Get the required format for batch prediction files
    """
    return {
        "required_columns": preprocessor.REQUIRED_COLUMNS,
        "valid_values": preprocessor.VALID_VALUES,
        "data_types": preprocessor.COLUMN_DTYPES,
        "example": {
            "age": 45,
            "height_cm": 170.0,
            "weight_kg": 70.0,
            "hypertension": "No",
            "diabetes": "No",
            "smoking_status": "Non-Smoker",
            "cholesterol_mg_dl": 220.0
        }
    }

def create_interpretation(patient_data: dict, prediction: dict) -> str:
    """Create interpretation text for prediction"""
    risk_level = prediction["stroke_risk"]
    probability = prediction["probability"]
    
    interpretations = {
        "Low": f"Low stroke risk ({probability:.1%}). Maintain healthy lifestyle with regular exercise and balanced diet.",
        "Medium": f"Moderate stroke risk ({probability:.1%}). Consider consulting a healthcare provider for preventive measures.",
        "High": f"High stroke risk ({probability:.1%}). Urgent medical consultation recommended. Monitor blood pressure and cholesterol regularly."
    }
    
    return interpretations.get(risk_level, "Risk assessment completed.")

def create_summary_statistics(results: List[dict]) -> dict:
    """Create summary statistics from prediction results"""
    if not results:
        return {}
    
    # Count risk levels
    risk_counts = {"Low": 0, "Medium": 0, "High": 0}
    for result in results:
        risk_level = result.get("stroke_risk", "Low")
        if risk_level in risk_counts:
            risk_counts[risk_level] += 1
    
    # Calculate averages
    avg_age = np.mean([r.get("age", 0) for r in results])
    avg_bmi = np.mean([r.get("bmi", 0) for r in results if r.get("bmi")])
    avg_cholesterol = np.mean([r.get("cholesterol_mg_dl", 0) for r in results])
    avg_probability = np.mean([r.get("probability", 0) for r in results])
    
    # Find high-risk patients
    high_risk_patients = [
        {"age": r["age"], "probability": r["probability"]}
        for r in results if r.get("stroke_risk") == "High"
    ][:5]  # Top 5
    
    return {
        "risk_distribution": risk_counts,
        "averages": {
            "age": round(avg_age, 1),
            "bmi": round(avg_bmi, 2),
            "cholesterol": round(avg_cholesterol, 1),
            "probability": round(avg_probability, 3)
        },
        "high_risk_count": risk_counts["High"],
        "top_high_risk": high_risk_patients
    }