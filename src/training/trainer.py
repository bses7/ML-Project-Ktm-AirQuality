import pandas as pd
import joblib
import os
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, VotingClassifier, StackingClassifier
import xgboost as xgb
from src.config.settings import Config
from src.utils.logger import get_logger
import json


logger = get_logger(__name__)

class ModelTrainer:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.scaler = StandardScaler()
        self.feature_names = None

    def prepare_data(self):
        """Handle dummies, scaling and time-series split."""
        # 1. One-Hot Encoding
        df_ml = pd.get_dummies(self.df, columns=Config.CATEGORICAL_COLS, drop_first=True)
        df_ml = df_ml.dropna()
        
        # 2. X/y Split
        X = df_ml.drop(columns=Config.DROP_COLS)
        y = df_ml[Config.TARGET]
        self.feature_names = X.columns.tolist()
        
        # 3. Time-Series Split (80/20)
        split_idx = int(len(df_ml) * (1 - Config.TEST_SIZE))
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        # 4. Scaling
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        return X_train_scaled, X_test_scaled, y_train, y_test

    def get_ensemble_models(self, params: dict):
        """Defines the model dictionary using best params."""

        with open(Config.PARAMS_PATH, 'r') as f:
            best_params = json.load(f)

        rf_best = RandomForestClassifier(**params['rf'])
        xgb_best = xgb.XGBClassifier(**params['xgb'])
        
        models = {
            "Random Forest": rf_best,
            "XGBoost": xgb_best,
            "Voting Ensemble": VotingClassifier(estimators=[
                ('lr', LogisticRegression(class_weight='balanced', max_iter=1000)),
                ('rf', rf_best),
                ('xgb', xgb_best)], voting='soft'),
            "Stacking Ensemble": StackingClassifier(estimators=[
                ('rf', rf_best),
                ('xgb', xgb_best)],
                final_estimator=LogisticRegression(), cv=5)
        }
        return models

    def save_artifacts(self, model, name):
        """Saves model and metadata using sanitized snake_case filenames."""
        os.makedirs(Config.MODEL_DIR, exist_ok=True)
        
        sanitized_name = name.lower().replace(" ", "_")
        
        model_path = os.path.join(Config.MODEL_DIR, f'{sanitized_name}.pkl')
        joblib.dump(model, model_path)
        
        joblib.dump(self.scaler, os.path.join(Config.MODEL_DIR, 'scaler.pkl'))
        joblib.dump(self.feature_names, os.path.join(Config.MODEL_DIR, 'features.pkl'))
        
        logger.info(f"Saved model artifact: {model_path}")