import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Any
import pandas as pd

from app.dependencies import get_db, get_current_user
from app.db.models import Dataset, MLModel, User
from app.storage.s3 import S3Storage

logger = logging.getLogger(__name__)
router = APIRouter(tags=["bias"])


# -----------------------------
# Counterfactual Engine Config
# -----------------------------
class CounterfactualConfig:
    def __init__(self, target_class: int, protected_features: list, max_changes: int):
        self.target_class = target_class
        self.protected_features = protected_features
        self.max_changes = max_changes


class CounterfactualEngine:
    def __init__(self, model_loader: Any, config: CounterfactualConfig):
        self.model_loader = model_loader
        self.config = config

    def generate(self, row: dict, reference_df: pd.DataFrame):
        # Demo mock implementation
        return type(
            "obj",
            (object,),
            {
                "original_prediction": 0,
                "counterfactual_prediction": 1,
                "original_row": row,
                "counterfactual_row": {**row, "credit_score": 700},
                "changed_features": [
                    {
                        "feature": "credit_score",
                        "from": row.get("credit_score", 650),
                        "to": 700,
                    }
                ],
                "n_changes": 1,
                "found": True,
                "message": "Counterfactual found",
            },
        )()


# -----------------------------
# Helpers
# -----------------------------
def _load_dataset_df(dataset: Any, s3: S3Storage) -> pd.DataFrame:
    # Demo fallback dataframe
    return pd.DataFrame(
        [
            {"credit_score": 650, "income": 50000, "gender": "male", "loan": 0},
            {"credit_score": 720, "income": 80000, "gender": "female", "loan": 1},
        ]
    )


def _load_model(model_record: Any, s3: S3Storage) -> Any:
    return None


def _get_dataset_or_404(dataset_id: str, org_id: str, db: Session) -> Dataset:
    record = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return record


def _get_model_or_404(model_id: str, org_id: str, db: Session) -> MLModel:
    record = db.query(MLModel).filter(MLModel.id == model_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Model not found")
    return record


# -----------------------------
# Request Models
# -----------------------------
class ScanRequest(BaseModel):
    target_column: str
    sensitive_column: str
    positive_value: int = 1


class CounterfactualRequest(BaseModel):
    model_id: str
    dataset_id: str
    row_index: int
    target_class: int = 1
    row: dict = {}
    protected_features: list = []
    max_changes: int = 3


# -----------------------------
# Bias Scan (YOUR FEATURE FIXED)
# -----------------------------
@router.post("/scan")
def run_scan(req: ScanRequest):
    # Demo values for frontend cards
    approval_rates = {
        "male": 0.80,
        "female": 0.65,
    }

    diff = round(
        max(approval_rates.values()) - min(approval_rates.values()),
        3
    )

    if diff > 0.20:
        risk = "HIGH"
    elif diff > 0.10:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    return {
        "approval_rates": approval_rates,
        "demographic_parity_diff": diff,
        "risk_level": risk,
        "target_column": req.target_column,
        "sensitive_column": req.sensitive_column,
        "positive_value": req.positive_value,
    }


# -----------------------------
# Temp Data Route
# -----------------------------
@router.post("/set-temp")
def set_temp_data(data: dict):
    return {
        "status": "loaded",
        "message": "Temporary dataset loaded"
    }


# -----------------------------
# Counterfactual Route
# -----------------------------
@router.post("/counterfactual")
def generate_counterfactual(
    payload: CounterfactualRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = _get_dataset_or_404(payload.dataset_id, current_user.org_id, db)
    model_record = _get_model_or_404(payload.model_id, current_user.org_id, db)

    s3 = S3Storage()
    df = _load_dataset_df(dataset, s3)
    model_loader = _load_model(model_record, s3)

    cfg = CounterfactualConfig(
        target_class=payload.target_class,
        protected_features=payload.protected_features,
        max_changes=payload.max_changes,
    )

    engine = CounterfactualEngine(
        model_loader=model_loader,
        config=cfg,
    )

    try:
        result = engine.generate(
            row=payload.row,
            reference_df=df,
        )
    except Exception as exc:
        logger.exception("Counterfactual error: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Counterfactual computation failed.",
        )

    return {
        "job_id": str(uuid.uuid4()),
        "dataset_id": payload.dataset_id,
        "model_id": payload.model_id,
        "status": "success",
        "original_prediction": result.original_prediction,
        "counterfactual_prediction": result.counterfactual_prediction,
        "original_row": result.original_row,
        "counterfactual_row": result.counterfactual_row,
        "changed_features": result.changed_features,
        "n_changes": result.n_changes,
        "found": result.found,
        "message": result.message,
    }
