import pandas as pd

def get_missing_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """Returns a dataframe showing missing value percentages."""
    stats = pd.DataFrame(df.isnull().sum()).reset_index()
    stats.columns = ['COLUMN NAME', 'MISSING VALUES']
    stats['% MISSING'] = round((stats['MISSING VALUES'] / len(df)) * 100, 2)
    return stats.sort_values('% MISSING', ascending=False)