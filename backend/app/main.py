import uvicorn
import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from app.api.v1.endpoints import predict
from app.services.data_fetcher import update_database_and_predict
from app.utils.converters import calculate_pm25_aqi
from app.api.v1.endpoints.predict import get_latest_prediction
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware
from app.schemas.predictions import (
    DashboardResponse,
    HistoricalDataPoint,
    AQIDistributionPoint
)
from typing import List
from app.services.email_service import send_aqi_alert
import os

last_alert_sent = {"timestamp": None, "aqi": 0}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Kathmandu Air Guard API...")
    
    scheduler = BackgroundScheduler()
    
    def hourly_task():
        asyncio.run(update_database_and_predict())
       
    def alert_check_task():
        asyncio.run(check_and_send_alert())
    
    scheduler.add_job(hourly_task, 'cron', minute=0)
    scheduler.add_job(alert_check_task, 'cron', hour=18, minute=0)
    scheduler.start()
    
    try:
        await update_database_and_predict()
        await check_and_send_alert()
    except Exception as e:
        print(f"Initial data fetch failed: {e}")
    
    yield  
    
    print("Shutting down scheduler...")
    scheduler.shutdown()

async def check_and_send_alert():
    """Check AQI and send email if threshold exceeded"""
    try:
        history_df = pd.read_csv("app/raw_data/current_history.csv")
        latest_raw = history_df.iloc[-1]
        aqi_val = calculate_pm25_aqi(latest_raw['pm25'])
        
        if aqi_val > 120:
            current_time = pd.Timestamp.now()
            
            if (last_alert_sent["timestamp"] is None or 
                (current_time - last_alert_sent["timestamp"]).total_seconds() > 10800):  # 3 hours
                
                recipient = os.getenv("ALERT_EMAIL", "your-email@example.com")
                
                success = await send_aqi_alert(
                    aqi_value=aqi_val,
                    pm25=latest_raw['pm25'],
                    recipient_email=recipient
                )
                
                if success:
                    last_alert_sent["timestamp"] = current_time
                    last_alert_sent["aqi"] = aqi_val
                    
    except Exception as e:
        print(f"Error checking AQI for alerts: {e}")

app = FastAPI(
    title="Kathmandu Air Guard API",
    lifespan=lifespan,
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.include_router(predict.router, prefix="/api/v1/predict", tags=["Prediction"])

@app.get("/")
async def root():
    return {"message": "Swaastha-Ktm API is Online", "docs": "/docs"}

@app.get("/api/dashboard", response_model=DashboardResponse)
async def get_dashboard_data():
    prediction = await get_latest_prediction()
    
    history_df = pd.read_csv("app/raw_data/current_history.csv")
    latest_raw = history_df.iloc[-1]
    
    aqi_val = calculate_pm25_aqi(latest_raw['pm25'])
    
    hazard_str = "High" if prediction['is_hazardous_upcoming'] else "Low"
    
    recommendations = [prediction['health_advice']]
    if aqi_val > 150:
        recommendations.append("Limit all outdoor physical activity.")
        recommendations.append("Keep all windows closed to prevent smog entry.")

    return {
        "aqi": aqi_val,
        "pm25": latest_raw['pm25'],
        "pm10": latest_raw.get('pm10', latest_raw['pm25'] * 1.2), 
        "humidity": latest_raw['humidity'],
        "visibility": latest_raw['visibility'],
        "timestamp": str(latest_raw['timestamp']),
        "hazard_level": hazard_str,
        "health_recommendations": recommendations,
        "last_updated": latest_raw['timestamp']
    }

@app.get("/api/historical", response_model=List[HistoricalDataPoint])
async def get_historical_data():
    """
    Returns the last 24 hours of historical data for visualization
    """
    try:
        history_df = pd.read_csv("app/raw_data/current_history.csv")
        
        history_df = history_df.tail(24)
        
        history_df['aqi'] = history_df['pm25'].apply(calculate_pm25_aqi)
        
        historical_data = []
        for _, row in history_df.iterrows():
            historical_data.append({
                "timestamp": str(row['timestamp']),
                "pm25": float(row['pm25']),
                "temp": float(row.get('temp', 0)),
                "humidity": float(row.get('humidity', 0)),
                "windspeed": float(row.get('windspeed', 0)),
                "aqi": int(row['aqi'])
            })
        
        return historical_data
    except Exception as e:
        print(f"Error fetching historical data: {e}")
        return []

@app.get("/api/aqi-distribution", response_model=List[AQIDistributionPoint])
async def get_aqi_distribution():
    """
    Returns average AQI by hour of day to show pollution patterns
    """
    try:
        history_df = pd.read_csv("app/raw_data/current_history.csv")
        
        history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
        
        history_df['hour'] = history_df['timestamp'].dt.hour
        
        history_df['aqi'] = history_df['pm25'].apply(calculate_pm25_aqi)
        
        hourly_avg = history_df.groupby('hour')['aqi'].mean().reset_index()
        
        distribution_data = []
        for _, row in hourly_avg.iterrows():
            hour_str = f"{int(row['hour']):02d}:00"
            aqi_val = int(row['aqi'])
            
            if aqi_val <= 50:
                category = "Good"
            elif aqi_val <= 100:
                category = "Moderate"
            elif aqi_val <= 150:
                category = "Unhealthy for Sensitive"
            elif aqi_val <= 200:
                category = "Unhealthy"
            elif aqi_val <= 300:
                category = "Very Unhealthy"
            else:
                category = "Hazardous"
            
            distribution_data.append({
                "hour": hour_str,
                "aqi": aqi_val,
                "category": category
            })
        
        distribution_data.sort(key=lambda x: int(x['hour'].split(':')[0]))
        
        return distribution_data
    except Exception as e:
        print(f"Error fetching AQI distribution: {e}")
        return []

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)