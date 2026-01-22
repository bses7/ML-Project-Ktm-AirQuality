import pandas as pd
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DataMerger:
    @staticmethod
    def merge(aq_df: pd.DataFrame, weather_df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Merging AQ and Weather datasets...")
        merged_df = pd.merge(aq_df, weather_df, on='timestamp', how='inner')
        merged_df = merged_df.sort_values('timestamp').reset_index(drop=True)
        
        logger.info(f"Merge complete. Final Rows: {len(merged_df)}")
        logger.info(f"Timeline: {merged_df['timestamp'].min()} to {merged_df['timestamp'].max()}")
        return merged_df