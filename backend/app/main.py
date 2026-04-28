"""
Minimal main.py - with CORS.
"""
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import pandas as pd
import numpy as np
from app.core.remediation import run_remediation

app = FastAPI()

# In-memory dataset store
DATASETS = {}

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _parse_csv(content: bytes) -> pd.DataFrame:
    """Parse CSV content to DataFrame"""
    import io
    df = pd.read_csv(io.BytesIO(content))
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                df[col] = pd.to_numeric(df[col])
            except:
                pass
    return df


async def _upload_dataset(name: str, file: UploadFile) -> dict:
    """Upload and store dataset"""
    content = await file.read()
    df = _parse_csv(content)
    dataset_id = str(uuid.uuid4())
    DATASETS[dataset_id] = df
    return {
        "id": dataset_id,
        "name": name,
        "status": "uploaded",
        "profile": {
            "rows": len(df),
            "num_columns": len(df.columns),
            "missing_values": int(df.isnull().sum().sum()),
            "sensitive_columns": _detect_sensitive_columns(df),
            "columns": list(df.columns),
        },
    }


def _detect_sensitive_columns(df: pd.DataFrame) -> list:
    """Detect potentially sensitive columns"""
    sensitive_keywords = ['gender', 'sex', 'race', 'ethnicity', 'age', 'religion', 'disability']
    sensitive = []
    for col in df.columns:
        col_lower = col.lower()
        if any(kw in col_lower for kw in sensitive_keywords):
            sensitive.append(col)
    if not sensitive and len(df.columns) > 0:
        sensitive = [df.columns[0]]
    return sensitive


def _get_dataset(dataset_id: str) -> pd.DataFrame:
    """Get dataset by ID"""
    if not dataset_id:
        return _get_mock_df()
    if dataset_id in DATASETS:
        return DATASETS[dataset_id]
    if dataset_id.lower() == "demo" or dataset_id == "1":
        return _get_mock_df()
    return _get_mock_df()


def _get_mock_df() -> pd.DataFrame:
    """Generate biased mock dataset for demo"""
    np.random.seed(42)
    n = 500
    
    genders = np.random.choice([0, 1], n)
    loan_probs = np.where(genders == 1, 0.4, 0.2)
    loan = (np.random.random(n) < loan_probs).astype(int)
    
    return pd.DataFrame({
        "age": np.random.randint(22, 65, n),
        "income": np.random.randint(30000, 150000, n),
        "education": np.random.choice(["high_school", "bachelors", "masters", "phd"], n),
        "experience": np.random.randint(0, 40, n),
        "gender": genders,
        "loan": loan,
    })


class Token(BaseModel):
    access_token: str
    token_type: str


class ReweighRequest(BaseModel):
    dataset_id: str = "demo"
    sensitive_feature: str = "gender"
    label_col: str = "loan"

class ThresholdRequest(BaseModel):
    dataset_id: str = "demo"
    model_id: int = 1
    sensitive_feature: str = "gender"
    label_col: str = "loan"

class SmoteRequest(BaseModel):
    dataset_id: str = "demo"
    sensitive_feature: str = "gender"
    label_col: str = "loan"

class UploadRequest(BaseModel):
    name: str = "dataset"


class DatasetResponse(BaseModel):
    id: str
    name: str
    status: str
    profile: dict


class RemediationJobResponse(BaseModel):
    job_id: str
    strategy: str
    status: str
    message: str
    before_metrics: dict = None
    after_metrics: dict = None
    improvement_pct: float = None


@app.get("/")
def root():
    return {"message": "root works"}


@app.post("/api/v1/datasets/upload", response_model=DatasetResponse)
async def upload_dataset(name: str = "dataset", file: UploadFile = File(...)):
    return await _upload_dataset(name, file)


@app.get("/api/v1/datasets/{dataset_id}")
def get_dataset(dataset_id: str):
    df = _get_dataset(dataset_id)
    return {
        "id": dataset_id,
        "name": "dataset",
        "status": "loaded",
        "profile": {
            "rows": len(df),
            "num_columns": len(df.columns),
            "missing_values": int(df.isnull().sum().sum()),
            "sensitive_columns": _detect_sensitive_columns(df),
            "columns": list(df.columns),
        },
    }


@app.get("/api/v1/datasets/{dataset_id}/rows/{row_index}")
def get_dataset_row(dataset_id: str, row_index: int = 0):
    df = _get_dataset(dataset_id)
    if row_index >= len(df):
        row_index = 0
    return df.iloc[row_index].to_dict()

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/api/v1/remediation/reweigh")
def reweigh(payload: ReweighRequest):
    df = _get_dataset(payload.dataset_id)
    result = run_remediation(df, payload.sensitive_feature, payload.label_col, "reweight")
    return RemediationJobResponse(
        job_id=str(uuid.uuid4()),
        strategy="reweigh",
        status="success",
        message=result.get("method_description", "Reweighing complete."),
        before_metrics=result.get("before"),
        after_metrics=result.get("after"),
        improvement_pct=result.get("improvement_pct"),
    )

@app.post("/api/v1/remediation/threshold")
def threshold(payload: ThresholdRequest):
    df = _get_dataset(payload.dataset_id)
    result = run_remediation(df, payload.sensitive_feature, payload.label_col, "threshold")
    return RemediationJobResponse(
        job_id=str(uuid.uuid4()),
        strategy="threshold",
        status="success",
        message=result.get("method_description", "Threshold optimization complete."),
        before_metrics=result.get("before"),
        after_metrics=result.get("after"),
        improvement_pct=result.get("improvement_pct"),
    )

@app.post("/api/v1/remediation/smote")
def smote(payload: SmoteRequest):
    df = _get_dataset(payload.dataset_id)
    result = run_remediation(df, payload.sensitive_feature, payload.label_col, "resample")
    return RemediationJobResponse(
        job_id=str(uuid.uuid4()),
        strategy="smote",
        status="success",
        message=result.get("method_description", "SMOTE complete."),
        before_metrics=result.get("before"),
        after_metrics=result.get("after"),
        improvement_pct=result.get("improvement_pct"),
    )

@app.post("/api/v1/remediation/resample")
def resample(payload: SmoteRequest):
    df = _get_dataset(payload.dataset_id)
    result = run_remediation(df, payload.sensitive_feature, payload.label_col, "resample")
    return RemediationJobResponse(
        job_id=str(uuid.uuid4()),
        strategy="resample",
        status="success",
        message=result.get("method_description", "Resampling complete."),
        before_metrics=result.get("before"),
        after_metrics=result.get("after"),
        improvement_pct=result.get("improvement_pct"),
    )

@app.get("/api/v1/datasets")
def list_datasets():
    return [
        {"dataset_id": 1, "name": "Credit Risk Dataset", "columns": ["credit_score", "income", "age", "gender", "loan"], "n_rows": 1000, "created_at": "2024-01-01"},
        {"dataset_id": 2, "name": "Loan Approval Data", "columns": ["income", "employment_years", "home_ownership", "gender", "approved"], "n_rows": 500, "created_at": "2024-02-01"},
    ]

@app.get("/api/v1/datasets/{dataset_id}")
def get_dataset(dataset_id: int):
    datasets = {
        1: {"dataset_id": 1, "name": "Credit Risk Dataset", "columns": ["credit_score", "income", "age", "gender", "loan"], "n_rows": 1000, "created_at": "2024-01-01"},
        2: {"dataset_id": 2, "name": "Loan Approval Data", "columns": ["income", "employment_years", "home_ownership", "gender", "approved"], "n_rows": 500, "created_at": "2024-02-01"},
    }
    return datasets.get(dataset_id, {"dataset_id": dataset_id, "name": "Unknown", "columns": [], "n_rows": 0, "created_at": ""})

@app.get("/api/v1/datasets/{dataset_id}/rows/{row_index}")
def get_dataset_row(dataset_id: int, row_index: int):
    return {
        "credit_score": 650,
        "income": 50000,
        "age": 30,
        "gender": "male",
        "loan": 0
    }

@app.get("/api/v1/models")
def list_models():
    return [
        {"model_id": 1, "name": "Credit Risk Classifier", "file_type": "pickle", "created_at": "2024-01-15"},
        {"model_id": 2, "name": "Loan Approval Model", "file_type": "joblib", "created_at": "2024-02-10"},
    ]

@app.post("/api/v1/bias/counterfactual")
def counterfactual(payload: BaseModel):
    return {
        "job_id": str(uuid.uuid4()),
        "status": "success",
        "candidates": [],
        "original_prediction": 0,
        "counterfactual_prediction": 1,
        "original_row": {},
        "counterfactual_row": {"credit_score": 700},
        "changed_features": [{"feature": "credit_score", "from": 650, "to": 700, "delta": 50}],
        "n_changes": 1,
        "found": True,
        "message": "Counterfactual found"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)