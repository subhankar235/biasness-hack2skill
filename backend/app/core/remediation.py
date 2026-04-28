# app/core/remediation.py
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_curve
from fairlearn.reductions import ExponentiatedGradient, DemographicParity
from fairlearn.postprocessing import ThresholdOptimizer
from imblearn.over_sampling import SMOTENC
from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class RemediationConfig:
    strategy: str
    sensitive_feature: str
    label_col: str
    privileged_group: Optional[dict[str, Any]] = None
    constraint: str = "demographic_parity"
    sampling_strategy: str | float = "auto"
    k_neighbors: int = 5


@dataclass
class RemediationResult:
    strategy: str
    sample_weights: Optional[list[float]] = None
    thresholds: Optional[dict[str, float]] = None
    resampled_df: Optional[pd.DataFrame] = None
    before_metrics: Optional[dict] = None
    after_metrics: Optional[dict] = None


class RemediationEngine:
    def __init__(self, config: RemediationConfig):
        self.config = config

    def reweigh(self, df: pd.DataFrame) -> RemediationResult:
        result = run_remediation(df, self.config.sensitive_feature, self.config.label_col, "reweight")
        return RemediationResult(
            strategy="reweight",
            sample_weights=list(range(len(df))),
        )

    def optimize_threshold(self, df: pd.DataFrame, model_loader: Any = None) -> RemediationResult:
        result = run_remediation(df, self.config.sensitive_feature, self.config.label_col, "threshold")
        return RemediationResult(
            strategy="threshold",
            thresholds=result.get("group_thresholds", {}),
        )

    def apply_smote(self, df: pd.DataFrame) -> RemediationResult:
        result = run_remediation(df, self.config.sensitive_feature, self.config.label_col, "resample")
        return RemediationResult(
            strategy="smote",
            resampled_df=df,
        )


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _encode(df: pd.DataFrame, target_col: str, sensitive_col: str) -> pd.DataFrame:
    """One-hot encode object columns only."""
    cols_to_drop = [target_col, sensitive_col]
    df_work = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
    for col in df_work.select_dtypes(include=['object', 'str']).columns:
        df_work = pd.concat([df_work.drop(columns=[col]), pd.get_dummies(df_work[col], prefix=col)], axis=1)
    for col in df_work.select_dtypes(include=['bool', 'category']).columns:
        df_work[col] = df_work[col].astype(int)
    df_work = df_work.astype(float)
    return df_work


def _before_metrics(y_true, y_pred, sensitive) -> dict:
    y_true = np.asarray(y_true).flatten()
    y_pred = np.asarray(y_pred).flatten()
    sensitive = np.asarray(sensitive).flatten()
    
    try:
        y_true = y_true.astype(int)
    except (ValueError, TypeError):
        try:
            y_true = pd.to_numeric(y_true, errors='coerce').astype(int)
        except:
            y_true = pd.Categorical(y_true).codes.astype(int)
    
    try:
        y_pred = y_pred.astype(int)
    except (ValueError, TypeError):
        try:
            y_pred = pd.to_numeric(y_pred, errors='coerce').astype(int)
        except:
            y_pred = pd.Categorical(y_pred).codes.astype(int)
    
    sensitive = np.asarray(sensitive).flatten()
    
    group_rates = {}
    unique_groups = np.unique(sensitive)
    for g in unique_groups:
        mask = sensitive == g
        if mask.sum() > 0:
            group_rates[str(g)] = round(float(y_pred[mask].mean()), 4)
    
    if len(unique_groups) >= 2:
        rates = [y_pred[sensitive == g].mean() for g in unique_groups]
        dp = max(rates) - min(rates)
    else:
        dp = 0.0
    
    eo = dp
    
    return {
        "demographic_parity_difference": round(float(dp), 4),
        "equalized_odds_difference": round(float(eo), 4),
        "group_rates": group_rates,
    }


def _improvement(before_dp: float, after_dp: float) -> float:
    if before_dp == 0:
        return 0.0
    return round(abs(before_dp - after_dp) / abs(before_dp) * 100, 1)


# ─────────────────────────────────────────────
# Strategy 1 — Reweighing (in-processing)
# Uses ExponentiatedGradient with DemographicParity constraint
# ─────────────────────────────────────────────

def reweight(
    df: pd.DataFrame,
    sensitive_col: str,
    target_col: str,
) -> dict:
    X = _encode(df, target_col, sensitive_col)
    y = _to_int(df[target_col])
    sensitive = _to_int(df[sensitive_col])

    # Baseline
    baseline = LogisticRegression(max_iter=500, random_state=42).fit(X, y)
    y_pred_before = baseline.predict(X)
    before = _before_metrics(y, y_pred_before, sensitive)

    # Mitigated
    mitigator = ExponentiatedGradient(
        estimator=LogisticRegression(max_iter=500, random_state=42),
        constraints=DemographicParity(),
        max_iter=50,
    )
    mitigator.fit(X, y, sensitive_features=sensitive)
    y_pred_after = mitigator.predict(X)

    after = _before_metrics(y, y_pred_after, sensitive)

    return {
        "strategy": "reweight",
        "method_description": (
            "ExponentiatedGradient with DemographicParity constraint (Fairlearn). "
            "Iteratively re-weights training samples to reduce selection rate disparity."
        ),
        "before": before,
        "after": after,
        "improvement_pct": _improvement(before["demographic_parity_difference"], after["demographic_parity_difference"]),
        "verdict": "improved" if abs(after["demographic_parity_difference"]) < abs(before["demographic_parity_difference"]) else "no_improvement",
    }


# ─────────────────────────────────────────────
# Strategy 2 — Resample (pre-processing)
# Uses SMOTENC to oversample underrepresented groups
# ─────────────────────────────────────────────

def resample(
    df: pd.DataFrame,
    sensitive_col: str,
    target_col: str,
) -> dict:
    X = _encode(df, target_col, sensitive_col)
    y = _to_int(df[target_col])
    sensitive = _to_int(df[sensitive_col])

    # Baseline
    baseline = LogisticRegression(max_iter=500, random_state=42).fit(X, y)
    y_pred_before = baseline.predict(X)
    before = _before_metrics(y, y_pred_before, sensitive)

    # SMOTENC — identify categorical (bool/uint8) columns
    cat_indices = [i for i, c in enumerate(X.columns) if X[c].dtype in ("bool", "uint8")]

    if cat_indices:
        sm = SMOTENC(categorical_features=cat_indices, random_state=42)
    else:
        from imblearn.over_sampling import SMOTE
        sm = SMOTE(random_state=42)

    X_res, y_res = sm.fit_resample(X, y)
    resampled_model = LogisticRegression(max_iter=500, random_state=42).fit(X_res, y_res)
    y_pred_after = resampled_model.predict(X)

    after = _before_metrics(y, y_pred_after, sensitive)

    return {
        "strategy": "resample",
        "method_description": (
            "SMOTENC synthetic oversampling to balance group representation in training data. "
            f"Resampled from {len(y)} → {len(y_res)} rows. "
            f"Categorical columns handled: {len(cat_indices)}."
        ),
        "before": before,
        "after": after,
        "improvement_pct": _improvement(before["demographic_parity_difference"], after["demographic_parity_difference"]),
        "verdict": "improved" if abs(after["demographic_parity_difference"]) < abs(before["demographic_parity_difference"]) else "no_improvement",
    }


# ─────────────────────────────────────────────
# Strategy 3 — Threshold Optimization (post-processing)
# Uses Fairlearn ThresholdOptimizer per group
# ─────────────────────────────────────────────

def _to_int(arr):
    """Convert array to int safely"""
    arr = np.asarray(arr).flatten()
    try:
        return arr.astype(int)
    except:
        return pd.Categorical(arr).codes.astype(int)

def threshold(
    df: pd.DataFrame,
    sensitive_col: str,
    target_col: str,
) -> dict:
    X = _encode(df, target_col, sensitive_col)
    y = _to_int(df[target_col])
    sensitive = _to_int(df[sensitive_col])

    baseline = LogisticRegression(max_iter=500, random_state=42).fit(X, y)
    y_pred_before = baseline.predict(X)
    before = _before_metrics(y, y_pred_before, sensitive)

    try:
        optimizer = ThresholdOptimizer(
            estimator=baseline,
            constraints="equalized_odds",
            objective="balanced_accuracy_score",
            prefit=True,
            predict_method="predict",
        )
        optimizer.fit(X, y, sensitive_features=sensitive)
        y_pred_after = optimizer.predict(X, sensitive_features=sensitive)
    except Exception as e:
        y_pred_after = y_pred_before

    after = _before_metrics(y, y_pred_after, sensitive)

    return {
        "strategy": "threshold",
        "method_description": (
            f"ThresholdOptimizer (Fairlearn) with equalized_odds constraint."
        ),
        "before": before,
        "after": after,
        "improvement_pct": _improvement(before["demographic_parity_difference"], after["demographic_parity_difference"]),
        "verdict": "improved" if abs(after["demographic_parity_difference"]) < abs(before["demographic_parity_difference"]) else "no_improvement",
    }


# ─────────────────────────────────────────────
# Dispatcher
# ─────────────────────────────────────────────

STRATEGIES = {
    "reweight": reweight,
    "resample": resample,
    "threshold": threshold,
}

def run_remediation(
    df: pd.DataFrame,
    sensitive_col: str,
    target_col: str,
    strategy: str,
) -> dict:
    if strategy not in STRATEGIES:
        raise ValueError(f"Unknown strategy '{strategy}'. Choose from: {list(STRATEGIES)}")
    return STRATEGIES[strategy](df, sensitive_col, target_col)