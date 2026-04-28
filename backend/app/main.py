"""
Minimal main.py - with CORS.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ReweighRequest(BaseModel):
    dataset_id: int = 1
    sensitive_feature: str = "gender"
    label_col: str = "loan"

class RemediationJobResponse(BaseModel):
    job_id: str
    strategy: str
    status: str
    message: str

@app.get("/")
def root():
    return {"message": "root works"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/api/v1/remediation/reweigh")
def reweigh(payload: ReweighRequest):
    return RemediationJobResponse(
        job_id=str(uuid.uuid4()),
        strategy="reweigh",
        status="success",
        message="Reweighing complete.",
    )

@app.post("/api/v1/remediation/threshold")
def threshold(payload: BaseModel):
    return RemediationJobResponse(
        job_id=str(uuid.uuid4()),
        strategy="threshold",
        status="success",
        message="Threshold optimization complete.",
    )

@app.post("/api/v1/remediation/smote")
def smote(payload: BaseModel):
    return RemediationJobResponse(
        job_id=str(uuid.uuid4()),
        strategy="smote",
        status="success",
        message="SMOTE complete.",
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