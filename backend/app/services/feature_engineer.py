import numpy as np
import pandas as pd

def apply_kathmandu_logic(df: pd.DataFrame):
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    df['month'] = df['timestamp'].dt.month
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    
    def get_season(month):
        if month in [12, 1, 2]: return 'Winter'
        elif month in [3, 4, 5]: return 'Pre-Monsoon'
        elif month in [6, 7, 8, 9]: return 'Monsoon'
        else: return 'Post-Monsoon'
    
    df['season'] = df['month'].apply(get_season)
    df['brick_kiln_active'] = df['month'].apply(lambda x: 1 if 1 <= x <= 5 else 0)
    
    df['month_sin'] = np.sin(2 * np.pi * df['month']/12)
    df['month_cos'] = np.cos(2 * np.pi * df['month']/12)
    df['hour_sin'] = np.sin(2 * np.pi * df['hour']/24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour']/24)
    
    df['is_rush_hour'] = df['hour'].apply(lambda x: 1 if (8 <= x <= 11) or (16 <= x <= 20) else 0)
    df['is_weekend'] = df['day_of_week'].apply(lambda x: 1 if x == 5 else 0)

    df['pm25_lag_1h'] = df['pm25'].shift(1)
    df['pm25_lag_2h'] = df['pm25'].shift(2)
    df['pm25_rolling_6h'] = df['pm25'].rolling(window=6).mean()
    df['pm25_rolling_24h'] = df['pm25'].rolling(window=24).mean()
    
    df['precip_lag_3h'] = df['precip'].shift(3)
    df['visibility_lag_3h'] = df['visibility'].shift(3)
    df['temp_diff_6h'] = df['temp'] - df['temp'].shift(6)
    
    return df

def create_ml_feature_row(history_list: list, trained_features: list):
    """
    Takes historical list, applies logic, and returns the LATEST row 
    formatted for the ML model.
    """
    df = pd.DataFrame([h.dict() for h in history_list])
    
    df = apply_kathmandu_logic(df)
    
    df = pd.get_dummies(df)
    
    latest_row = df.iloc[[-1]].copy()
    
    for col in trained_features:
        if col not in latest_row.columns:
            latest_row[col] = 0
            
    return latest_row[trained_features]

def create_ml_feature_row_from_df(df: pd.DataFrame, trained_features: list):
    """
    Directly processes the DataFrame loaded from CSV.
    """
    df = apply_kathmandu_logic(df)
    
    df = pd.get_dummies(df)
    
    latest_row = df.iloc[[-1]].copy()
    
    for col in trained_features:
        if col not in latest_row.columns:
            latest_row[col] = 0
            
    return latest_row[trained_features]