import argparse
import sys
import os
import json
import pandas as pd
import joblib

# Project Imports
from src.config.settings import Config
from src.utils.logger import get_logger
from src.utils.stats import get_missing_statistics

# Stage Imports
from src.databuilder.processor import DataMerger as RawMerger
from src.datacleaner.cleaner import AirQualityCleaner, WeatherCleaner
from src.datacleaner.merger import DataMerger
from src.preprocessing.engineer import FeatureEngineer
from src.training.trainer import ModelTrainer
from src.training.tuner import ModelTuner
from src.evaluation.evaluator import ModelEvaluator

from src.utils.deploy import deploy_pipeline

logger = get_logger("MAIN_PIPELINE")

def run_build_stage():
    """Stage 1: Build - Merges raw CSV files from data folders."""
    logger.info(">>> STARTING STAGE: BUILD")
    RawMerger(Config.AQ_DATA_DIR, Config.AQ_RAW_MERGED).run(Config.AQ_DATE_COL)
    RawMerger(Config.WEATHER_DATA_DIR, Config.WEATHER_RAW_MERGED).run(Config.WEATHER_DATE_COL)
    logger.info(">>> STAGE BUILD COMPLETED")

def run_clean_stage():
    """Stage 2: Clean - Cleans AQ and Weather data, then merges them."""
    logger.info(">>> STARTING STAGE: CLEAN")
    aq_cleaner = AirQualityCleaner(Config.AQ_RAW_MERGED)
    df_aq = aq_cleaner.clean()
    
    weather_cleaner = WeatherCleaner(Config.WEATHER_RAW_MERGED)
    df_weather = weather_cleaner.clean()
    
    final_df = DataMerger.merge(df_aq, df_weather)
    
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    final_df.to_csv(Config.FINAL_CLEANED_DATA, index=False)
    
    stats = get_missing_statistics(final_df)
    logger.info(f"Missing Stats:\n{stats}")
    logger.info(">>> STAGE CLEAN COMPLETED")

def run_preprocess_stage():
    """Stage 3: Preprocess - Feature engineering and target creation."""
    logger.info(">>> STARTING STAGE: PREPROCESS")
    try:
        df = pd.read_csv(Config.FINAL_CLEANED_DATA)
    except FileNotFoundError:
        logger.error("Cleaned data not found. Run 'clean' stage first.")
        sys.exit(1)

    engineer = FeatureEngineer(df)
    ml_ready_df = (
        engineer
        .add_temporal_features()
        .add_lag_features()
        .add_targets()
        .finalize()
    )
    
    ml_ready_df.to_csv(Config.ML_READY_DATA, index=False)
    logger.info(f"ML-ready data saved. Shape: {ml_ready_df.shape}")
    logger.info(">>> STAGE PREPROCESS COMPLETED")

def run_train_stage(mode='default'):
    """Stage 4: Train - Model training with optional hyperparameter tuning."""
    logger.info(f">>> STARTING STAGE: TRAIN (Mode: {mode})")
    
    try:
        df = pd.read_csv(Config.ML_READY_DATA)
    except FileNotFoundError:
        logger.error("ML-ready data not found. Run 'preprocess' stage first.")
        sys.exit(1)

    trainer = ModelTrainer(df)
    X_train, X_test, y_train, y_test = trainer.prepare_data()

    if mode == 'tune':
        logger.info("Starting Hyperparameter Optimization with Optuna...")
        tuner = ModelTuner(X_train, y_train)
        best_params = {
            "xgb": tuner.tune_xgb(n_trials=50),
            "rf": tuner.tune_rf(n_trials=50)
        }
        os.makedirs(os.path.dirname(Config.PARAMS_PATH), exist_ok=True)
        with open(Config.PARAMS_PATH, 'w') as f:
            json.dump(best_params, f, indent=4)
        logger.info(f"Best parameters saved to {Config.PARAMS_PATH}")
    else:
        if os.path.exists(Config.PARAMS_PATH):
            with open(Config.PARAMS_PATH, 'r') as f:
                best_params = json.load(f)
            logger.info("Loaded best parameters from JSON.")
        else:
            logger.warning("best_params.json not found. Using default fallback parameters.")
            best_params = {
                "rf": {'n_estimators': 423, 'max_depth': 26, 'min_samples_leaf': 8},
                "xgb": {'n_estimators': 302, 'max_depth': 3, 'learning_rate': 0.007}
            }

    models = trainer.get_ensemble_models(best_params)
    for name, model in models.items():
        logger.info(f"Fitting model: {name}")
        model.fit(X_train, y_train)
        trainer.save_artifacts(model, name)
    
    logger.info(">>> STAGE TRAIN COMPLETED")

def run_evaluate_stage():
    logger.info(">>> STARTING STAGE: EVALUATE")
    
    df = pd.read_csv(Config.ML_READY_DATA)
    trainer = ModelTrainer(df)
    X_train, X_test, y_train, y_test = trainer.prepare_data()
    
    model_files = [f for f in os.listdir(Config.MODEL_DIR) if f.endswith('.pkl') and f not in ['scaler.pkl', 'features.pkl']]
    
    if not model_files:
        logger.error("No models found. Run 'train' stage first.")
        return

    results_probs = {}
    evaluator = ModelEvaluator()
    
    for model_file in model_files:
        name = model_file.replace('.pkl', '')
        model = joblib.load(os.path.join(Config.MODEL_DIR, model_file))
        
        probs = model.predict_proba(X_test)[:, 1]
        results_probs[name] = probs
        
        evaluator.plot_confusion_matrix(y_test, probs, name)
        evaluator.plot_threshold_tradeoff(y_test, probs, name)
        
        if name in ["random_forest", "XGBoost"]:
            evaluator.plot_feature_importance(model, trainer.feature_names, name)

    evaluator.plot_pr_curves(y_test, results_probs)
    evaluator.plot_probability_distribution(y_test, results_probs)
    evaluator.plot_calibration(y_test, results_probs)

    if "Voting Ensemble" in results_probs:
        voting_model_path = os.path.join(Config.MODEL_DIR, "voting_ensemble.pkl")
        if os.path.exists(voting_model_path):
            voting_model = joblib.load(voting_model_path)
            evaluator.explain_lime(X_train, X_test, trainer.feature_names, voting_model)

    logger.info(f"Evaluation complete. All plots saved to {Config.EVAL_DIR}")

def main():
    parser = argparse.ArgumentParser(description="Kathmandu Air Quality ML Pipeline")
    parser.add_argument(
        "--stage", 
        type=str, 
        choices=['build', 'clean', 'preprocess', 'train', 'evaluate', 'deploy', 'all'],
        default='all',
        help="Specify the pipeline stage to run"
    )
    parser.add_argument("--mode", type=str, default='default')

    args = parser.parse_args()

    stage_map = {
        'build': run_build_stage,
        'clean': run_clean_stage,
        'preprocess': run_preprocess_stage,
        'train': lambda: run_train_stage(args.mode),
        'evaluate': run_evaluate_stage,
        'deploy': deploy_pipeline  
    }

    try:
        if args.stage == 'all':
            logger.info("Running FULL Pipeline (Build to Evaluate)...")
            run_build_stage()
            run_clean_stage()
            run_preprocess_stage()
            run_train_stage(mode='default')
            run_evaluate_stage()
            logger.info("Pipeline finished. Use '--stage deploy' to launch containers.")
            
        else:
            logger.info(f"Running SINGLE Stage: {args.stage}")
            stage_map[args.stage]()

    except Exception as e:
        logger.error(f"Pipeline failed at stage {args.stage}: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()