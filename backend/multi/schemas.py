from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal, Union
from datetime import datetime
import numpy as np

# Single prediction schemas
class PatientData(BaseModel):
    age: int = Field(..., ge=0, le=120, description="Patient age in years")
    height_cm: float = Field(..., gt=0, le=250, description="Height in centimeters")
    weight_kg: float = Field(..., gt=0, le=300, description="Weight in kilograms")
    hypertension: str = Field(..., pattern="^(Yes|No)$", description="Hypertension status")
    diabetes: str = Field(..., pattern="^(Yes|No)$", description="Diabetes status")
    smoking_status: str = Field(
        ...,
        pattern="^(Non-Smoker|Formerly Smoked|Smokes)$",
        description="Smoking status"
    )
    cholesterol_mg_dl: float = Field(..., gt=0, le=500, description="Cholesterol level in mg/dL")
    
    @validator('height_cm')
    def validate_height(cls, v):
        if v < 50 or v > 250:
            raise ValueError('Height must be between 50cm and 250cm')
        return v
    
    @validator('weight_kg')
    def validate_weight(cls, v):
        if v < 10 or v > 300:
            raise ValueError('Weight must be between 10kg and 300kg')
        return v

class SinglePredictionResponse(BaseModel):
    patient_id: Optional[str] = None
    age: int
    height_cm: float
    weight_kg: float
    hypertension: str
    diabetes: str
    smoking_status: str
    cholesterol_mg_dl: float
    stroke_risk: Literal["Low", "Medium", "High"]
    probability: float = Field(..., ge=0, le=1)
    bmi: float
    interpretation: str
    timestamp: datetime
    
    class Config:
        json_encoders = {
            np.float64: lambda v: float(v),
            np.float32: lambda v: float(v),
            np.int64: lambda v: int(v),
            np.int32: lambda v: int(v),
            datetime: lambda v: v.isoformat()
        }

# Batch prediction schemas
class BatchPredictionRequest(BaseModel):
    """Schema for batch prediction file upload"""
    file_type: Literal["excel", "csv"] = "excel"

class BatchResult(BaseModel):
    """Individual result within batch prediction"""
    age: int
    height_cm: float
    weight_kg: float
    hypertension: str
    diabetes: str
    smoking_status: str
    cholesterol_mg_dl: float
    stroke_risk: Literal["Low", "Medium", "High"]
    probability: Optional[float] = None
    bmi: Optional[float] = None
    
    class Config:
        json_encoders = {
            np.float64: lambda v: float(v) if v is not None else None,
            np.float32: lambda v: float(v) if v is not None else None,
        }

class BatchPredictionResponse(BaseModel):
    """Response schema for batch predictions"""
    filename: str
    total_patients: int
    processed_patients: int
    failed_patients: int
    results: List[BatchResult]
    summary: dict
    processing_time: float
    timestamp: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }