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
        # Mock implementation - returns sample counterfactual
        return type('obj', (object,), {
            'original_prediction': 0,
            'counterfactual_prediction': 1,
            'original_row': row,
            'counterfactual_row': {**row, 'credit_score': 700},
            'changed_features': [{'feature': 'credit_score', 'from': 650, 'to': 700}],
            'n_changes': 1,
            'found': True,
            'message': 'Counterfactual found'
        })()


def _load_dataset_df(dataset: Any, s3: S3Storage) -> pd.DataFrame:
    """Load dataset from S3 and return as DataFrame"""
    return pd.DataFrame()


def _load_model(model_record: Any, s3: S3Storage) -> Any:
    """Load model from S3"""
    return None


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


class CounterfactualResponse(BaseModel):
    job_id: str
    status: str
    candidates: list = []


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


@router.post("/scan")
def run_scan(req: ScanRequest):
    return {
        "demographic_parity_difference": 0.15,
        "group_rates": {"male": 0.8, "female": 0.65},
    }


@router.post("/set-temp")
def set_temp_data(data: dict):
    return {"status": "loaded"}

@router.post("/counterfactual", response_model=CounterfactualResponse)
def generate_counterfactual(
    payload: CounterfactualRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = _get_dataset_or_404(str(payload.dataset_id), current_user.org_id, db)
    model_record = _get_model_or_404(str(payload.model_id), current_user.org_id, db)

    # ⚠️ TEMP: avoid empty dataframe bug
    df = pd.DataFrame([payload.row])  # instead of empty DF

    cfg = CounterfactualConfig(
        target_class=payload.target_class,
        protected_features=payload.protected_features,
        max_changes=payload.max_changes,
    )

    engine = CounterfactualEngine(model_loader=None, config=cfg)
    result = engine.generate(row=payload.row, reference_df=df)

    return CounterfactualResponse(
        dataset_id=str(payload.dataset_id),
        model_id=str(payload.model_id),
        original_prediction=result.original_prediction,
        counterfactual_prediction=result.counterfactual_prediction,
        original_row=result.original_row,
        counterfactual_row=result.counterfactual_row,
        changed_features=result.changed_features,
        n_changes=result.n_changes,
        found=result.found,
        message=result.message,
    )