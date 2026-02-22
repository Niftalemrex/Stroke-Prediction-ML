import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns

# Set style for better visualizations
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def generate_realistic_stroke_data(n_samples=10000):
    """
    Generate realistic stroke prediction dataset with medical correlations
    """
    np.random.seed(42)
    
    # Age distribution - higher risk for older ages
    age = np.random.normal(55, 15, n_samples).astype(int)
    age = np.clip(age, 18, 90)
    
    # Height and Weight with correlation
    height = np.random.normal(170, 10, n_samples).astype(int)
    height = np.clip(height, 150, 200)
    
    # Weight correlated with height (BMI calculation)
    weight = np.random.normal(75, 15, n_samples)
    weight = np.clip(weight, 45, 120)
    
    # Calculate BMI
    bmi = np.round(weight / ((height / 100) ** 2), 1)
    
    # Medical conditions with age correlation
    # Hypertension probability increases with age
    hypertension_prob = 0.1 + 0.005 * (age - 40).clip(0)
    hypertension = (np.random.random(n_samples) < hypertension_prob).astype(int)
    
    # Diabetes probability increases with age and BMI
    diabetes_prob = 0.05 + 0.003 * (age - 40).clip(0) + 0.002 * (bmi - 25).clip(0)
    diabetes = (np.random.random(n_samples) < diabetes_prob).astype(int)
    
    # Smoking with age correlation (younger people smoke more)
    smoking_prob = 0.25 - 0.003 * (age - 30).clip(0)
    smoking = (np.random.random(n_samples) < smoking_prob).astype(int)
    
    # Cholesterol with age and weight correlation
    cholesterol_base = np.random.normal(200, 30, n_samples)
    cholesterol_age_effect = (age - 40).clip(0) * 0.5
    cholesterol_bmi_effect = (bmi - 25).clip(0) * 2
    cholesterol = cholesterol_base + cholesterol_age_effect + cholesterol_bmi_effect
    cholesterol = np.clip(cholesterol, 150, 350).astype(int)
    
    # Blood pressure (systolic) - correlated with age and hypertension
    blood_pressure = np.random.normal(120, 15, n_samples)
    blood_pressure += hypertension * 20 + (age - 50).clip(0) * 0.3
    blood_pressure = np.clip(blood_pressure, 90, 200).astype(int)
    
    # Heart rate
    heart_rate = np.random.normal(75, 10, n_samples)
    heart_rate = np.clip(heart_rate, 50, 120).astype(int)
    
    # Family history of stroke
    family_history = (np.random.random(n_samples) < 0.15).astype(int)
    
    # Physical activity (hours per week)
    physical_activity = np.random.exponential(5, n_samples)
    physical_activity = np.clip(physical_activity, 0, 20).round(1)
    
    # Stress level (0-10 scale)
    stress_level = np.random.beta(2, 3, n_samples) * 10
    stress_level = stress_level.round(1)
    
    # Create comprehensive stroke risk score
    risk_score = (
        (age - 40).clip(0) * 0.05 +          # Age factor
        (bmi - 25).clip(0) * 0.1 +           # BMI factor
        hypertension * 0.8 +                  # Hypertension
        diabetes * 0.7 +                      # Diabetes
        smoking * 0.6 +                       # Smoking
        (cholesterol > 240) * 0.5 +           # High cholesterol
        (blood_pressure > 140) * 0.4 +        # High BP
        family_history * 0.3 +                # Family history
        (physical_activity < 2.5) * 0.2 +     # Low activity
        (stress_level > 6) * 0.1              # High stress
    )
    
    # Normalize risk score and apply sigmoid
    risk_score_normalized = risk_score / risk_score.max()
    stroke_probability = 1 / (1 + np.exp(-10 * (risk_score_normalized - 0.5)))
    
    # Generate stroke risk labels based on probability
    stroke_risk = (np.random.random(n_samples) < stroke_probability).astype(int)
    
    # Create DataFrame
    df = pd.DataFrame({
        'age': age,
        'bmi': bmi,
        'hypertension': hypertension,
        'diabetes': diabetes,
        'smoking': smoking,
        'cholesterol': cholesterol,
        'blood_pressure': blood_pressure,
        'heart_rate': heart_rate,
        'family_history': family_history,
        'physical_activity': physical_activity,
        'stress_level': stress_level,
        'stroke_risk': stroke_risk
    })
    
    return df

def train_and_evaluate_model(df, use_extended_features=False):
    """
    Train and evaluate the stroke prediction model
    """
    print("🧠 Training Stroke Prediction Model...")
    
    # Select features
    if use_extended_features:
        features = ['age', 'bmi', 'hypertension', 'diabetes', 'smoking', 
                   'cholesterol', 'blood_pressure', 'heart_rate', 
                   'family_history', 'physical_activity', 'stress_level']
    else:
        features = ['age', 'bmi', 'hypertension', 'diabetes', 'smoking', 'cholesterol']
    
    X = df[features]
    y = df['stroke_risk']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"📊 Dataset Info:")
    print(f"   Total samples: {len(df)}")
    print(f"   Stroke cases: {y.sum()} ({y.mean()*100:.1f}%)")
    print(f"   Non-stroke cases: {len(df) - y.sum()}")
    print(f"   Features used: {len(features)}")
    print(f"   Train samples: {len(X_train)}")
    print(f"   Test samples: {len(X_test)}")
    
    # Train Random Forest with optimized parameters
    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=15,
        min_samples_split=10,
        min_samples_leaf=4,
        max_features='sqrt',
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'
    )
    
    model.fit(X_train, y_train)
    
    # Predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    
    print("\n📈 Model Performance:")
    print(f"   Accuracy: {accuracy:.4f}")
    print(f"   Precision: {precision:.4f}")
    print(f"   Recall: {recall:.4f}")
    print(f"   F1 Score: {f1:.4f}")
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': features,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n🎯 Feature Importance:")
    for _, row in feature_importance.iterrows():
        print(f"   {row['feature']}: {row['importance']:.4f}")
    
    # Save model
    joblib.dump(model, "stroke_model.pkl")
    print(f"\n💾 Model saved as 'stroke_model.pkl'")
    
    # Save feature names
    joblib.dump(features, "model_features.pkl")
    
    # Generate detailed report
    generate_model_report(model, X_test, y_test, y_pred, y_pred_proba, feature_importance)
    
    return model, X_test, y_test, y_pred, feature_importance

def generate_model_report(model, X_test, y_test, y_pred, y_pred_proba, feature_importance):
    """
    Generate comprehensive model evaluation report with visualizations
    """
    print("\n📋 Generating Model Report...")
    
    # Create directory for reports
    import os
    os.makedirs('reports', exist_ok=True)
    
    # 1. Classification Report
    report = classification_report(y_test, y_pred, output_dict=True)
    report_df = pd.DataFrame(report).transpose()
    report_df.to_csv('reports/classification_report.csv')
    
    # 2. Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['No Stroke', 'Stroke'],
                yticklabels=['No Stroke', 'Stroke'])
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig('reports/confusion_matrix.png', dpi=300)
    plt.close()
    
    # 3. Feature Importance Plot
    plt.figure(figsize=(10, 6))
    sns.barplot(data=feature_importance, x='importance', y='feature')
    plt.title('Feature Importance in Stroke Prediction')
    plt.xlabel('Importance')
    plt.ylabel('Feature')
    plt.tight_layout()
    plt.savefig('reports/feature_importance.png', dpi=300)
    plt.close()
    
    # 4. ROC Curve
    from sklearn.metrics import roc_curve, auc
    fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
    roc_auc = auc(fpr, tpr)
    
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, 
             label=f'ROC curve (AUC = {roc_auc:.2f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic (ROC) Curve')
    plt.legend(loc="lower right")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('reports/roc_curve.png', dpi=300)
    plt.close()
    
    # 5. Probability Distribution
    plt.figure(figsize=(10, 6))
    plt.hist(y_pred_proba[y_test == 0], bins=30, alpha=0.5, label='No Stroke', color='blue')
    plt.hist(y_pred_proba[y_test == 1], bins=30, alpha=0.5, label='Stroke', color='red')
    plt.title('Predicted Probability Distribution')
    plt.xlabel('Predicted Probability of Stroke')
    plt.ylabel('Frequency')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('reports/probability_distribution.png', dpi=300)
    plt.close()
    
    print("📊 Reports and visualizations saved in 'reports/' directory")

def create_sample_api_test():
    """
    Create sample test data for API testing
    """
    sample_data = {
        "low_risk_patient": {
            "age": 35,
            "bmi": 22.5,
            "hypertension": 0,
            "diabetes": 0,
            "smoking": 0,
            "cholesterol": 180
        },
        "moderate_risk_patient": {
            "age": 55,
            "bmi": 28.5,
            "hypertension": 1,
            "diabetes": 0,
            "smoking": 1,
            "cholesterol": 220
        },
        "high_risk_patient": {
            "age": 68,
            "bmi": 32.0,
            "hypertension": 1,
            "diabetes": 1,
            "smoking": 1,
            "cholesterol": 280
        }
    }
    
    import json
    with open('sample_test_cases.json', 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    print("📝 Sample test cases saved to 'sample_test_cases.json'")

if __name__ == "__main__":
    # Generate realistic dataset
    print("🔄 Generating realistic stroke prediction dataset...")
    df = generate_realistic_stroke_data(10000)
    
    # Save dataset for reference
    df.to_csv('stroke_dataset.csv', index=False)
    print("💾 Dataset saved as 'stroke_dataset.csv'")
    
    # Display dataset info
    print(f"\n📊 Dataset Shape: {df.shape}")
    print(f"📈 Stroke Rate: {df['stroke_risk'].mean()*100:.2f}%")
    
    # Train model
    model, X_test, y_test, y_pred, feature_importance = train_and_evaluate_model(
        df, 
        use_extended_features=False  # Set to True for more features
    )
    
    # Create sample test cases
    create_sample_api_test()
    
    print("\n" + "="*50)
    print("✅ Stroke Prediction Model Training Complete!")
    print("="*50)
    print("\n📁 Files Created:")
    print("   - stroke_model.pkl (Trained model)")
    print("   - model_features.pkl (Feature names)")
    print("   - stroke_dataset.csv (Training data)")
    print("   - sample_test_cases.json (API test cases)")
    print("   - reports/ (Performance metrics and visualizations)")
    
    print("\n🚀 Next Steps:")
    print("   1. Start the FastAPI server: uvicorn ml_api_stroke:app --reload")
    print("   2. Test the API with sample_test_cases.json")
    print("   3. Integrate with your React application")