import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    confusion_matrix, classification_report, precision_recall_curve,
    average_precision_score
)
import lime
import lime.lime_tabular
from src.config.settings import Config
from src.utils.logger import get_logger
from sklearn.calibration import calibration_curve 


logger = get_logger(__name__)

class ModelEvaluator:
    def __init__(self):
        self.eval_dir = Config.EVAL_DIR
        os.makedirs(self.eval_dir, exist_ok=True)
        # Set professional style
        plt.style.use('seaborn-v0_8-whitegrid')

    def save_and_clear(self, filename: str):
        """Saves the current plot and closes the figure to free memory."""
        path = os.path.join(self.eval_dir, filename)
        plt.savefig(path, bbox_inches='tight', dpi=300)
        logger.info(f"Saved plot: {path}")
        plt.close()

    def plot_confusion_matrix(self, y_true, y_probs, model_name: str):
        """Saves a 'Mickey' styled confusion matrix."""
        preds = (y_probs >= Config.PROB_THRESHOLD).astype(int)
        cm = confusion_matrix(y_true, preds)
        
        plt.figure(figsize=(7, 5))
        sns.heatmap(cm, annot=True, fmt='d', cmap='YlOrRd', linewidths=2, 
                    linecolor=Config.COLOR_BLACK,
                    xticklabels=['Safe', 'TOXIC'], 
                    yticklabels=['Safe', 'TOXIC'],
                    annot_kws={"size": 14, "weight": "bold"})
        
        plt.title(f"Confusion Matrix: {model_name}\n(Threshold {Config.PROB_THRESHOLD})")
        self.save_and_clear(f"cm_{model_name.replace(' ', '_').lower()}.png")

    def plot_pr_curves(self, y_test, results_probs: dict):
        """Comparison of Precision-Recall curves for all models."""
        plt.figure(figsize=(12, 7))
        for name, probs in results_probs.items():
            precision, recall, _ = precision_recall_curve(y_test, probs)
            score = average_precision_score(y_test, probs)
            plt.plot(recall, precision, label=f'{name} (AUPRC: {score:.2f})')

        plt.axhline(0.5, color='gray', linestyle='--', alpha=0.5)
        plt.title('MODEL COMPARISON: PRECISION-RECALL CURVE')
        plt.xlabel('RECALL (Catch Rate)')
        plt.ylabel('PRECISION (Accuracy of Warning)')
        plt.legend()
        self.save_and_clear("comparison_pr_curves.png")

    def plot_probability_distribution(self, y_test, results_probs: dict):
        """Comparison of probability densities."""
        plt.figure(figsize=(12, 6))
        for name, probs in results_probs.items():
            sns.kdeplot(probs[y_test == 0], label=f"{name} (Safe)", fill=True, alpha=0.2)
            sns.kdeplot(probs[y_test == 1], label=f"{name} (TOXIC)", fill=True, alpha=0.2)
        
        plt.axvline(Config.PROB_THRESHOLD, color='red', linestyle='--', label=f'Threshold ({Config.PROB_THRESHOLD})')
        plt.title("Probability Distribution by Class")
        plt.xlabel("Predicted Probability of Toxicity")
        plt.ylabel("Density")
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        self.save_and_clear("comparison_prob_dist.png")

    def plot_feature_importance(self, model, feature_names: list, model_name: str):
        """Horizontal bar chart for feature importance."""
        if not hasattr(model, 'feature_importances_'):
            logger.warning(f"Model {model_name} does not support feature_importances_")
            return

        importances = model.feature_importances_
        indices = np.argsort(importances)[-15:] 
        
        plt.figure(figsize=(10, 8))
        plt.barh(range(len(indices)), importances[indices], color='firebrick', align='center')
        plt.yticks(range(len(indices)), [feature_names[i] for i in indices])
        plt.title(f"Top 15 Drivers of Toxicity ({model_name})")
        plt.xlabel('Relative Importance')
        self.save_and_clear(f"importance_{model_name.replace(' ', '_').lower()}.png")

    def plot_calibration(self, y_test, results_probs: dict):
        """Reliability curve."""
        plt.figure(figsize=(8, 8))
        plt.plot([0, 1], [0, 1], "k:", label="Perfectly calibrated")
        for name, probs in results_probs.items():
            prob_true, prob_pred = calibration_curve(y_test, probs, n_bins=10)
            plt.plot(prob_pred, prob_true, "s-", label=name)
        plt.ylabel("Fraction of Positives (Actual)")
        plt.xlabel("Mean Predicted Probability")
        plt.title("Calibration Curve (Reliability)")
        plt.legend(loc="lower right")
        self.save_and_clear("comparison_calibration.png")

    def plot_threshold_tradeoff(self, y_test, probs, model_name: str):
        """P-R-F1 tradeoff against threshold levels."""
        p, r, t = precision_recall_curve(y_test, probs)
        f1 = [2 * (pi * ri) / (pi + ri) if (pi + ri) > 0 else 0 for pi, ri in zip(p, r)]
        
        plt.figure(figsize=(10, 5))
        plt.plot(t, p[:-1], 'b--', label='Precision')
        plt.plot(t, r[:-1], 'g-', label='Recall')
        plt.plot(t, f1[:-1], 'r-', label='F1 Score', linewidth=2)
        plt.axvline(Config.PROB_THRESHOLD, color='black', linestyle=':', label='Threshold')
        plt.title(f'Threshold Trade-off: {model_name}')
        plt.legend()
        self.save_and_clear(f"tradeoff_{model_name.replace(' ', '_').lower()}.png")

    def explain_lime(self, X_train, X_test, feature_names, model, idx=10):
        """Saves a LIME explanation as an HTML file."""
        explainer = lime.lime_tabular.LimeTabularExplainer(
            training_data=X_train,
            feature_names=feature_names,
            class_names=['Safe', 'Hazardous'],
            mode='classification'
        )
        exp = explainer.explain_instance(X_test[idx], model.predict_proba)
        output_path = os.path.join(self.eval_dir, 'lime_explanation.html')
        exp.save_to_file(output_path)
        logger.info(f"LIME explanation saved to {output_path}")