"""
SentinelGuard — Model Training Pipeline

Trains a RandomForestClassifier on behavioral mouse telemetry features.
Evaluates metrics with stratified train/test split and serializes model to model.joblib.

Usage:
    python backend/ml/train_model.py
"""

import os
import sys
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)

# Ensure backend root is on sys.path for direct script execution
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from ml.features import FEATURE_NAMES
from ml.dataset import generate_synthetic_data, save_synthetic_dataset


MODEL_FILE_PATH = CURRENT_DIR / "model.joblib"
METADATA_FILE_PATH = CURRENT_DIR / "model_meta.json"
DATASET_FILE_PATH = CURRENT_DIR / "data" / "synthetic_mouse_telemetry.csv"


def train_and_evaluate(
    data_path: Path = None,
    save_model: bool = True,
    n_samples: int = 1400,
    random_state: int = 42
) -> dict:
    """
    Executes end-to-end dataset generation/loading, training, evaluation, and serialization.
    """
    print("=" * 60)
    print("SENTINELGUARD — ML MODEL TRAINING PIPELINE")
    print("=" * 60)

    # 1. Dataset generation / loading
    if data_path and Path(data_path).exists():
        print(f"[Dataset] Loading existing dataset from: {data_path}")
        df = pd.read_csv(data_path)
    else:
        print(f"[Dataset] Generating synthetic telemetry dataset (n={n_samples}, seed={random_state})...")
        save_synthetic_dataset(DATASET_FILE_PATH, n_samples=n_samples, random_state=random_state)
        df = pd.read_csv(DATASET_FILE_PATH)
        print(f"[Dataset] Saved dataset artifact to: {DATASET_FILE_PATH}")

    # 2. Validation of required features
    missing_cols = [col for col in FEATURE_NAMES + ["label"] if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Training dataset is missing required columns: {missing_cols}")

    X = df[FEATURE_NAMES]
    y = df["label"].astype(int)

    print(f"[Data Summary] Total samples: {len(df)}")
    print(f"[Data Summary] Class distribution: Human (0) = {(y == 0).sum()}, Bot (1) = {(y == 1).sum()}")
    print(f"[Data Summary] Features used ({len(FEATURE_NAMES)}): {', '.join(FEATURE_NAMES)}")

    # 3. Stratified Train / Test split (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        stratify=y,
        random_state=random_state
    )
    print(f"[Split] Train samples: {len(X_train)} | Test samples: {len(X_test)}")

    # 4. Train RandomForestClassifier
    # Restrict max_depth to maintain smooth probability estimates and prevent memorization of noise
    print("[Training] Fitting RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)...")
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=6,
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=random_state,
        n_jobs=-1
    )
    clf.fit(X_train, y_train)

    # 5. Evaluate on Test set
    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)[:, 1]  # Class 1 = Bot probability

    accuracy = float(accuracy_score(y_test, y_pred))
    precision = float(precision_score(y_test, y_pred, zero_division=0))
    recall = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_test, y_proba))
    cm = confusion_matrix(y_test, y_pred).tolist()

    # Feature importances
    feature_importances = {
        name: round(float(imp), 4)
        for name, imp in zip(FEATURE_NAMES, clf.feature_importances_)
    }
    sorted_importances = dict(sorted(feature_importances.items(), key=lambda item: item[1], reverse=True))

    print("\n" + "-" * 40)
    print("EVALUATION METRICS (TEST SET)")
    print("-" * 40)
    print(f"Accuracy:         {accuracy:.4f}")
    print(f"Precision:        {precision:.4f}")
    print(f"Recall:           {recall:.4f}")
    print(f"F1-Score:         {f1:.4f}")
    print(f"ROC-AUC:          {roc_auc:.4f}")
    print(f"Confusion Matrix: TN={cm[0][0]}, FP={cm[0][1]}, FN={cm[1][0]}, TP={cm[1][1]}")
    print("\nTop Feature Importances:")
    for f, imp in sorted_importances.items():
        print(f"  - {f}: {imp:.4f}")

    metrics = {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "roc_auc": roc_auc,
        "confusion_matrix": {
            "true_negative": cm[0][0],
            "false_positive": cm[0][1],
            "false_negative": cm[1][0],
            "true_positive": cm[1][1]
        },
        "feature_importances": sorted_importances,
        "feature_names": FEATURE_NAMES,
        "random_state": random_state,
        "dataset_samples": len(df),
        "test_samples": len(X_test),
        "model_type": "RandomForestClassifier",
    }

    # 6. Save model and metadata
    if save_model:
        CURRENT_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(clf, MODEL_FILE_PATH)
        print(f"\n[Artifact] Model serialized successfully to: {MODEL_FILE_PATH}")

        with open(METADATA_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        print(f"[Artifact] Metadata written to: {METADATA_FILE_PATH}")

    print("=" * 60)
    print("TRAINING PIPELINE COMPLETED")
    print("=" * 60)
    return metrics


if __name__ == "__main__":
    train_and_evaluate()
