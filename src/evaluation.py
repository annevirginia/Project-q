"""
Evaluation & Benchmarking Utilities.
Calculates honest statistical metrics, confusion matrices, ROC metrics,
and renders visual analytical charts.
"""

import os
import json
from typing import Dict, Any, List, Optional
import numpy as np
from PIL import Image, ImageDraw
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, confusion_matrix, classification_report
)

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: Optional[np.ndarray] = None) -> Dict[str, Any]:
    """Computes all genuine classification metrics."""
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
    
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    
    auc = None
    if y_prob is not None:
        try:
            auc = roc_auc_score(y_true, y_prob)
        except Exception:
            auc = None
            
    return {
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "specificity": round(float(specificity), 4),
        "false_positive_rate": round(float(fpr), 4),
        "roc_auc": round(float(auc), 4) if auc is not None else None,
        "confusion_matrix": {
            "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
            "matrix": cm.tolist()
        }
    }


def save_confusion_matrix_plot(cm: np.ndarray, title: str, output_path: str):
    """Renders a styled confusion matrix heatmap using PIL without DLL dependencies."""
    width, height = 540, 400
    img = Image.new("RGB", (width, height), color=(15, 23, 42))  # #0f172a
    draw = ImageDraw.Draw(img)
    
    # Title
    draw.text((30, 25), title, fill=(56, 189, 248))
    
    # Grid coordinates
    ox, oy = 140, 90
    cw, ch = 170, 120
    
    # Headers
    draw.text((ox + 20, oy - 25), "Pred Normal (0)", fill=(148, 163, 184))
    draw.text((ox + cw + 20, oy - 25), "Pred Threat (1)", fill=(148, 163, 184))
    draw.text((20, oy + 45), "True Normal (0)", fill=(148, 163, 184))
    draw.text((20, oy + ch + 45), "True Threat (1)", fill=(148, 163, 184))
    
    total = int(np.sum(cm)) if np.sum(cm) > 0 else 1
    max_val = max(1, int(np.max(cm)))
    
    cell_names = [["TN", "FP"], ["FN", "TP"]]
    for r in range(2):
        for c in range(2):
            val = int(cm[r, c]) if r < cm.shape[0] and c < cm.shape[1] else 0
            x1 = ox + c * cw
            y1 = oy + r * ch
            x2 = x1 + cw - 12
            y2 = y1 + ch - 12
            
            intensity = min(1.0, val / max_val)
            if (r, c) in ((0, 0), (1, 1)):
                bg_color = (int(15 + 20 * intensity), int(45 + 95 * intensity), int(80 + 140 * intensity))
            else:
                bg_color = (int(50 + 120 * intensity), int(25 + 20 * intensity), int(35 + 30 * intensity)) if val > 0 else (30, 41, 59)
                
            draw.rectangle([x1, y1, x2, y2], fill=bg_color, outline=(51, 65, 85), width=2)
            
            label_str = f"{val:,}"
            sub_str = f"({cell_names[r][c]}: {val/total*100:.1f}%)"
            draw.text((x1 + 50, y1 + 40), label_str, fill=(255, 255, 255))
            draw.text((x1 + 40, y1 + 70), sub_str, fill=(203, 213, 225))
            
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path)
    
    try:
        static_img = os.path.join(os.path.dirname(RESULTS_DIR), "static", "img", os.path.basename(output_path))
        os.makedirs(os.path.dirname(static_img), exist_ok=True)
        img.save(static_img)
    except Exception:
        pass


def save_benchmark_results(data: Dict[str, Any], filepath: Optional[str] = None):
    """Saves benchmark results to JSON."""
    if filepath is None:
        os.makedirs(RESULTS_DIR, exist_ok=True)
        filepath = os.path.join(RESULTS_DIR, "benchmark_results.json")
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Results saved to {filepath}")


def load_benchmark_results(filepath: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Loads existing benchmark results if available."""
    if filepath is None:
        filepath = os.path.join(RESULTS_DIR, "benchmark_results.json")
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception:
        return None
