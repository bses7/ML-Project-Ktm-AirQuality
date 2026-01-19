import httpx
import pandas as pd
import os
from datetime import timedelta, datetime
from dotenv import load_dotenv
from app.services.data_cleaner import clean_and_merge_logic

load_dotenv()

# --- CONFIGURATION ---
OPENAQ_LOCATION_ID = "3459"
OPENAQ_SENSOR_ID = 7710
OPENAQ_API_KEY = os.getenv("OPENAQ_API_KEY")
VC_API_KEY = os.getenv("VC_API_KEY")
DATA_FOLDER = os.path.join("app", "raw_data")

async def fetch_latest_raw_data():
    """
    Fetches the single latest record from both APIs as DataFrames.
    """
    async with httpx.AsyncClient() as client:
        aq_url = f"https://api.openaq.org/v3/locations/{OPENAQ_LOCATION_ID}/sensors"
        aq_headers = {"accept": "application/json", "X-API-Key": OPENAQ_API_KEY}
        aq_resp = await client.get(aq_url, headers=aq_headers)
        aq_json = aq_resp.json()
        
        latest_aq_df = pd.DataFrame()
        for sensor in aq_json.get("results", []):
            if sensor["id"] == OPENAQ_SENSOR_ID:
                latest = sensor["latest"]
                latest_aq_df = pd.DataFrame([{
                    "timestamp": latest["datetime"]["local"],
                    "value": latest["value"]
                }])
                break
        latest_aq_df['timestamp'] = pd.to_datetime(latest_aq_df['timestamp'])
        latest_aq_df['timestamp'] = latest_aq_df['timestamp'].dt.tz_localize(None)

        w_url = (f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/Kathmandu?"
                 f"unitGroup=metric&include=current&key={VC_API_KEY}&contentType=csv")
        w_resp = await client.get(w_url)
        
        from io import StringIO
        w_df = pd.read_csv(StringIO(w_resp.text))
        
        # w_df.rename(columns={'datetime': 'timestamp'}, inplace=True)
        # w_df['timestamp'] = pd.to_datetime(w_df['timestamp'])
        # w_df['timestamp'] = (w_df['timestamp'] + pd.Timedelta(minutes=45)).dt.floor('H')

        return latest_aq_df, w_df

async def update_database_and_predict():
    print("Hourly Update Started...")
    
    new_aq, new_w = await fetch_latest_raw_data()

    print(new_aq.head())
    print(new_w.head())
    
    if new_aq.empty or new_w.empty:
        print("Failed to fetch new data slice.")
        return

    print("test1")
    aq_history_path = os.path.join(DATA_FOLDER, "aq_last_48.csv")
    w_history_path = os.path.join(DATA_FOLDER, "weather_last_48.csv")
    
    print("test2")
    if not os.path.exists(aq_history_path):
        print("Error: Run seed_data.py first.")
        return

    print("test3")
    aq_history = pd.read_csv(aq_history_path)
    w_history = pd.read_csv(w_history_path)

    print(aq_history.tail())
    print(w_history.tail())

    updated_aq = pd.concat([aq_history, new_aq], ignore_index=True)

    print("test4")
    updated_w = pd.concat([w_history, new_w], ignore_index=True)

    # updated_aq['timestamp'] = pd.to_datetime(updated_aq['timestamp']).dt.tz_localize(None).dt.floor('H')
    # updated_w['datetime'] = pd.to_datetime(updated_w['datetime']).dt.tz_localize(None).dt.floor('H')

    # updated_aq = updated_aq.drop_duplicates('timestamp').sort_values('timestamp').tail(60).reset_index(drop=True)
    # updated_w = updated_w.drop_duplicates('datetime').sort_values('datetime').tail(60).reset_index(drop=True)

    updated_aq.to_csv(aq_history_path, index=False)
    updated_w.to_csv(w_history_path, index=False)

    # 5. Pass to cleaner
    df_final = clean_and_merge_logic(updated_aq, updated_w)

    history_path = os.path.join(DATA_FOLDER, "current_history.csv")
    df_final.to_csv(history_path, index=False)

    print(f"Hourly update successful at {datetime.now()}.")