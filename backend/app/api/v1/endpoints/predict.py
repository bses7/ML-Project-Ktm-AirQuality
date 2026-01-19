import pandas as pd
from fastapi import APIRouter, HTTPException
from app.services.predictor import AirPredictor
from app.services.feature_engineer import create_ml_feature_row_from_df 
from app.schemas.predictions import PredictionResponse 
import os 

router = APIRouter()
predictor = AirPredictor() 

@router.get("/latest", response_model=PredictionResponse)
async def get_latest_prediction():
    """
    Returns the hazard prediction based on the data fetched 
    automatically by the background scheduler.
    """
    try:
        history_path = os.path.join("app", "raw_data", "current_history.csv")
        try:
            history_df = pd.read_csv(history_path)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="History file not found. Wait for first fetch.")

        if len(history_df) < 25:
            raise HTTPException(status_code=400, detail="Not enough history yet to calculate lags.")

        feature_row = create_ml_feature_row_from_df(history_df, predictor.features)
        
        prob, is_hazard = predictor.predict(feature_row)
        advice = predictor.get_advice(is_hazard)
        
        return {
            "pm25_current": float(history_df.iloc[-1]['pm25']),
            "hazard_probability": round(float(prob), 4),
            "is_hazardous_upcoming": is_hazard,
            "health_advice": advice
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference Error: {str(e)}")

# You can keep your old POST method here too, if you want to allow 
# users to upload their own data for testing.