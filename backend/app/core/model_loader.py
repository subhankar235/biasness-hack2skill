"""
core/model_loader.py
Loads a persisted model from a local path.
Supports:
  - sklearn-compatible models saved with joblib
  - ONNX models via onnxruntime
Exposes a unified .predict() / .predict_proba() interface used by
shap_engine and counterfactual engines.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class ModelLoader:
    """
    Load a model once; reuse for many predictions.

    Usage
    -----
        loader = ModelLoader.from_path("/tmp/my_model.joblib")
        preds  = loader.predict(df)
        probas = loader.predict_proba(df)   # only for classifiers
    """

    def __init__(self, raw_model: Any, model_type: str):
        self.raw_model = raw_model
        self.model_type = model_type   # "joblib" | "onnx"

    # ------------------------------------------------------------------
    # Factory methods
    # ------------------------------------------------------------------

    @classmethod
    def from_path(cls, path: str | Path) -> "ModelLoader":
        """
        Auto-detect model type from file extension and load.
        Raises ValueError for unsupported extensions.
        """
        path = Path(path)
        ext = path.suffix.lower()

        if ext in (".joblib", ".pkl", ".pickle"):
            return cls._load_joblib(path)
        elif ext == ".onnx":
            return cls._load_onnx(path)
        else:
            raise ValueError(
                f"Unsupported model file extension '{ext}'. "
                "Expected .joblib, .pkl, .pickle, or .onnx"
            )

    @classmethod
    def _load_joblib(cls, path: Path) -> "ModelLoader":
        import joblib  # lazy import — not needed for ONNX path

        logger.info("Loading joblib model from %s", path)
        model = joblib.load(path)
        return cls(raw_model=model, model_type="joblib")

    @classmethod
    def _load_onnx(cls, path: Path) -> "ModelLoader":
        import onnxruntime as ort  # lazy import — not needed for joblib path

        logger.info("Loading ONNX model from %s", path)
        session = ort.InferenceSession(str(path))
        return cls(raw_model=session, model_type="onnx")

    # ------------------------------------------------------------------
    # Inference interface
    # ------------------------------------------------------------------

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Return hard class predictions (or regression values)."""
        if self.model_type == "joblib":
            return np.array(self.raw_model.predict(X))
        elif self.model_type == "onnx":
            return self._onnx_predict(X)
        raise RuntimeError(f"Unknown model_type: {self.model_type}")

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Return class probabilities.
        Falls back to one-hot encoding of hard predictions for models
        that don't expose probabilities (e.g. plain regressors or ONNX
        models without a probability output).
        """
        if self.model_type == "joblib":
            if hasattr(self.raw_model, "predict_proba"):
                return np.array(self.raw_model.predict_proba(X))
            logger.warning("Model has no predict_proba; returning hard predictions.")
            return self.predict(X).reshape(-1, 1)

        elif self.model_type == "onnx":
            return self._onnx_predict_proba(X)

        raise RuntimeError(f"Unknown model_type: {self.model_type}")

    # ------------------------------------------------------------------
    # ONNX helpers
    # ------------------------------------------------------------------

    def _onnx_prepare_input(self, X: pd.DataFrame) -> dict[str, np.ndarray]:
        """
        ONNX Runtime expects a dict of {input_name: numpy_array}.
        We assume a single float32 input tensor named after the first
        input node.
        """
        import onnxruntime as ort  # noqa: F401 — already loaded at this point

        session: Any = self.raw_model
        input_name = session.get_inputs()[0].name
        X_array = X.values.astype(np.float32)
        return {input_name: X_array}

    def _onnx_predict(self, X: pd.DataFrame) -> np.ndarray:
        session: Any = self.raw_model
        inputs = self._onnx_prepare_input(X)
        # First output is typically the label
        outputs = session.run(None, inputs)
        return np.array(outputs[0]).flatten()

    def _onnx_predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        session: Any = self.raw_model
        inputs = self._onnx_prepare_input(X)
        outputs = session.run(None, inputs)

        if len(outputs) >= 2:
            # Second output is typically the probability map (list of dicts or array)
            proba_output = outputs[1]
            if isinstance(proba_output, list):
                # [{0: p0, 1: p1}, ...] format from sklearn ONNX export
                classes = sorted(proba_output[0].keys())
                return np.array([[d[c] for c in classes] for d in proba_output])
            return np.array(proba_output)

        # Fallback: hard predictions only
        logger.warning("ONNX model has only one output; returning hard predictions.")
        return self._onnx_predict(X).reshape(-1, 1)

    # ------------------------------------------------------------------
    # Metadata helpers
    # ------------------------------------------------------------------

    def feature_names(self) -> list[str] | None:
        """Return feature names if the underlying model exposes them."""
        if self.model_type == "joblib" and hasattr(self.raw_model, "feature_names_in_"):
            return list(self.raw_model.feature_names_in_)
        return None

    def __repr__(self) -> str:
        return f"ModelLoader(type={self.model_type}, model={type(self.raw_model).__name__})"