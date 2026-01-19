import pandas as pd
import numpy as np

def clean_and_merge_logic(aq_raw_df: pd.DataFrame, weather_raw_df: pd.DataFrame):
    aq_df = aq_raw_df.copy()
    
    aq_df['timestamp'] = pd.to_datetime(aq_df['timestamp']).dt.tz_localize(None).dt.floor('H')

    aq_df = aq_df.groupby('timestamp')[['value']].mean().reset_index()
    
    aq_df = aq_df.sort_values('timestamp').reset_index(drop=True)

    aq_df['value'] = aq_df['value'].replace(-999, np.nan)
    aq_df['value'] = aq_df['value'].interpolate(method='linear', limit_direction='both').fillna(0)

    aq_df['value_median'] = aq_df['value'].rolling(window=7, center=True, min_periods=1).median()
    aq_df['value_median'] = aq_df['value_median'].ffill().bfill()
    
    is_outlier = (aq_df['value'] > 400) & (aq_df['value'] > aq_df['value_median'] * 5)
    aq_df.loc[is_outlier, 'value'] = aq_df.loc[is_outlier, 'value_median']
    
    aq_df['pm25'] = aq_df['value'].clip(upper=400)
    aq_clean = aq_df[['timestamp', 'pm25']].copy()

    weather_df = weather_raw_df.copy()
    if 'datetime' in weather_df.columns:
        weather_df = weather_df.rename(columns={'datetime': 'timestamp'})
    
    weather_df['timestamp'] = pd.to_datetime(weather_df['timestamp']).dt.tz_localize(None).dt.floor('H')
    
    weather_df = weather_df.groupby('timestamp').first().reset_index()
    weather_df = weather_df.sort_values('timestamp').reset_index(drop=True)
    
    if 'preciptype' in weather_df.columns:
        weather_df['preciptype'] = weather_df['preciptype'].fillna('none')
    
    cols_to_drop = ['stations', 'name', 'snow', 'snowdepth', 'severerisk']
    weather_clean = weather_df.drop(columns=[c for c in cols_to_drop if c in weather_df.columns])
    
    if 'visibility' in weather_clean.columns:
        weather_clean['visibility'] = weather_clean['visibility'].interpolate(method='linear').ffill().bfill()
    
    weather_clean = weather_clean.ffill().bfill()

    df_merged = pd.merge(aq_clean, weather_clean, on='timestamp', how='inner')
    df_final = df_merged.sort_values('timestamp').drop_duplicates('timestamp').reset_index(drop=True)

    if 'icon' in df_final.columns:
        df_final = df_final.rename(columns={'icon': 'weather_summary'})

    return df_final