import joblib
import os
from datetime import datetime

MODEL_PATH = "app/ml_models/artifacts/voting_ensemble.pkl"
SCALER_PATH = "app/ml_models/artifacts/scaler.pkl"
FEATURES_PATH = "app/ml_models/artifacts/features.pkl"

class AirPredictor:
    def __init__(self):
        self.model = joblib.load(MODEL_PATH)
        self.scaler = joblib.load(SCALER_PATH)
        self.features = joblib.load(FEATURES_PATH)
        self.threshold = 0.25

    def predict(self, feature_df):

        print("Running prediction...")

        print(f"Feature row:\n{feature_df.columns}")
  
        scaled_data = self.scaler.transform(feature_df)
        
        prob = self.model.predict_proba(scaled_data)[:, 1][0]
        
        is_hazard = bool(prob >= self.threshold)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] MODEL INFERENCE: Prob={prob:.4f} | Hazard={is_hazard}")
        
        return prob, is_hazard

    def get_advice(self, is_hazard):
        if is_hazard:
            return "HIGH RISK: Hazardous air predicted within 24h. Use N95 masks and limit outdoor activities."
        return "LOW RISK: Air quality is expected to remain within acceptable limits."