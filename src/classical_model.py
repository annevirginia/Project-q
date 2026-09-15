"""
Classical Machine Learning Models for Cyber Threat Detection.
Implements Random Forest (primary baseline), Logistic Regression, and Support Vector Machines.
Measures real training duration, inference latency, and performance metrics.
"""

import os
import time
from typing import Dict, Any, Optional, Tuple
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)
import joblib

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")


class ClassicalThreatClassifier:
    """
    Wrapper for classical machine learning classifiers with real execution benchmarking.
    """
    def __init__(self, model_type: str = "random_forest", random_state: int = 42):
        self.model_type = model_type
        self.random_state = random_state
        self.training_time: float = 0.0
        self.inference_time_per_sample: float = 0.0
        self.is_trained: bool = False
        
        if model_type == "random_forest":
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=12,
                min_samples_split=4,
                min_samples_leaf=2,
                class_weight="balanced",
                random_state=random_state,
                n_jobs=-1
            )
        elif model_type == "logistic_regression":
            self.model = LogisticRegression(
                max_iter=1000,
                class_weight="balanced",
                random_state=random_state
            )
        elif model_type == "svm":
            self.model = SVC(
                kernel="rbf",
                probability=True,
                class_weight="balanced",
                random_state=random_state
            )
        else:
            raise ValueError(f"Unsupported model_type: {model_type}")

    def train(self, X_train: np.ndarray, y_train: np.ndarray) -> Dict[str, Any]:
        """
        Trains the classical classifier and measures exact wall-clock training time.
        """
        start_time = time.perf_counter()
        self.model.fit(X_train, y_train)
        self.training_time = time.perf_counter() - start_time
        self.is_trained = True
        
        train_preds = self.model.predict(X_train)
        train_acc = accuracy_score(y_train, train_preds)
        
        return {
            "model_type": self.model_type,
            "training_time_seconds": round(self.training_time, 4),
            "training_samples": len(X_train),
            "num_features": X_train.shape[1],
            "train_accuracy": round(float(train_acc), 4)
        }

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generates class predictions (0 = Normal, 1 = Threat)."""
        if not self.is_trained:
            raise ValueError("Model must be trained before predicting.")
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Returns predicted class probabilities [P(Normal), P(Threat)]."""
        if not self.is_trained:
            raise ValueError("Model must be trained before predicting probabilities.")
        if hasattr(self.model, "predict_proba"):
            return self.model.predict_proba(X)
        elif hasattr(self.model, "decision_function"):
            df = self.model.decision_function(X)
            prob1 = 1 / (1 + np.exp(-df))
            return np.column_stack([1 - prob1, prob1])
        else:
            preds = self.predict(X)
            return np.column_stack([1 - preds, preds])

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        """
        Evaluates model on held-out test data and returns genuine metrics.
        Measures real inference latency per sample.
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation.")
        
        # Benchmark inference latency
        start_inf = time.perf_counter()
        y_pred = self.model.predict(X_test)
        total_inf_time = time.perf_counter() - start_inf
        self.inference_time_per_sample = total_inf_time / len(X_test) if len(X_test) > 0 else 0.0
        
        # Probabilities for ROC-AUC
        try:
            y_proba = self.predict_proba(X_test)[:, 1]
            auc = round(float(roc_auc_score(y_test, y_proba)), 4)
        except Exception:
            auc = None
            
        acc = round(float(accuracy_score(y_test, y_pred)), 4)
        prec = round(float(precision_score(y_test, y_pred, zero_division=0)), 4)
        rec = round(float(recall_score(y_test, y_pred, zero_division=0)), 4)
        f1 = round(float(f1_score(y_test, y_pred, zero_division=0)), 4)
        
        cm = confusion_matrix(y_test, y_pred)
        # tn, fp, fn, tp
        tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
        
        return {
            "model_type": self.model_type,
            "test_samples": len(X_test),
            "num_features": X_test.shape[1],
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1_score": f1,
            "roc_auc": auc,
            "training_time_seconds": round(self.training_time, 4),
            "total_inference_seconds": round(total_inf_time, 5),
            "inference_time_ms_per_sample": round(self.inference_time_per_sample * 1000, 4),
            "confusion_matrix": {
                "true_negative": int(tn),
                "false_positive": int(fp),
                "false_negative": int(fn),
                "true_positive": int(tp),
                "matrix": cm.tolist()
            },
            "classification_report": classification_report(y_test, y_pred, target_names=["Normal", "Threat"], output_dict=True, zero_division=0)
        }

    def save(self, filepath: Optional[str] = None):
        """Serializes the trained model."""
        if filepath is None:
            os.makedirs(MODELS_DIR, exist_ok=True)
            filepath = os.path.join(MODELS_DIR, f"classical_{self.model_type}.joblib")
        joblib.dump(self, filepath)
        print(f"Classical model saved to {filepath}")

    @classmethod
    def load(cls, filepath: Optional[str] = None, model_type: str = "random_forest") -> "ClassicalThreatClassifier":
        """Loads a serialized classical model."""
        if filepath is None:
            filepath = os.path.join(MODELS_DIR, f"classical_{model_type}.joblib")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Classical model file not found at {filepath}")
        return joblib.load(filepath)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.data_loader import find_default_dataset, load_dataset
    from src.preprocessing import ThreatDataPreprocessor

    dataset_path = find_default_dataset()
    print(f"Loading dataset from: {dataset_path}")
    df = load_dataset(dataset_path)
    
    preprocessor = ThreatDataPreprocessor(n_quantum_features=4)
    data_splits = preprocessor.prepare_dataset(df)
    
    print("\n--- Training Classical Random Forest Classifier ---")
    rf_classifier = ClassicalThreatClassifier(model_type="random_forest")
    train_res = rf_classifier.train(data_splits["X_train_classical"], data_splits["y_train"])
    print(f"Training Time: {train_res['training_time_seconds']}s, Train Accuracy: {train_res['train_accuracy']*100:.2f}%")
    
    print("\n--- Evaluating on Held-Out Test Split (995 samples) ---")
    eval_res = rf_classifier.evaluate(data_splits["X_test_classical"], data_splits["y_test"])
    print(f"Test Accuracy: {eval_res['accuracy']*100:.2f}%")
    print(f"Precision: {eval_res['precision']*100:.2f}%")
    print(f"Recall: {eval_res['recall']*100:.2f}%")
    print(f"F1 Score: {eval_res['f1_score']*100:.2f}%")
    print(f"ROC-AUC: {eval_res['roc_auc']}")
    print(f"Inference Latency: {eval_res['inference_time_ms_per_sample']} ms/sample")
    print("Confusion Matrix:", eval_res['confusion_matrix'])
    
    rf_classifier.save()
    print("Classical Model training and evaluation SUCCESS!")
