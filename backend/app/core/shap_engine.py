import pandas as pd
import numpy as np
import shap
import hashlib
import joblib
import os

from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder


MODELS_DIR = Path(__file__).parent.parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)


def _get_data_seed(df: pd.DataFrame) -> int:
    """Generate deterministic seed from data content."""
    data_str = df.to_csv(index=False)
    hash_obj = hashlib.sha256(data_str.encode())
    return int(hash_obj.hexdigest()[:8], 16) % (2**31)


def _get_model_path(dataset_name: str = None, df: pd.DataFrame = None) -> Path:
    """Get model save path - uses data content hash if available."""
    if df is not None:
        data_hash = hashlib.sha256(df.to_csv(index=False).encode()).hexdigest()[:16]
        return MODELS_DIR / f"shap_model_{data_hash}.joblib"
    if dataset_name:
        safe_name = "".join(c for c in dataset_name if c.isalnum()).lower()[:20]
        return MODELS_DIR / f"shap_model_{safe_name}.joblib"
    return MODELS_DIR / "shap_model_default.joblib"


def run_shap_analysis(df: pd.DataFrame, dataset_name: str = None):
    """
    Production-grade SHAP explainability engine
    - Handles strings
    - Handles missing values
    - Handles binary/multiclass targets
    - Returns stable JSON response
    """
    import logging
    logger = logging.getLogger(__name__)

    if df is None or df.empty:
        return {
            "top_features": [],
            "bias_flags": ["Dataset is empty."]
        }

    logger.info(f"SHAP analysis input: {len(df)} rows, columns: {list(df.columns)}")

    if df is None or df.empty:
        return {
            "top_features": [],
            "bias_flags": ["Dataset is empty."]
        }

    if len(df.columns) < 2:
        return {
            "top_features": [],
            "bias_flags": ["Need at least 2 columns."]
        }

    target_col = df.columns[-1]

    X = df.drop(columns=[target_col]).copy()
    y = df[target_col].copy()

    X = X.fillna("Unknown")
    y = y.fillna("Unknown")

    encoders = {}

    for col in X.columns:
        if X[col].dtype == "object":
            le = LabelEncoder()
            X[col] = le.fit_transform(
                X[col].astype(str).str.strip()
            )
            encoders[col] = le

    for col in X.columns:
        if X[col].dtype == "bool":
            X[col] = X[col].astype(int)

    X = X.apply(pd.to_numeric, errors="coerce").fillna(0)

    if y.dtype == "object":
        y_encoder = LabelEncoder()
        y = y_encoder.fit_transform(
            y.astype(str).str.strip()
        )

    # Need at least 2 classes
    if len(np.unique(y)) < 2:
        return {
            "top_features": [],
            "bias_flags": ["Target column needs 2+ classes."]
        }

    # Always train fresh model for each dataset (no caching)
    seed = _get_data_seed(df)
    logger.info(f"Generated seed: {seed}")

    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=6,
        random_state=seed
    )
    model.fit(X, y)

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    if isinstance(shap_values, list):
        vals = shap_values[-1]
    else:
        vals = shap_values

    vals = np.array(vals)

    if vals.ndim == 3:
        vals = vals[:, :, 0]

    importance = np.abs(vals).mean(axis=0)

    if len(importance.shape) > 1:
        importance = importance.flatten()

    results = []

    for feature, score in zip(X.columns, importance):
        results.append({
            "feature": str(feature),
            "importance": round(float(score), 4)
        })

    results = sorted(
        results,
        key=lambda x: x["importance"],
        reverse=True
    )

    top_features = results[:8]

    raw_base = explainer.expected_value if hasattr(explainer, 'expected_value') else None
    if raw_base is not None:
        base_arr = np.array(raw_base)
        if base_arr.ndim == 0:
            base_value = float(base_arr)
        elif base_arr.size > 0:
            base_value = float(base_arr.flatten()[0])
        else:
            base_value = 0.0
    else:
        base_value = 0.0

    local_explanations = []
    for i in range(min(5, len(vals))):
        row_shap = []
        for feat, shap_val in zip(X.columns, vals[i]):
            row_shap.append({
                "feature": str(feat),
                "value": round(float(shap_val), 4),
                "positive": bool(shap_val > 0)
            })
        row_shap = sorted(row_shap, key=lambda x: abs(x["value"]), reverse=True)[:5]
        local_explanations.append({
            "row_index": i,
            "contributions": row_shap,
            "base_value": base_value,
            "prediction": round(base_value + sum(vals[i]), 4)
        })

    flags = []
    total_importance = sum(item["importance"] for item in top_features)

    for item in top_features:
        name = item["feature"].lower()
        imp_pct = (item["importance"] / total_importance * 100) if total_importance > 0 else 0

        if "gender" in name or "sex" in name:
            flags.append({
                "type": "gender",
                "message": f"Gender shows {imp_pct:.1f}% feature influence, potential bias indicator",
                "impact": round(imp_pct, 1)
            })

        if "age" in name or "dob" in name:
            flags.append({
                "type": "age",
                "message": f"Age contributes {imp_pct:.1f}% to prediction, check for age bias",
                "impact": round(imp_pct, 1)
            })

        if "race" in name or "ethnicity" in name:
            flags.append({
                "type": "race",
                "message": f"Race/ethnicity shows {imp_pct:.1f}% impact, may indicate historical bias",
                "impact": round(imp_pct, 1)
            })

        if "religion" in name:
            flags.append({
                "type": "religion",
                "message": f"Religion feature detected with {imp_pct:.1f}% influence",
                "impact": round(imp_pct, 1)
            })

    if not flags:
        flags.append({
            "type": "none",
            "message": "No dominant sensitive feature influence detected.",
            "impact": 0.0
        })

    return {
        "top_features": top_features,
        "bias_flags": flags,
        "local_explanations": local_explanations,
        "base_value": base_value
    }