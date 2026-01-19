import requests
import pandas as pd
import urllib.parse
import os
from datetime import datetime, timedelta
from app.services.data_cleaner import clean_and_merge_logic

OPENAQ_SENSOR_ID = "7710"
OPENAQ_API_KEY = "d44de1af94a65b225622ebda9613901f62f5c7235731daeba81a8a924690f8c7"
VC_API_KEY = "SE5P48R4L5GPVYY2P7YGC58W5"
LOCATION = "Kathmandu"
DATA_FOLDER = os.path.join("app", "raw_data")

os.makedirs(DATA_FOLDER, exist_ok=True)

datetime_to = datetime.utcnow()
datetime_from = datetime_to - timedelta(hours=48)
datetime_to_str = datetime_to.strftime("%Y-%m-%dT%H:%M:%SZ")
datetime_from_str = datetime_from.strftime("%Y-%m-%dT%H:%M:%SZ")

def run_seeding_pipeline():
    print(f"Fetching AQ data...")
    aq_url = f"https://api.openaq.org/v3/sensors/{OPENAQ_SENSOR_ID}/measurements/hourly"
    headers = {"accept": "application/json", "X-API-Key": OPENAQ_API_KEY}
    
    all_results = []
    page = 1
    while True:
        params = {"datetime_from": datetime_from_str, "datetime_to": datetime_to_str, "limit": 100, "page": page}
        response = requests.get(aq_url, params=params, headers=headers)
        data = response.json()
        results = data.get("results", [])
        if not results: break
        all_results.extend(results)
        if page * params["limit"] >= data.get("meta", {}).get("found", 0): break
        page += 1
    
    aq_raw = pd.json_normalize(all_results)
    aq_raw = aq_raw[["period.datetimeFrom.local", "value"]]
    aq_raw.columns = ["timestamp", "value"]
    aq_raw['timestamp'] = pd.to_datetime(aq_raw['timestamp']).dt.tz_localize(None).dt.floor('H')
    aq_raw.to_csv(os.path.join(DATA_FOLDER, "aq_last_48.csv"), index=False)

    print(f"Fetching Weather data...")
    w_url = (f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"
             f"{urllib.parse.quote_plus(LOCATION)}/last2days?"
             f"unitGroup=metric&contentType=csv&include=hours&key={VC_API_KEY}")
    
    w_raw = pd.read_csv(w_url)
    w_raw.to_csv(os.path.join(DATA_FOLDER, "weather_last_48.csv"), index=False)

    df_final = clean_and_merge_logic(aq_raw, w_raw)

    history_path = os.path.join(DATA_FOLDER, "current_history.csv")
    df_final.to_csv(history_path, index=False)
    print(f"SUCCESS! Clean history saved to {history_path} ({len(df_final)} rows).")

if __name__ == "__main__":
    run_seeding_pipeline()