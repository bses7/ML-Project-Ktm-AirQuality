import pandas as pd
import numpy as np
from src.utils.logger import get_logger
from src.config.settings import Config

logger = get_logger(__name__)

class AirQualityCleaner:
    def __init__(self, file_path: str):
        self.df = pd.read_csv(file_path)

    def clean(self) -> pd.DataFrame:
        logger.info(f"Cleaning AQ Data. Initial shape: {self.df.shape}")
        
        # Handle -999 and Missing values
        self.df['value'] = self.df['value'].replace(-999, np.nan)
        self.df['value'] = self.df['value'].interpolate(method='linear', limit_direction='both')

        # Outlier handling
        median_val = self.df['value'].rolling(window=Config.ROLLING_WINDOW, center=True).median()
        is_outlier = (self.df['value'] > Config.AQ_OUTLIER_THRESHOLD) & (self.df['value'] > median_val * 5)
        self.df.loc[is_outlier, 'value'] = median_val
        self.df['value'] = self.df['value'].clip(upper=Config.AQ_OUTLIER_THRESHOLD)
        
        # Time alignment
        self.df['datetimeLocal'] = pd.to_datetime(self.df['datetimeLocal'])
        self.df['timestamp'] = self.df['datetimeLocal'].dt.floor('H').dt.tz_localize(None)
        
        # Aggregation
        aq_clean = self.df[['timestamp', 'value']].rename(columns={'value': 'pm25'})
        aq_clean = aq_clean.groupby('timestamp').mean().reset_index()
        
        logger.info(f"AQ Cleaned. Final shape: {aq_clean.shape}")
        return aq_clean

class WeatherCleaner:
    def __init__(self, file_path: str):
        self.df = pd.read_csv(file_path)

    def clean(self) -> pd.DataFrame:
        logger.info(f"Cleaning Weather Data. Initial shape: {self.df.shape}")
        
        self.df['timestamp'] = pd.to_datetime(self.df['datetime'])
        self.df['preciptype'] = self.df['preciptype'].fillna('none')
        
        # Drop irrelevant columns
        cols_to_drop = ['stations', 'name', 'snow', 'snowdepth', 'severerisk', 'datetime']
        self.df = self.df.drop(columns=[c for c in cols_to_drop if c in self.df.columns])
        
        # Imputation
        if 'visibility' in self.df.columns:
            self.df['visibility'] = self.df['visibility'].interpolate(method='linear')
        self.df = self.df.ffill()
        
        logger.info(f"Weather Cleaned. Final shape: {self.df.shape}")
        return self.df