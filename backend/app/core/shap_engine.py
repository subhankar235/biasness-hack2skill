import pandas as pd
import numpy as np
import shap

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder


def run_shap_analysis(df: pd.DataFrame):
    """
    Production-grade SHAP explainability engine
    - Handles strings
    - Handles missing values
    - Handles binary/multiclass targets
    - Returns stable JSON response
    """

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

    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=6,
        random_state=42
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

    flags = []

    for item in top_features:
        name = item["feature"].lower()

        if "gender" in name or "sex" in name:
            flags.append(
                "Gender-related feature has measurable impact."
            )

        if "age" in name or "dob" in name:
            flags.append(
                "Age-related feature influences outcomes."
            )

        if "race" in name or "ethnicity" in name:
            flags.append(
                "Race / ethnicity signal detected."
            )

        if "religion" in name:
            flags.append(
                "Religion-related attribute detected."
            )

    if not flags:
        flags.append(
            "No dominant sensitive feature influence detected."
        )

    return {
        "top_features": top_features,
        "bias_flags": list(set(flags))
    }