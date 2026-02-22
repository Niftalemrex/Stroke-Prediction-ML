import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Optional
import logging
from datetime import datetime
import io

logger = logging.getLogger(__name__)

class DataPreprocessor:
    """Handles data preprocessing for stroke prediction"""
    
    REQUIRED_COLUMNS = [
        'age', 'height_cm', 'weight_kg', 'hypertension',
        'diabetes', 'smoking_status', 'cholesterol_mg_dl'
    ]
    
    COLUMN_DTYPES = {
        'age': 'int64',
        'height_cm': 'float64',
        'weight_kg': 'float64',
        'hypertension': 'object',
        'diabetes': 'object',
        'smoking_status': 'object',
        'cholesterol_mg_dl': 'float64'
    }
    
    VALID_VALUES = {
        'hypertension': ['Yes', 'No'],
        'diabetes': ['Yes', 'No'],
        'smoking_status': ['Non-Smoker', 'Formerly Smoked', 'Smokes']
    }
    
    def __init__(self):
        self.validation_errors = []
    
    def validate_file(self, file_content: bytes, file_type: str) -> Tuple[bool, List[str]]:
        """Validate uploaded file"""
        try:
            if file_type == 'excel':
                df = pd.read_excel(io.BytesIO(file_content))
            elif file_type == 'csv':
                df = pd.read_csv(io.BytesIO(file_content))
            else:
                return False, ["Unsupported file type"]
            
            return self.validate_dataframe(df)
            
        except Exception as e:
            logger.error(f"File validation error: {e}")
            return False, [f"Error reading file: {str(e)}"]
    
    def validate_dataframe(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate dataframe structure and content"""
        errors = []
        
        # Check required columns
        missing_cols = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns: {', '.join(missing_cols)}")
        
        # Check for empty dataframe
        if df.empty:
            errors.append("File is empty")
        
        # Check data types
        for col in self.REQUIRED_COLUMNS:
            if col in df.columns:
                try:
                    if col in ['age', 'height_cm', 'weight_kg', 'cholesterol_mg_dl']:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    else:
                        df[col] = df[col].astype(str).str.strip()
                except Exception as e:
                    errors.append(f"Invalid data type for column '{col}': {str(e)}")
        
        # Check for missing values
        for col in self.REQUIRED_COLUMNS:
            if col in df.columns:
                missing_count = df[col].isna().sum()
                if missing_count > 0:
                    errors.append(f"Column '{col}' has {missing_count} missing values")
        
        # Validate categorical values
        for col, valid_values in self.VALID_VALUES.items():
            if col in df.columns:
                invalid_values = df[~df[col].isin(valid_values)][col].unique()
                if len(invalid_values) > 0:
                    errors.append(
                        f"Column '{col}' contains invalid values: {invalid_values}. "
                        f"Valid values are: {valid_values}"
                    )
        
        # Validate numerical ranges
        if 'age' in df.columns:
            invalid_age = df[(df['age'] < 0) | (df['age'] > 120)]
            if not invalid_age.empty:
                errors.append(f"Age must be between 0 and 120 years")
        
        if 'height_cm' in df.columns:
            invalid_height = df[(df['height_cm'] < 50) | (df['height_cm'] > 250)]
            if not invalid_height.empty:
                errors.append(f"Height must be between 50cm and 250cm")
        
        if 'weight_kg' in df.columns:
            invalid_weight = df[(df['weight_kg'] < 10) | (df['weight_kg'] > 300)]
            if not invalid_weight.empty:
                errors.append(f"Weight must be between 10kg and 300kg")
        
        if 'cholesterol_mg_dl' in df.columns:
            invalid_chol = df[(df['cholesterol_mg_dl'] < 100) | (df['cholesterol_mg_dl'] > 500)]
            if not invalid_chol.empty:
                errors.append(f"Cholesterol must be between 100 and 500 mg/dL")
        
        return len(errors) == 0, errors
    
    def preprocess_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and preprocess the dataframe"""
        df_clean = df.copy()
        
        # Ensure required columns
        for col in self.REQUIRED_COLUMNS:
            if col not in df_clean.columns:
                raise ValueError(f"Required column '{col}' not found")
        
        # Convert data types
        df_clean['age'] = pd.to_numeric(df_clean['age'], errors='coerce').astype('int64')
        df_clean['height_cm'] = pd.to_numeric(df_clean['height_cm'], errors='coerce').astype('float64')
        df_clean['weight_kg'] = pd.to_numeric(df_clean['weight_kg'], errors='coerce').astype('float64')
        df_clean['cholesterol_mg_dl'] = pd.to_numeric(df_clean['cholesterol_mg_dl'], errors='coerce').astype('float64')
        
        # Clean categorical columns
        df_clean['hypertension'] = df_clean['hypertension'].astype(str).str.strip()
        df_clean['diabetes'] = df_clean['diabetes'].astype(str).str.strip()
        df_clean['smoking_status'] = df_clean['smoking_status'].astype(str).str.strip()
        
        # Standardize categorical values
        df_clean['hypertension'] = df_clean['hypertension'].apply(
            lambda x: 'Yes' if x.lower() in ['yes', 'y', 'true', '1'] else 'No'
        )
        df_clean['diabetes'] = df_clean['diabetes'].apply(
            lambda x: 'Yes' if x.lower() in ['yes', 'y', 'true', '1'] else 'No'
        )
        
        # Handle smoking status variations
        smoking_mapping = {
            'non-smoker': 'Non-Smoker',
            'non smoker': 'Non-Smoker',
            'never smoked': 'Non-Smoker',
            'former': 'Formerly Smoked',
            'formerly smoked': 'Formerly Smoked',
            'ex-smoker': 'Formerly Smoked',
            'smoker': 'Smokes',
            'smokes': 'Smokes',
            'current': 'Smokes'
        }
        
        df_clean['smoking_status'] = df_clean['smoking_status'].apply(
            lambda x: smoking_mapping.get(x.lower(), x) if isinstance(x, str) else x
        )
        
        # Remove rows with missing values
        initial_count = len(df_clean)
        df_clean = df_clean.dropna(subset=self.REQUIRED_COLUMNS)
        removed_count = initial_count - len(df_clean)
        
        if removed_count > 0:
            logger.warning(f"Removed {removed_count} rows with missing values")
        
        # Reset index
        df_clean = df_clean.reset_index(drop=True)
        
        return df_clean
    
    def create_sample_template(self) -> pd.DataFrame:
        """Create a sample template DataFrame"""
        sample_data = {
            'age': [45, 60, 35],
            'height_cm': [170.0, 165.0, 180.0],
            'weight_kg': [70.0, 80.0, 90.0],
            'hypertension': ['No', 'Yes', 'No'],
            'diabetes': ['No', 'Yes', 'No'],
            'smoking_status': ['Non-Smoker', 'Formerly Smoked', 'Smokes'],
            'cholesterol_mg_dl': [220.0, 240.0, 200.0]
        }
        
        return pd.DataFrame(sample_data)