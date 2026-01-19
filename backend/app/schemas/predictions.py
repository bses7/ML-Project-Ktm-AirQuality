from pydantic import BaseModel
from typing import List

class WeatherReading(BaseModel):
    timestamp: str 
    pm25: float
    temp: float
    humidity: float
    visibility: float
    windspeed: float
    precip: float

class PredictionRequest(BaseModel):
    history: List[WeatherReading]

class PredictionResponse(BaseModel):
    pm25_current: float
    hazard_probability: float 
    is_hazardous_upcoming: bool
    health_advice: str

class DashboardResponse(BaseModel):
    aqi: int
    pm25: float
    pm10: float
    humidity: float
    visibility: float
    timestamp: str
    hazard_level: str
    health_recommendations: List[str]
    last_updated: str

class HistoricalDataPoint(BaseModel):
    timestamp: str
    pm25: float
    temp: float
    humidity: float
    windspeed: float
    aqi: int

class AQIDistributionPoint(BaseModel):
    hour: str
    aqi: int
    category: str