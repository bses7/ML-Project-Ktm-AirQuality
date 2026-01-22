import pandas as pd
import glob
import os
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DataMerger:
    """Handles the aggregation of multiple CSV files into single datasets."""
    
    def __init__(self, folder_path: str, output_path: str):
        self.folder_path = folder_path
        self.output_path = output_path

    def run(self, datetime_col: str, sort: bool = True) -> pd.DataFrame:
        """Executes the merge process."""
        all_files = glob.glob(os.path.join(self.folder_path, "*.csv"))
        
        if not all_files:
            logger.error(f"No CSV files found in {self.folder_path}")
            raise FileNotFoundError(f"Missing data in {self.folder_path}")

        logger.info(f"Merging {len(all_files)} files from {self.folder_path}")

        # Processing
        df_list = [pd.read_csv(f) for f in all_files]
        full_df = pd.concat(df_list, axis=0, ignore_index=True)

        # Datetime handling
        if datetime_col in full_df.columns:
            full_df[datetime_col] = pd.to_datetime(full_df[datetime_col], errors="coerce")
            if sort:
                full_df = full_df.sort_values(by=datetime_col)
        
        # IO Operations
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        full_df.to_csv(self.output_path, index=False)
        
        logger.info(f"Successfully saved merged data to {self.output_path}")
        return full_df