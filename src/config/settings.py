import os

class Config:
    """Project-wide configurations and constants."""
    
    # 1. Input Directories
    AQ_DATA_DIR = "aqData"
    WEATHER_DATA_DIR = "weatherData"
    
    # 2. Output Directories
    OUTPUT_DIR = "outputs"
    
    # 3. Intermediate Raw Merged Files (Build Stage Outputs)
    # These match what main.py and the cleaners expect
    AQ_RAW_MERGED = os.path.join(OUTPUT_DIR, "aq_data_full.csv")
    WEATHER_RAW_MERGED = os.path.join(OUTPUT_DIR, "weather_data_full.csv")
    
    # 4. Final Dataset (Clean Stage Output)
    FINAL_CLEANED_DATA = os.path.join(OUTPUT_DIR, "df_final.csv")
    
    # 5. Column Names (Used for sorting and merging)
    AQ_DATE_COL = "datetimeUtc"
    WEATHER_DATE_COL = "datetime"
    
    # 6. Cleaning Constants
    AQ_OUTLIER_THRESHOLD = 400
    ROLLING_WINDOW = 7
    HAZARD_THRESHOLD = 150
    PREDICTION_WINDOW = 24
    
    # 7. Machine Learning Constants
    ML_READY_DATA = os.path.join(OUTPUT_DIR, "kathmandu_aq_ml_ready.csv")
    PARAMS_PATH = os.path.join(OUTPUT_DIR, "params", "best_params.json")
    MODEL_DIR = "models"
    EVAL_DIR = os.path.join(MODEL_DIR, "evaluations")

    CATEGORICAL_COLS = ['season', 'preciptype', 'conditions', 'weather_summary']
    DROP_COLS = ['timestamp', 'is_hazardous_now', 'target_next_24h']
    TARGET = 'target_next_24h'
    TEST_SIZE = 0.2
    PROB_THRESHOLD = 0.25
    
    COLOR_SAFE = "#2E86C1"  # Blue
    COLOR_TOXIC = "#CB4335" # Red
    COLOR_BLACK = "#17202A"

    DEPLOY_ARTIFACT_DIR = os.path.join("..", "backend", "app", "ml_models", "artifacts")
    
    