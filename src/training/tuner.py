import optuna
import numpy as np
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import average_precision_score

class ModelTuner:
    def __init__(self, X_train, y_train):
        self.X_train = X_train
        self.y_train = y_train
        self.tscv = TimeSeriesSplit(n_splits=5)

    def tune_xgb(self, n_trials=50):
        def objective(trial):
            param = {
                'n_estimators': trial.suggest_int('n_estimators', 200, 600),
                'max_depth': trial.suggest_int('max_depth', 3, 12),
                'learning_rate': trial.suggest_float('learning_rate', 0.005, 0.05, log=True),
                'scale_pos_weight': trial.suggest_float('scale_pos_weight', 10, 30),
                'random_state': 42,
                'eval_metric': 'logloss'
            }
            return self._cross_val_score(xgb.XGBClassifier(**param))
        
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=n_trials)
        return study.best_params

    def tune_rf(self, n_trials=50):
        def objective(trial):
            param = {
                'n_estimators': trial.suggest_int('n_estimators', 200, 500),
                'max_depth': trial.suggest_int('max_depth', 10, 30),
                'min_samples_leaf': trial.suggest_int('min_samples_leaf', 2, 10),
                'class_weight': 'balanced_subsample',
                'random_state': 42
            }
            return self._cross_val_score(RandomForestClassifier(**param))
        
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=n_trials)
        return study.best_params

    def _cross_val_score(self, model):
        scores = []
        for t, v in self.tscv.split(self.X_train):
            model.fit(self.X_train[t], self.y_train.iloc[t])
            probs = model.predict_proba(self.X_train[v])[:, 1]
            scores.append(average_precision_score(self.y_train.iloc[v], probs))
        return np.mean(scores)