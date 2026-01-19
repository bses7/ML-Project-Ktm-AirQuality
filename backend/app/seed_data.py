import requests
import pandas as pd
import urllib.parse
import os
from dotenv import load_dotenv
import csv
import codecs
from datetime import datetime, timedelta
from app.services.data_cleaner import clean_and_merge_logic

load_dotenv()

OPENAQ_SENSOR_ID = "7710"
OPENAQ_API_KEY = os.getenv("OPENAQ_API_KEY")
VC_API_KEY = os.getenv("VC_API_KEY")
LOCATION = "Kathmandu"
DATA_FOLDER = os.path.join("app", "raw_data")

os.makedirs(DATA_FOLDER, exist_ok=True)

datetime_to = datetime.utcnow()
datetime_from = datetime_to - timedelta(hours=48)
datetime_to_str = datetime_to.strftime("%Y-%m-%dT%H:%M:%SZ")
datetime_from_str = datetime_from.strftime("%Y-%m-%dT%H:%M:%SZ")

def fetch_weather_csv(location: str, api_key: str, output_file: str):
    """Fetch weather data for the last 48 hours using urllib and save to CSV."""
    start_date = (datetime.utcnow() - timedelta(hours=48)).strftime('%Y-%m-%dT%H:%M:%S')
    base_url = 'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/'
    params = f"{urllib.parse.quote_plus(location)}/{start_date}/now?unitGroup=metric&include=hours&key={api_key}&contentType=csv"
    url = base_url + params

    try:
        with urllib.request.urlopen(url) as response:
            if response.getcode() == 200:
                reader = csv.reader(codecs.iterdecode(response, "utf-8"))
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    for row in reader:
                        writer.writerow(row)
                print(f"48-hour weather data for {location} saved to {output_file}")
            else:
                print(f"Error: Received HTTP {response.getcode()}")

    except urllib.error.HTTPError as e:
        print(f"HTTPError: {e.reason}")
    except urllib.error.URLError as e:
        print(f"URLError: {e.reason}")
    except Exception as e:
        print(f"Unexpected error: {e}")

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
    weather_file = os.path.join(DATA_FOLDER, "weather_last_48.csv")
    fetch_weather_csv(LOCATION, VC_API_KEY, weather_file)
    
    w_raw = pd.read_csv(weather_file)
    df_final = clean_and_merge_logic(aq_raw, w_raw)

    history_path = os.path.join(DATA_FOLDER, "current_history.csv")
    df_final.to_csv(history_path, index=False)
    print(f"SUCCESS! Clean history saved to {history_path} ({len(df_final)} rows).")
    
if __name__ == "__main__":
    run_seeding_pipeline()