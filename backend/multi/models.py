import numpy as np
import pandas as pd
import joblib
import pickle
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
import logging
from datetime import datetime
import hashlib
import json
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    """Configuration for the stroke prediction model"""
    model_path: str = "models/stroke_model.pkl"
    scaler_path: str = "models/scaler.pkl"
    encoder_path: str = "models/encoder.pkl"
    risk_thresholds: Tuple[float, float] = (0.3, 0.7)  # Low: <0.3, Medium: 0.3-0.7, High: >0.7
    feature_columns: Tuple = (
        'age', 'bmi', 'hypertension_encoded', 'diabetes_encoded',
        'smoking_status_encoded', 'cholesterol_mg_dl'
    )
    categorical_mapping: Dict = None

class StrokeRiskPredictor:
    """Machine Learning model for stroke risk prediction"""
    
    _instance = None
    
    def __init__(self, config: ModelConfig = None):
        self.config = config or ModelConfig()
        self.model = None
        self.scaler = None
        self.encoder = None
        self.is_trained = False
        self._initialize_model()
    
    @classmethod
    def get_instance(cls):
        """Singleton pattern to get model instance"""
        if cls._instance is None:
            cls._instance = StrokeRiskPredictor()
        return cls._instance
    
    def _initialize_model(self):
        """Initialize or train the model"""
        try:
            # Try to load pre-trained model
            self._load_model()
            logger.info("✅ Pre-trained model loaded successfully")
        except FileNotFoundError:
            # Train new model if pre-trained doesn't exist
            logger.info("🔄 No pre-trained model found. Training new model...")
            self._train_model()
            self._save_model()
            logger.info("✅ Model trained and saved successfully")
        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
            raise
    
    def _load_model(self):
        """Load pre-trained model, scaler, and encoder"""
        models_dir = Path("models")
        models_dir.mkdir(exist_ok=True)
        
        # Load model
        with open(self.config.model_path, 'rb') as f:
            self.model = pickle.load(f)
        
        # Load scaler
        with open(self.config.scaler_path, 'rb') as f:
            self.scaler = pickle.load(f)
        
        # Load encoder
        with open(self.config.encoder_path, 'rb') as f:
            self.encoder = pickle.load(f)
        
        self.is_trained = True
    
    def _save_model(self):
        """Save model, scaler, and encoder"""
        models_dir = Path("models")
        models_dir.mkdir(exist_ok=True)
        
        # Save model
        with open(self.config.model_path, 'wb') as f:
            pickle.dump(self.model, f)
        
        # Save scaler
        with open(self.config.scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        # Save encoder
        with open(self.config.encoder_path, 'wb') as f:
            pickle.dump(self.encoder, f)
    
    def _train_model(self):
        """Train a stroke risk prediction model with synthetic data"""
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import StandardScaler, LabelEncoder
        from sklearn.model_selection import train_test_split
        
        # Generate synthetic training data
        np.random.seed(42)
        n_samples = 5000
        
        # Generate features
        age = np.random.normal(55, 15, n_samples).clip(18, 90)
        height = np.random.normal(170, 10, n_samples).clip(150, 200)
        weight = np.random.normal(75, 15, n_samples).clip(40, 150)
        bmi = weight / ((height / 100) ** 2)
        
        # Generate categorical features with realistic distributions
        hypertension = np.random.choice(['Yes', 'No'], n_samples, p=[0.3, 0.7])
        diabetes = np.random.choice(['Yes', 'No'], n_samples, p=[0.2, 0.8])
        smoking = np.random.choice(['Non-Smoker', 'Formerly Smoked', 'Smokes'], 
                                  n_samples, p=[0.5, 0.3, 0.2])
        cholesterol = np.random.normal(200, 40, n_samples).clip(100, 400)
        
        # Create target variable with realistic relationships
        stroke_risk_prob = (
            age * 0.02 +
            (hypertension == 'Yes') * 0.3 +
            (diabetes == 'Yes') * 0.25 +
            (smoking == 'Smokes') * 0.35 +
            (smoking == 'Formerly Smoked') * 0.15 +
            (cholesterol - 200) * 0.001 +
            np.where(bmi > 30, 0.2, 0) +
            np.random.normal(0, 0.1, n_samples)
        ).clip(0, 1)
        
        stroke_risk = (stroke_risk_prob > 0.5).astype(int)
        
        # Create DataFrame
        df = pd.DataFrame({
            'age': age,
            'height_cm': height,
            'weight_kg': weight,
            'bmi': bmi,
            'hypertension': hypertension,
            'diabetes': diabetes,
            'smoking_status': smoking,
            'cholesterol_mg_dl': cholesterol,
            'stroke_risk': stroke_risk
        })
        
        # Prepare features
        X = df[['age', 'bmi', 'hypertension', 'diabetes', 'smoking_status', 'cholesterol_mg_dl']].copy()
        y = df['stroke_risk']
        
        # Encode categorical variables
        self.encoder = {}
        categorical_cols = ['hypertension', 'diabetes', 'smoking_status']
        
        for col in categorical_cols:
            le = LabelEncoder()
            X[f'{col}_encoded'] = le.fit_transform(X[col])
            self.encoder[col] = le
        
        # Drop original categorical columns
        X = X[['age', 'bmi', 'hypertension_encoded', 'diabetes_encoded', 
               'smoking_status_encoded', 'cholesterol_mg_dl']]
        
        # Scale numerical features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            class_weight='balanced',
            random_state=42
        )
        
        self.model.fit(X_train, y_train)
        
        # Calculate training accuracy
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)
        
        logger.info(f"📊 Model trained - Train accuracy: {train_score:.3f}, Test accuracy: {test_score:.3f}")
        self.is_trained = True
    
    def _preprocess_features(self, df: pd.DataFrame) -> np.ndarray:
        """Preprocess input features for prediction"""
        # Calculate BMI
        df['bmi'] = df['weight_kg'] / ((df['height_cm'] / 100) ** 2)
        
        # Encode categorical variables
        df_processed = df.copy()
        for col, encoder in self.encoder.items():
            # Handle unseen categories
            df_processed[f'{col}_encoded'] = df_processed[col].apply(
                lambda x: encoder.transform([x])[0] if x in encoder.classes_ else -1
            )
        
        # Select features
        features = df_processed[self.config.feature_columns].copy()
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        return features_scaled
    
    def predict_single(self, patient_data: Dict) -> Dict:
        """Predict stroke risk for a single patient"""
        try:
            # Convert to DataFrame
            df = pd.DataFrame([patient_data])
            
            # Preprocess
            features = self._preprocess_features(df)
            
            # Predict
            probability = self.model.predict_proba(features)[0][1]
            prediction = self.model.predict(features)[0]
            
            # Determine risk level
            if probability < self.config.risk_thresholds[0]:
                risk_level = "Low"
            elif probability < self.config.risk_thresholds[1]:
                risk_level = "Medium"
            else:
                risk_level = "High"
            
            return {
                "stroke_risk": risk_level,
                "probability": float(probability),
                "prediction": int(prediction),
                "bmi": float(df['bmi'].iloc[0])
            }
            
        except Exception as e:
            logger.error(f"Error in single prediction: {e}")
            raise
    
    def predict_batch(self, df: pd.DataFrame) -> List[Dict]:
        """Predict stroke risk for multiple patients"""
        try:
            if not self.is_trained:
                raise ValueError("Model is not trained")
            
            # Preprocess
            features = self._preprocess_features(df)
            
            # Predict
            probabilities = self.model.predict_proba(features)[:, 1]
            predictions = self.model.predict(features)
            
            results = []
            for idx, (prob, pred) in enumerate(zip(probabilities, predictions)):
                # Determine risk level
                if prob < self.config.risk_thresholds[0]:
                    risk_level = "Low"
                elif prob < self.config.risk_thresholds[1]:
                    risk_level = "Medium"
                else:
                    risk_level = "High"
                
                # Calculate BMI for this patient
                bmi = df.iloc[idx]['weight_kg'] / ((df.iloc[idx]['height_cm'] / 100) ** 2)
                
                result = {
                    "age": int(df.iloc[idx]['age']),
                    "height_cm": float(df.iloc[idx]['height_cm']),
                    "weight_kg": float(df.iloc[idx]['weight_kg']),
                    "hypertension": str(df.iloc[idx]['hypertension']),
                    "diabetes": str(df.iloc[idx]['diabetes']),
                    "smoking_status": str(df.iloc[idx]['smoking_status']),
                    "cholesterol_mg_dl": float(df.iloc[idx]['cholesterol_mg_dl']),
                    "stroke_risk": risk_level,
                    "probability": float(prob),
                    "bmi": float(bmi)
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch prediction: {e}")
            raise
    
    def get_model_info(self) -> Dict:
        """Get information about the trained model"""
        if not self.model:
            return {"status": "Model not loaded"}
        
        return {
            "model_type": type(self.model).__name__,
            "is_trained": self.is_trained,
            "n_features": len(self.config.feature_columns),
            "risk_thresholds": self.config.risk_thresholds,
            "feature_importance": self._get_feature_importance()
        }
    
    def _get_feature_importance(self) -> Dict:
        """Get feature importance from the model"""
        if not hasattr(self.model, 'feature_importances_'):
            return {}
        
        importance = dict(zip(self.config.feature_columns, self.model.feature_importances_))
        return {k: float(v) for k, v in sorted(importance.items(), key=lambda x: x[1], reverse=True)}