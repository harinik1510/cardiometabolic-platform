import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import pickle
import os

def create_synthetic_data(n_samples_per_class=500):
    np.random.seed(42)
    
    data_list = []
    
    for target_class in [0, 1, 2]: # 0: Low, 1: Moderate, 2: High
        count = 0
        while count < n_samples_per_class:
            # Generate random features
            age = np.random.randint(20, 80)
            gender = np.random.randint(0, 2)
            fbs = np.random.randint(70, 200)
            hba1c = np.random.uniform(4, 12)
            chol = np.random.randint(150, 300)
            ldl = np.random.randint(70, 200)
            hdl = np.random.randint(30, 80)
            trig = np.random.randint(100, 400)
            sys_bp = np.random.randint(100, 180)
            dia_bp = np.random.randint(60, 110)
            bmi = np.random.uniform(18, 40)
            creatinine = np.random.uniform(0.5, 2.5)
            smoking = np.random.randint(0, 2)
            alcohol = np.random.randint(0, 2)
            
            # Risk Scoring Logic (Must match the one in predict_risk or be the ground truth)
            risk_score = (
                (fbs > 126) * 2 + (hba1c > 6.5) * 2 + 
                (sys_bp > 140) * 2 + (bmi > 30) * 1 + 
                (ldl > 160) * 1 + (smoking == 1) * 1 +
                (age > 60) * 1
            )
            
            # Assign class based on score
            actual_class = 2 if risk_score >= 5 else (1 if risk_score >= 2 else 0)
            
            # Only keep if it matches our target class for this iteration
            if actual_class == target_class:
                data_list.append({
                    'age': age, 'gender': gender, 'fbs': fbs, 'hba1c': hba1c,
                    'chol': chol, 'ldl': ldl, 'hdl': hdl, 'trig': trig,
                    'sys_bp': sys_bp, 'dia_bp': dia_bp, 'bmi': bmi,
                    'creatinine': creatinine, 'smoking': smoking, 'alcohol': alcohol,
                    'target': actual_class
                })
                count += 1
                
    df = pd.DataFrame(data_list)
    # Shuffle the dataset
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    return df

def train_models():
    if not os.path.exists('models'):
        os.makedirs('models')
        
    df = create_synthetic_data()
    X = df.drop('target', axis=1)
    y = df['target']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Random Forest
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X_train, y_train)
    
    # Logistic Regression
    lr = LogisticRegression(max_iter=1000)
    lr.fit(X_train, y_train)
    
    # Save models
    with open('models/rf_model.pkl', 'wb') as f:
        pickle.dump(rf, f)
    with open('models/lr_model.pkl', 'wb') as f:
        pickle.dump(lr, f)
        
    print("Models trained and saved successfully.")

def predict_risk(data):
    # data should be a dictionary or list matching features
    # Convert to DataFrame
    df = pd.DataFrame([data])
    
    with open('models/rf_model.pkl', 'rb') as f:
        rf = pickle.load(f)
    with open('models/lr_model.pkl', 'rb') as f:
        lr = pickle.load(f)
        
    rf_pred = rf.predict(df)[0]
    lr_pred = lr.predict(df)[0]
    
    # Final prediction logic (e.g., take the higher risk if models disagree)
    final_pred = max(rf_pred, lr_pred)
    
    # Predicted Diseases Logic
    diseases = []
    if data['fbs'] > 126 or data['hba1c'] > 6.5: diseases.append('Type 2 Diabetes')
    if data['sys_bp'] > 140: diseases.append('Hypertension')
    if data['bmi'] > 30: diseases.append('Obesity')
    if data['ldl'] > 160 or data['chol'] > 240: diseases.append('Dyslipidemia')
    if data['hba1c'] > 5.7 and data['hba1c'] <= 6.5: diseases.append('Pre-diabetes')
    
    # Cardiovascular/Heart Disease Risk
    if data['chol'] > 200 or data['ldl'] > 130 or data['sys_bp'] > 130:
        diseases.append('Cardiovascular Disease Risk')
    
    if not diseases and final_pred > 0:
        diseases.append('Metabolic Syndrome (General)')
    elif not diseases:
        diseases.append('None Detected')

    # Calculate Contributors for Pie Chart (Core Factors Only)
    # Increased scaling to make the chart more responsive to high values
    contributors = {
        'Glucose': max(2, (data['fbs'] - 90) / 5 + (data['hba1c'] - 5.5) * 10),
        'Blood Pressure': max(2, (data['sys_bp'] - 110) / 3 + (data['dia_bp'] - 70) / 3),
        'BMI': max(2, (data['bmi'] - 20) * 8),
        'Cholesterol': max(2, (data['ldl'] - 90) / 5 + (data['chol'] - 180) / 10),
        'Lifestyle/Age': max(2, (data['age'] - 30) / 5 + (data['smoking'] + data['alcohol']) * 15)
    }

    risk_levels = {0: 'Low Risk', 1: 'Moderate Risk', 2: 'High Risk'}
    
    return {
        'rf_prediction': risk_levels[rf_pred],
        'lr_prediction': risk_levels[lr_pred],
        'rf_raw': int(rf_pred),
        'lr_raw': int(lr_pred),
        'final_prediction': risk_levels[final_pred],
        'final_raw': int(final_pred),
        'predicted_diseases': diseases,
        'risk_contributors': contributors
    }

if __name__ == '__main__':
    train_models()
