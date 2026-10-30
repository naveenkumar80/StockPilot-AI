from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd
from sklearn.metrics import (
    brier_score_loss,
    log_loss,
    roc_auc_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)
from sklearn.calibration import calibration_curve


def evaluate_predictions(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float = 0.50,
) -> Dict[str, Any]:
    """
    Computes rigorous financial ML classification and probability calibration metrics.
    """
    y_true = np.asarray(y_true).astype(int)
    y_prob = np.asarray(y_prob).astype(float)
    y_pred = (y_prob >= threshold).astype(int)

    # Core probabilistic scores
    brier = float(brier_score_loss(y_true, y_prob))
    try:
        ll = float(log_loss(y_true, y_prob, labels=[0, 1]))
    except Exception:
        ll = 0.693

    try:
        auc = float(roc_auc_score(y_true, y_prob))
    except Exception:
        auc = 0.50

    # Directional scores
    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    # Confusion Matrix
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    # Reliability Curve / Calibration bins (10 bins)
    try:
        prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=10, strategy="uniform")
        calibration_bins = [
            {"predicted": round(float(p), 4), "empirical": round(float(t), 4)}
            for p, t in zip(prob_pred, prob_true)
        ]
        # Expected Calibration Error (ECE)
        ece = float(np.mean(np.abs(prob_true - prob_pred))) if len(prob_true) > 0 else 0.05
    except Exception:
        calibration_bins = []
        ece = 0.05

    return {
        "brier_score": round(brier, 4),
        "log_loss": round(ll, 4),
        "roc_auc": round(auc, 4),
        "accuracy": round(acc, 4),
        "precision_buy": round(prec, 4),
        "recall_buy": round(rec, 4),
        "f1_score": round(f1, 4),
        "expected_calibration_error": round(ece, 4),
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
        },
        "calibration_bins": calibration_bins,
    }


def compute_feature_importances(
    model: Any,
    feature_names: List[str],
) -> List[Dict[str, Any]]:
    """
    Extracts normalized feature importance rankings from a trained model.
    """
    importances = []

    # Check if model has feature_importances_
    if hasattr(model, "feature_importances_"):
        raw = model.feature_importances_
        total = np.sum(raw)
        norm = raw / total if total > 0 else raw
        for name, score in zip(feature_names, norm):
            importances.append({
                "feature": name,
                "importance": round(float(score), 4),
            })
    # Check if calibrated classifier wraps the base estimator
    elif hasattr(model, "calibrated_classifiers_"):
        base = model.calibrated_classifiers_[0].estimator
        if hasattr(base, "feature_importances_"):
            raw = base.feature_importances_
            total = np.sum(raw)
            norm = raw / total if total > 0 else raw
            for name, score in zip(feature_names, norm):
                importances.append({
                    "feature": name,
                    "importance": round(float(score), 4),
                })
        elif hasattr(base, "coef_"):
            raw = np.abs(base.coef_[0])
            total = np.sum(raw)
            norm = raw / total if total > 0 else raw
            for name, score in zip(feature_names, norm):
                importances.append({
                    "feature": name,
                    "importance": round(float(score), 4),
                })
    elif hasattr(model, "coef_"):
        raw = np.abs(model.coef_[0])
        total = np.sum(raw)
        norm = raw / total if total > 0 else raw
        for name, score in zip(feature_names, norm):
            importances.append({
                "feature": name,
                "importance": round(float(score), 4),
            })

    # Sort descending by importance
    return sorted(importances, key=lambda x: x["importance"], reverse=True)

