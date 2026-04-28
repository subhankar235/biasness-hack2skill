# app/core/remediation.py
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_curve
from fairlearn.reductions import ExponentiatedGradient, DemographicParity
from fairlearn.postprocessing import ThresholdOptimizer
from fairlearn.metrics import (
    demographic_parity_difference,
    equalized_odds_difference,
)
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
    """One-hot encode everything except target + sensitive."""
    drop_cols = [c for c in [target_col, sensitive_col] if c in df.columns]
    return pd.get_dummies(df.drop(columns=drop_cols))


def _before_metrics(y_true, y_pred, sensitive) -> dict:
    dp = float(demographic_parity_difference(y_true, y_pred, sensitive_features=sensitive))
    eo = float(equalized_odds_difference(y_true, y_pred, sensitive_features=sensitive))
    group_rates = {
        str(g): round(float((y_pred[sensitive == g]).mean()), 4)
        for g in sensitive.unique()
    }
    return {
        "demographic_parity_difference": round(dp, 4),
        "equalized_odds_difference": round(eo, 4),
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
    y = df[target_col]
    sensitive = df[sensitive_col]

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

    after_dp = float(demographic_parity_difference(y, y_pred_after, sensitive_features=sensitive))
    after_eo = float(equalized_odds_difference(y, y_pred_after, sensitive_features=sensitive))
    after_rates = {
        str(g): round(float((y_pred_after[sensitive == g]).mean()), 4)
        for g in sensitive.unique()
    }
    after = {
        "demographic_parity_difference": round(after_dp, 4),
        "equalized_odds_difference": round(after_eo, 4),
        "group_rates": after_rates,
    }

    return {
        "strategy": "reweight",
        "method_description": (
            "ExponentiatedGradient with DemographicParity constraint (Fairlearn). "
            "Iteratively re-weights training samples to reduce selection rate disparity."
        ),
        "before": before,
        "after": after,
        "improvement_pct": _improvement(before["demographic_parity_difference"], after_dp),
        "verdict": "improved" if abs(after_dp) < abs(before["demographic_parity_difference"]) else "no_improvement",
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
    y = df[target_col]
    sensitive = df[sensitive_col]

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
    y_pred_after = resampled_model.predict(X)   # evaluate on original distribution

    after_dp = float(demographic_parity_difference(y, y_pred_after, sensitive_features=sensitive))
    after_eo = float(equalized_odds_difference(y, y_pred_after, sensitive_features=sensitive))
    after_rates = {
        str(g): round(float((y_pred_after[sensitive == g]).mean()), 4)
        for g in sensitive.unique()
    }
    after = {
        "demographic_parity_difference": round(after_dp, 4),
        "equalized_odds_difference": round(after_eo, 4),
        "group_rates": after_rates,
    }

    return {
        "strategy": "resample",
        "method_description": (
            "SMOTENC synthetic oversampling to balance group representation in training data. "
            f"Resampled from {len(y)} → {len(y_res)} rows. "
            f"Categorical columns handled: {len(cat_indices)}."
        ),
        "before": before,
        "after": after,
        "improvement_pct": _improvement(before["demographic_parity_difference"], after_dp),
        "verdict": "improved" if abs(after_dp) < abs(before["demographic_parity_difference"]) else "no_improvement",
    }


# ─────────────────────────────────────────────
# Strategy 3 — Threshold Optimization (post-processing)
# Uses Fairlearn ThresholdOptimizer per group
# ─────────────────────────────────────────────

def threshold(
    df: pd.DataFrame,
    sensitive_col: str,
    target_col: str,
) -> dict:
    X = _encode(df, target_col, sensitive_col)
    y = df[target_col]
    sensitive = df[sensitive_col]

    # Baseline
    baseline = LogisticRegression(max_iter=500, random_state=42).fit(X, y)
    y_pred_before = baseline.predict(X)
    before = _before_metrics(y, y_pred_before, sensitive)

    # ThresholdOptimizer — post-processing, equalized odds constraint
    optimizer = ThresholdOptimizer(
        estimator=baseline,
        constraints="equalized_odds",
        objective="balanced_accuracy_score",
        prefit=True,
        predict_method="predict_proba",
    )
    optimizer.fit(X, y, sensitive_features=sensitive)
    y_pred_after = optimizer.predict(X, sensitive_features=sensitive)

    # Also compute per-group thresholds for transparency
    y_proba = baseline.predict_proba(X)[:, 1]
    group_thresholds = {}
    for group in sensitive.unique():
        mask = sensitive == group
        fpr, tpr, thresh = roc_curve(y[mask], y_proba[mask])
        best_idx = int(np.argmax(tpr - fpr))   # Youden's J
        group_thresholds[str(group)] = round(float(thresh[best_idx]), 4)

    after_dp = float(demographic_parity_difference(y, y_pred_after, sensitive_features=sensitive))
    after_eo = float(equalized_odds_difference(y, y_pred_after, sensitive_features=sensitive))
    after_rates = {
        str(g): round(float((y_pred_after[sensitive == g]).mean()), 4)
        for g in sensitive.unique()
    }
    after = {
        "demographic_parity_difference": round(after_dp, 4),
        "equalized_odds_difference": round(after_eo, 4),
        "group_rates": after_rates,
    }

    return {
        "strategy": "threshold",
        "method_description": (
            f"ThresholdOptimizer (Fairlearn) with equalized_odds constraint. "
            f"Per-group Youden's J thresholds: {group_thresholds}."
        ),
        "before": before,
        "after": after,
        "improvement_pct": _improvement(before["demographic_parity_difference"], after_dp),
        "verdict": "improved" if abs(after_dp) < abs(before["demographic_parity_difference"]) else "no_improvement",
        "group_thresholds": group_thresholds,
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