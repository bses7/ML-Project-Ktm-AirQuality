import pandas as pd
import numpy as np
from src.utils.logger import get_logger
from src.config.settings import Config

logger = get_logger(__name__)

class FeatureEngineer:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        # Ensure timestamp is datetime
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])

    def add_temporal_features(self):
        """Adds time-based features specific to Kathmandu's environment."""
        logger.info("Adding temporal and cyclical features...")
        df = self.df
        
        df['hour'] = df['timestamp'].dt.hour
        df['month'] = df['timestamp'].dt.month
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        # Season Mapping
        def get_season(month):
            if month in [12, 1, 2]: return 'Winter'
            elif month in [3, 4, 5]: return 'Pre-Monsoon'
            elif month in [6, 7, 8, 9]: return 'Monsoon'
            else: return 'Post-Monsoon'
        
        df['season'] = df['month'].apply(get_season)
        
        # Brick Kiln Operation (Jan - May)
        df['brick_kiln_active'] = df['month'].apply(lambda x: 1 if 1 <= x <= 5 else 0)
        
        # Cyclical Encoding
        df['month_sin'] = np.sin(2 * np.pi * df['month']/12)
        df['month_cos'] = np.cos(2 * np.pi * df['month']/12)
        df['hour_sin'] = np.sin(2 * np.pi * df['hour']/24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour']/24)
        
        # Rush Hour and Weekend
        df['is_rush_hour'] = df['hour'].apply(lambda x: 1 if (8 <= x <= 11) or (16 <= x <= 20) else 0)
        df['is_weekend'] = df['day_of_week'].apply(lambda x: 1 if x == 5 else 0)
        
        # Human-readable day
        day_map = {0:'Mon', 1:'Tue', 2:'Wed', 3:'Thu', 4:'Fri', 5:'SAT', 6:'Sun'}
        df['day_name'] = df['day_of_week'].map(day_map)
        
        return self

    def add_lag_features(self):
        """Adds historical lags and rolling averages."""
        logger.info("Adding lag and rolling features...")
        df = self.df
        
        # PM2.5 Momentum
        df['pm25_lag_1h'] = df['pm25'].shift(1)
        df['pm25_lag_2h'] = df['pm25'].shift(2)
        df['pm25_rolling_6h'] = df['pm25'].rolling(window=6).mean()
        df['pm25_rolling_24h'] = df['pm25'].rolling(window=24).mean()
        
        # Weather Interaction Lags
        df['precip_lag_3h'] = df['precip'].shift(3)
        df['visibility_lag_3h'] = df['visibility'].shift(3)
        df['temp_diff_6h'] = df['temp'] - df['temp'].shift(6)
        
        return self

    def add_targets(self):
        """Creates classification targets for the model."""
        logger.info("Creating Hazard targets...")
        df = self.df
        
        # Current Hazard
        df['is_hazardous_now'] = (df['pm25'] >= Config.HAZARD_THRESHOLD).astype(int)
        
        # Target: Will it be hazardous anytime in the next 24 hours?
        df['target_next_24h'] = (
            df['is_hazardous_now']
            .rolling(window=Config.PREDICTION_WINDOW)
            .max()
            .shift(-Config.PREDICTION_WINDOW)
        )
        return self

    def finalize(self):
        """Cleans up columns and drops rows with NaN from lags."""
        logger.info("Finalizing dataset...")
        df = self.df
        
        if 'icon' in df.columns:
            df = df.rename(columns={'icon': 'weather_summary'})
            
        # Drop cleanup columns
        cols_to_drop = ['temp_change_bin', 'year_month', 'day_name']
        df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
        
        # Drop rows where lag/target produced NaNs
        old_count = len(df)
        df = df.dropna().reset_index(drop=True)
        
        logger.info(f"Dropped {old_count - len(df)} rows containing NaNs from feature engineering.")
        return df