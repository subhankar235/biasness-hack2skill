# Tools used:

# pandas → handle data
# numpy → prepare model input
# joblib / onnxruntime → Load Model/run model
# shap (optional) → explain why change happened
# FastAPI → create API endpoint
# React → display results (flip rate, comparisons)


"""
Counterfactual explanation engine.
Given a row and a loaded model, find the minimal feature flips
that change the prediction outcome.
"""

from __future__ import annotations

import itertools
from typing import Any

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _predict(model: Any, row_df: pd.DataFrame) -> Any:
    """Run model.predict on a single-row DataFrame; return scalar label."""
    pred = model.predict(row_df)
    return pred[0] if hasattr(pred, "__len__") else pred


def _predict_proba(model: Any, row_df: pd.DataFrame) -> np.ndarray | None:
    if hasattr(model, "predict_proba"):
        return model.predict_proba(row_df)[0]
    return None


# ---------------------------------------------------------------------------
# main function
# ---------------------------------------------------------------------------

def generate_counterfactuals(
    row: dict,
    model: Any,
    feature_ranges: dict[str, list | tuple],
    sensitive_features: list[str] | None = None,
    max_features_to_flip: int = 3,
    max_results: int = 10,
) -> dict:
    """
    Parameters
    ----------
    row : dict
        Original input row (feature_name -> value).
    model : Any
        Loaded sklearn / onnx model with a .predict() method.
    feature_ranges : dict
        Candidate values per feature, e.g.
          {"age": [25, 35, 45], "income": [30000, 60000, 90000]}
        Sensitive features are excluded automatically.
    sensitive_features : list[str], optional
        Features that must NOT be changed in counterfactuals.
    max_features_to_flip : int
        Maximum number of features to change at once (1..3 recommended).
    max_results : int
        Cap on returned counterfactuals.

    Returns
    -------
    dict with keys:
        original_prediction, original_proba,
        counterfactuals (list of dicts)
    """
    sensitive = set(sensitive_features or [])
    mutable = {k: v for k, v in feature_ranges.items() if k not in sensitive}

    original_df = pd.DataFrame([row])
    original_pred = _predict(model, original_df)
    original_proba = _predict_proba(model, original_df)

    results: list[dict] = []

    for n_flips in range(1, max_features_to_flip + 1):
        for feature_combo in itertools.combinations(mutable.keys(), n_flips):
            candidate_value_lists = [mutable[f] for f in feature_combo]

            for value_combo in itertools.product(*candidate_value_lists):
                if len(results) >= max_results:
                    break

                modified = dict(row)
                changes = {}
                for feat, val in zip(feature_combo, value_combo):
                    if modified[feat] == val:
                        continue
                    changes[feat] = {"from": modified[feat], "to": val}
                    modified[feat] = val

                if not changes:
                    continue

                mod_df = pd.DataFrame([modified])
                new_pred = _predict(model, mod_df)
                new_proba = _predict_proba(model, mod_df)

                if new_pred != original_pred:
                    results.append(
                        {
                            "row": modified,
                            "changes": changes,
                            "new_prediction": new_pred,
                            "new_proba": (
                                new_proba.tolist() if new_proba is not None else None
                            ),
                            "n_changes": len(changes),
                        }
                    )

            if len(results) >= max_results:
                break

    # sort by fewest changes first
    results.sort(key=lambda x: x["n_changes"])

    return {
        "original_row": row,
        "original_prediction": int(original_pred)
        if hasattr(original_pred, "item")
        else original_pred,
        "original_proba": original_proba.tolist()
        if original_proba is not None
        else None,
        "counterfactzuals": results[:max_results],
    }