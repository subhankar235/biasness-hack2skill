from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    datasets,
    bias,
    reports,
    models,
    remediation,
)

app = FastAPI(title="FairLens API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "FairLens API running"}


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

app.include_router(
    datasets.router,
    prefix="/api/v1/datasets",
    tags=["Datasets"]
)

app.include_router(
    bias.router,
    prefix="/api/v1/bias",
    tags=["Bias"]
)

app.include_router(
    models.router,
    prefix="/api/v1/models",
    tags=["Models"]
)

app.include_router(
    reports.router,
    prefix="/api/v1/report",
    tags=["Reports"]
)

app.include_router(
    remediation.router,
    prefix="/api/v1/remediation",
    tags=["Remediation"]
)